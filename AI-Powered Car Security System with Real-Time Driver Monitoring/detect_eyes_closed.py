import cv2
import mediapipe as mp
import face_recognition
import numpy as np
from modules.camera_module import WebCamera_module

cam = WebCamera_module()
cam.init_camera()
# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Load your reference image and encode it
reference_image = face_recognition.load_image_file("mohamed.jpg")  # Replace with your reference image file
reference_encoding = face_recognition.face_encodings(reference_image)[0]

# Eye landmarks for MediaPipe
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Function to calculate Eye Aspect Ratio (EAR)
def calculate_ear(landmarks, eye_points):
    A = np.linalg.norm(landmarks[eye_points[1]] - landmarks[eye_points[5]])
    B = np.linalg.norm(landmarks[eye_points[2]] - landmarks[eye_points[4]])
    C = np.linalg.norm(landmarks[eye_points[0]] - landmarks[eye_points[3]])
    return (A + B) / (2.0 * C)

process_allowed=True
# Start capturing video
while cam.get_cam_status():
    frame = cam.read_cam_frame()
       # Flip and process frame
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if process_allowed : 
    # Recognize face using face_recognition
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces([reference_encoding], face_encoding)
            if matches[0]:  # If the face matches your reference image
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, "Mohamed", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Use MediaPipe for facial landmarks
                results = face_mesh.process(rgb_frame)
                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in face_landmarks.landmark])
                        h, w, _ = frame.shape
                        landmarks = landmarks * [w, h, 1]

                        # Calculate EAR for eyes
                        left_ear = calculate_ear(landmarks, LEFT_EYE)
                        right_ear = calculate_ear(landmarks, RIGHT_EYE)
                        ear = (left_ear + right_ear) / 2.0

                        # Check if eyes are closed
                        if ear < 0.25:  # Adjust threshold if needed
                            cv2.putText(frame, "Eyes Closed", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        else:
                            cv2.putText(frame, "Eyes Open", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    process_allowed = not process_allowed
    # Show the video feed
    cv2.imshow("Face Recognition and Eye Detection", frame)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.stop_camera()
cv2.destroyAllWindows()
