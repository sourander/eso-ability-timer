from skimage.metrics import structural_similarity as ssim
from imutils import paths
from imutils.video import FPS
from helpers.abilitybar import AbilityBar
from helpers.abilitybar import LongAbilityBar
from helpers.abilitybar import LaAbilityBar
import subprocess as sp
import cv2
import numpy as np
import argparse
import datetime


ap = argparse.ArgumentParser()
ap.add_argument("-p", "--profile", 
    help='Choose your profile. Available: TankDK, MagPlar, MagDen, StamBlade, StamCro, BowCro') 
ap.add_argument('--nographics', action='store_true', 
    help='Toggle the ability bars off. Just display the raw input image.')
ap.add_argument('--fullscreen', action='store_true', 
    help='Launch in full screen. Your monitor should have Full HD display resolution for this to function correctly.')
ap.add_argument('--fps', action='store_true', 
    help='Turn FPS calculations ON.')
args = vars(ap.parse_args())


if args["profile"] == "TankDK":
    SKILLS_BEING_TRACKED = {'images/cropped/BlockadeOfStorms.png': 14.0,
                            'images/cropped/Balance.png': 25.0,
                            'images/cropped/BlockadeOfFrost.png': 14.0}

    LONG_SKILLS = ['images/cropped/Balance.png']

elif args["profile"] == "MagPlar":
    SKILLS_BEING_TRACKED = {'images/cropped/UnstableWallOfElements.png': 10.0,
                            'images/cropped/BarbedTrap.png': 18.0}

    LONG_SKILLS = ['images/cropped/BarbedTrap.png']

elif args["profile"] == "MagDen":
    SKILLS_BEING_TRACKED = {'images/cropped/GrippingShards.png': 12.0,
                            'images/cropped/BlueBetty.png': 25.0}

    LONG_SKILLS = ['images/cropped/BlueBetty.png']

elif args["profile"] == "StamBlade":
    SKILLS_BEING_TRACKED = {'images/cropped/LeechingStrikes.png': 10.0,
                            'images/cropped/RaceAgainstTheTime.png': 12.0}

    LONG_SKILLS = ['images/cropped/RaceAgainstTheTime.png']

elif args["profile"] == "StamCro":
    SKILLS_BEING_TRACKED = {'images/cropped/EndlessHail.png': 14.0,
                            'images/cropped/BarbedTrap.png': 18.0}

    LONG_SKILLS = ['images/cropped/BarbedTrap.png']

elif args["profile"] == "BowCro":
    SKILLS_BEING_TRACKED = {'images/cropped/EndlessHail.png': 14.0,
                            'images/cropped/SkeletalArcher.png': 16.0}

    LONG_SKILLS = ['images/cropped/SkeletalArcher.png']

else:
    print("[WARNING] You are not using ANY profile.")

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

def strip_locations():
    # Set values from ESO UI. Offset is 64x64 box's width plus the 10px margin.
    OFFSET = 64 + 10
    CROPSIZE = 67

    # Reserve a dictionary for skill xy coords
    skills = {}

    # Calculate xy-coordinates of the skill icons
    for i in range(0,5):
        yStart, yEnd = 982, 984
        xStart = 786 + (i * OFFSET)
        xEnd = xStart + CROPSIZE
        skills[i+1] = (yStart, yEnd, xStart, xEnd)

    return skills

def blackmagic_image():
    # Capture data from pipe
    raw_image = pipe.stdout.read(1920*1080*3)

    # transform the raw data into a numpy array
    image =  np.fromstring(raw_image, dtype='uint8')

    # Reshape to Full HD
    image = image.reshape((1080,1920,3))

    return image

def crop_ability_icons(skill_coords, image, bgr=False):
    bm_crops = []

    for i in skill_coords.keys():
        (yStart, yEnd, xStart, xEnd) = skill_coords[i]
        crop = image[yStart:yEnd, xStart:xEnd]
        
        # BGR channels not wanted, keep only R. 
        if not bgr:
            _,_,crop = cv2.split(crop)
        
        bm_crops.append(crop)

    return bm_crops

def compare_icons(bm_icons, query_icon):
    for i, icon in enumerate(bm_icons, 1):
        ss = ssim(icon, query_icon)
        if ss > 0.80:
            return i
    return None

def analyse_icon(bm_icon_tops, threshold=20, verbose=False):
    # Similar to compare icons, but finds out if a skill
    # has been activated without caring what the actual skill
    # is. Reasoning: if a skill has been activated, we must
    # be interested in global cooldown metronome. 
    LA_FOUND = False

    for i, icon in enumerate(bm_icon_tops, start=1):
        feature = cv2.mean(icon)
        
        hsv = cv2.cvtColor(icon, cv2.COLOR_BGR2HSV)
        feature = np.array(cv2.mean(hsv)[:3]).astype(int)

        # Let's half the saturation and value to reduce their weight on euclidean distance.
        feature[1] = feature[1] // 2
        feature[2] = feature[2] // 2

        # These HSV values correspond to the yellow glow around
        # an activated skill icon
        ICON = [42, 120, 90]
        dist = np.linalg.norm(feature - ICON).astype(int)

        if verbose and dist < threshold:
            print(f"[INFO] Slot {i}, feature: {feature}, dist: {dist}")

        if dist < threshold:
            LA_FOUND = True
    
    return LA_FOUND

