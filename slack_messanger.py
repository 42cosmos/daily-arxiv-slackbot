import os
import sys
import json
import slack_sdk
import requests


def load_secret(name, key_path=None):
    if not key_path:
        key_path = os.getcwd()
    with open(key_path, "r") as f:
        secret = json.load(f)[name]
    return secret


class SlackMessenger:
    def __init__(self, test=False, key_path=None):
        name = "TEST_SLACK" if test else "SLACK"
        secret = load_secret(name, key_path=key_path)
        self._channel = secret["CHANNEL"]
        self._token = secret["ACCESSED_TOKEN"]
        self._web_hook_url = secret["WEB_HOOK_URL"]
        self._client = slack_sdk.WebClient(token=self._token)

    def send_file(self, file_path, file_title):
        response = self._client.files_upload(
            channels=self._channel,
            file=file_path,
            title=file_title,
            filetype='pdf'
        )

    def send_msg(self, slack_text):
        slack_text = make_slack_format(slack_text)
        response = requests.post(self._web_hook_url, data=slack_text, headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            raise ValueError(response.status_code, response.text)

    def alarm_msg(self, slack_attachment_text: dict):
        """
        :param slack_attachment_text:
        you must follow this rule
        https://api.slack.com/messaging/composing/layouts#building-attachments
        :return: status code
        """
        slack_text = self._make_alarm_format(slack_attachment_text)
        response = requests.post(self._web_hook_url, data=slack_text, headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            raise ValueError(response.status_code, response.text)

        return response.status_code

    @staticmethod
    def _make_alarm_format(attachment_dict: dict):
        """
        :param title:
        :param text:
        :param footer:
        :param colour: Hex colour code ex, #000000
        :return:
        """
        # TODO: Attachment is legacy, Change to Block Builder
        # https://app.slack.com/block-kit-builder/

        # attachment fields described here
        # https://api.slack.com/reference/messaging/attachments#legacy_fields
        result = {"attachments": [attachment_dict]}

        return json.dumps(result)


def make_slack_format(text: str):
    return json.dumps({"text": text})
