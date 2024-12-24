import statistics
import threading
import time
import cv2
from matplotlib import pyplot as plt
import numpy as np
import copy


MIN_AREA = 20
# Load in external webcam's video path
cap = cv2.VideoCapture(1)

# blue color range in HSV
lower_blue = np.array([90, 77, 50])
upper_blue = np.array([115, 255, 255])

# green color range in HSV
lower_green = np.array([43, 70, 70])
upper_green = np.array([85, 255, 255])

def nothing(x):
    pass

def tune_HSV_Blue():
    global lower_blue, upper_blue

    cv2.namedWindow("Trackbars-Blue")
    cv2.createTrackbar("BLUEL-H1", "Trackbars-Blue", 90, 255, nothing)
    cv2.createTrackbar("BLUEL-S1", "Trackbars-Blue", 77, 255, nothing)
    cv2.createTrackbar("BLUEL-V1", "Trackbars-Blue", 50, 255, nothing)
    cv2.createTrackbar("BLUEU-H1", "Trackbars-Blue", 115, 255, nothing)
    cv2.createTrackbar("BLUEU-S1", "Trackbars-Blue", 255, 255, nothing)
    cv2.createTrackbar("BLUEU-V1", "Trackbars-Blue", 255, 255, nothing)

    while True:
        if not cap.isOpened():
            print("Error. Could not open webcam.")
            return
        ret, frame = cap.read()
        if not ret:
            # Reset to the first frame/loop the video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  
            continue  

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lh1 = cv2.getTrackbarPos("BLUEL-H1", "Trackbars-Blue")
        ls1 = cv2.getTrackbarPos("BLUEL-S1", "Trackbars-Blue")
        lv1 = cv2.getTrackbarPos("BLUEL-V1", "Trackbars-Blue")
        uh1 = cv2.getTrackbarPos("BLUEU-H1", "Trackbars-Blue")
        us1 = cv2.getTrackbarPos("BLUEU-S1", "Trackbars-Blue")
        uv1 = cv2.getTrackbarPos("BLUEU-V1", "Trackbars-Blue")

        lower_blue = np.array([lh1, ls1, lv1])
        upper_blue = np.array([uh1, us1, uv1])

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        hsv_frame[:, :, 2] = clahe.apply(hsv_frame[:, :, 2])

        mask = cv2.inRange(hsv_frame, lower_blue, upper_blue)

        cv2.imshow("Mask-Blue", mask)
        key  = cv2.waitKey(1)
        if key == 13:
            break
    cv2.destroyWindow("Trackbars-Blue")
    cv2.destroyWindow("Mask-Blue")

def tune_HSV_Green():
    global lower_green, upper_green

    cv2.namedWindow("Trackbars-Green")
    cv2.createTrackbar("GREL-H1", "Trackbars-Green", 43, 255, nothing)
    cv2.createTrackbar("GREL-S1", "Trackbars-Green", 70, 255, nothing)
    cv2.createTrackbar("GREL-V1", "Trackbars-Green", 70, 255, nothing)
    cv2.createTrackbar("GREU-H1", "Trackbars-Green", 85, 255, nothing)
    cv2.createTrackbar("GREU-S1", "Trackbars-Green", 255, 255, nothing)
    cv2.createTrackbar("GREU-V1", "Trackbars-Green", 255, 255, nothing)

    while True:
        if not cap.isOpened():
            print("Error. Could not open webcam.")
            return
        ret, frame = cap.read()
        if not ret:
            # Reset to the first frame/loop the video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  
            continue  

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lh1 = cv2.getTrackbarPos("GREL-H1", "Trackbars-Green")
        ls1 = cv2.getTrackbarPos("GREL-S1", "Trackbars-Green")
        lv1 = cv2.getTrackbarPos("GREL-V1", "Trackbars-Green")
        uh1 = cv2.getTrackbarPos("GREU-H1", "Trackbars-Green")
        us1 = cv2.getTrackbarPos("GREU-S1", "Trackbars-Green")
        uv1 = cv2.getTrackbarPos("GREU-V1", "Trackbars-Green")

        lower_green = np.array([lh1, ls1, lv1])
        upper_green = np.array([uh1, us1, uv1])

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        hsv_frame[:, :, 2] = clahe.apply(hsv_frame[:, :, 2])

        mask = cv2.inRange(hsv_frame, lower_green, upper_green)

        cv2.imshow("Mask-Green", mask)

        key = cv2.waitKey(1)
        if key == 13:
            break
    cv2.destroyWindow("Trackbars-Green")
    cv2.destroyWindow("Mask-Green")


bufSize = 10
bufferBlue = np.zeros(bufSize, dtype = int)
bufferGreen = np.zeros(bufSize, dtype = int)
bufIndex = 0

predictionGreen = -1
predictionBlue = -1
   
drum0XMin = 0
drum0XMax = 0
drum0YMin = 0
drum0YMax = 0

drum1XMin = 0
drum1XMax = 0
drum1YMin = 0
drum1YMax = 0

