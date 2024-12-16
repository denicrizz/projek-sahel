import cv2
import time
import math

# Classifier File
carCascade = cv2.CascadeClassifier("vech.xml")

# Video file capture
video = cv2.VideoCapture("carsVideo.mp4")

# Constant Declaration
WIDTH = 1280
HEIGHT = 720

def estimateSpeed(location1, location2):
    """
    Estimate vehicle speed based on pixel movement
    
    :param location1: Previous location [x, y, w, h]
    :param location2: Current location [x, y, w, h]
    :return: Estimated speed in km/h
    """
    d_pixels = math.sqrt(math.pow(location2[0] - location1[0], 2) + math.pow(location2[1] - location1[1], 2))
    ppm = 8.8  # pixels per meter
    d_meters = d_pixels / ppm
    fps = 18
    speed = d_meters * fps * 3.6
    return speed

def trackMultipleObjects():
    rectangleColor = (0, 255, 255)
    frameCounter = 0
    currentCarID = 0
    fps = 0

    # Tracker list and locations
    trackers = []
    carLocation1 = {}
    carLocation2 = {}
    speed = [None] * 1000
    carIDs = []

    # Video writer
    out = cv2.VideoWriter('outTraffic.avi', cv2.VideoWriter_fourcc('M','J','P','G'), 10, (WIDTH, HEIGHT))

    while True:
        start_time = time.time()
        rc, image = video.read()
        if image is None:
            break

        image = cv2.resize(image, (WIDTH, HEIGHT))
        resultImage = image.copy()

        frameCounter += 1

        # Detect cars every 10 frames
        if frameCounter % 10 == 0:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))

            # Reset trackers
            trackers = []
            carLocation1.clear()
            carLocation2.clear()
            carIDs.clear()

            # Add new trackers for detected cars
            for (x, y, w, h) in cars:
                # Create tracker
                tracker = cv2.legacy.TrackerKCF_create()
                tracker.init(image, (x, y, w, h))
                trackers.append(tracker)
                
                # Store car location
                carLocation1[currentCarID] = [x, y, w, h]
                carIDs.append(currentCarID)
                currentCarID += 1

        # Update trackers
        for idx, tracker in enumerate(trackers):
            success, box = tracker.update(image)
            
            if success:
                x, y, w, h = [int(v) for v in box]
                cv2.rectangle(resultImage, (x, y), (x+w, y+h), rectangleColor, 4)
                
                # Update car locations
                carID = carIDs[idx]
                carLocation2[carID] = [x, y, w, h]

                # Speed estimation
                if frameCounter % 1 == 0:
                    [x1, y1, w1, h1] = carLocation1[carID]
                    
                    # Update location for next iteration
                    carLocation1[carID] = [x, y, w, h]

                    # Speed calculation similar to original code
                    if [x1, y1, w1, h1] != [x, y, w, h]:
                        if speed[carID] is None and y1 >= 275 and y1 <= 285:
                            speed[carID] = estimateSpeed([x1, y1, w1, h1], [x, y, w, h])

                        if speed[carID] is not None and y1 >= 180:
                            cv2.putText(resultImage, f"{int(speed[carID])}km/h", 
                                        (int(x1 + w1/2), int(y1-5)), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 100), 2)

        # Display and write output
        cv2.imshow('result', resultImage)
        out.write(resultImage)

        # Exit on ESC key
        if cv2.waitKey(1) == 27:
            break

    # Cleanup
    cv2.destroyAllWindows()
    out.release()
    video.release()

if __name__ == '__main__':
    trackMultipleObjects()