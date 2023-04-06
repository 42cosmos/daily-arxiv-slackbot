import re
import json
import yaml
import datetime
import argparse
import requests
import logging


import arxiv

logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", datefmt="%m/%d/%Y %H:%M:%S", level=logging.INFO)

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"


def load_config(config_file: str) -> dict:
    """
    config_file: input config file path
    return: a dict of configuration
    """

    # make filters pretty
    def pretty_filters(**config) -> dict:
        keywords = dict()
        EXCAPE = '"'
        QUOTA = ""  # NO-USE
        OR = "OR"  # TODO

        def parse_filters(filters: list):
            ret = ""
            for idx in range(0, len(filters)):
                filter = filters[idx]
                if len(filter.split()) > 1:
                    ret += EXCAPE + filter + EXCAPE
                else:
                    ret += QUOTA + filter + QUOTA
                if idx != len(filters) - 1:
                    ret += OR
            return ret

        for k, v in config["keywords"].items():
            keywords[k] = parse_filters(v["filters"])
        return keywords

    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        config["kv"] = pretty_filters(**config)
    return config


def get_authors(authors, first_author=False):
    output = str()
    if first_author is False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def sort_papers(papers):
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output


def get_code_link(abs: str) -> str:
    """
    @param abs: str: paper abstract
    @return: str
    """
    matched_github_url = False
    github_base_url = r"https://github\.com/\S+(?=\.)"
    searched_github_url = re.search(github_base_url, abs)

    if searched_github_url:
        matched_github_url = searched_github_url.group()

    return matched_github_url


def get_daily_papers(topic, query="nlp", max_results=2):
    """
    @param topic: str
    @param query: str
    @return paper_with_code: dict
    """
    # output
    content = dict()
    search_engine = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)

    for result in search_engine.results():

        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id
        code_url = base_url + paper_id  # TODO
        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)  # noqa
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category  # noqa
        publish_time = result.published.date()  # noqa
        update_time = result.updated.date()

        logging.info(f"Time = {update_time} title = {paper_title} author = {paper_first_author}")

        # eg: 2108.09112v1 -> 2108.09112
        ver_pos = paper_id.find("v")
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]

        try:
            # source code link
            r = requests.get(code_url).json()
            repo_url = None
            if "official" in r and r["official"]:
                repo_url = r["official"]["url"]
            # TODO: not found, two more chances
            else:
               repo_url = get_code_link(paper_abstract)

            content[paper_key] = {
                "topic": topic,
                "update_time": update_time,
                "paper_title": paper_title,
                "paper_first_author": paper_first_author,
                "paper_id": paper_id,
                "paper_url": paper_url,
                "github_url": repo_url,
                "paper_abstract": paper_abstract
            }
        except Exception as e:
            logging.error(f"exception: {e} with id: {paper_key}")

    return content


def get_all_keyword_papers():
    config = load_config("config.yaml")
    # TODO: use config
    data_collector = {}

    keywords = config["kv"]
    max_results = config["max_results"]

    if config["update_paper_links"] is False:
        logging.info("GET daily papers begin")
        for topic, keyword in keywords.items():
            logging.info(f"topic = {topic} keyword = {keyword}")
            data = get_daily_papers(topic, query=keyword, max_results=max_results)
            data_collector.update(data)
            print("\n")
        logging.info("GET daily papers end")

    return data_collector
