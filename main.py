import os
import json
import datetime
import time
import logging
import logging.config
import traceback

from openai_chatgpt import OpenAIGpt
from slack_messanger import SlackMessenger
from daily_arxiv import get_daily_papers, load_config

from dotenv import load_dotenv


def handle_exception(exception, sleep_time=300):
    logging.error(f"{exception.__class__.__name__}: {exception}")
    traceback.print_exc()
    time.sleep(sleep_time)


def main():
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

        data = None
        while data is None:
            try:
                data = get_daily_papers(topic, query=keyword, max_results=max_results)

            except AttributeError as attr_err:
                handle_exception(attr_err)

            except KeyError as key_err:
                handle_exception(key_err)

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

            if paper_abs:
                summarised_text = None
                for _ in range(5):
                    summarised_text_result = translator.summarise(paper_abs)
                    if summarised_text_result == "Rate Limit Error":
                        logging.info("Rate Limit Error in Summarisation. Wait one minute and then restart.")
                        slack.send_msg(f"Rate Limit Error in Summarisation. Wait one minute and then restart. :arxiv:")
                        time.sleep(60)
                        continue
                    elif summarised_text_result == "API Error":
                        logging.info("API Error. Stopping the program.")
                        slack.send_msg("API Error occurred. Stopping the program.")
                        raise SystemExit()

                    else:
                        summarised_text = summarised_text_result
                        break

                if summarised_text:
                    translated_to_ko = None
                    for _ in range(5):
                        translated_to_ko_result = translator.translate(summarised_text)
                        if translated_to_ko_result == "Rate Limit Error":
                            logging.info("Rate Limit Error in Translation. Wait one minute and then restart.")
                            slack.send_msg(
                                f"Rate Limit Error in Translation. Wait one minute and then restart. :arxiv:")
                            time.sleep(60)
                            continue

                        elif translated_to_ko_result == "API Error":
                            logging.info("API Error. Stopping the program.")
                            slack.send_msg("API Error occurred. Stopping the program.")
                            raise SystemExit()

                        else:
                            translated_to_ko = translated_to_ko_result
                            break

                    if translated_to_ko:
                        logging.info("Summarisation and Translation Success")
                        slack_text.update({"text": translated_to_ko})
                    else:  # 번역 실패
                        logging.info("Only Translation Success")
                        slack_text.update({"text": summarised_text})
                else:  # 요약 실패
                    logging.info("All Failed")
                    slack_text.update({"text": paper_abs})
            else:
                logging.info("No Abstract found.")
                slack_text.update({"text": "No Abstract found."})

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


if __name__ == "__main__":
    main()
