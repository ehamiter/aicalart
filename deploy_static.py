import asyncio
import asyncssh
import logging
from colorama import Fore, Style
from constants import (
    AICALART_SFTP_SERVER,
    AICALART_SFTP_USERNAME,
    AICALART_SFTP_PASSWORD,
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

REMOTE_BASE = "/media/sdc1/eddielomax/www/aical.art/public_html"

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

async def upload_directory_via_sftp(local_dir, remote_dir):
    """Upload a directory recursively to web hosting via SFTP."""
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
                await sftp.put(local_dir, remote_dir, recurse=True, preserve=True)
                logger.info(f"Uploaded directory {local_dir} to {remote_dir}")
    except Exception as e:
        logger.error(f"Error uploading directory {local_dir} via SFTP: {e}")

async def main():
    logger.info("Deploying static files...")
    
    # Upload index.html
    await upload_file_via_sftp("./index.html", f"{REMOTE_BASE}/index.html")
    
    # Upload static directory
    await upload_directory_via_sftp("./static", f"{REMOTE_BASE}/static")
    
    logger.info("Deployment complete!")

if __name__ == "__main__":
    asyncio.run(main())
