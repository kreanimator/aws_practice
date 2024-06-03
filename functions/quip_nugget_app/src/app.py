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

__author__ = "Valentin Bakin"

MAX_INPUT_LENGTH = 32

logger = Logger()
patch_all()

IS_PROD = os.getenv('env') == 'prod'


class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
        'init_clients':      ['ssm', 'DynamoDb'],
        'dynamo_db_config':  {
            'table_name':      'dev_quip_nugget_data_analytics',
            'row_mapper':      {
                'id':          'S',
                'user_input':  'S',
                'created_at':  'N',
                'usage_count': 'N',
                'jokes':       'L',
                'facts':       'L',
            },
            'required_fields': ['id', 'user_input', 'created_at'],
        },
        'max_input_length':  32,
        'path_prefix':       '/prod',
        'fields_to_extract': ['queryStringParameters.user_input', 'requestContext.time', 'detail.meta'],

    }

    ssm_client: boto3.client = None
    dynamo_db_client: DynamoDbClient = None


    def get_config(self, name):
        pass


    def __call__(self, event):
        user_input = self.get_user_input_from_event(event)
        logger.info(f"User input: {user_input}")
        try:
            if self.validate_input(user_input):
                response = self.generate_response(event, user_input)
                logger.info(f"Response: {response}")
                if response:
                    entry = self.make_entry_from_event(event, response)
                    if not self.find_prompt(entry, response):
                        self.send_event_to_ddb(entry)
                    else:
                        self.update_data_in_ddb(entry, response)

                return response
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


    def make_entry_from_event(self, event, response):

        rec_id = str(uuid.uuid4())

        event_time = event.get('requestContext', {}).get('time')
        created_at = datetime.strptime(event_time, "%d/%b/%Y:%H:%M:%S %z").timestamp()

        user_input = event.get('queryStringParameters', {}).get('user_input')
        meta = event.get('requestContext', {}).get('http')
        jokes = []
        facts = []
        jokes.append(response['joke'])
        facts.append(response['fact'])

        entry = {
            'id':          rec_id,
            'created_at':  created_at,
            'user_input':  user_input,
            'usage_count': 1,
            'meta':        meta,
            'jokes':       jokes,
            'facts':       facts
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


    def find_prompt(self, entry: dict, response: dict) -> None:
        user_input = entry.get('user_input')

        if user_input:
            table_name = self.config['dynamo_db_config']['table_name']
            index_name = 'user_input'
            keys = {'user_input': user_input}
            comparisons = {'user_input': '='}

            is_found = self.dynamo_db_client.get_by_query(keys=keys, table_name=table_name, comparisons=comparisons,
                                                          index_name=index_name)
            logger.debug(f"Prompt result: {is_found}")
            if is_found:
                logger.debug("Found existing entry by user_input: %s", is_found)
                return True

        return False


    def update_data_in_ddb(self, entry: dict, response: dict) -> None:
        try:
            user_input = entry.get('user_input')
            query_result = self.dynamo_db_client.get_by_query(
                keys={'user_input': user_input},
                table_name=self.config['dynamo_db_config']['table_name'],
                index_name='user_input'
            )

            if query_result:
                existing_item = query_result[0]
                item_id = existing_item['id']

                scan_query = {
                    'filter_expression': f'id = {item_id}',
                    'table_name':        self.config['dynamo_db_config']['table_name'],
                    'index_name':        'user_input'
                }

                existing_items = list(self.get_by_scan_generator(**scan_query))
                logger.info(f"Existing items {existing_items}")

                if existing_items:
                    existing_item = existing_items[0]

                    usage_count = int(existing_item.get('usage_count', 0)) + 1
                    existing_item['usage_count'] = usage_count

                    jokes = existing_item.get('jokes', [])
                    facts = existing_item.get('facts', [])
                    logger.info(f"Existing jokes: {jokes} Existing facts: {facts}")
                    if 'joke' in response:
                        jokes.append(response['joke'])
                    if 'fact' in response:
                        facts.append(response['fact'])

                    existing_item['jokes'] = jokes
                    existing_item['facts'] = facts
                    logger.info(
                        f"After append Existing jokes: {existing_item.get('jokes', [])} Existing facts: {existing_item.get('facts', [])}")

                    attributes_to_update = {
                        'jokes':       existing_item['jokes'],
                        'facts':       existing_item['facts'],
                        'usage_count': existing_item['usage_count']
                    }

                    self.dynamo_db_client.update(
                        keys={'id': item_id},
                        attributes_to_update=attributes_to_update,
                        table_name=self.config['dynamo_db_config']['table_name']
                    )
                    logger.info(f"Successfully updated entry with id '{item_id}': {entry}")
                else:
                    logger.warning(f"No full entry found with id '{item_id}' in the table.")
            else:
                logger.warning(f"No entry found with user_input '{user_input}' in the index.")
        except Exception as e:
            logger.error(f"Error updating entry: {e}")


    def get_by_scan_generator(self, attrs=None, table_name=None, index_name=None, fetch_all_fields=None,
                              consistent_read=None, filter_expression=None):
        """
        Scans a table. Don't use this method if you want to select by keys. It is SLOW compared to get_by_query.
        Careful - don't make queries of too many items, this could run for a long time.
        Same as get_by_scan, but yields parts of the results.
        """
        ddbc = self.dynamo_db_client
        fetch_all_fields = fetch_all_fields if fetch_all_fields is not None else False

        response_iterator = self._build_scan_iterator(attrs, table_name, index_name, consistent_read, filter_expression)
        logger.debug(f"Paginating response_iterator: {response_iterator}")

        for page in response_iterator:
            self.stats['dynamo_scan_queries'] += 1
            logger.debug(f"Processing page with {len(page['Items'])} rows")
            for row in page['Items']:
                yield ddbc.dynamo_to_dict(row, fetch_all_fields=fetch_all_fields)


    def _build_scan_iterator(self, attrs=None, table_name=None, index_name=None, consistent_read=None,
                             filter_expression=None):
        ddbc = self.dynamo_db_client
        table_name = ddbc._get_validate_table_name(table_name)

        query_args = {
            'TableName':                 table_name,
            'Select':                    'ALL_ATTRIBUTES',
            'ExpressionAttributeValues': {}
        }

        if filter_expression:
            expr, values = ddbc._parse_filter_expression(filter_expression)
            query_args['FilterExpression'] = expr
            query_args['ExpressionAttributeValues'].update(values)

        if consistent_read is not None:
            logger.debug(f"Forcing ConsistentRead to: {consistent_read}")
            query_args['ConsistentRead'] = consistent_read

        logger.debug(f"Scanning DynamoDB with query args: {query_args}")

        paginator = ddbc.dynamo_client.get_paginator('scan')
        response_iterator = paginator.paginate(**query_args)

        return response_iterator


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
