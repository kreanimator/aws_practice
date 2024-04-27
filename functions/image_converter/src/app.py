import os
import io
from PIL import Image
import boto3

from aws_lambda_powertools import Logger
from aws_xray_sdk.core import patch_all

from sosw.app import Processor as SoswProcessor, get_lambda_handler, LambdaGlobals

logger = Logger()
patch_all()

IS_PROD = os.getenv('env') == 'prod'  # TEMPORARY


class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
        'init_clients': ['s3'],
        's3_config':    {
            'bucket_name': 'test',
            'path':        '/img',

            'image_types': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'],
        },
        'path_prefix':  '/prod',
    }

    s3_client: boto3.client = None


    def get_config(self, name):
        pass


    def __call__(self, event):

        bucket_name = self.config['s3_config']['bucket_name']
        path = self.config['s3_config']['path']
        objects = self.list_s3_objects(bucket_name,path)

        for obj in objects:
            key = obj['Key']
            file_format = key.split('.')[-1].lower()
            if file_format not in self.config['s3_config']['image_types']:
                continue

            image_data = self.download_from_s3(bucket_name, key)

            if file_format != 'webp':
                webp_data = self.convert_to_webp(image_data)
                new_key = key.rsplit('.', 1)[0] + '.webp'
                self.upload_to_s3(bucket_name, new_key, webp_data)


    def convert_to_webp(self, image_data):
        image = Image.open(io.BytesIO(image_data))
        output = io.BytesIO()
        image.save(output, format="WEBP")
        return output.getvalue()

    def list_s3_objects(self, bucket_name, path):
        response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=path)
        return response.get('Contents', [])

    def download_from_s3(self, bucket_name, key):
        response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
        return response['Body'].read()

    def upload_to_s3(self, bucket_name, key, data):
        self.s3_client.put_object(Bucket=bucket_name, Key=key, Body=data)