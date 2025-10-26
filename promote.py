import argparse
import logging
import asyncio
import asyncssh
from colorama import Fore, Style
from constants import (
    AICALART_SFTP_SERVER,
    AICALART_SFTP_USERNAME,
    AICALART_SFTP_PASSWORD,
    AICALART_IMAGES_PATH,
    AICALART_PROMPTS_PATH,
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

async def upload_file_via_sftp(local_path, remote_path):
    """Upload a file to web hosting via SFTP."""
    if not all([AICALART_SFTP_SERVER, AICALART_SFTP_USERNAME, AICALART_SFTP_PASSWORD]):
        logger.error("Web hosting credentials not configured")
        return
    
    try:
        async with asyncssh.connect(
            AICALART_SFTP_SERVER,
            username=AICALART_SFTP_USERNAME,
            password=AICALART_SFTP_PASSWORD,
            known_hosts=None
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                await sftp.put(local_path, remote_path)
                logger.info(f"Uploaded {local_path} to {remote_path}")
    except FileNotFoundError:
        logger.error(f"The file was not found: {local_path}")
    except Exception as e:
        logger.error(f"Error uploading {local_path} via SFTP: {e}")

async def main(date):
    # Separate the date and time components for the image files
    date_part, time_part = date.split("T")

    # Construct the file paths
    landscape_file = f"./staging/landscape-{date_part}T{time_part}.webp"
    portrait_file = f"./staging/portrait-{date_part}T{time_part}.webp"
    prompt_file = f"./staging/prompt-{date_part}.json"

    # Upload the files to hosting
    await upload_file_via_sftp(landscape_file, f"{AICALART_IMAGES_PATH}/{date_part}-landscape.webp")
    await upload_file_via_sftp(portrait_file, f"{AICALART_IMAGES_PATH}/{date_part}-portrait.webp")
    await upload_file_via_sftp(portrait_file, f"{AICALART_IMAGES_PATH}/portrait.webp")  # for iPhone wallpaper shortcut
    await upload_file_via_sftp(prompt_file, f"{AICALART_PROMPTS_PATH}/{date_part}-prompt.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload daily files to web hosting.")
    parser.add_argument("date", type=str, help="Date for the files to upload (format: YYYY-MM-DD)")
    args = parser.parse_args()
    asyncio.run(main(args.date))
