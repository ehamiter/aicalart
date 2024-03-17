import argparse
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
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        extra_args = {}
        if local_path.endswith(".txt"):
            extra_args = {"ContentType": "text/plain"}
        elif local_path.endswith(".webp"):
            extra_args = {"ContentType": "image/webp"}
        elif local_path.endswith(".json"):
            extra_args = {"ContentType": "application/json"}

        print(local_path)

        s3.upload_file(local_path, bucket, s3_key, ExtraArgs=extra_args)
        logger.info(f"Uploaded {local_path} to {bucket}/{s3_key}")

    except FileNotFoundError:
        logger.error("The file was not found")
    except NoCredentialsError:
        logger.error("Credentials not available")

def main(date):
    # Separate the date and time components for the image files
    date_part, time_part = date.split("T")

    # Construct the file paths
    landscape_file = f"./staging/landscape-{date_part}T{time_part}.webp"
    portrait_file = f"./staging/portrait-{date_part}T{time_part}.webp"
    prompt_file = f"./staging/prompt-{date_part}.json"

    # Upload the files to S3
    upload_file_to_s3(landscape_file, AWS_S3_BUCKET, f"images/{date_part}-landscape.webp")
    upload_file_to_s3(portrait_file, AWS_S3_BUCKET, f"images/{date_part}-portrait.webp")
    upload_file_to_s3(portrait_file, AWS_S3_BUCKET, "images/portrait.webp")  # for iPhone wallpaper shortcut
    upload_file_to_s3(prompt_file, AWS_S3_BUCKET, f"prompts/{date_part}-prompt.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload daily files to S3.")
    parser.add_argument("date", type=str, help="Date for the files to upload (format: YYYY-MM-DD)")
    args = parser.parse_args()
    main(args.date)
