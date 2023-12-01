import argparse
import datetime
import time
from base64 import b64decode
from io import BytesIO

from colorama import Fore, Style
from constants import AICALART_OPENAI_KEY, GPT_MODEL, IMAGE_MODEL
from openai import BadRequestError, OpenAI
from PIL import Image, ImageDraw

now = f"{datetime.datetime.utcnow().isoformat()}Z"


def logo_maker(description):
    # Time it from beginning to end
    t1 = time.perf_counter()

    prompt = f"""
    Imagine you are a master prompt maker for DALL-E. You specialize in
    creating logos based on simple descriptions. These logos embody the very
    spirit of the essential elements that make a good logo:

    Simplicity; memorability; modern yet timeless; balance; complementary;
    versatility.

    You represent all of these qualities in your greatest prompt design to
    date: {description}.

    A good designer will understand all this and create a logo that works in
    all situations, and have an aesthetic to it that looks clean and crisp.
    The last thing it shold look is "busy". Every stroke of the pen has a
    purpose. Include a primary color with a secondary one to use as an accent.

    The logo should be centered in the image, and have a sensible border around
    it to give it the proper amount of negative space. The outside lines of the
    logo should be solid and well-defined without anti-aliasing.

    Do not include multiple images of varying sizes-- it is essential the focus
    is drawn to the singular element.

    Respond with the prompt only.
    """

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
    print(f"\n{GPT_MODEL} prompt:\n{dalle_prompt}")

    # Let's try to make these things. It could be rejected because god only knows
    # what the hell it's going to come up with. If it rejects it, just regenerate
    # and see. Some keywords it will have a problem with... for example, "genocide".
    try:
        print(f"{Fore.YELLOW}Generating logo...{Style.RESET_ALL}")
        dalle_response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=f"{dalle_prompt}",
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
    except BadRequestError:
        msg = """"OpenAI's safety system rejected this due to its interpretation of
        the prompt. Try re-generating or altering the text in order to process an image.
        """
        print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
        exit(1)

    # The finalized prompt is revised by GPT and slightly different for each orientation
    dalle_prompt = dalle_response.data[0].revised_prompt
    print(f"\n{IMAGE_MODEL} prompt:\n{dalle_prompt}")

    # Image processing
    dalle_data = dalle_response.data[0].model_dump()["b64_json"]
    dalle_image = Image.open(BytesIO(b64decode(dalle_data)))
    ImageDraw.Draw(dalle_image)

    # These files get dumped into the /staging folder that is ignored by git
    dalle_image.save(f"./staging/logo-{now}.png")

    t2 = time.perf_counter()
    print(f"{Fore.CYAN}Done!{Style.RESET_ALL} [Total time: {t2 - t1:.2f} seconds]")  # fmt: skip


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a logo based on your description."
    )
    parser.add_argument(
        "description",
        help="Description for the logo. Be as descriptive as possible about the business, mission, etc.",
    )
    args = parser.parse_args()
    logo_maker(description=args.description)
