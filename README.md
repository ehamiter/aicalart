# AI Calendar Art

[aical.art](https://aical.art)

This repo hosts the scripts and template that powers the above website.


## AWS S3 url patterns

### webp image paths (much smaller filesize compared to png)
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
