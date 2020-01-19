import cv2

# Set Skill slot # here.
SKILL = "SkeletalArcher"
SLOT = 2

# Expecting 4K still PNG from Resolve.
image = cv2.imread("StamCro/{}_noncropped.png".format(SKILL))
image = cv2.resize(image, (1920, 1080), interpolation = cv2.INTER_AREA)

# Keep only red channel.
_,_,image = cv2.split(image)


# Set values from ESO UI. Offset is 64x64 box's width plus the 10px margin.
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

# Crop all the skill icon areas in skills dict
"""
for i in skills.keys():
	(yStart, yEnd, xStart, xEnd) = skills[i]
	crop = image[yStart:yEnd, xStart:xEnd]
"""

(yStart, yEnd, xStart, xEnd) = skills[SLOT]
crop = image[yStart:yEnd, xStart:xEnd]
cv2.imshow('Crop', crop)
cv2.waitKey(0)
cv2.imwrite("images/cropped/{}.png".format(SKILL), crop)
cv2.destroyAllWindows()