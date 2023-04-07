import os
import json
import argparse
import datetime

import logging
import logging.config
from dotenv import load_dotenv

import openai

logger = logging.getLogger("openai").setLevel(logging.INFO)


class OpenAIGpt:
    def __init__(self):
        load_dotenv()
        self._api_key = os.getenv("OPENAI_API_KEY")
        assert self._api_key is not None, "Please set OPENAI_API_KEY in .env file"
        openai.api_key = self._api_key

    def request(self, request_data: list, model="gpt-3.5-turbo"):
        request_data = [{"role": role, "content": content} for role, content in request_data]
        completion = openai.ChatCompletion.create(
            model=model,
            messages=request_data,
        )
        try:
            return completion['choices'][0]['message']['content']

        except Exception as e:
            logger.exception(f"Error: {e}")
            return False
        except openai.error.APIError as e:
            logger.exception(f"API Error: 502 Bad Gateway")
            return False

    def translate(self, text):
        prompt = f'Translate the following English text to Korean: {text}'
        request_data = [("system", "You are a helpful assistant that translates English to Korean."), ("user", text)]
        return self.request(request_data=request_data)

    def summarize(self, text):
        prompt = f'Please summarize the following text into 3 sentences and extract only the essentials what paper ' \
                 f'authors do: {text} '
        request_data = [("system", "You are a helpful research paper assistant that makes awesome summarised text."),
                        ("user", prompt)]
        return self.request(request_data=request_data)
