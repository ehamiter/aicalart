import argparse
from datetime import datetime, timedelta
import logging
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
        logging.CRITICAL: Fore.MAGENTA + "[CRITICAL] %(message)s" + Style.RESET_ALL,
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


def extract_datetime(filename):
    # Extract the part after "landscape-" or "portrait-" and keep 'Z' at the end
    datetime_part = filename.split("-", 1)[1]
    # Replace slashes with colons in the time part
    datetime_with_colons = datetime_part.replace("/", ":")
    return datetime_with_colons

def adjust_to_cst(the_datetime):
    # Convert the UTC datetime string to a datetime object
    datetime_obj = datetime.strptime(the_datetime, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Adjust to CST by subtracting 6 hours
    cst_datetime_obj = datetime_obj - timedelta(hours=6)

    # Convert back to string to extract the date
    cst_datetime_str = cst_datetime_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return cst_datetime_str

def upload_file_to_s3(local_path, bucket, s3_key):
    logger.info(f"Uploading file {local_path}...")

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        # Set content-type so we're not downloading objects
        if local_path.endswith(".txt"):
            extra_args = {"ContentType": "text/plain"}
        elif local_path.endswith(".webp"):
            extra_args = {"ContentType": "image/webp"}
        else:
            extra_args = {}

        # Upload the file with specified content type
        s3.upload_file(local_path, bucket, s3_key, ExtraArgs=extra_args)

        logger.info(f"File {local_path} uploaded to {bucket}/{s3_key}")

    except FileNotFoundError:
        logger.error("The file was not found")
    except NoCredentialsError:
        logger.error("Credentials not available")

def main(file_tag, archive_only=False):
    input_filename = file_tag
    the_datetime = extract_datetime(input_filename)
    cst_datetime = adjust_to_cst(the_datetime)
    the_date = cst_datetime.split("T")[0]

    # Local file paths using the full datetime so you can generate several per day
    landscape_file = f"./staging/landscape-{the_datetime}.webp"
    portrait_file = f"./staging/portrait-{the_datetime}.webp"
    prompt_original_file = f"./staging/original-{the_datetime}.txt"
    prompt_landscape_file = f"./staging/landscape-{the_datetime}.txt"
    prompt_portrait_file = f"./staging/portrait-{the_datetime}.txt"

    replace_current_files = not archive_only  # Making a double negative not unclear
    if replace_current_files:
        # For immediate usage
        upload_file_to_s3(landscape_file, AWS_S3_BUCKET, "images/landscape.webp")
        upload_file_to_s3(portrait_file, AWS_S3_BUCKET, "images/portrait.webp")
        upload_file_to_s3(prompt_original_file, AWS_S3_BUCKET, "prompts/original.txt")
        upload_file_to_s3(prompt_landscape_file, AWS_S3_BUCKET, "prompts/landscape.txt")
        upload_file_to_s3(prompt_portrait_file, AWS_S3_BUCKET, "prompts/portrait.txt")

    # Archival
    # fmt: off
    upload_file_to_s3(landscape_file, AWS_S3_BUCKET, f"images/{the_date}-landscape.webp")
    upload_file_to_s3(portrait_file, AWS_S3_BUCKET, f"images/{the_date}-portrait.webp")
    upload_file_to_s3(prompt_original_file, AWS_S3_BUCKET, f"prompts/{the_date}-original.txt")
    upload_file_to_s3(prompt_landscape_file, AWS_S3_BUCKET, f"prompts/{the_date}-landscape.txt")
    upload_file_to_s3(prompt_portrait_file, AWS_S3_BUCKET, f"prompts/{the_date}-portrait.txt")
    # fmt: on


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload files to S3 with optional replacement.")  # fmt: skip
    parser.add_argument("file_tag", type=str, help="Tag of the file to upload")
    parser.add_argument(
        "--archive-only",
        action="store_true",
        help="Current images are replaced by default, so use this flag to only archive the images.",
    )
    args = parser.parse_args()
    main(args.file_tag, args.archive_only)
