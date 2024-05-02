import base64
import json
import os
from urllib.parse import parse_qs

import boto3
from openai import OpenAI
from typing import List
from aws_lambda_powertools import Logger
from aws_xray_sdk.core import patch_all
from sosw.app import Processor as SoswProcessor, LambdaGlobals, get_lambda_handler

import re

MAX_INPUT_LENGTH = 32

logger = Logger()
patch_all()

IS_PROD = os.getenv('env') == 'prod'


class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
        'init_clients':     ['ssm'],
        'max_input_length': 32,
        'path_prefix':      '/prod',

    }

    ssm_client: boto3.client = None


    def get_config(self, name):
        pass


    def __call__(self, event):

        user_input = self.get_user_input_from_event(event)
        logger.info(f"User input: {user_input}")
        try:
            if self.validate_input(user_input):
                result = self.generate_response(event, user_input)
                return result
            else:
                input_length = self.config['max_input_length']
                return f'Your input is more than {input_length}'
        except ValueError as ve:
            return {
                'statusCode': 400,
                'body':       json.dumps({'message': str(ve)})
            }


    def generate_response(self, event: dict, prompt: str) -> dict:
        api_key = self.get_parameter('OPENAI_API_KEY')
        client = OpenAI(api_key=api_key)
        path_parts = event['rawPath'].split('/')
        path = path_parts[-1]
        result = {}

        if path == 'generate_joke':
            result['joke'] = self.generate_joke(prompt, client)
        elif path == 'generate_fact':
            result['fact'] = self.generate_fact(prompt, client)
        elif path == 'generate_keywords':
            result['keywords'] = self.generate_keywords(prompt, client)
        elif path == 'generate_data':
            result['joke'] = self.generate_joke(prompt, client)
            result['fact'] = self.generate_fact(prompt, client)
            result['keywords'] = self.generate_keywords(prompt, client)
        else:
            return {
                'statusCode': 404,
                'body':       json.dumps({'message': 'Not Found'})
            }
        logger.info(f'Result: {result}')
        return result


    def get_user_input_from_event(self, event: dict) -> str:
        query_params = event.get('queryStringParameters')
        if query_params:
            user_input = query_params.get('user_input', '')
            if user_input:
                user_input_str = user_input
                logger.info(f"user_input: {user_input_str}")
                return user_input_str
        logger.info("user_input is empty")
        return ""
    # def get_user_input_from_event(self, event: dict) -> str:
    #     body = event.get('body')
    #     if body:
    #         decoded_body = base64.b64decode(body).decode('utf-8')
    #         logger.info(f"Decoded body: {decoded_body}")
    #         query_params = parse_qs(decoded_body)
    #         user_input = query_params.get('user_input', '')
    #         if user_input:
    #             user_input_str = user_input[0]
    #             logger.info(f"user_input: {user_input_str}")
    #             return user_input_str
    #     logger.info("user_input is empty")
    #     return ""


    def validate_input(self, prompt: str) -> bool:
        return len(prompt) <= self.config['max_input_length']


    def generate_joke(self, prompt: str, client) -> str:

        enriched_prompt = f"Generate a joke about {prompt}:"
        logger.info(f"Enriched prompt: {enriched_prompt}")
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=enriched_prompt,
            max_tokens=32
        )

        joke_text: str = response.choices[0].text.strip()
        joke_text = joke_text.replace('\n', ' ')
        last_char = joke_text[-1]
        if last_char not in {".", "!", "?"}:
            joke_text += "..."

        return joke_text


    def get_parameter(self, parameter_name):
        response = self.ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        # logger.info(f'Key: {response}')
        return response['Parameter']['Value']


    def generate_fact(self, prompt: str, client) -> str:

        enriched_prompt = f"Generate a fan fact about {prompt}:"
        logger.info(f"Enriched prompt: {enriched_prompt}")
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=enriched_prompt,
            max_tokens=150
        )

        fact_text: str = response.choices[0].text.strip()
        last_char = fact_text[-1]
        if last_char not in {".", "!", "?"}:
            fact_text += "..."

        return fact_text


    def generate_keywords(self, prompt: str, client) -> List[str]:

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
