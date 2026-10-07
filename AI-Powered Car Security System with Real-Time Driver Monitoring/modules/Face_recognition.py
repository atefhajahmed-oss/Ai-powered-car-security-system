import face_recognition
import os, sys
import cv2
import math
import numpy as np
from modules.camera_module import WebCamera_module
import time 
import platform

# GPIO Configuration - only for Raspberry Pi
if platform.system() == 'Linux' and os.path.exists('/sys/firmware/devicetree/base/model'):
    import RPi.GPIO as GPIO
    FACE_LED_PIN = 17
    USE_GPIO = True
else:
    USE_GPIO = False

def face_confidence(face_distance, face_match_threshold=0.6):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'

class FaceRecognition:
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_encodings = []
    known_face_names = []
    process_current_frame = True

    def __init__(self):
        # Setup GPIO only if on Raspberry Pi
        if USE_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(FACE_LED_PIN, GPIO.OUT)
        self.encode_faces()
        self.init_cv2_camera(0)

    def init_cv2_camera(self, webcam):
        self.cam = WebCamera_module()
        self.cam.init_camera()
        if not self.cam.get_cam_status():
            print("Error: Could not open video device, exiting ... ")
            self.stop_cv2_camera()
            sys.exit()

    def encode_faces(self):
        for image in os.listdir('faces'):
            face_image = face_recognition.load_image_file(f'faces/{image}')
            face_encodings = face_recognition.face_encodings(face_image)
            
            if face_encodings:
                self.known_face_encodings.append(face_encodings[0])
                self.known_face_names.append(image)
            else:
                print(f"No face found in image {image}")
                break

        print(self.known_face_names)

    def read_frame_cv2(self):
        return self.video_capture.read()

    def stop_cv2_camera(self):
        self.cam.stop_camera()
        if USE_GPIO:
            GPIO.output(FACE_LED_PIN, GPIO.LOW)

    def run_recognition(self):
        print("Appuyez sur 'q' pour quitter...")
        if USE_GPIO:
            GPIO.output(FACE_LED_PIN, GPIO.HIGH)
        
        while True:
            frame = self.cam.read_cam_frame()
            if frame is None:
                break
                
            frame = cv2.flip(frame, 1)
            
            if self.process_current_frame:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                self.face_locations = face_recognition.face_locations(rgb_small_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)

                self.face_names = []
                for face_encoding in self.face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = 'Inconnu'
                    confidence = 'Inconnu'

                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index].split('.')[0]
                            confidence = face_confidence(face_distances[best_match_index])
                    
                    self.face_names.append(f'{name} ({confidence})')

            self.process_current_frame = not self.process_current_frame

            # Contrôle de la LED
            if not self.face_locations:
                if USE_GPIO:
                    GPIO.output(FACE_LED_PIN, GPIO.LOW)
            else:
                if USE_GPIO:
                    GPIO.output(FACE_LED_PIN, GPIO.HIGH)

            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow('Reconnaissance Faciale', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop_cv2_camera()
        cv2.destroyAllWindows()
    
    def check_face(self):
        start_time = time.time()
        valid = False
        names = 'Unknown'
        
        while True:
            if time.time()-start_time > 10:
                self.stop_cv2_camera()
                cv2.destroyAllWindows()
                self.cam = None
                return False
                
            frame = self.cam.read_cam_frame()
            if frame is None:
                break
                
            frame = cv2.flip(frame, 1)
            
            if self.process_current_frame:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                self.face_locations = face_recognition.face_locations(rgb_small_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)

                self.face_names = []
                for face_encoding in self.face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    names = 'Unknown'
                    confidence = 'Unknown'

                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)

                    if matches[best_match_index]:
                        names = self.known_face_names[best_match_index].split('.')[0]
                        confidence = face_confidence(face_distances[best_match_index])
                        valid = True
                        
                    self.face_names.append(f'{names} ({confidence})')

            self.process_current_frame = not self.process_current_frame

            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom), (right, bottom + 20), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom + 15), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

            cv2.imshow('Face Recognition', frame)
            if valid:
                break
            if cv2.waitKey(1) == ord('q'):
                break

        self.stop_cv2_camera()
        cv2.destroyAllWindows()
        self.cam = None
        return names if valid else False