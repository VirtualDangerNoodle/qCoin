#! python3

import os
from pathlib import Path
import pyinputplus as pyip
from PIL import Image, ImageEnhance

# 'filtername' : [brightness, contrast, sharpness]
filterDict = {'albr': [0.9, 1.50, 5], 'bimetal': [1.15, 1.5, 5], 'brass': [0.8, 1.25, 3],
              'copper': [0.8, 1.35, 5], 'gold': [1, 1.5, 4], 'silver': [0.8, 1.6, 5]}


# Edit depending on the filter
def filterApply(filtername, img_file, name):

    crop_img = current_img.crop((600, 20, 3500, 3500))
    # Filter values
    b, c, s = filterDict[filtername]

    filter_br = ImageEnhance.Brightness(crop_img)
    filter_cont = ImageEnhance.Contrast(filter_br.enhance(b))
    filter_sharp = ImageEnhance.Sharpness(filter_cont.enhance(c))
    final_img = filter_sharp.enhance(s)
    final_img.save(myDesktop / 'Edited' / name)


myDesktop = Path.home() / 'Desktop'

# Check and make original/folders

if 'Original' not in os.listdir(myDesktop):
    os.makedirs(myDesktop / 'Original')
if 'Edited' not in os.listdir(myDesktop):
    os.makedirs(myDesktop / 'Edited')

# Prompt to ask what filter to use

picFilter = pyip.inputChoice(['AlBr', 'BiMetal', 'Brass', 'Copper', 'Gold', 'Silver']).lower()

print('%s filter was selected' % picFilter.title())

# Iterate, crop and add filter per image

for picture in os.listdir(myDesktop / 'Original'):
    current_img = Image.open(myDesktop / 'Original' / picture)
    print('%s was edited' % picture)
    filterApply(picFilter, current_img, picture)
