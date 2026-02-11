import argparse
import asyncio
import base64
from datetime import timezone
import datetime
import json
import logging
import os
import requests
import time
from base64 import b64decode
from io import BytesIO
from textwrap import dedent
# from tqdm import tqdm

from colorama import Fore, Style
from constants import (
    OPENROUTER_AICALART_API_KEY,
    OPENROUTER_BASE_URL,
    ALWAYS_INCLUDE_IN_PROMPT,
    GOOGLE_CALENDAR_ID,
    GPT_MODEL,
    IMAGE_MODEL,
    IMAGE_SIZE,
    LANDSCAPE_ASPECT_RATIO,
    PORTRAIT_ASPECT_RATIO,
    SCOPES,
    STYLE_BASES,
    STYLE_PHRASES,
)
from holidays_helper import get_holiday, get_silly_day, get_todays_holidays_display
from randomish import get_random_style
from gnews import GNews
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
from PIL import Image, ImageDraw
from promote import main as promote_file

import socket
socket.setdefaulttimeout(150)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# for holiday fetching in localtime -- "2023-11-25"
now_cst = datetime.datetime.now().date().strftime("%Y-%m-%d")

# for Google calendar event fetching -- "2023-11-25T00:43:27.521185+00:00Z"
now_utc = now = f"{datetime.datetime.now(timezone.utc).isoformat()}Z"

openai_client = OpenAI(api_key=OPENROUTER_AICALART_API_KEY, base_url=OPENROUTER_BASE_URL)


def get_news(country="US", period="1h"):
    title = ''
    gn = GNews(language="en", country=country, period=period)
    top_news = gn.get_top_news()
    if top_news:
        news = top_news[0]
        title = news.get("title", '')
    # news is typically not great. I wish that weren't the case. :|
    news_is_okay = prompt_passes_moderation(title)

    return title if news_is_okay else ''


def get_style():
    return get_random_style(STYLE_BASES, STYLE_PHRASES)


def get_today_and_newslist(the_date, holiday, silly_day, news):
    holiday_is_happening = True  # I mean, the odds are high

    if holiday and silly_day:
        the_day = f"{holiday} and {silly_day}"
    elif holiday:
        the_day = holiday
    elif silly_day:
        the_day = silly_day
    else:
        holiday_is_happening = False

    if holiday_is_happening:
        today = f"{the_date}, {the_day}; ranked in order of importance"
    else:
        today = f"{the_date}; approximate the seasonal feel in the United States"

    newslist = (
        f'events, holidays-- and particularly engrossed in the breaking news story "{news}"'
        if news
        else "events and holidays"
    )
    return today, newslist


def refresh_credentials(token_path, credentials_path):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        logger.info("Credentials not found or invalid.")
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Sending request for credentials refresh.")
                creds.refresh(Request())
            except RefreshError:
                logger.info("Refresh token invalid, re-authenticating.")
                os.remove(token_path)
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
        else:
            logger.info("Please log in using your web browser.")
            if os.path.exists(token_path):
                os.remove(token_path)
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds


def process_calendars(creds, prompt, the_date):
    calendar_prompt = """
    Remove any personally identifiable information and do not mention dates. Each
    event is a special one that deserves to share the spotlight with the other
    elements of the scene we are setting.
    """

    if the_date:
        # We're requesting a specific date, so we need to convert to the day's full datetime string
        now_utc = f"{the_date}T14:00:00.000000Z"
        today = now_utc.split('T')[0]
        end_of_day_utc = today + 'T23:59:59.999999Z'


    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get("items", [])

        if not calendars:
            logger.info("No calendars found.")
            return prompt

        events = []

        # Uncomment for using all calendars
        # for calendar in tqdm(calendars, desc="Fetching calendars", ncols=75):
        #     calendar_id = calendar["id"]
        #     events_result = (
        #         service.events()
        #         .list(
        #             calendarId=calendar_id,
        #             timeMin=now_utc,
        #             maxResults=3,
        #             singleEvents=True,
        #             orderBy="startTime",
        #         )
        #         .execute()
        #     )
        #     events += events_result.get("items", [])

        calendar_id = GOOGLE_CALENDAR_ID
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now_utc,
                timeMax=end_of_day_utc,
                maxResults=3,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events += events_result.get("items", [])
        # print(f'Events: {[e for e in events]}')

        if not events:
            logger.info(f"No upcoming events found for calendar.")
        else:
            prompt += "Today also has some key events: "
            logger.info(f"Upcoming events found for calendar:")
            for event in events:

                if event.get("recurringEventId", "") == "fbakiorghcmpbacoi7n9o7ft8k":
                    continue

                prompt += str(event["summary"]) + "; "
                print(f"\n→ {event['summary']}\n")
            prompt += calendar_prompt

        return prompt

    except HttpError as error:
        logger.error(f"An error occurred: {error}")
        return prompt