drum2XMin = 0
drum2XMax = 0
drum2YMin = 0
drum2YMax = 0

drum3XMin = 0
drum3XMax = 0
drum3YMin = 0
drum3YMax = 0

def processDrumPads(drumPads):
    global drum0XMin
    global drum0XMax
    global drum0YMin
    global drum0YMax

    global drum1XMin
    global drum1XMax
    global drum1YMin
    global drum1YMax

    global drum2XMin
    global drum2XMax
    global drum2YMin
    global drum2YMax

    global drum3XMin
    global drum3XMax
    global drum3YMin
    global drum3YMax

    drum0X, drum0Y, drum0R = drumPads[0]
    drum0XMin = drum0X - drum0R
    drum0XMax = drum0X + drum0R
    drum0YMin = drum0Y - drum0R
    drum0YMax = drum0Y + drum0R

    drum1X, drum1Y, drum1R = drumPads[1]
    drum1XMin = drum1X - drum1R
    drum1XMax = drum1X + drum1R
    drum1YMin = drum1Y - drum1R
    drum1YMax = drum1Y + drum1R

    drum2X, drum2Y, drum2R = drumPads[2]
    drum2XMin = drum2X - drum2R
    drum2XMax = drum2X + drum2R
    drum2YMin = drum2Y - drum2R
    drum2YMax = drum2Y + drum2R

    drum3X, drum3Y, drum3R = drumPads[3]
    drum3XMin = drum3X - drum3R
    drum3XMax = drum3X + drum3R
    drum3YMin = drum3Y - drum3R
    drum3YMax = drum3Y + drum3R


def getPrediction(x, y):
    if ((x >= drum0XMin) and (x <= drum0XMax) and 
        (y >= drum0YMin) and (y <= drum0YMax)):
        return 1
    elif ((x >= drum1XMin) and (x <= drum1XMax) and 
        (y >= drum1YMin) and (y <= drum1YMax)):
        return 2
    elif ((x >= drum2XMin) and (x <= drum2XMax) and 
        (y >= drum2YMin) and (y <= drum2YMax)):
        return 3
    elif ((x >= drum3XMin) and (x <= drum3XMax) and 
        (y >= drum3YMin) and (y <= drum3YMax)):
        return 4
    else:
        # Ignore if not in a drum ring
        return -1
    
processTimes = []

greenBufferLock = threading.Lock()
blueBufferLock = threading.Lock()
bufIndexLock = threading.Lock()
def readFrames(color, drumPads, testing=False):
    processDrumPads(drumPads)
    global lower_blue, upper_blue
    global lower_green, upper_green
    global predictionGreen, predictionBlue
    global processTimes

    while True:
        if not cap.isOpened():
            print("Error. Could not open webcam.")
            return
        ret, frame = cap.read()
        if not ret:
            # Reset to the first frame/loop the video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  
            continue  

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        hsv_frame[:, :, 2] = clahe.apply(hsv_frame[:, :, 2])

        if (color == "green"):
            mask = cv2.inRange(hsv_frame, lower_green, upper_green)
        else:
            mask = cv2.inRange(hsv_frame, lower_blue, upper_blue)
        blurred_mask = cv2.GaussianBlur(mask, (5, 5), 2)

        contours, _ = cv2.findContours(blurred_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        prediction = -1
        # Continuously yield and store predictions
        if len(contours) > 0:
            if cv2.contourArea(contours[0]) > MIN_AREA:
                (x, y), r = cv2.minEnclosingCircle(contours[0])
                if testing == True:
                    if r > 4:  # Check for a reasonable size
                        cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 0), 2)
                        cv2.putText(frame, "Tip Detected", (int(x), int(y) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                    cv2.imshow("Detection", frame)
                    cv2.waitKey(1)
                prediction = getPrediction(x, y)
            if color == 'green':
                with greenBufferLock:
                    predictionGreen = prediction
            else:
                with blueBufferLock:
                    predictionBlue = prediction

alpha = 0.8

def plot_data():
    global processTimes

    times_cp = processTimes[:]
    avg = statistics.mean(times_cp)
    print("Average: ", avg)
    
    plt.scatter(range(len(times_cp)), times_cp, label=f'CV processing latency')
    plt.xlabel('Time step (s)')
    plt.ylabel("Processing Time (s)")
    plt.title("CV Processing Times per Frame")
    plt.legend()
    plt.grid()
    plt.show()

def findDSBlue():
    global predictionBlue
    with blueBufferLock:
        return predictionBlue

def findDSGreen():
    global predictionGreen
    with greenBufferLock:
        return predictionGreen

if __name__ == '__main__':
    print("Tuning Blue")
    tune_HSV_Blue()
    print("Tuning Green")
    tune_HSV_Green()
    drumPadLocations = [(677.0, 180.0, 54.0), (526.0, 170.0, 72.0), (610.0, 306.0, 84.0), (380.0, 260.0, 92.0)]
    readFrames('green', drumPadLocations)


