import json
import os

import boto3
from fastapi import FastAPI, HTTPException
from quip_nugget import generate_joke, generate_fact, generate_keywords, validate_input
from aws_lambda_powertools import Logger
from aws_xray_sdk.core import patch_all
from sosw.app import Processor as SoswProcessor, LambdaGlobals, get_lambda_handler

logger = Logger()
patch_all()

IS_PROD = os.getenv('env') == 'prod'

app = FastAPI()
MAX_INPUT_LENGTH = 32


class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
        'init_clients': ['s3'],
        's3_config':    {
            'bucket_name': 'img-converter-test',
            'path':        'img/',

            'image_types': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'],
        },
        'path_prefix':  '/prod',
    }

    s3_client: boto3.client = None


    def get_config(self, name):
        pass


    def __call__(self, event):
        path = event['path']
        query_params = event['queryStringParameters'] if 'queryStringParameters' in event else {}
        prompt = query_params.get('prompt', '')

        if path == '/generate_joke':
            return self.generate_joke_response(prompt)
        elif path == '/generate_fact':
            return self.generate_fact_response(prompt)
        elif path == '/generate_keywords':
            return self.generate_keywords_response(prompt)
        elif path == '/generate_data':
            return self.generate_data_response(prompt)
        else:
            return {
                'statusCode': 404,
                'body':       json.dumps({'message': 'Not Found'})
            }


    def generate_joke_response(self, prompt: str) -> dict:
        if validate_input(prompt):
            joke = generate_joke(prompt)
            return {
                'statusCode': 200,
                'body':       json.dumps({'joke': joke, 'fact': None, 'keywords': []})
            }
        else:
            return {
                'statusCode': 400,
                'body':       json.dumps(
                    {'message': f'Invalid input length! Should be no more than {MAX_INPUT_LENGTH}'})
            }

    def generate_fact_response(self, prompt: str) -> dict:
        if validate_input(prompt):
            fact = generate_fact(prompt)
            return {
                'statusCode': 200,
                'body':       json.dumps({'joke': None, 'fact': fact, 'keywords': []})
            }
        else:
            return {
                'statusCode': 400,
                'body':       json.dumps(
                    {'message': f'Invalid input length! Should be no more than {MAX_INPUT_LENGTH}'})
            }

    def generate_keywords_response(self, prompt: str) -> dict:
        if validate_input(prompt):
            keywords = generate_keywords(prompt)
            return {
                'statusCode': 200,
                'body':       json.dumps({'joke': None, 'fact': None, 'keywords': keywords})
            }
        else:
            return {
                'statusCode': 400,
                'body':       json.dumps(
                    {'message': f'Invalid input length! Should be no more than {MAX_INPUT_LENGTH}'})
            }

    def generate_data_response(self, prompt: str) -> dict:
        if validate_input(prompt):
            joke = generate_joke(prompt)
            fact = generate_fact(prompt)
            keywords = generate_keywords(prompt)
            return {
                'statusCode': 200,
                'body':       json.dumps({'joke': joke, 'fact': fact, 'keywords': keywords})
            }
        else:
            return {
                'statusCode': 400,
                'body':       json.dumps(
                    {'message': f'Invalid input length! Should be no more than {MAX_INPUT_LENGTH}'})
            }


#   uvicorn quip_nugget_api:src --reload