import argparse
import base64
import datetime
import json
import logging
import os
import time
from base64 import b64decode
from io import BytesIO
from textwrap import dedent
# from tqdm import tqdm

from colorama import Fore, Style
from constants import (
    AICALART_OPENAI_KEY,
    ALWAYS_INCLUDE_IN_PROMPT,
    GOOGLE_CALENDAR_ID,
    GPT_MODEL,
    HOLIDAYS,
    IMAGE_MODEL,
    SCOPES,
    SILLY_DAYS,
    generate_random_style,
)
from gnews import GNews
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import BadRequestError, OpenAI
from PIL import Image, ImageDraw
from promote import main as promote_file
from randomish import randomish

import socket
socket.setdefaulttimeout(150)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# for holiday fetching in localtime -- "2023-11-25"
now_cst = datetime.datetime.now().date().strftime("%Y-%m-%d")

# for Google calendar event fetching -- "2023-11-25T00:43:27.521185+00:00Z"
now_utc = now = f"{datetime.datetime.utcnow().isoformat()}Z"

openai_client = OpenAI(api_key=AICALART_OPENAI_KEY)


# `date` here is just a key of sorts in YYYY-MM-DD format
def get_holiday(date):
    return HOLIDAYS.get(date, "")


def get_silly_day(date):
    events = SILLY_DAYS.get(date, [])

    if not events:
        return ""

    # Use Oxford comma when there are more than two events, otherwise just join with ", "
    if len(events) > 2:
        return ", ".join(events[:-1]) + ", and " + events[-1]
    else:
        # Join with " and " if there are exactly two events, else return single event
        return " and ".join(events)


def get_todays_holidays_display(the_date):
    holiday = get_holiday(the_date)
    silly_day = get_silly_day(the_date)

    # Concatenate holiday and silly day, if both exist
    if holiday and silly_day:
        return f"{holiday}, {silly_day}"
    else:
        # Return either holiday or silly day, or an empty string if neither exists
        return holiday or silly_day


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
    style = generate_random_style()
    return style


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


        if not events:
            logger.info(f"No upcoming events found for calendar.")
        else:
            prompt += "Today also has some key events: "
            logger.info(f"Upcoming events found for calendar:")
            for event in events:
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
    print(f"{Fore.YELLOW}Moderating prompt...{Style.RESET_ALL}")
    mod_obj = openai_client.moderations.create(input=prompt)
    results = mod_obj.results[0]
    if results.flagged == True:
        print(f"{Fore.RED}Prompt failed moderation.{Style.RESET_ALL}")
        return False
    print(f"{Fore.GREEN}Prompt passed moderation.{Style.RESET_ALL}")
    return True


def write_daily_prompt_json(date, landscape_prompt, portrait_prompt, holidays, style):
    prompt_file_path = f"./staging/prompt-{date}.json"
    prompt_data = {
        "landscape": landscape_prompt,
        "portrait": portrait_prompt,
        "holidays": holidays,
        "style": style
    }

    with open(prompt_file_path, "w") as file:
        json.dump(prompt_data, file, indent=4)


