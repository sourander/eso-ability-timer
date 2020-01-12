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
ap.add_argument('--fullscreen', action='store_true', 
    help='Launch in full screen. Your monitor should have Full HD display resolution.')
args = vars(ap.parse_args())

SKILLS_BEING_TRACKED = {'images/cropped/ArrowBarrage.png': 10.0,
                        'images/cropped/UnstableWallOfElements.png': 10.0,
                        'images/cropped/ChanneledAcceleration.png': 36.0}

LONG_SKILLS = ['images/cropped/ChanneledAcceleration.png']

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


def crop_ability_icons(skill_coords, image):
    bm_crops = []

    for i in skill_coords.keys():
        (yStart, yEnd, xStart, xEnd) = skill_coords[i]
        crop = image[yStart:yEnd, xStart:xEnd]
        _,_,crop = cv2.split(crop)
        bm_crops.append(crop)

    return bm_crops

def compare_icons(bm_icons, query_icon):
    for i, icon in enumerate(bm_icons, 1):
        ss = ssim(icon, query_icon)
        if ss > 0.85:
            return i
    return None

def load_query_icons():
    # Reserve lists for query images and their paths
    query_icons = []
    query_paths = []

    # Load all images from images/cropped/ and store them in lists
    for path in paths.list_images("images/cropped/"):
        
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

    # This will be removed at some point if I end up using a Graphbar Class
    timeremaining_top = 0.0
    timeremaining_bottom = 0.0
    upper_skill_duration = 0.0
    lower_skill_duration = 0.0

    if args['fullscreen']:
        cv2.namedWindow('frame', cv2.WINDOW_FREERATIO)
        cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Main loop
    while True:
        # Get time for deltaTime calculations
        start = datetime.datetime.now()

        # Get a single frame from capture card
        bm_capture = blackmagic_image()

        bm_icons = crop_ability_icons(skill_coords, bm_capture)

        # Load query icons and their relative paths
        query_icons, query_paths = load_query_icons()

        # Loop queries and compare those to the icons in the image stream.
        for query_icon, query_path in zip(query_icons, query_paths):

            # Fetch the id [1-5] of a slotted skill that has ss < threshold.
            matched_idx = compare_icons(bm_icons, query_icon)

            if matched_idx is not None:
                if query_path in LONG_SKILLS:
                    timeremaining_bottom = SKILLS_BEING_TRACKED[query_path]
                    lower_skill_duration = SKILLS_BEING_TRACKED[query_path]

                else:
                    timeremaining_top = SKILLS_BEING_TRACKED[query_path]
                    upper_skill_duration = SKILLS_BEING_TRACKED[query_path]



        # Display 
        if bm_capture is not None:
            
            # Generate the top bar graph
            if timeremaining_top > 0:
                up_bar_lenght = int(600 * (timeremaining_top / upper_skill_duration))
                cv2.rectangle(bm_capture, 
                    (660, 815),
                    (1260, 820),
                    (255,255,255), thickness=1)
                
                cv2.rectangle(bm_capture, 
                    (660, 815),
                    (660+up_bar_lenght, 820),
                    (255,255,255), thickness=-1)
            
            # Generate the bottom bar graph
            if timeremaining_bottom > 0:
                low_bar_lenght = int(600 * (timeremaining_bottom / lower_skill_duration))

                if low_bar_lenght < 150 and (low_bar_lenght % 10) is 0:
                    color = (0,0,255)
                else:
                    color = (0,255,255)

                cv2.rectangle(bm_capture, 
                    (660, 835),
                    (1260, 840),
                    (0,255,255), thickness=1)
                cv2.rectangle(bm_capture, 
                    (660, 835),
                    (660+low_bar_lenght, 840),
                    color, thickness=-1)
            
            # Draw image on screen
            cv2.imshow('frame', bm_capture)
            
        
        # Exit if Q has been pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


        # Check how many seconds did the processing take
        deltaTime = (datetime.datetime.now() - start).total_seconds()

        if timeremaining_top > 0:
            timeremaining_top -= deltaTime

        if timeremaining_bottom > 0:
            timeremaining_bottom -= deltaTime

        # Empty pipe read
        pipe.stdout.flush()

    cv2.destroyAllWindows()
