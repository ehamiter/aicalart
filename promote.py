import argparse
import datetime
import logging
import os.path
import random
import time
from base64 import b64decode
from io import BytesIO
from textwrap import dedent

import boto3
from botocore.exceptions import NoCredentialsError
from colorama import Fore, Style
from constants import (
    AICALART_OPENAI_KEY,
    AWS_ACCESS_KEY_ID,
    AWS_S3_BUCKET,
    AWS_SECRET_ACCESS_KEY,
    GPT_MODEL,
    HOLIDAYS,
    IMAGE_MODEL,
    SCOPES,
    SILLY_DAYS,
    STYLES,
)
from gnews import GNews
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from icecream import install
from openai import BadRequestError, OpenAI
from PIL import Image, ImageDraw
from tqdm import tqdm

import shutil
import boto3
from botocore.exceptions import NoCredentialsError
import logging
from colorama import Fore, Style
import os
import datetime
import sys

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assuming the first argument is the filename
if len(sys.argv) < 2:
    print("Example usage: python promote.py landscape-2023-12-03T01/50/17.205070Z")
    sys.exit(1)

input_filename = sys.argv[1]
datetime_with_colons = input_filename.replace('/', ':')
_datetime = datetime_with_colons.split('-')[1]  # Extract datetime part
date = _datetime[:10]  # Extract YYYY-MM-DD part

# Define image file paths for .gitignored /staging
landscape_file = f"./staging/landscape-{datetime}.png"
portrait_file = f"./staging/portrait-{datetime}.png"

# ...and prompt file paths
prompt_original_file = f"./staging/original-{datetime}.txt"
prompt_landscape_file = f"./staging/landscape-{datetime}.txt"
prompt_portrait_file = f"./staging/portrait-{datetime}.txt"

# Define static dir paths
dest_images = "./static/images"
dest_prompt = "./static/prompt"


### Copy files into the repo for deployment
def copy_file(src, dest):
    try:
        shutil.copy(src, dest)
        logger.info(f"Copied {src} to {dest}")
    except FileNotFoundError:
        logger.error("The file was not found")

# Copy images
copy_file(landscape_file, f"{dest_images}/landscape.png")
copy_file(portrait_file, f"{dest_images}/portrait.png")

# ...and prompts
copy_file(prompt_original_file, f"{dest_prompt}/original.txt")
copy_file(landscape_file, f"{dest_prompt}/landscape.txt")
copy_file(portrait_file, f"{dest_prompt}/portrait.txt")


### Upload files to AWS S3
def upload_file_to_s3(local_path, bucket, s3_key):
    logger.info(f"{Fore.YELLOW}Uploading file {local_path}...{Style.RESET_ALL}")
    try:
        s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        s3.upload_file(local_path, bucket, s3_key)
        logger.info(f"File {local_path} uploaded to {bucket}/{s3_key}")
    except FileNotFoundError:
        logger.error("The file was not found")
    except NoCredentialsError:
        logger.error("Credentials not available")

# Upload image files to S3
upload_file_to_s3(landscape_file, AWS_S3_BUCKET, f"images/{date}-landscape.png")
upload_file_to_s3(portrait_file, AWS_S3_BUCKET, f"images/{date}-portrait.png")

# Upload prompts to S3
upload_file_to_s3(prompt_original_file, AWS_S3_BUCKET, f"prompts/{date}-original.txt")
upload_file_to_s3(prompt_landscape_file, AWS_S3_BUCKET, f"prompts/{date}-landscape.txt")
upload_file_to_s3(prompt_portrait_file, AWS_S3_BUCKET, f"promtps/{date}-portrait.txt")
