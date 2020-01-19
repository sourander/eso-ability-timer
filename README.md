
# ESO ability timer
Elder Scrolls Online Add-ons on PS4? Sure! This software mimics similar ability timer addons available on PC. It keeps track of when you have activated an ability and creates an animated bar based on the time data.

**Important** The software works only on two skills per character profile.

## Requirements
This project requires that you have ffmpeg installed with Blackmagic SDK. The code has been tested with FFmpeg 2.1.0 and Blackmagic Desktop 11.4 (and same version for SDK). My setup during dev phase was:
 * Ubuntu 18.04 Desktop
 * Blackmagic Intensity Pro 4K capture card
 * PS4 (with Elder Scrolls Online)
 * Python 3 with pip

## Features

The software's core functionality is to grab a frame from gameplay, crop the ability icons, and check whether the icon is activated or not. This comparison is performed using *structural imilarity* function from Sklearn. For this comparison to work, you must manually grab a frame when the icons activates. I have provided the icons I am using, but if your build uses completely different skills, you must grab these yourself.

![Program's core logic](/images/readme-explanation.png)

Assumed that you have a screenshot of the game taken at the moment when the ability icon is in its activated state, you can save the icon by modifying and running a helper script: *./tools/generate_crop_from_still.py*

## Installation

Check the requirements section for other software.

```bash
git clone https://github.com/sourander/eso-ability-timer.git
pip install -r requirements
```

## Usage

Before using the script, you must configure the capture.py's profiles. Open the file in any text editor and change the values to your liking. The dict SKILLS_BEING_TRACKED should always contain exactly two skills and their duration in seconds. The abilitys location in the ability bar (*index*) is detected automatically.

When the setup is done, you can launch the software using various parameters. I recommend checking that the ffmpeg pipe is set up correctly by running the software with **--nographics** parameter. This will pass the grabbed image to OpenCV's imshow function without drawing any graphics or without performing any icon comparisons.

```bash
python capture.py --nographics
```

Assuming that the command above worked, you can exit the software by pressing 'Q' button on your keyboard.

To launch the software with a profile that you have set in capture.py, type

```bash
python capture.py --profile ProfileName

# e.g. python capture.py --profile StamDK 
```