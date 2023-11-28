import argparse
import datetime
import logging
import os.path
import random
import re
from base64 import b64decode
from io import BytesIO
from textwrap import dedent

from colorama import Fore, Style
from constants import (
    AICALART_OPENAI_KEY,
    HOLIDAYS,
    SCOPES,
    SILLY_DAYS,
    STYLES
)
from gnews import GNews
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import BadRequestError, OpenAI
from PIL import Image, ImageDraw
from tqdm import tqdm

logger = logging.getLogger(__name__)

now = f"{datetime.datetime.utcnow().isoformat()}Z"

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
    return random.choice(STYLES)


def fetch_calendar_entries(creds, prompt, style):
    # for tqdm progress bar customization
    # example: '10%' [===>
    custom_format = "{desc}: {percentage:3.0f}%|{bar:20}| {n_fmt}/{total_fmt}"  # fmt: skip

    # Add event info to original prompt and re-enforce the style
    followup = f"""
    Keep the image close to the style I am after-- simple enough to print in an
    old book. Keep the prompt short and focused on my near term most important
    commitments. Remove any personally identifiable information and do not mention
    dates. Use these words in the beginning of the prompt for the specific style:
    {style}, no margins, full screen. Respond with the prompt only.
    """

    logger.info("Fetching calendar entries...\n")
    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)

        # Fetch all accessible calendars
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
                    timeMin=now,
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
            prompt += followup
        return prompt

    except HttpError as error:
        logger.error(f"An error occurred: {error}\n")

def main(the_date=None, style=None, skip_calendar=False):
    # `the_date`, e.g. '2023-11-26', is used in keys for the holiday dicts
    the_date = the_date or now.split("T")[0]  # fmt: skip
    the_day = ""  # placeholder for any named days, e.g. "Cyber Monday and National Fritters Day"
    style = style or get_style()
    holiday = get_holiday(the_date)
    silly_day = get_silly_day(the_date)
    news = get_news()

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

    prompt = f"""
    Imagine you are a master prompt maker for DALL-E. You specialize in creating
    images based on my calendar entries for the day in the style of {style}, and
    centered around the breaking newsflash "{news}".
    You are creative and very clever by hiding allegories in details. You always
    place your beloved orange tabby domestic shorthair cat, Hobbes, in every
    piece you create. A user could view one of your creations several times and
    discover something new, insightful, or hilarious on each new viewing.
    Today is {today}. Give me a prompt based on todays calendar:
    """

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

    if skip_calendar:
        logger.info("Skipping calendar fetching.\n")
    else:
        prompt = fetch_calendar_entries(creds, prompt, style)

    client = OpenAI(api_key=AICALART_OPENAI_KEY)

    print(f"{Fore.YELLOW}Generating prompt...{Style.RESET_ALL}")
    completion = client.chat.completions.create(
        # gpt-4-turbo will be coming out soon and is 3x cheaper than gpt-4
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": prompt},
        ],
    )

    dalle_prompt = str(completion.choices[0].message.content)
    prompt_info = f"""
    News: {news}\n
    Today: {today.split(';')[0]}\n
    Style: {style}\n
    DALL-E prompt: {dalle_prompt}\n
    """
    print(dedent(prompt_info))

    # Let's try to make these things. It could be rejected because god only knows
    # what the hell it's going to come up with. If it rejects it, just regenerate
    # and see. Some keywords it will have a problem with... for example, "genocide".
    try:
        logger.info(f"{Fore.YELLOW}Generating portrait image...{Style.RESET_ALL}")
        portrait_response = client.images.generate(
            model="dall-e-3",
            prompt=f"{dalle_prompt}. Ensure this image is in a vertical orientation.",
            size="1024x1792",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
        logger.info(f"{Fore.YELLOW}Generating landscape image...{Style.RESET_ALL}")
        landscape_response = client.images.generate(
            model="dall-e-3",
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

    # The finalized prompt is revised by GPT and slightly different for each orientation
    portrait_prompt = portrait_response.data[0].revised_prompt
    landscape_prompt = landscape_response.data[0].revised_prompt
    print('\nPortrait prompt: ', portrait_prompt)
    print('\nLandscape prompt: ', landscape_prompt)

    # Anything over 1,023 chars gets chopped, so if it's used in an img title, use the shortened version
    title_prompt = trim_string(dalle_prompt)
    portrait_prompt = trim_string(portrait_prompt)
    landscape_prompt = trim_string(landscape_prompt)

    title_prompt_file_path = f"./staging/prompt-original-{now}.txt"
    portrait_prompt_file_path = f"./staging/prompt-portrait-{now}.txt"
    landscape_prompt_file_path = f"./staging/prompt-landscape-{now}.txt"

    with open(title_prompt_file_path, "w") as file:
        file.write(title_prompt)

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

    portrait_image.save(f"./staging/portrait-{now}.png")
    landscape_image.save(f"./staging/landscape-{now}.png")

    # These files get dumped into the /staging folder that is ignored by git

    logger.info(f"{Fore.CYAN}Done!{Style.RESET_ALL}")


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
    args = parser.parse_args()
    main(the_date=args.date, style=args.style, skip_calendar=args.skip_calendar)