def fetch_calendar_entries(prompt, style, the_date):
    token_path = "./token.json"
    credentials_path = "./credentials.json"

    creds = refresh_credentials(token_path, credentials_path)

    return process_calendars(creds, prompt, the_date)


def decode_b64_json(b64_data):
    json_data = base64.b64decode(b64_data).decode("utf-8")
    return json.loads(json_data)


def prompt_passes_moderation(prompt):
    # Moderation endpoint not available via OpenRouter; the image model
    # (Nano Banana Pro) applies its own content filters.
    print(f"{Fore.GREEN}Skipping moderation (handled by image model).{Style.RESET_ALL}")
    return True


def write_daily_prompt_json(date, landscape_prompt, portrait_prompt, holidays, style):
    prompt_file_path = f"./staging/prompt-{date}.json"
    clean_landscape = landscape_prompt.strip('"').replace('\\n', '\n')
    clean_portrait = portrait_prompt.strip('"').replace('\\n', '\n')

    # Remove both types of markers
    for marker in ['**Image Prompt:**\n\n', '**Prompt:** ']:
        clean_landscape = clean_landscape.replace(marker, '')
        clean_portrait = clean_portrait.replace(marker, '')

    prompt_data = {
        "landscape": clean_landscape,
        "portrait": clean_portrait,
        "holidays": holidays,
        "style": style
    }

    with open(prompt_file_path, "w") as file:
        json.dump(prompt_data, file, indent=4, ensure_ascii=False)


def generate_prompt(prompt, style, news, today):
    print(f"{Fore.YELLOW}Generating prompt...{Style.RESET_ALL}")
    completion = openai_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": prompt},
        ],
    )

    dalle_prompt = completion.choices[0].message.content

    prompt_info = f"""
    Style: {style}\n
    News: {news}\n
    Today: {today.split(';')[0]}\n
    Image prompt: {dalle_prompt}
    """
    print(dedent(prompt_info))
    return dalle_prompt

    # print(f"Prompt '{prompt}' failed moderation. Try with another prompt.")
    # exit()

def generate_image_via_openrouter(prompt, aspect_ratio):
    """Generate a single image via OpenRouter using Nano Banana Pro."""
    response = requests.post(
        url=f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_AICALART_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": IMAGE_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "modalities": ["image", "text"],
            "image_config": {
                "aspect_ratio": aspect_ratio,
                "image_size": IMAGE_SIZE,
            },
        },
        timeout=150,
    )
    response.raise_for_status()
    result = response.json()

    message = result["choices"][0]["message"]
    images = message.get("images", [])
    if not images:
        raise ValueError("No images returned in response")

    # Extract base64 data from data URL (format: data:image/png;base64,...)
    data_url = images[0]["image_url"]["url"]
    base64_data = data_url.split(",", 1)[1]
    return base64_data