def load_query_icons(only_two_skills=None):
    # Reserve lists for query images and their paths
    query_icons = []
    query_paths = []

    # Either go through all skills in SKILLS_BEING_TRACKED
    # Or use the ones already set in both Ability bars.
    # This is useful e.g. if using both lightning and ice staves
    # on a tank in different content.
    if only_two_skills is None:
        paths = SKILLS_BEING_TRACKED.keys()
    else:
        paths = only_two_skills

    # Load all images from images/cropped/ and store them in lists
    for path in paths:
        
        # Load image and keep only Red channel
        query_icon = cv2.imread(path)
        _,_,query_icon = cv2.split(query_icon)

        # Append to lists
        query_icons.append(query_icon)
        query_paths.append(path)

    return query_icons, query_paths

if __name__ == "__main__":

    # Launch FFMPEG with Blackmagic settings    
    FFMPEG_BIN = "ffmpeg"
    command = [ FFMPEG_BIN,
        '-hide_banner',
        '-loglevel','warning',
        '-raw_format','bgra',
        '-format_code','Hp59',
        '-f','decklink',
        '-i', 'Intensity Pro 4K',
        '-pix_fmt', 'bgr24',
        '-vcodec', 'rawvideo',
        '-an','-sn',
        '-f', 'image2pipe', '-'] 

    # Get data from ffmpeg pipe    
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=-1)

    # Instansiate classes and important variables
    if not args['nographics']:
        # Dictionary for skills[i] = (yStart, yEnd, xStart, xEnd)
        skill_coords = skill_locations()
        skill_tops_coords = strip_locations()

        # Instanciate ability bars.
        upperbar = AbilityBar()
        lowerbar = LongAbilityBar()
        lightatt_bar = LaAbilityBar()


    # Load the initial query icons and paths. ALL of these
    # will be compared to slots 1-5 before the set_timer()
    # has been run on 1 long and 1 short skill
    query_icons, query_paths = load_query_icons()
    selected = None

    if args['fullscreen']:
        cv2.namedWindow('ElderSCrollsOnline', cv2.WINDOW_FREERATIO)
        cv2.setWindowProperty('ElderSCrollsOnline', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    if args['fps']:
        fps = FPS().start()

    # Main loop
    while True:
        
        if not args['nographics']:
            # Get time for deltaTime calculations
            start = datetime.datetime.now()

        # Get a single ElderSCrollsOnline from capture card
        bm_capture = blackmagic_image()

        # Empty pipe read
        pipe.stdout.flush()

        # Crop icons from the BlackMagic source
        if not args['nographics']:
            bm_icons = crop_ability_icons(skill_coords, bm_capture)

            # Try to select only two abilities to boost performance 
            # in a situation where len(SKILLS_BEING_TRACKED) > 2
            if  selected == None:
                if None not in [upperbar.skillPath, lowerbar.skillPath]:
                    # Load query icons and paths again.
                    # If e.g. lightning and ice staff abilities are both in
                    # SKILLS_BEING_TRACKED, one is now dropped out.
                    selected = [upperbar.skillPath, lowerbar.skillPath]
                    query_icons, query_paths = load_query_icons(only_two_skills=selected)

                            
            # Loop queries and compare those to the icons in the image stream.
            for query_icon, query_path in zip(query_icons, query_paths):

                # Fetch the id [1-5] of a slotted skill that has ss < threshold.
                matched_idx = compare_icons(bm_icons, query_icon)

                if matched_idx is not None:
                    if query_path in LONG_SKILLS:
                        lowerbar.set_timer(query_path, matched_idx, SKILLS_BEING_TRACKED[query_path])
                    else:
                        upperbar.set_timer(query_path, matched_idx, SKILLS_BEING_TRACKED[query_path])


        # Crop strips and compare their HSV values to the values set in analyse_icon()
        if not args['nographics']:
            bm_icon_tops = crop_ability_icons(skill_tops_coords, bm_capture, bgr=True)

            ANY_SKILL_PRESSED = analyse_icon(bm_icon_tops, verbose=False)

            if ANY_SKILL_PRESSED:
                print("Setting timer")
                lightatt_bar.set_la_timer()


        """
        DISPLAY IMAGES
        """

        if bm_capture is not None:
            # Update graphics bars
            if not args['nographics']:
                if upperbar.active():
                    bm_capture = upperbar.draw_bar(bm_capture)

                if lowerbar.active():
                    bm_capture = lowerbar.draw_bar(bm_capture, flicker=True)

                if lightatt_bar.active():
                    bm_capture = lightatt_bar.draw_bar(bm_capture)
            
            # Draw image on screen
            cv2.imshow('ElderSCrollsOnline', bm_capture)
            
        # Exit if Q has been pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        """
        UPDATE TIMERS
        """

        if not args['nographics']:
            # Check how many seconds did the processing take
            deltaTime = (datetime.datetime.now() - start).total_seconds()


            # Reduce the deltaTime from any active ability timers
            if upperbar.active():
                upperbar.reduce_time(deltaTime)

            if lowerbar.active():
                lowerbar.reduce_time(deltaTime)

            if lightatt_bar.active():
                lightatt_bar.reduce_time(deltaTime)

        if args['fps']:
            fps = FPS().start()


    """
    PERFORM CLEANUP
    """

    if args['fps']:
        fps.stop()
        print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    
    # Empty pipe read
    pipe.stdout.flush()
    cv2.destroyAllWindows()
