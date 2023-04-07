import os
import json
import datetime
import logging
import logging.config

from openai_chatgpt import OpenAIGpt
from slack_messanger import SlackMessenger
from daily_arxiv import get_daily_papers, load_config

from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    today, hour = datetime.datetime.today().strftime("%Y-%m-%d %H").split()

    base_dir = os.getenv("WORKSPACE")
    log_config_file = os.path.join(base_dir, os.getenv("LOGGING_CONFIG_FILE"))
    paper_config_file = os.path.join(base_dir, os.getenv("CONFIG_FILE"))
    slack_token_file = os.path.join(base_dir, os.getenv("KEY_FILE"))

    if os.path.exists(log_config_file):
        os.makedirs("log", exist_ok=True)
        with open(log_config_file, 'rt') as f:
            config = json.load(f)
            config["handlers"]["file"].update({"filename": os.path.join(base_dir, "log", f"{today}.log")})

            logging.config.dictConfig(config)
    else:
        logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", datefmt="%m/%d/%Y %H:%M:%S",
                            level=logging.INFO)

    slack = SlackMessenger(test=False,
                           key_path=slack_token_file)
    translator = OpenAIGpt()

    config = load_config(paper_config_file)

    work_dir = os.path.join(base_dir, "already_sent")
    os.makedirs(work_dir, exist_ok=True)

    DB_file_name = os.path.join(work_dir, "papers.txt")
    append_write = "w" if not os.path.exists(DB_file_name) else "a"

    status_check = []
    data_collector = {}
    keywords = config["kv"]

    logging.info("GET daily papers begin")
    for topic, keyword in keywords.items():
        max_results = 20 if topic == "LLM" else config["max_results"]

        logging.info(f"topic = {topic} keyword = {keyword}")
        data = get_daily_papers(topic, query=keyword, max_results=2)
        data_collector.update(data)
        print("\n")

        for idx, papers in enumerate(data.items()):
            paper_number, paper_info = papers
            # paper_number 2303.18181

            topic = paper_info.get("topic", "")
            paper_title = paper_info.get("paper_title", "")
            update_time = paper_info.get("update_time", "")
            first_author = paper_info.get("paper_first_author", "")
            paper_url = paper_info.get("paper_url", "")
            paper_abs = paper_info.get("paper_abstract", "")
            github_url = paper_info.get("github_url", "")

            # 작성용 파일이 이미 있는 경우
            if append_write == "a":
                with open(DB_file_name, "r") as f:
                    file_content = f.read().strip().split()

                # 내부에 이미 있는 경우 == 슬랙에 보내진 경우
                if paper_number in file_content:
                    logging.info("Already sent")
                    continue

            slack_text = {
                "color": "#ab142c" if idx % 2 else "#7c746c",
                "title": f"{paper_title}",
                "text": paper_abs,
                "title_link": f"{paper_url}",
                "footer": f"{first_author} | {update_time} | {topic}",
            }
            if github_url:
                github_button = {"actions": [
                    {
                        "text": ":octocat: Github Repository",
                        "type": "button",
                        "url": f"{github_url}"
                    }]
                }
                slack_text.update(github_button)
            summarised_text = translator.summarize(paper_abs)

            translated_to_ko = False
            if summarised_text:
                slack_text.update({"text": summarised_text})
                translated_to_ko = translator.translate(summarised_text)

                if translated_to_ko:
                    print(translated_to_ko)
                    slack_text.update({"text": translated_to_ko})

            slack_status_code = slack.alarm_msg(slack_text)
            status_check.append(slack_status_code)
            # 슬랙으로 보낸 걸 확인하면 파일에 기록
            if slack_status_code == 200:
                with open(DB_file_name, append_write) as f:
                    f.write(f"\n{paper_number}")

    if status_check:
        slack.send_msg(f"{today}'s {hour}h is Done ! Enjoy with your papers :arxiv:")
    else:
        slack.send_msg(f"Nothing to share {today}'s {hour}h :arxiv:")