def generate_images(dalle_prompt, style, image_args, failed_attempts=0):
    # Let's try to make these things. It could be rejected because god only knows
    # what the hell it's going to come up with. If it rejects it, just regenerate
    # and see. Some keywords it will have a problem with... for example, "genocide".

    (
        the_date,
        style,
        image_model,
        skip_calendar,
        skip_holidays,
        skip_silly_days,
        skip_news,
        skip_upload,
    ) = image_args

    full_prompt = f"{style}, no margins, full screen. {dalle_prompt}"

    try:
        logger.info(f"{Fore.YELLOW}Generating portrait image...{Style.RESET_ALL}")
        logger.info(f"Request parameters: model={image_model}, aspect_ratio={PORTRAIT_ASPECT_RATIO}, image_size={IMAGE_SIZE}")
        portrait_data = generate_image_via_openrouter(full_prompt, PORTRAIT_ASPECT_RATIO)
        logger.info(f"Portrait response received successfully!")

        logger.info(f"{Fore.YELLOW}Generating landscape image...{Style.RESET_ALL}")
        logger.info(f"Request parameters: model={image_model}, aspect_ratio={LANDSCAPE_ASPECT_RATIO}, image_size={IMAGE_SIZE}")
        landscape_data = generate_image_via_openrouter(full_prompt, LANDSCAPE_ASPECT_RATIO)
        logger.info(f"Landscape response received successfully!")
    except (requests.exceptions.HTTPError, ValueError, KeyError) as e:
        logger.error(f"Image generation error: {str(e)}")
        failed_attempts += 1

        if failed_attempts <= 5:
            # Define a dictionary mapping the attempt number to the changes
            attempt_changes = {
                1: {},
                2: {"skip_news": True},
                3: {"skip_calendar": True, "skip_news": True},
                4: {
                    "skip_calendar": True,
                    "skip_holidays": True,
                    "skip_silly_days": True,
                    "skip_news": True,
                },
                5: {
                    "style": "Bob Ross, with peaceful happy little trees",
                    "skip_calendar": True,
                    "skip_holidays": True,
                    "skip_silly_days": True,
                    "skip_news": True,
                },
            }

            # Get the changes for the current attempt
            changes = attempt_changes[failed_attempts]

            # Call main with updated arguments
            main(
                the_date=the_date,
                style=changes.get("style", style),
                model=image_model,
                skip_calendar=changes.get("skip_calendar", skip_calendar),
                skip_holidays=changes.get("skip_holidays", skip_holidays),
                skip_silly_days=changes.get("skip_silly_days", skip_silly_days),
                skip_news=changes.get("skip_news", skip_news),
                skip_upload=skip_upload,
                failed_attempts=failed_attempts,
            )
            return True
        else:
            logger.info(f"{Fore.RED}Error: could not process images.{Style.RESET_ALL}")
            exit(1)

    # Clean up the prompt for metadata
    clean_prompt = dalle_prompt.replace('\\n', '\n').replace('\\"', '"')
    for marker in ['**Image Prompt:**\n\n', '**Prompt:** ']:
        clean_prompt = clean_prompt.replace(marker, '')

    portrait_prompt = clean_prompt
    landscape_prompt = clean_prompt

    print(f"\nPortrait prompt: {portrait_prompt}")
    print(f"\nLandscape prompt: {landscape_prompt}\n")

    todays_holidays = get_todays_holidays_display(the_date)
    print("TODAYS HOLIDAYS\n\n", todays_holidays)
    if not os.path.exists("./staging"):
        os.makedirs("./staging")

    # Update the JSON file with the new prompts and holidays
    write_daily_prompt_json(the_date, landscape_prompt, portrait_prompt, todays_holidays, style)

    # Image processing - decode base64 to PIL Image
    portrait_image = Image.open(BytesIO(b64decode(portrait_data)))
    landscape_image = Image.open(BytesIO(b64decode(landscape_data)))

    ImageDraw.Draw(portrait_image)
    ImageDraw.Draw(landscape_image)

    # Save them into the /staging folder that is ignored by git for convenience
    portrait_image_path = f"./staging/portrait-{now}.webp"
    portrait_image.save(portrait_image_path, format="webp")

    landscape_image_path = f"./staging/landscape-{now}.webp"
    landscape_image.save(landscape_image_path, format="webp")

    if landscape_image and portrait_image:
        return True
    return False


