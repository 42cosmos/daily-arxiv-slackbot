import os
import openai
import argparse
from dotenv import load_dotenv


class OpenAIGpt:
    def __init__(self):
        load_dotenv()
        _api_key = os.getenv("OPENAI_API_KEY")
        assert _api_key is not None, "Please set OPENAI_API_KEY in .env file"
        openai.api_key = os.getenv("OPENAI_API_KEY", "")

    @staticmethod
    def translate(text):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates English to Korean."},
                {"role": "user", "content": f'Translate the following English text to Korean: "{text}"'}
            ]
        )
        try:
            return completion['choices'][0]['message']['content']
        except:
            return False

    @staticmethod
    def summarize(text):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful research paper assistant that makes awesome summarised text."},
                {"role": "user",
                 "content": f'Please summarize the following text into 3 sentences and extract only the essentials what paper authors do: "{text}"'}
            ]
        )
        try:
            return completion['choices'][0]['message']['content']
        except:
            return False
