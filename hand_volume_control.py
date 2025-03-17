import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Camera settings
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)  # Use laptop camera
cap.set(3, wCam)
cap.set(4, hCam)

pTime = 0
detector = htm.handDetector(detectionCon=0.7)

# Audio settings
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

volRange = volume.GetVolumeRange()
minVol, maxVol = volRange[0], volRange[1]
print(f"Volume Range: {minVol} to {maxVol}")

vol = 0
volBar = 400
volPer = 0

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture image")
        continue
        
    # Find hands
    img = detector.findHands(img)
    
    # IMPORTANT CHANGE: Unpack the tuple returned by findPosition
    lmList, bbox = detector.findPosition(img, draw=False)
    
    if len(lmList) != 0:  # Check if landmarks were detected
        # Thumb tip is landmark 4, index finger tip is landmark 8
        x1, y1 = lmList[4][1], lmList[4][2]   # Thumb tip
        x2, y2 = lmList[8][1], lmList[8][2]   # Index finger tip
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        # Draw hand points and connections
        cv2.circle(img, (x1, y1), 5, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 5, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        # Calculate distance
        length = math.hypot(x2 - x1, y2 - y1)
        print(f"Distance: {length}")

        # Hand range 50 - 300
        # Volume Range -65.25 - 0
        vol = np.interp(length, [50, 300], [minVol, maxVol])
        volBar = np.interp(length, [50, 300], [400, 150])
        volPer = np.interp(length, [50, 300], [0, 100])
        
        print(f"Volume: {vol}, Bar: {volBar}, Percent: {volPer}")
        
        # Set volume
        try:
            volume.SetMasterVolumeLevel(vol, None)
        except Exception as e:
            print(f"Error setting volume: {e}")

        # Visual indicator for close fingers
        if length < 50:
            cv2.circle(img, (cx, cy), 5, (0, 240, 0), cv2.FILLED)

    # Draw Volume Bar
    cv2.rectangle(img, (50, 150), (85, 400), (0, 235, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450),
                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 235, 0), 3)

    # Display FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50),
                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Img", img)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()