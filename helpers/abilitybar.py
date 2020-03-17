
import cv2

class AbilityBar():
    """
    A helper for keeping time values for ability bar.
    """
    def __init__(self):
        # Set ability info
        self.skillPath = None
        self.skillDuration = None
        self.skillIndex = None
        self.timeremaining = None

        # Set bar graph info
        self.bar_max_lenght = 400
        self.bar_color = (255, 255, 255)
        self.startXY = (260, 805)
        self.endXY = (660, 825)

    def set_timer(self, path, index, duration):
        
        if self.skillPath is None:
            print("[INFO] Skill detected. Setting path as: ", path)
            self.skillPath = path

        if self.skillIndex is None:
            print("[INFO] with index as: ", index)
            self.skillIndex = index

        if self.skillDuration is None:
            print("[INFO] and duration as: ", duration)
            self.skillDuration = duration
        
        self.timeremaining = duration


    def reduce_time(self, deltaTime):
        self.timeremaining -= deltaTime


    def _get_bar(self, flicker):
        # Calculate the lenght
        lenght = int(self.bar_max_lenght * (self.timeremaining / self.skillDuration))
        
        # Set default colors for the bar graph
        color = self.bar_color
        out_color = self.bar_color

        # Set the inner color to flicker color, if enabled.
        if flicker and lenght < 150 and (lenght % 10) == 0:
            return lenght, self.flicker_color, out_color

        return lenght, color, out_color

    def active(self):
        if self.timeremaining is not None:
            if self.timeremaining > 0 and self.skillDuration is not None:
                return True
        # Return False if set_timer() hasn't been run or timer has reached 0.
        return False

    def draw_bar(self, bm_capture, flicker=False):
        # Get bar lenght and color
        lenght, color, out_color = self._get_bar(flicker)
        
        # Get values for readability reasons
        startXY = self.startXY
        endXY = self.endXY

        # Calculate end point for the bar rectangle
        endVals = (startXY[0] + lenght, endXY[1])

        # Draw outer border
        cv2.rectangle(bm_capture, startXY, endXY, out_color, thickness=1)
        
        # Draw inner bar
        cv2.rectangle(bm_capture, startXY, endVals, color, thickness=-1)

        return bm_capture


class LongAbilityBar(AbilityBar):
    def __init__(self):
        # Initialize with superclass's values
        super().__init__()

        # Add own spices
        self.bar_color = (0, 255, 255)
        self.flicker_color = (0, 0, 255)
        self.startXY = (260, 835)
        self.endXY = (660, 855)


class LaAbilityBar(AbilityBar):
    def __init__(self):
        # Initialize with superclass's values
        super().__init__()

        # Add own spices
        self.bar_color = (255, 255, 255)
        self.flicker_color = (0, 0, 255)
        self.startXY = (760, 150)
        self.endXY = (1160, 170)

        # Global cooldown
        self.skillDuration = 0.9

    def set_la_timer(self):
        self.timeremaining = self.skillDuration



if __name__ == "__main__":
    print("Welcome to the testing area!")
    upperbar = AbilityBar()
    lowerbar = LongAbilityBar()
    lightatt_bar = LaAbilityBar(gdc=1.0)

    upperbar.set_timer("Parent_path", 1, 10.0)
    lowerbar.set_timer("Child path", 2, 20.0)
    lightatt_bar.set_la_timer()