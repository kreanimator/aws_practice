import base64
import json
import os
import uuid
from datetime import datetime
from urllib.parse import parse_qs

import boto3
from openai import OpenAI
from typing import List, Dict
from aws_lambda_powertools import Logger
from aws_xray_sdk.core import patch_all
from sosw.app import Processor as SoswProcessor, LambdaGlobals, get_lambda_handler

import re

from sosw.components.dynamo_db import DynamoDbClient
from sosw.components.helpers import recursive_matches_extract
from sosw.components.sns import SnsManager

MAX_INPUT_LENGTH = 32

logger = Logger()
patch_all()

IS_PROD = os.getenv('env') == 'prod'


class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
        'init_clients':     ['ssm', 'DynamoDb', 'sns'],
        'dynamo_db_config': {
            'table_name': 'dev_quip_nugget_data_analytics',
            'row_mapper': {
                'id':          'S',
                'prompt':      'S',
                'created_at':  'N',
                'usage_count': 'N',
            },
            'required_fields': ['id', 'prompt', 'created_at'],
        },
        'max_input_length': 32,
        'path_prefix':      '/prod',
        'sns_config': {
            'recipient': 'arn:aws:sns:us-west-2:992382783020:quip_nugget_app',  # FIXME Hardcoded
            'subject':   'Day analytics',
        },
        'fields_to_extract': ['queryStringParameters.user_input', 'requestContext.time', 'detail.meta'],

    }

    ssm_client: boto3.client = None
    dynamo_db_client: DynamoDbClient = None
    sns_client: SnsManager = None

    def get_config(self, name):
        pass


    def __call__(self, event):
        user_input = self.get_user_input_from_event(event)
        logger.info(f"User input: {user_input}")
        try:
            if self.validate_input(user_input):
                result = self.generate_response(event, user_input)
                if result:
                    response = self.make_entry_from_event(event)
                    self.find_prompt(response)

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
        logger.debug(f'Result: {result}')
        return result


    def get_user_input_from_event(self, event: dict) -> str:
        query_params = event.get('queryStringParameters')
        if query_params:
            user_input = query_params.get('user_input', '')
            if user_input:
                user_input_str = user_input
                logger.debug(f"user_input: {user_input_str}")
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
            max_tokens=96
        )

        joke_text: str = response.choices[0].text.strip()
        joke_text = joke_text.replace('\n', ' ')
        last_char = joke_text[-1]
        if last_char not in {".", "!", "?"}:
            joke_text += "..."

        return joke_text


    def make_entry_from_event(self, event):

        rec_id = str(uuid.uuid4())

        event_time = event.get('requestContext', {}).get('time')
        created_at = datetime.strptime(event_time, "%d/%b/%Y:%H:%M:%S %z").timestamp()

        user_input = event.get('queryStringParameters', {}).get('user_input')
        meta = event.get('requestContext', {}).get('http')

        entry = {
            'id':         rec_id,
            'created_at': created_at,
            'user_input': user_input,
            'usage_count': 1,
            'meta':       meta
        }

        entry = self.validate_entry(entry)
        return entry

    def get_parameter(self, parameter_name):
        response = self.ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        logger.debug(f'Key: {response}')
        return response['Parameter']['Value']


    def generate_fact(self, prompt: str, client) -> str:

        enriched_prompt = f"Generate a fan fact about {prompt}:"
        logger.debug(f"Enriched prompt: {enriched_prompt}")
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
        logger.debug(f"Enriched prompt: {enriched_prompt}")
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=enriched_prompt,
            max_tokens=64
        )

        keywords_text = response.choices[0].text.strip()
        keywords_text = re.sub(r'\d+\.', '', keywords_text)
        keywords_text = re.sub(r'\s+', ' ', keywords_text)
        keywords_list = keywords_text.strip().split()
        keywords_list = [k.lower() for k in keywords_list]

        return keywords_list


    def find_prompt(self, entry: dict) -> None:
        user_input = entry.get('user_input')

        if user_input:
            table_name = self.config['dynamo_db_config']['table_name']
            index_name = 'user_input'
            keys = {'user_input': user_input}
            comparisons = {'user_input': '='}

            result = self.dynamo_db_client.get_by_query(keys=keys, table_name=table_name, comparisons=comparisons,
                                                        index_name=index_name)
            logger.debug(f"Prompt result: {result}")
            if result:
                logger.debug("Found existing entry by user_input: %s", result)
                existing_entry = result[0]
                usage_count = int(existing_entry.get('usage_count', 0))
                usage_count += 1
                existing_entry['usage_count'] = usage_count
                entry.update(existing_entry)

        self.send_event_to_ddb(entry)


    def send_event_to_sns(self, event):
        logger.info("Sending to SNS event: %s", event)
        self.sns_client.send_message(message=json.dumps(event), forse_commit=True)


    def send_event_to_ddb(self, entry):
        try:
            # Put the row into DynamoDB
            self.dynamo_db_client.put(entry)
            logger.info("Successfully inserted item into DynamoDB: %s", entry['id'])
        except Exception as e:
            logger.critical(e)


    def validate_entry(self, entry):
        logger.info(entry)
        return entry


global_vars = LambdaGlobals()
lambda_handler = get_lambda_handler(Processor, global_vars)
