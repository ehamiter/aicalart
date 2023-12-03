import logging
import sys
import boto3
from botocore.exceptions import NoCredentialsError
from colorama import Fore, Style
from constants import (
    AWS_ACCESS_KEY_ID,
    AWS_S3_BUCKET,
    AWS_SECRET_ACCESS_KEY,
)


class CustomFormatter(logging.Formatter):
    format_dict = {
        logging.DEBUG: Fore.CYAN + "[DEBUG] %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "[INFO] %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "[WARNING] %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "[ERROR] %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.MAGENTA + "[CRITICAL] %(message)s" + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.format_dict.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# console handler for logging
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


if len(sys.argv) < 2:
    print('Example usage: python promote.py landscape-2023-12-03T01/50/17.205070Z')
    sys.exit(1)


def extract_datetime(filename):
    # Extract the part after "landscape-" or "portrait-" and keep 'Z' at the end
    datetime_part = filename.split('-', 1)[1]
    # Replace slashes with colons in the time part
    datetime_with_colons = datetime_part.replace('/', ':')
    return datetime_with_colons

def upload_file_to_s3(local_path, bucket, s3_key):
    logger.info(f"Uploading file {local_path}...")

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        # Set content-type so we're not downloading objects
        if local_path.endswith('.txt'):
            extra_args = {'ContentType': 'text/plain'}
        elif local_path.endswith('.webp'):
            extra_args = {'ContentType': 'image/webp'}
        else:
            extra_args = {}

        # Upload the file with specified content type
        s3.upload_file(local_path, bucket, s3_key, ExtraArgs=extra_args)

        logger.info(f"File {local_path} uploaded to {bucket}/{s3_key}")

    except FileNotFoundError:
        logger.error("The file was not found")
    except NoCredentialsError:
        logger.error("Credentials not available")

input_filename = sys.argv[1]
the_datetime = extract_datetime(input_filename)
the_date = the_datetime.split('T')[0]

# Local file paths using the full datetime so you can generate more than one per day
landscape_file = f"./staging/landscape-{the_datetime}.webp"
portrait_file = f"./staging/portrait-{the_datetime}.webp"
prompt_original_file = f"./staging/original-{the_datetime}.txt"
prompt_landscape_file = f"./staging/landscape-{the_datetime}.txt"
prompt_portrait_file = f"./staging/portrait-{the_datetime}.txt"

# For immediate usage
upload_file_to_s3(landscape_file, AWS_S3_BUCKET, f"images/landscape.webp")
upload_file_to_s3(portrait_file, AWS_S3_BUCKET, f"images/portrait.webp")
upload_file_to_s3(prompt_original_file, AWS_S3_BUCKET, f"prompts/original.txt")
upload_file_to_s3(prompt_landscape_file, AWS_S3_BUCKET, f"prompts/landscape.txt")
upload_file_to_s3(prompt_portrait_file, AWS_S3_BUCKET, f"prompts/portrait.txt")

# Archival
upload_file_to_s3(landscape_file, AWS_S3_BUCKET, f"images/{the_date}-landscape.webp")
upload_file_to_s3(portrait_file, AWS_S3_BUCKET, f"images/{the_date}-portrait.webp")
upload_file_to_s3(prompt_original_file, AWS_S3_BUCKET, f"prompts/{the_date}-original.txt")
upload_file_to_s3(prompt_landscape_file, AWS_S3_BUCKET, f"prompts/{the_date}-landscape.txt")
upload_file_to_s3(prompt_portrait_file, AWS_S3_BUCKET, f"prompts/{the_date}-portrait.txt")
