## AI Calendar Art

This repo hosts the scripts and template that powers [aical.art](https://aical.art). This project is heavily inspired by "Kuvastin - An E Ink art piece that displays daily AI art inspired by your calendar" ([Blog post here](https://turunen.dev/2023/11/20/Kuvastin-Unhinged-AI-eink-display/); [GitHub repo here](https://github.com/Iletee/kuvastin)).

### Prerequisites

Follow the directions for each respective link to set up your API keys:

  * [Google API / OAuth token credentials](https://developers.google.com/calendar/api/quickstart/python)
  * [OpenaAI API key](https://platform.openai.com/docs/quickstart?context=python)
  * [GitHub Personal Access Token with full repo scope](https://docs.github.com/en/enterprise-server@3.9/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) (you'll need this to clone this private repo)

### Setup

```
cd <to the root of where you want this project to live>
git clone https://github.com/ehamiter/aicalart.git  # Note this is HTTPS and not SSH

<Enter username>
<Enter GitHub Personal Access Token for password>

cp example.env .env  # And update this file with your API keys
python -m venv env
source env/bin/activate
pip install -r aical-reqs.txt  # Intentionally not named `requirements.txt` to save time on auto-build deployment systems
```

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

Skip uploading to S3, so the generated images will be created and saved in `staging/`, but not uploaded. Useful for experimentation:

```
python generate.py --skip-upload
```


### Examples

All of the examples below additionally have `--skip-upload` passed in so the current production image files aren't replaced. Basically whenever you want to experiment, or, say, make screenshots while generating examples, it's a nice option to have. New images are generated and stored in a `staging/` folder.

Additionally, I have some items on my personal calendar that involve my youngest son attending soccer practices. They are titled things like "Practice: B07 Academy" so there are interesting interpretations of what that means exactly. These aren't echoed in the description print outs, but are still a part of the prompt that DALL-E receives, so there will be elements revolving around calendar events unless specifically skipped.

<details>
<summary><code>python generate.py --date="2024-02-11" --skip-upload</code></summary>
<figure>
  <img src="./static/images/examples/2024-02-11-landscape.webp" alt="An AI-generated image showcasing a vibrant sports stadium scene with emotional distortion in Neo-Expressionism style.">
  <figcaption>
    <h3>February 11, 2024: The Super Bowl, Don't Cry Over Spilled Milk Day, and Make A Friend Day</h3>
    <p>Style: Neo-Expressionism, raw imagery, intense colors, emotional distortion</p>
    <p>News: University of Pennsylvania president steps down amid criticism of antisemitism testimony - NBC News</p>
    <p>Today: 2024-02-11, Super Bowl and Make a Friend Day and Dont Cry Over Spilled Milk Day</p>
    <p>DALL-E prompt: Digital art, full screen, intense colors, Neo-Expressionism, emotional distortion, picturing a vibrant sports stadium filled with fans during the pinnacle of a championship game. Hobbes, the orange tabby, is seen amongst the crowd, wearing a miniature football jersey, sitting beside a new unlikely friend, a mouse with a tiny friendship bracelet. Behind them, an overturned milk glass, its contents ignored for the thrill of the game. All around, elements of celebration, teamwork, and camaraderie blend together in a dynamic expression of festive chaos, hinting at upcoming athletic practices and the joyous spirit of special personal celebrations without revealing specifics.</p>
    <p>Landscape prompt: Full screen digital art embodying the Neo-Expressionism movement featuring emotional distortion and intense colors. The focal point is a bustling sports stadium filled to the brim with fans totally engrossed in the climax of a championship game. In the crowd, an identifiable orange-striped tabby character dressed in a tiny football jersey is found, sitting next to an unusual buddy, a mouse sporting a minuscule friendship bracelet. A further element behind them is a tipped over glass of milk, ignored in favor of the exciting sporting event. The atmosphere exhibits aspects of celebration, teamwork, and camaraderie in a vibrant display of joyful disorder, subtly indicating future athletic practices and the heartening ambiance of meaningful personal festivities without giving away detailed information. The image is crafted in a landscape format.</p>
  </figcaption>
</figure>
</details>

<details>
<summary><code>python generate.py --date="2024-05-04" --skip-calendar --skip-news --skip-upload</code></summary>
<figure>
  <img src="./static/images/examples/2024-05-04-landscape.webp" alt="An AI-generated image showing a tabby cat frolicking in a space-age-inspired retro kitchen, where an egg fries nearby, and fireworks explode in the background night sky.">
  <figcaption>
    <h3>May 4th 2024: May The Fourth Be With You; Also EOD Day, I'm Surprised This Was Generated</h3>
    <p>Style: Renaissance portrait, realistic details, chiaroscuro lighting, classical beauty</p>
    <p>News: None</p>
    <p>Today: 2024-05-04, National Explosive Ordnance Disposal (EOD) Day and Star Wars Day, Herb Day and Free Comic Book Day</p>
    <p>DALL-E prompt: Digital art, award-winning art in 4k/8k resolution with realistic details and chiaroscuro lighting capturing classical beauty, no margins, full screen: Envision a tapestry that honors National Explosive Ordnance Disposal (EOD) Day through an allegorical scene where EOD technicians are depicted as Jedi from Star Wars, expertly disarming a variety of devices with lightsabers in hand. Amongst the high-tech gear and defused ordinance, intertwine herbs indigenous to the galaxy, symbolizing Herb Day. Woven into the backdrop are iconic comic book pages, representing Free Comic Book Day, each frame capturing a heroic moment of defusal. In the midst of this intricate ensemble, hide Hobbes the orange tabby cat playfully pawing at a deactivated thermal detonator, while donning a tiny EOD bomb suit, his whiskers twitching in the thrill of the disarmament, subtly blending into the narrative as both an observer and a silent hero.</p>
    <p>Landscape prompt: Create a 4k/8k resolution digital art with meticulous details and chiaroscuro lighting highlighting classical beauty in full screen. Picture a tapestry commemorating National Explosive Ordnance Disposal (EOD) Day symbolically. The scene depicts EOD technicians of differing descents and genders, proficiently nullifying various devices, holding advanced tech tools in their hands. Enrich the backdrop with high-tech gear and neutralized ordnance. Intersperse species-specific flora from a faraway galaxy, giving a nod to Herb day. Embed the background with iconic scenes from an imaginary graphic novel, each frame displaying a gallant moment of disarming, this alludes to Free Comic Book Day. Central to this complex montage, incorporate a disguised generic orange tabby cat playfully batting a deactivated futuristic explosive device, adorning a miniature EOD explosive armor. The cat, merging smoothly into the narrative, serves as a silent observer and a subdued protagonist. This image should have a landscape orientation.</p>
  </figcaption>
</figure>
</details>


<details>
<summary><code>python generate.py --date="2024-07-04" --style="space age retro futurism, optimistic future visions, sleek designs, technological themes, cosmic exploration" --skip-upload</code></summary>
<figure>
  <img src="./static/images/examples/2024-07-04-portrait.webp" alt="An AI-generated image showing a tabby cat frolicking in a space-age-inspired retro kitchen, where an egg fries nearby, and fireworks explode in the background night sky.">
  <figcaption>
    <h3>July 4th 2024: Sure, it's Independence Day; Did You Know It's Also Sidewalk Egg Frying Day?</h3>
    <p>Style: space age retro futurism, optimistic future visions, sleek designs, technological themes, cosmic exploration</p>
    <p>News: Penn President Liz Magill resigns days after antisemitism hearing - NPR</p>
    <p>Today: 2024-07-04, Independence Day and Sidewalk Egg Frying Day</p>
    <p>DALL-E prompt: "Space age retro futurism meets a patriotic celebration and whimsical summer shenanigans as Hobbes, the cunning orange tabby, tiptoes across a sleek, high-tech kitchen where an egg fries on the sidewalk-themed countertop, amidst a display of red, white, and blue cosmic explorations, with hidden symbols of familial affection and festive cheer, encapsulated in a full screen, no-margins tableau of optimistic future visions."</p>
    <p>Portrait prompt: Envision a scene rendered in retro futurism, blended with a whimsical summer vibe and patriotic symbols. Picture a clever orange-striped cat, reminiscent of a carefree, playful character, steadily walking across a shiny, innovative kitchen that features a countertop designed to mimic a heated sidewalk where an egg is frying. The whole surrounding bursts with hues of red, white, and blue - a celebration of cosmic exploration. Concealed within this tableau are symbols expressing familial love and holiday cheer, all enclosed within a full screen, margin-free composition that displays a hopeful vision of the future- captured in a vertical orientation.</p>
  </figcaption>
</figure>
</details>


### Why Is There A Cat In Every Image?

That's Hobbes, and he instructed me to do so.


### File Structure

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


### AWS S3

#### Granting public viewing permissions:
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

#### CORS settings so fetching the prompts will work:
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
# Current images
https://aicalart.s3.amazonaws.com/images/landscape.webp
https://aicalart.s3.amazonaws.com/images/portrait.webp

# Archived images
https://aicalart.s3.amazonaws.com/images/YYYY-MM-DD-landscape.webp
https://aicalart.s3.amazonaws.com/images/YYYY-MM-DD-portrait.webp
```

### original prompt from Chat GPT; finalized orientation prompts from DALL-E
```
# Current prompts
https://aicalart.s3.amazonaws.com/prompts/original.txt
https://aicalart.s3.amazonaws.com/prompts/landscape.txt
https://aicalart.s3.amazonaws.com/prompts/portrait.txt

# Archived prompts
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-original.txt
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-landscape.txt
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-portrait.txt
```
