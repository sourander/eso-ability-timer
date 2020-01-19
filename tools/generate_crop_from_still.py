""" 
Before using this script, modify the file paths to match your setup.
Use PNG for safety. JPEG compressiong might mess up the similarity match.

The screenshot MUST INCLUDE the ability in ACTIVATED STATE. When you activate
an ability, the icon will animate. Find the keyframe where the animation is in
its climax.

My folder structure for the input images was:
* StamDK/ArrowBarrage_noncropped.png
* StamDK/SomeOtherSkill_noncropped.png
* MagDK/SomeSkill_noncropped.png

And for output:
* skills/SkillName.png
"""

import cv2

# Set skill name here. This should match the filename.
SKILL = "ArrowBarrage"

# Select the ability slot. Index from 1 to 5.
# '1' being the square button slot.
SLOT = 2


image = cv2.imread("StamDK/{}_noncropped.png".format(SKILL))

# Keep only red channel.
_,_,image = cv2.split(image)


# Set values from ESO UI. Offset is 64x64 box's width plus the 10px margin.
# Do not touch these.
OFFSET = 64 + 10
CROPSIZE = 60

# Reserve a dictionary for skill xy coords
skills = {}

# Calculate xy-coordinates of the skill icons
for i in range(0,5):
	yStart, yEnd = 986, 986 + CROPSIZE
	xStart = 790 + (i * OFFSET)
	xEnd = xStart + CROPSIZE
	skills[i+1] = (yStart, yEnd, xStart, xEnd)

# Save the cropped image and preview it for sanity check.
(yStart, yEnd, xStart, xEnd) = skills[SLOT]
crop = image[yStart:yEnd, xStart:xEnd]
cv2.imshow('Crop', crop)
cv2.waitKey(0)
cv2.imwrite("skills/{}.png".format(SKILL), crop)
cv2.destroyAllWindows()