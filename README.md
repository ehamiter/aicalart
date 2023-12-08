# AI Calendar Art

This repo hosts the scripts and template that powers [aical.art](https://aical.art).

## Prerequisites

Follow the directions for each respective link to set up your API keys:

  * [Google API / OAuth token credentials](https://developers.google.com/calendar/api/quickstart/python)
  * [OpenaAI API key](https://platform.openai.com/docs/quickstart?context=python)
  * [GitHub Personal Access Token with full repo scope](https://docs.github.com/en/enterprise-server@3.9/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## Setup

```
cd <to the root of where you want this project to live>
git clone https://github.com/ehamiter/aicalart.git

<Enter username>
<Enter GitHub Personal Access Token for password>

mkdir staging
cp example.env .env  # And update this file with your API keys
python3 -m venv env
source env/bin/activate
pip install -r requirements
```

## Example Usage

### Generation

```
python generate.py [--date --style --skip-news --skip-calendar --skip-holidays --skip-silly-days --skip-upload]
```

All paramaters are optional-- `generate.py` run by itself will randomize elements and pull data from all available sources.

You can pass in a string value for `date` ("YYYY-MM-DD") or `style`.

```
python generate.py --date="2024-12-25"
python generate.py --style="Graffiti street art, bold spray paint, dynamic figures, urban expression"
python generate.py --date="2024-02-05" --style="1920s satirical black and white newspaper comics"
```


Skip fetching for news, calendar, holidays, and silly days:

```
python generate.py --date="2024-02-05" --skip-calendar
python generate.py --skip-news --skip-holidays
```

Skip uploading to S3, so the generated will be created and saved in staging/, but not uploaded. Useful for experimentation:

```
python generate.py --skip-upload
```


Each successful run will generate two images and three prompts and save them in the .gitignored `staging/` directory. They are stored as `webp` files, which are significantly smaller in size compared to `png` files. The only browser that doesn't support it is Internet Explorer, so `webp` it is.

The file structure looks like this:

```
landscape-<YYYY-MM-DDTHH:M:SS:MS>Z.webp
portrait-<YYYY-MM-DDTHH:M:SS:MS>Z.webp

landscape-<YYYY-MM-DDTHH:M:SS:MS>Z.txt
portrait-<YYYY-MM-DDTHH:M:SS:MS>Z.txt
original-<YYYY-MM-DDTHH:M:SS:MS>Z.txt
```

**This will also cost you ~$0.16 for every run.** [Keep an eye on your usage](https://platform.openai.com/usage), and set notifications and credit limits. It adds up quick.

You might have noticed there are three prompts. The original is the one that is reciprocated from feeding Chat-GPT the initial prompt. The other respective orientation prompts are from revisions generated from DALL-E and are much closer aligned with what the final appearances seem to be.


### A Word On Generation Failures
Sometimes it happens to be a bad news day, or questionable events might be happening on your personal calendar. No judgment here. However, DALL-E might balk at a particularly grievous description that would violate its content policies. Try to re-word the initial prompt, or skip the news or calendar if that's the culprit. There's an automatic gradual removal of potentially negatively-influential prompts (e.g., war atrocities in the news, a particularly questionable personal event in your calendar, etc.) until it's just a prompt to make a day about a cat. If that fails, then it bails.


### Manual Promotion
If you skip the upload, you can still upload manually. Clicking either of the image filenames on a Mac in Finder will conveniently select the entirety of the name up until the extension, but the colons are represented in slashes. Example:

```
portrait-2023-12-03T05/04/58.791456Z
```

So you can plug it in like so:
```
python promote.py portrait-2023-12-03T05/04/58.791456Z
```
(At the conclusion of a prompt generation, this line is printed out at the end by itself, so if you use iTerm and have "Copy to pasteboard on selection" enabled, you can double-click the line and it auto-selects and copies it for ease of pasting into the command line. Boy howdy!)

After entering this line, it will upload the images and prompts to S3, and the site will reflect the new sources immediately. Whatever YYYY-MM-DD format is in that string will be applied for that day for both images and all three prompts.


## AWS S3

### Granting public viewing permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::aicalart/*"
        }
    ]
}
```

### CORS settings so fetching the prompts will work:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET"],
        "AllowedOrigins": ["https://aical.art"],
        "ExposeHeaders": [],
        "MaxAgeSeconds": 3000
    }
]
```

To make every object publicly available, you can edit the access control list (ACL) and check "List" and "Read" for "Everyone (public access)".

### webp image orientation paths
```
https://aicalart.s3.amazonaws.com/images/YYYY-MM-DD-landscape.webp
https://aicalart.s3.amazonaws.com/images/YYYY-MM-DD-portrait.webp
```

### original prompt from Chat GPT; finalized orientation prompts from DALL-E
```
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-original.txt
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-landscape.txt
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-portrait.txt
```
