import os

from dotenv import load_dotenv
from openai import OpenAI
from typing import List
from aws_lambda_powertools import Logger
from aws_xray_sdk.core import patch_all
from sosw.app import Processor as SoswProcessor, LambdaGlobals, get_lambda_handler

import re

load_dotenv('key.env')
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)


MAX_INPUT_LENGTH = 32

logger = Logger()
patch_all()

IS_PROD = os.getenv('env') == 'prod'


class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
        'init_clients': [],
        'max_input_length': 32,
        'path_prefix': '/prod',

    }



    def get_config(self, name):
        pass


    def __call__(self, event):

        user_input = self.get_user_input_from_event(event)
        logger.info(f"User input: {user_input}")
        if self.validate_input(user_input):
            joke_result = self.generate_joke(user_input)
            fact_result = self.generate_fact(user_input)
            keyword_result = self.generate_keywords(user_input)
            logger.info(f"Joke: {joke_result} \nInteresting fact: {fact_result} \nKeywords: {keyword_result}")
        else:
            raise ValueError(f"Input is too long. Must be under {12} symbols! Submitted input is {len(user_input)}")


    def get_user_input_from_event(self, event: dict) -> str:
        response = event.get('user_input')
        return response

    def validate_input(self, prompt: str) -> bool:
        return len(prompt) <= self.config['max_input_length']


    def generate_joke(self, prompt: str) -> str:

        enriched_prompt = f"Generate a joke about {prompt}:"
        logger.info(f"Enriched prompt: {enriched_prompt}")
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=enriched_prompt,
            max_tokens=32
        )

        joke_text: str = response.choices[0].text.strip()
        # joke_text = joke_text.replace('\n', ' ')
        last_char = joke_text[-1]
        if last_char not in {".", "!", "?"}:
            joke_text += "..."

        return joke_text


    def generate_fact(self, prompt: str) -> str:

        enriched_prompt = f"Generate a fan fact about {prompt}:"
        logger.info(f"Enriched prompt: {enriched_prompt}")
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=enriched_prompt,
            max_tokens=32
        )

        fact_text: str = response.choices[0].text.strip()
        last_char = fact_text[-1]
        if last_char not in {".", "!", "?"}:
            fact_text += "..."

        return fact_text


    def generate_keywords(self, prompt: str) -> List[str]:

        enriched_prompt = f"Generate related branding keywords for {prompt}:"
        logger.info(f"Enriched prompt: {enriched_prompt}")
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=enriched_prompt,
            max_tokens=32
        )

        keywords_text = response.choices[0].text.strip()
        keywords_text = re.sub(r'\d+\.', '', keywords_text)
        keywords_text = re.sub(r'\s+', ' ', keywords_text)
        keywords_list = keywords_text.strip().split()
        keywords_list = [k.lower() for k in keywords_list]

        return keywords_list


global_vars = LambdaGlobals()
lambda_handler = get_lambda_handler(Processor, global_vars)