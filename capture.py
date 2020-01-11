from skimage.metrics import structural_similarity as ssim
from imutils import paths
import subprocess as sp
import cv2
import numpy
import argparse
import datetime

ap = argparse.ArgumentParser()
ap.add_argument('--debug', action='store_true', 
    help='Use video file instead of ffmpeg steam data.')
args = vars(ap.parse_args())

SKILLS_BEING_TRACKED = {'images/cropped/ArrowBarrage.png': 10.0}

def skill_locations():
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

    return skills


def blackmagic_image():
    # Capture data from pipe
    raw_image = pipe.stdout.read(1920*1080*3)

    # transform the raw data into a numpy array
    image =  numpy.fromstring(raw_image, dtype='uint8')

    # Reshape to Full HD
    image = image.reshape((1080,1920,3))

    return image


def compare_icons(skill_coords, image, query_icon):
    for i in skill_coords.keys():
        (yStart, yEnd, xStart, xEnd) = skill_coords[i]
        crop = image[yStart:yEnd, xStart:xEnd]
        _,_,crop = cv2.split(crop)
        ss = ssim(crop, query_icon)
        if ss > 0.90:
            return i
    return None

def load_query_icons():
    # Reserve lists for query images and their paths
    query_icons = []
    query_paths = []

    # Load all images from images/cropped/ and store them in lists
    for path in paths.list_images("images"):
        
        # Fetch only the queries that user wants
        if path not in SKILLS_BEING_TRACKED:
            continue

        # Load image and keep only Red channel
        query_icon = cv2.imread(path)
        _,_,query_icon = cv2.split(query_icon)

        # Append to lists
        query_icons.append(query_icon)
        query_paths.append(path)

    return query_icons, query_paths

if __name__ == "__main__":

    # Launch ffmpeg and pipe the rawdata
    if not args['debug']:
        FFMPEG_BIN = "ffmpeg"
        command = [ FFMPEG_BIN,
            '-hide_banner',
            '-loglevel','warning',
            '-raw_format','bgra',
            '-channels','2',
            '-format_code','Hp59',
            '-f','decklink',
            '-i', 'Intensity Pro 4K',
            '-pix_fmt', 'bgr24',
            '-vcodec', 'rawvideo',
            '-an','-sn',
            '-f', 'image2pipe', '-'] 

        # Get data from ffmpeg pipe    
        pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

    # Dictionary for skills[i] = (yStart, yEnd, xStart, xEnd)
    skill_coords = skill_locations()

    # This will be removed at some point
    timeremaining = 0.0
    index = 1
    filenumber = 1

    # Main loop
    while True:
        # Index number for saving PNG/JPEG sequences
        index += 1

        # Get time for deltaTime calculations
        start = datetime.datetime.now()

        # Get a single frame from capture card
        bm_capture = blackmagic_image()

        # Load query icons and their relative paths
        query_icons, query_paths = load_query_icons()


        # Loop queries and compare those to the icons in the image stream.
        for query_icon, query_path in zip(query_icons, query_paths):

            # Fetch the id [1-5] of a slotted skill that has ss < threshold.
            matched_idx = compare_icons(skill_coords, bm_capture, query_icon)

            if matched_idx is not None:
                print("{} DETECTED at slot {}! ALARM! PANIC!".format(query_path, matched_idx))
                timeremaining = SKILLS_BEING_TRACKED[query_path]

                """
                Pseudo-code-thinking:

                if query_path in SKILLS_FOR_TIMER_ONE
                    timer_one_remaining = SKILLS_BEING_TRACKED['query_path']
                elif query path in SKILLS_FOR_TIMER_TWO
                    timer_two_remaining = 
                """


        # Display
        if bm_capture is not None:
            if timeremaining > 0:
                bar_lenght = int(600 * (timeremaining * 0.1))
                cv2.rectangle(bm_capture, 
                    (660, 820),
                    (1260, 825),
                    (255,255,255), thickness=1)
                cv2.rectangle(bm_capture, 
                    (660, 820),
                    (660+bar_lenght, 825),
                    (255,255,255), thickness=-1)
            cv2.imshow('Video', bm_capture)
            
            if index > 60 and (index % 2) == 0:
                filenumber += 1
                cv2.imwrite('output-jpeg/sequence_%03d.jpeg' % filenumber, bm_capture)
        
        # Exit if Q has been pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


        # Check how many seconds did the processing take
        deltaTime = (datetime.datetime.now() - start).total_seconds()

        if timeremaining > 0:
            timeremaining -= deltaTime

        # Empty pipe read
        pipe.stdout.flush()

    cv2.destroyAllWindows()
