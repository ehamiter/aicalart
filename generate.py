import argparse
import base64
import datetime
import json
import logging
import os.path
import random
import time
from base64 import b64decode
from io import BytesIO
from textwrap import dedent

from colorama import Fore, Style
from constants import (
    AICALART_OPENAI_KEY,
    GPT_MODEL,
    HOLIDAYS,
    IMAGE_MODEL,
    PRE_STYLE,
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

install()  # This makes icecream debugging available everywhere via ic()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# for holiday fetching in localtime -- "2023-11-25"
now_cst = datetime.datetime.now().date().strftime("%Y-%m-%d")

# for Google calendar event fetching -- "2023-11-25T00:43:27.521185+00:00Z"
now_utc = now = f"{datetime.datetime.utcnow().isoformat()}Z"


def trim_string(text, char_limit=1023):
    if len(text) <= char_limit:
        return text
    trimmed_text = text[: char_limit + 1]
    last_period = trimmed_text.rfind(".")

    # Add back the removed quote
    if last_period != -1:
        return f'{trimmed_text[: last_period + 1]}"'
    else:
        return f'{trimmed_text[:char_limit]}"'


# `date` here is just a key of sorts in YYYY-MM-DD format
def get_holiday(date):
    return HOLIDAYS.get(date, "")


def get_silly_day(date):
    events = SILLY_DAYS.get(date, [])

    if not events:
        return ""

    if len(events) == 1:
        return events[0]
    else:
        return ", ".join(events[:-1]) + " and " + events[-1]


def get_news(country="US", period="1h"):
    gn = GNews(language="en", country=country, period=period)
    top_news = gn.get_top_news()
    title = top_news[0]["title"]
    return title


def get_style():
    style = PRE_STYLE
    style += random.choice(STYLES)
    return style


def fetch_calendar_entries(prompt, style, the_date=None):
    # Google Calendar creds
    creds = None
    if os.path.exists("./token.json"):
        creds = Credentials.from_authorized_user_file("./token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "./credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("./token.json", "w") as token:
            token.write(creds.to_json())

    if the_date:
        now_utc = f"{the_date}T14:00:00.000000Z"

    # for tqdm progress bar customization
    # example: '10%' [===>
    custom_format = "{desc}: {percentage:3.0f}%|{bar:20}| {n_fmt}/{total_fmt}"  # fmt: skip

    calendar_prompt = f"""
    Keep the prompt short and focused on my near-term most important commitments.
    Remove any personally identifiable information and do not mention dates. Each
    event is a special one that deserves to share the spotlight with the other
    elements of the scene we are setting.
    """

    logger.info("Fetching calendar entries...\n")
    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get("items", [])

        if not calendars:
            logger.info("No calendars found.")
            return

        events = []
        for calendar in tqdm(
            calendars,
            desc=f"{Fore.GREEN}Fetching calendars{Style.RESET_ALL}",
            ncols=75,
            bar_format=custom_format,
        ):
            calendar_id = calendar["id"]

            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=now_utc,
                    maxResults=3,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events += events_result.get("items", [])

        if not events:
            logger.info(
                f"No upcoming events found for calendar: {calendar['summary']}\n"
            )
        else:
            for event in tqdm(
                events,
                desc=f"{Fore.BLUE}Fetching events{Style.RESET_ALL}",
                ncols=75,
                bar_format=custom_format,
            ):
                start = event["start"].get("dateTime", event["start"].get("date"))
                prompt += start + " " + str(event["summary"]) + ", "
            prompt += calendar_prompt
        return prompt

    except HttpError as error:
        logger.error(f"An error occurred: {error}\n")


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
        'events, holidays-- and particularly engrossed in the breaking news story "{news}"'
        if news
        else "events and holidays"
    )
    return today, newslist


def decode_b64_json(b64_data):
    json_data = base64.b64decode(b64_data).decode("utf-8")
    return json.loads(json_data)


def main(
    the_date=None,
    style=None,
    skip_calendar=False,
    skip_holidays=False,
    skip_silly_days=False,
    skip_news=False,
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

    You are creative and very clever by hiding allegories in details. You always
    place your beloved orange tabby domestic shorthair cat, Hobbes, in every
    piece you create. A user could look at one of your creations several times
    and discover something new, insightful, or hilarious on each repeated viewing.
    Today is {today}.
    """

    if not skip_calendar:
        prompt = fetch_calendar_entries(prompt, style, the_date=the_date)

    # Put a bow on the prompt
    prompt += f"""
        Use these words in the beginning of the prompt for the specific style:
        {style}, no margins, full screen. Respond with the prompt only.
    """

    # OpenAI prompts and images generation
    client = OpenAI(api_key=AICALART_OPENAI_KEY)

    print(f"{Fore.YELLOW}Generating prompt...{Style.RESET_ALL}")
    completion = client.chat.completions.create(
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
    style_display = style.replace(PRE_STYLE, "")

    prompt_info = f"""
    Style: {style_display}\n
    News: {news}\n
    Today: {today.split(';')[0]}\n
    DALL-E prompt: {dalle_prompt}
    """
    print(dedent(prompt_info))

    warning = """
    Review the days and news and make sure it's not something that will clearly be rejected.
    Type 'ok' to continue.
    """
    print(dedent(warning))
    proceed = input()
    if proceed.strip().lower() != "ok":
        logger.info(
            "Bailing. Try appending --skip-news or wait until a more appropriate day."
        )
        exit(1)

    # Let's try to make these things. It could be rejected because god only knows
    # what the hell it's going to come up with. If it rejects it, just regenerate
    # and see. Some keywords it will have a problem with... for example, "genocide".
    try:
        logger.info(f"{Fore.YELLOW}Generating portrait image...{Style.RESET_ALL}")
        portrait_response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"{dalle_prompt}. Ensure this image is in a vertical orientation.",
            size="1024x1792",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
        logger.info(f"{Fore.YELLOW}Generating landscape image...{Style.RESET_ALL}")
        landscape_response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"{dalle_prompt}. Ensure this image is in a horizontal orientation.",
            size="1792x1024",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
    except BadRequestError:
        logger.error(
            "OpenAI's safety system rejected this due to its interpretation of the prompt. "
            "Try re-generating or altering the text in order to process an image.          "
        )
        exit(1)

    # Extract revised prompts directly from the response objects
    portrait_prompt = portrait_response.data[0].revised_prompt
    landscape_prompt = landscape_response.data[0].revised_prompt

    print(f"\nPortrait prompt: {portrait_prompt}")
    print(f"\nLandscape prompt: {landscape_prompt}\n")

    # Anything over 1,023 chars gets chopped, so if it's used in an img title, use the shortened version
    portrait_prompt = trim_string(portrait_prompt)
    landscape_prompt = trim_string(landscape_prompt)

    original_prompt_file_path = f"./staging/original-{now}.txt"
    portrait_prompt_file_path = f"./staging/portrait-{now}.txt"
    landscape_prompt_file_path = f"./staging/landscape-{now}.txt"

    with open(original_prompt_file_path, "w") as file:
        file.write(dalle_prompt)

    with open(portrait_prompt_file_path, "w") as file:
        file.write(portrait_prompt)

    with open(landscape_prompt_file_path, "w") as file:
        file.write(landscape_prompt)

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

    t2 = time.perf_counter()
    logger.info(f"{Fore.CYAN}Done!{Style.RESET_ALL} [Total time: {t2 - t1:.2f} seconds]\n\n")  # fmt: skip
    print("To promote these images, run:\n\n")
    print(f"python3 promote.py landscape-{now}")


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
    args = parser.parse_args()
    main(
        the_date=args.date,  # the_date because date contextually means an object
        style=args.style,
        skip_calendar=args.skip_calendar,
        skip_holidays=args.skip_holidays,
        skip_silly_days=args.skip_silly_days,
        skip_news=args.skip_news,
    )
