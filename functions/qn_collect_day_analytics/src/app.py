import base64
import json
import os
import uuid
from datetime import datetime

import boto3
from typing import List, Dict
from aws_lambda_powertools import Logger
from aws_xray_sdk.core import patch_all
from sosw.app import Processor as SoswProcessor, LambdaGlobals, get_lambda_handler

import re

from sosw.components.dynamo_db import DynamoDbClient
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
        },
        'max_input_length': 32,
        'path_prefix':      '/prod',
        'sns_config': {
            'recipient': 'arn:aws:sns:us-west-2:992382783020:quip_nugget_app',  # FIXME Hardcoded
            'subject':   'Day analytics',
        },
    }

    dynamo_db_client: DynamoDbClient = None
    sns_client: SnsManager = None

    def get_config(self, name):
        pass


    def __call__(self, event):
        pass

    def get_config(self, name):
        logger.debug("Bypassing get_config from DDB")
        pass

    def scan_database_and_compile_data(self, st_date: int, en_date: int) -> dict:

        fieldnames = self.config['cnv_dynamo_db_config']['row_mapper'].keys()
        result = {}
        scan_query = {
            'filter_expression': f'date BETWEEN {st_date} AND {en_date}',
            'table_name': self.config['ddb_table_name']
        }
        logger.info(scan_query)

        response = self.get_by_scan_generator(**scan_query)

        for row in response:
            result += row
        return result




    def send_event_to_sns(self, event):
        logger.info("Sending to SNS event: %s", event)
        self.sns_client.send_message(message=json.dumps(event), forse_commit=True)



global_vars = LambdaGlobals()
lambda_handler = get_lambda_handler(Processor, global_vars)