def main(
    the_date=None,
    style=None,
    model=None,
    skip_calendar=False,
    skip_holidays=False,
    skip_silly_days=False,
    skip_news=False,
    skip_upload=False,
    failed_attempts=0,
):
    # Time it from beginning to end
    t1 = time.perf_counter()

    # Print out any args that we're skipping so there are no surprises. No alarms, and no surprise, please
    args = locals()
    skipped_args = [
        arg_name.replace("skip_", "")
        for arg_name, arg_value in args.items()
        if arg_name.startswith("skip_") and arg_value
    ]
    skipped_args_str = ", ".join(skipped_args)
    if skipped_args:
        logger.info(f"Skipping: {skipped_args_str}\n")

    # `the_date`, e.g. '2023-11-26', is used in keys for the holiday dicts
    the_date = the_date or now_cst.split("T")[0]  # fmt: skip
    the_day = ""  # placeholder for any named days, e.g. "Cyber Monday and National Fritters Day"
    style = style or get_style()

    image_model = model or IMAGE_MODEL

    holiday = None if skip_holidays else get_holiday(the_date)
    silly_day = None if skip_silly_days else get_silly_day(the_date)
    news = None if skip_news else get_news()

    today, newslist = get_today_and_newslist(the_date, holiday, silly_day, news)

    prompt = f"""
    You are an expert prompt creator for AI image generation. You specialize in creating images based on current {newslist}.
    You incorporate the pure embodiment of the style of {style} into your creations-- you take it to the extreme. Really push your limits for organic, creative, and clever imagery.
    You are exceptionally clever and inventive by hiding allegories in details.
    A user could look at one of your creations several times and discover something new, insightful, or hilarious on each repeated viewing.
    {ALWAYS_INCLUDE_IN_PROMPT}
    Today is {today}.
    Craft a prompt for a scene that incorporates all of these elements together into a spectacular work of art.
    Use the full screen, no margins.
    IMPORTANT: Respond with the prompt only.
    """

    if not skip_calendar:
        prompt = fetch_calendar_entries(prompt, style, the_date)

    dalle_prompt = generate_prompt(prompt, style, news, today)

    image_args = (
        the_date,
        style,
        image_model,
        skip_calendar,
        skip_holidays,
        skip_silly_days,
        skip_news,
        skip_upload,
    )

    successful_result = generate_images(dalle_prompt, style, image_args, failed_attempts)

    t2 = time.perf_counter()

    if successful_result:
        logger.info(f"{Fore.CYAN}Generation complete.{Style.RESET_ALL} [Total time: {t2 - t1:.2f} seconds]\n\n")  # fmt: skip
    else:
        logger.info(f"{Fore.RED}Generation failed.{Style.RESET_ALL} [Total time: {t2 - t1:.2f} seconds]\n\n")  # fmt: skip
        exit(1)

    if not skip_upload:
        asyncio.run(promote_file(now))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate an AI calendar art piece with a specific style and/or from a specific date."
    )
    parser.add_argument(
        "--date",
        default=None,
        help='Date for the calendar prompt (e.g., "2023-11-25").',
    )
    parser.add_argument(
        "--style",
        default=None,
        help='Style for the calendar prompt (e.g., "1970s Miami funkadelic neon color vibe, ocean pastels, stucco mansions, seafood party").',
    )
    parser.add_argument(
        "--model",
        default=None,
        help='Model for image generation (e.g., "google/gemini-3-pro-image-preview").',
    )
    parser.add_argument(
        "--skip-calendar",
        action="store_true",
        help="Include this flag to skip fetching Google calendar entries. Helpful if all you have are dentist appointments and trash reminders.",
    )
    parser.add_argument(
        "--skip-holidays",
        action="store_true",
        help="Skip fetching Holidays. Hard to not get something rejected when it's a day honoring past survivors of atrocities.",
    )
    parser.add_argument(
        "--skip-silly-days",
        action="store_true",
        help="Most of the time this is fine, but sometimes you don't want 'Did You Fart? Day'...  but sometimes you do.",
    )
    parser.add_argument(
        "--skip-news",
        action="store_true",
        help="Skip fetching the top news headline. Sometimes there's terrible shit happening out there.",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip uploading generated images. Useful for experimenting with styles or prompts. Will store generated images in the staging/ folder.",
    )
    args = parser.parse_args()
    main(
        the_date=args.date,  # the_date because date contextually means an object
        style=args.style,
        model=args.model,
        skip_calendar=True,  # args.skip_calendar,
        skip_holidays=args.skip_holidays,
        skip_silly_days=args.skip_silly_days,
        skip_news=True,  # args.skip_news,
        skip_upload=args.skip_upload,
    )
