# face_recognition.py
import cv2
import numpy as np
import os
import RPi.GPIO as GPIO
import time
from modules.camera_module import WebCamera_module


GPIO.setmode(GPIO.BCM)
GPIO.setup(14,GPIO.OUT)
GPIO.setup(15,GPIO.OUT)

# Charger le classificateur de visage LBPH
face_recognizer = cv2.face.LBPHFaceRecognizer_create()
face_recognizer.read("face_trained.yml")  # Assurez-vous que le modèle est bien entraîné

# Charger le dictionnaire d'étiquettes pour les noms
label_dict = np.load("face_labels.npy", allow_pickle=True).item()

# Initialiser le détecteur de visages
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialiser la caméra
cam = WebCamera_module()
cam.init_camera()

while True:
    #ret, frame = cap.read()
    frame = cam.read_cam_frame()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    for (x, y, w, h) in faces:
        face_region = gray[y:y+h, x:x+w]
        face_id, confidence = face_recognizer.predict(face_region)

        # Identifier le nom de la personne avec une confiance seuil
        if confidence < 80:
            name = label_dict[face_id]
        else:
            name = "Inconnu"

        if name == "Inconnu":
            GPIO.output(14,GPIO.HIGH)
            GPIO.output(15,GPIO.LOW)
        else:
            GPIO.output(14,GPIO.LOW)
            GPIO.output(15,GPIO.HIGH)
        # Afficher l'identité
        cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow('Reconnaissance faciale', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
