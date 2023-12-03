#!/bin/zsh

# Replace slashes with colons in the datetime part of the filename
input_filename="$1"
datetime_with_colons="${input_filename//\//:}"

# Extract the date and time from the argument
datetime="${datetime_with_colons#*-}"   # Removes the part before and including the first hyphen, leaving the datetime part
date="${datetime:0:10}" # Extracts the YYYY-MM-DD part

landscape_file="./staging/landscape-${datetime}.png"
portrait_file="./staging/portrait-${datetime}.png"

prompt_original_file="./staging/original-${datetime}.txt"
prompt_landscape_file="./staging/landscape-${datetime}.txt"
prompt_portrait_file="./staging/portrait-${datetime}.txt"

dest_images="./static/images"
dest_prompt="./static/prompt"
dest_archive="./static/archive"

cp "${landscape_file}" "${dest_images}/landscape.png"
cp "${portrait_file}" "${dest_images}/portrait.png"

cp "${prompt_original_file}" "${dest_prompt}/original.txt"
cp "${prompt_landscape_file}" "${dest_prompt}/landscape.txt"
cp "${prompt_portrait_file}" "${dest_prompt}/portrait.txt"

mkdir -p "${dest_archive}/prompt"
# cp "${landscape_file}" "${dest_image_archive}/landscape/${date}.png"
# cp "${portrait_file}" "${dest_image_archive}/portrait/${date}.png"

cp "${prompt_original_file}" "${dest_archive}/${date}-original.txt"
cp "${prompt_landscape_file}" "${dest_archive}/${date}-landscape.txt"
cp "${prompt_portrait_file}" "${dest_archive}/${date}-portrait.txt"
