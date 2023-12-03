import logging
import shutil
import sys
import os
import boto3
from botocore.exceptions import NoCredentialsError
from colorama import Fore, Style
from constants import (
    AWS_ACCESS_KEY_ID,
    AWS_S3_BUCKET,
    AWS_SECRET_ACCESS_KEY,
)

# Debug function to print file paths
def print_debug_info(file_path):
    if os.path.exists(file_path):
        logger.info(f"File exists: {file_path}")
    else:
        logger.warning(f"File not found: {file_path}")


# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assuming the first argument is the filename
if len(sys.argv) < 2:
    print("Example usage: python promote.py landscape-2023-12-03T01/50/17.205070Z")
    sys.exit(1)


def extract_datetime(filename):
    # Extract the part after "landscape-" or "portrait-" and keep 'Z' at the end
    datetime_part = filename.split('-', 1)[1]
    # Replace slashes with colons in the time part
    datetime_with_colons = datetime_part.replace('/', ':')
    return datetime_with_colons


def extract_date(datetime_with_colons):
    # Extract only the date part
    date_part = datetime_with_colons.split('T')[0]
    return date_part


input_filename = sys.argv[1]  # Full input filename

the_datetime = extract_datetime(input_filename)  # Full datetime with colons
the_date = extract_date(the_datetime)  # Only the date part

# Local file paths using the full datetime
landscape_file = f"./staging/landscape-{the_datetime}.webp"
portrait_file = f"./staging/portrait-{the_datetime}.webp"
prompt_original_file = f"./staging/original-{the_datetime}.txt"
prompt_landscape_file = f"./staging/landscape-{the_datetime}.txt"
prompt_portrait_file = f"./staging/portrait-{the_datetime}.txt"


# Define static dir paths
dest_images = "./static/images"
dest_prompt = "./static/prompts"


### Copy files into the repo for deployment
def copy_file(src, dest):
    try:
        shutil.copy(src, dest)
        logger.info(f"Copied {src} to {dest}")
    except FileNotFoundError:
        logger.error("The file was not found")


copy_file(landscape_file, f"{dest_images}/landscape.webp")
copy_file(portrait_file, f"{dest_images}/portrait.webp")
copy_file(prompt_original_file, f"{dest_prompt}/original.txt")
copy_file(landscape_file, f"{dest_prompt}/landscape.txt")
copy_file(portrait_file, f"{dest_prompt}/portrait.txt")


### Upload files to AWS S3
def upload_file_to_s3(local_path, bucket, s3_key):
    logger.info(f"{Fore.YELLOW}Uploading file {local_path}...{Style.RESET_ALL}")
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        s3.upload_file(local_path, bucket, s3_key)
        logger.info(f"File {local_path} uploaded to {bucket}/{s3_key}")
    except FileNotFoundError:
        logger.error("The file was not found")
    except NoCredentialsError:
        logger.error("Credentials not available")


upload_file_to_s3(landscape_file, AWS_S3_BUCKET, f"images/{the_date}-landscape.webp")
upload_file_to_s3(portrait_file, AWS_S3_BUCKET, f"images/{the_date}-portrait.webp")
upload_file_to_s3(prompt_original_file, AWS_S3_BUCKET, f"prompts/{the_date}-original.txt")
upload_file_to_s3(prompt_landscape_file, AWS_S3_BUCKET, f"prompts/{the_date}-landscape.txt")
upload_file_to_s3(prompt_portrait_file, AWS_S3_BUCKET, f"prompts/{the_date}-portrait.txt")
