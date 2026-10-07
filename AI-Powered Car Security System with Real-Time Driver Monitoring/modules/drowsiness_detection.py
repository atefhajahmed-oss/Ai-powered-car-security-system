import cv2
import dlib
import numpy as np
import time
import sys
from scipy.spatial import distance
from modules.camera_module import WebCamera_module

# Constants for drowsiness detection
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 20

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

class drowsiness:
    def __init__(self):
        try:
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor('modules/shape_predictor_68_face_landmarks.dat')
            self.cam = WebCamera_module()
            self.cam.init_camera()
            
            if not self.cam.get_cam_status():
                print("Error: Could not open video device")
                self.cleanup()
                sys.exit(1)
                
            self.last_alert_time = time.time()
            self.alert_interval = 2.0
            self.last_ear = 0.0  # Stocker le dernier EAR calculé
            
        except Exception as e:
            print(f"Error initializing camera: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        if hasattr(self, 'cam'):
            self.cam.stop_camera()
        cv2.destroyAllWindows()

    def get_last_ear(self):
        return self.last_ear

    def detect_drowsiness_state(self):
        try:
            counter_sleep = 0
            counter_awake = 0
            ALERT_TRIGGERED = False
            start_time = time.time()
            face_detected = False

            while True:
                frame = self.cam.read_cam_frame()
                if frame is None:
                    print("Error: Could not read frame from camera")
                    return None

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.detector(gray)

                if len(faces) == 0:
                    face_detected = False
                    return None

                face_detected = True
                for face in faces:
                    landmarks = self.predictor(gray, face)
                    left_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)])
                    right_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)])

                    left_ear = eye_aspect_ratio(left_eye)
                    right_ear = eye_aspect_ratio(right_eye)
                    ear = (left_ear + right_ear) / 2.0
                    self.last_ear = ear  # Stocker le dernier EAR

                    if ear < EYE_AR_THRESH:
                        counter_sleep += 1
                        if counter_sleep >= 10:
                            counter_awake = 0
                    else:
                        counter_awake += 1
                        if counter_awake >= 15:
                            counter_sleep = 0
                            return False

                    current_time = time.time()
                    if counter_sleep == EYE_AR_CONSEC_FRAMES:
                        if not ALERT_TRIGGERED and (current_time - self.last_alert_time) >= self.alert_interval:
                            ALERT_TRIGGERED = True
                            self.last_alert_time = current_time
                            elapsed_time = int(current_time - start_time)
                            print(f"Drowsiness detected! Session time: {elapsed_time}s")
                            return True
                    else:
                        ALERT_TRIGGERED = False

                    left_eye_hull = cv2.convexHull(left_eye)
                    right_eye_hull = cv2.convexHull(right_eye)
                    cv2.drawContours(frame, [left_eye_hull], -1, (0, 255, 0), 1)
                    cv2.drawContours(frame, [right_eye_hull], -1, (0, 255, 0), 1)
                    cv2.putText(frame, f"EAR: {ear:.2f}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow("Drowsiness Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            return False if face_detected else None

        except Exception as e:
            print(f"Error in drowsiness detection: {str(e)}")
            return None
        finally:
            self.cleanup()

# Function to run drowsiness detection
def detect_drowsiness():
    try:
        detect = drowsiness()
        counter = 0
        first_alert = False
        second_alert = False
        third_alert = False
        
        print("Drowsiness detection started. Press 'q' to quit.")
        
        while True:
            result = detect.detect_drowsiness_state()
            if result is None:
                continue  # No face detected or frame couldn't be read
                
            if result:
                counter += 1
                print(f"Drowsy state detected! Counter: {counter}")
            else:
                if counter > 0:
                    print("Alert cleared - Driver is awake")
                counter = 0
                first_alert = False
                second_alert = False
                third_alert = False
                
            if counter == 1 and not first_alert:
                first_alert = True
                print("First alert on - Please stay alert!")
            elif counter == 2 and not second_alert:
                second_alert = True
                print("Second alert on - Warning: High drowsiness detected!")
            elif counter == 3 and not third_alert:
                third_alert = True
                print("Emergency: Car stopped - Driver is too drowsy to continue")
                break
    
    except Exception as e:
        print(f"Error in drowsiness detection: {str(e)}")
    finally:
        if 'detect' in locals():
            detect.cleanup()

# Run the drowsiness detection function
"""
if __name__ == "__main__":
    #print(detect_drowsiness_state())
    coutner = 0
    first_alert = False
    second_alert = False
    third_alert = False
    detect = drowsiness()
    while True:
        if detect.detect_drowsiness_state():
            counter += 1
        else :
            counter = 0
            first_alert = False
            second_alert = False
            third_alert = False
            
        if counter == 1 and not first_alert:
            first_alert= True
            print("first alers onn")
        elif counter == 2 and not second_alert:
            second_alert= True
            print("second alers on")
        elif counter == 3 and not third_alert:
            third_alert= True
            print("car stoped")
            break
"""