import os
from datetime import datetime, timedelta

from aws_lambda_powertools import Logger
from aws_xray_sdk.core import patch_all
from sosw.app import Processor as SoswProcessor, LambdaGlobals, get_lambda_handler
from sosw.components.dynamo_db import DynamoDbClient
from sosw.components.sns import SnsManager

__author__ = "Valentin Bakin"


logger = Logger()
patch_all()

IS_PROD = os.getenv('env') == 'prod'


class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
        'init_clients':     ['Sns', 'DynamoDb'],
        'path_prefix':      '/prod',
        'sns_config':       {
            'recipient': 'arn:aws:sns:us-west-2:992382783020:quip_nugget_app',  # FIXME Hardcoded
            'subject':   'Day analytics',
        },
        'dynamo_db_config': {
            'table_name':      'quip_nugget_data_analytics' if IS_PROD else 'dev_quip_nugget_data_analytics',
            'row_mapper':      {
                'id':          'S',
                'user_input':  'S',
                'created_at':  'N',
                'usage_count': 'N',
            },
            'required_fields': ['id', 'prompt', 'created_at', 'usage_count']
        }
    }
    dynamo_db_client: DynamoDbClient = None
    sns_client: SnsManager = None


    def get_config(self, name):
        logger.debug("Bypassing get_config from DDB")
        pass


    def __call__(self, event):
        dates = self.get_time_range()
        compiled_data = self.scan_database_and_compile_data(*dates)
        self.send_event_to_sns(compiled_data)


    @staticmethod
    def get_time_range():
        st_date = int((datetime.now() - timedelta(hours=24)).timestamp())
        en_date = int(datetime.now().timestamp())
        return st_date, en_date


    def scan_database_and_compile_data(self, st_date: int, en_date: int) -> str:
        compiled_data = {}
        scan_query = {
            'filter_expression': f'created_at BETWEEN {st_date} AND {en_date}',
            'table_name':        self.config['dynamo_db_config']['table_name']
        }
        logger.info(f"Scan query: {scan_query}")

        response = self.get_by_scan_generator(**scan_query)
        logger.info(f"Response generator created: {response}")

        for row in response:
            logger.info(f"Row: {row}")
            try:
                user_input = row['user_input']
                created_at = datetime.utcfromtimestamp(int(row['created_at'])).strftime('%H:%M, %d %b %Y')
                usage_count = row['usage_count']
                if user_input in compiled_data:
                    compiled_data[user_input].append((created_at, usage_count))
                else:
                    compiled_data[user_input] = [(created_at, usage_count)]
            except KeyError as e:
                logger.error(f"KeyError: {e}, Row: {row}")
                continue

        sorted_data = sorted(compiled_data.items(), key=lambda item: sum(count for _, count in item[1]), reverse=True)
        message_lines = []
        for i, (user_input, data) in enumerate(sorted_data):
            for created_at, count in data:
                message_lines.append(f"{i + 1}. {user_input} - used {count} times since {created_at}")
        message = "\n".join(message_lines)

        return message


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


    def send_event_to_sns(self, message):
        logger.info("Successfully sent message to SNS. Message:%s", message)
        self.sns_client.send_message(message=message, subject=self.config['sns_config']['subject'], forse_commit=True)


global_vars = LambdaGlobals()
lambda_handler = get_lambda_handler(Processor, global_vars)