def generate_prompt(prompt, style, news, today):
    if prompt_passes_moderation(prompt):
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
        DALL-E prompt: {dalle_prompt}
        """
        print(dedent(prompt_info))
        return dalle_prompt

    print(f"Prompt '{prompt}' failed moderation. Try with another prompt.")
    exit()

def generate_images(dalle_prompt, image_args, failed_attempts=0):
    # Let's try to make these things. It could be rejected because god only knows
    # what the hell it's going to come up with. If it rejects it, just regenerate
    # and see. Some keywords it will have a problem with... for example, "genocide".

    (
        the_date,
        style,
        skip_calendar,
        skip_holidays,
        skip_silly_days,
        skip_news,
        skip_upload,
    ) = image_args

    try:
        logger.info(f"{Fore.YELLOW}Generating portrait image...{Style.RESET_ALL}")
        portrait_response = openai_client.images.generate(
            model=IMAGE_MODEL,
            prompt=dalle_prompt,
            size="1024x1792",
            quality="hd",
            n=1,
            response_format="b64_json",
        )
        logger.info(f"{Fore.YELLOW}Generating landscape image...{Style.RESET_ALL}")
        landscape_response = openai_client.images.generate(
            model=IMAGE_MODEL,
            prompt=dalle_prompt,
            size="1792x1024",
            quality="hd",
            n=1,
            response_format="b64_json",
        )
    except BadRequestError:
        failed_attempts += 1
        logger.error(
            "OpenAI's safety system rejected this due to its interpretation of the prompt. "
            f"Attempting to regenerate... [#{failed_attempts} of 5]"
        )

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
                skip_calendar=changes.get("skip_calendar", skip_calendar),
                skip_holidays=changes.get("skip_holidays", skip_holidays),
                skip_silly_days=changes.get("skip_silly_days", skip_silly_days),
                skip_news=changes.get("skip_news", skip_news),
                skip_upload=skip_upload,
                failed_attempts=failed_attempts,
            )
        else:
            logger.info(f"{Fore.RED}Error: could not process images.{Style.RESET_ALL}")
            exit(1)

    # Extract revised prompts directly from the response objects
    portrait_prompt = portrait_response.data[0].revised_prompt
    landscape_prompt = landscape_response.data[0].revised_prompt

    print(f"\nPortrait prompt: {portrait_prompt}")
    print(f"\nLandscape prompt: {landscape_prompt}\n")


    todays_holidays = get_todays_holidays_display(the_date)
    print("TODAYS HOLIDAYS\n\n", todays_holidays)
    if not os.path.exists("./staging"):
        os.makedirs("./staging")

    # Update the JSON file with the new prompts and holidays
    write_daily_prompt_json(the_date, landscape_prompt, portrait_prompt, todays_holidays, style)

    # Image processing
    portrait_data = portrait_response.data[0].model_dump()["b64_json"]
    landscape_data = landscape_response.data[0].model_dump()["b64_json"]

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

    holiday = None if skip_holidays else get_holiday(the_date)
    silly_day = None if skip_silly_days else get_silly_day(the_date)
    news = None if skip_news else get_news()

    today, newslist = get_today_and_newslist(the_date, holiday, silly_day, news)

    prompt = f"""
    Imagine you are a master prompt maker for DALL-E. You specialize in creating
    images based on current {newslist}.

    You are creative and very clever by hiding allegories in details.
    {ALWAYS_INCLUDE_IN_PROMPT} A user could look at one of your creations several times
    and discover something new, insightful, or hilarious on each repeated viewing.
    Today is {today}.
    """

    if not skip_calendar:
        prompt = fetch_calendar_entries(prompt, style, the_date)

    # Put a bow on the prompt
    prompt += f"""
        Use these words in the beginning of the prompt for the specific style:
        {style}, no margins, full screen. Respond with the prompt only.
    """

    dalle_prompt = generate_prompt(prompt, style, news, today)

    image_args = (
        the_date,
        style,
        skip_calendar,
        skip_holidays,
        skip_silly_days,
        skip_news,
        skip_upload,
    )

    successful_result = generate_images(dalle_prompt, image_args, failed_attempts)

    t2 = time.perf_counter()

    if successful_result:
        logger.info(f"{Fore.CYAN}Generation complete.{Style.RESET_ALL} [Total time: {t2 - t1:.2f} seconds]\n\n")  # fmt: skip
    else:
        logger.info(f"{Fore.RED}Generation failed.{Style.RESET_ALL} [Total time: {t2 - t1:.2f} seconds]\n\n")  # fmt: skip
        exit(1)

    if not skip_upload:
        promote_file(now)


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
        help="Skip uploading generated images to S3. Useful for experimenting with styles or prompts. Will store generated images in the staging/ folder.",
    )
    args = parser.parse_args()
    main(
        the_date=args.date,  # the_date because date contextually means an object
        style=args.style,
        skip_calendar=args.skip_calendar,
        skip_holidays=args.skip_holidays,
        skip_silly_days=args.skip_silly_days,
        skip_news=True,  #args.skip_news,
        skip_upload=args.skip_upload,
    )
