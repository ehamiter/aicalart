# AI Calendar Art

[aical.art](https://aical.art)

This repo hosts the scripts and template that powers the above website.

## Example Usage

### Generation

All paramaters are optional-- `generate.py` run by itself will randomize elements and pull data from all available sources.


```
python generate.py [--date --style --skip-news --skip-calendar --skip-holidays --skip-silly-days]

python generate.py --date="2024-02-05" --skip-news
python generate.py --style="Graffiti street art, bold spray paint, dynamic figures, urban expression"
```

* date  # "YYYY-MM-DD"  -- used for fetching specific days and calendar events
* style # "A descriptive phrase that will drive the imagery narrative"  -- randomized if not provided


Each run will generate 2 images and three prompts and save them in the .gitignored `staging/` directory. They are stored as `webp` files, which are significantly smaller in size compared to `png`s. The only browsers that don't support it are Internet Explorer and the KaiOS Browser, and I don't give a shit about either one of them. So... `webp` it is.

The file structure looks like this:

```
landscape-<YYYY-MM-DDTHH:M:SS:MS>Z.webp
portrait-<YYYY-MM-DDTHH:M:SS:MS>Z.webp

landscape-<YYYY-MM-DDTHH:M:SS:MS>Z.txt
portrait-<YYYY-MM-DDTHH:M:SS:MS>Z.txt
original-<YYYY-MM-DDTHH:M:SS:MS>Z.txt
```

**This will also cost you ~$0.16 for every run.**

You might have noticed there are three prompts. The original is the one that is reciprocated from feeding Chat-GPT the initial prompt. The other respective orientation prompts are from revisions generated from DALL-E and are much closer aligned with what the images final appearances seem to be.

Once you like an image pair, you can promote everything to production.


### Promotion
Clicking either of the image filenames on a Mac in Finder will conveniently select the entirety of the name up until the extension, but the colons are represented in slashes. Example:

```
portrait-2023-12-03T05/04/58.791456Z
```

So you can plug it in like so:
```
python promote.py portrait-2023-12-03T05/04/58.791456Z
```

...and it will upload the images and prompts to S3, and the site will reflect the new sources immediately. On a prompt generation, this line is printed out, so if you use iTerm, you can double-click the line and it auto-selects and copies it for ease of pasting into the command line.


## AWS S3 url patterns

### webp image paths
```
https://aicalart.s3.amazonaws.com/images/YYYY-MM-DD-landscape.webp
https://aicalart.s3.amazonaws.com/images/YYYY-MM-DD-portrait.webp
```

### original prompt from Chat GPT; finalized prompts from DALL-E
```
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-original.txt
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-landscape.txt
https://aicalart.s3.amazonaws.com/prompts/YYYY-MM-DD-portrait.txt
```
