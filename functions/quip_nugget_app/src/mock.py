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



class Processor(SoswProcessor):
    DEFAULT_CONFIG = {
    }



    def get_config(self, name):
        pass


    def __call__(self, event):
        pass

