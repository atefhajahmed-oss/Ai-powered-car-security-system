import cv2
import dlib
import numpy as np
from modules.Face_recognition import FaceRecognition
from modules.drowsiness_detection import drowsiness
from modules.camera_module import WebCamera_module
from modules.shared import IS_RASPBERRY_PI, init_gpio, handle_drowsy_state, cleanup_gpio, control_face_led
from scipy.spatial import distance
import time
import sys

print("Initializing test environment...")
if IS_RASPBERRY_PI:
    init_gpio()

# Constantes pour la détection de somnolence
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 20

def test_face_recognition():
    print("\n=== Test de la reconnaissance faciale ===")
    face_recognizer = FaceRecognition()
    
    try:
        print("Démarrage de la reconnaissance faciale...")
        print("Les visages connus sont:", face_recognizer.known_face_names)
        print("Pressez 'q' pour quitter le test de reconnaissance faciale")
        face_recognizer.run_recognition()
    except Exception as e:
        print(f"Erreur lors de la reconnaissance faciale: {str(e)}")
    finally:
        face_recognizer.stop_cv2_camera()
        cv2.destroyAllWindows()

def test_drowsiness_detection():
    print("\n=== Test de la détection de somnolence ===")
    detector = None
    try:
        # Initialize the drowsiness detector
        print("Initialisation du détecteur de somnolence...")
        detector = drowsiness()
        
        print("Démarrage de la détection de somnolence...")
        print("Instructions:")
        print("- Gardez les yeux ouverts normalement")
        print("- Fermez les yeux pendant quelques secondes pour tester la détection")
        print("- Pressez 'q' pour quitter le test de somnolence")
        
        # Run the drowsiness detection
        state = detector.detect_drowsiness_state()
        if state:
            print("Somnolence détectée!")
        
    except Exception as e:
        print(f"Erreur lors de la détection de somnolence: {str(e)}")
        if detector and hasattr(detector, 'cam'):
            try:
                detector.cam.stop_camera()
            except:
                pass
        cv2.destroyAllWindows()
        return False
    finally:
        if detector and hasattr(detector, 'cam'):
            try:
                detector.cam.stop_camera()
            except:
                pass
        cv2.destroyAllWindows()
    return True

def eye_aspect_ratio(eye_points, landmarks):
    # Calculate the distances between the vertical eye landmarks
    A = distance.euclidean((landmarks.part(eye_points[1]).x, landmarks.part(eye_points[1]).y),
                          (landmarks.part(eye_points[5]).x, landmarks.part(eye_points[5]).y))
    B = distance.euclidean((landmarks.part(eye_points[2]).x, landmarks.part(eye_points[2]).y),
                          (landmarks.part(eye_points[4]).x, landmarks.part(eye_points[4]).y))
    # Calculate the distance between the horizontal eye landmarks
    C = distance.euclidean((landmarks.part(eye_points[0]).x, landmarks.part(eye_points[0]).y),
                          (landmarks.part(eye_points[3]).x, landmarks.part(eye_points[3]).y))
    # Calculate the eye aspect ratio
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(landmarks):
    # Calculate vertical distances
    A = distance.euclidean((landmarks.part(51).x, landmarks.part(51).y),
                          (landmarks.part(57).x, landmarks.part(57).y))
    # Calculate horizontal distance
    B = distance.euclidean((landmarks.part(48).x, landmarks.part(48).y),
                          (landmarks.part(54).x, landmarks.part(54).y))
    # Calculate mouth aspect ratio
    mar = A / B
    return mar

def test_shape_predictor():
    print("\n=== Test du détecteur de points de repère facial ===")
    
    # Initialize face detector and predictor
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor('modules/shape_predictor_68_face_landmarks.dat')
    
    # Initialize face recognition
    face_recognizer = FaceRecognition()
    
    # Define eye points
    LEFT_EYE_POINTS = [36, 37, 38, 39, 40, 41]
    RIGHT_EYE_POINTS = [42, 43, 44, 45, 46, 47]
    
    # Initialize thresholds
    EYE_AR_THRESH_CLOSED = 0.19  # Threshold for closed eyes
    EYE_AR_THRESH_PARTIAL = 0.24  # Threshold for partially closed eyes
    SMILE_THRESH = 0.4
    
    try:
        print("\nAnalyse faciale démarrée!")
        if IS_RASPBERRY_PI:
            print("GPIO et Buzzer actifs")
        print("Instructions:")
        print("- Regardez la caméra normalement")
        print("- Des informations sur votre état seront affichées")
        print("- Pressez 'q' pour quitter le test")
        
        # Variables for face detection blinking
        last_blink_time = time.time()
        blink_interval = 0.5  # 500ms blink interval
        led_state = False
        
        while True:
            frame = face_recognizer.cam.read_cam_frame()
            if frame is None:
                print("Erreur: Impossible de lire l'image de la caméra")
                break
            
            # Convert to grayscale for dlib
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = detector(gray)
            
            # Handle face detection and UI
            current_time = time.time()
            if len(faces) > 0:
                if current_time - last_blink_time >= blink_interval:
                    led_state = not led_state
                    control_face_led(led_state)  # Toggle face LED and relay together
                    last_blink_time = current_time
            else:
                control_face_led(False)  # Turn off face LED and relay
                cv2.putText(frame, "Aucun visage détecté", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Draw background rectangle for text
            cv2.rectangle(frame, (5, 5), (300, 160), (0, 0, 0), -1)
            
            for face in faces:
                # Get facial landmarks
                landmarks = predictor(gray, face)
                
                # Calculate eye aspect ratios
                left_ear = eye_aspect_ratio(LEFT_EYE_POINTS, landmarks)
                right_ear = eye_aspect_ratio(RIGHT_EYE_POINTS, landmarks)
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Calculate mouth aspect ratio
                mar = mouth_aspect_ratio(landmarks)
                
                # Draw facial landmarks
                for n in range(68):
                    x = landmarks.part(n).x
                    y = landmarks.part(n).y
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
                
                # Draw face rectangle
                cv2.rectangle(frame, (face.left(), face.top()), 
                            (face.right(), face.bottom()), (0, 255, 0), 2)
                
                # Add name to display
                name = face_recognizer.known_face_names[0] if face_recognizer.known_face_names else "Inconnu"
                cv2.putText(frame, f"Nom: {name}", (10, 150),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Eye state detection and LED/buzzer control
                if avg_ear < EYE_AR_THRESH_CLOSED:
                    eye_state = "FERMÉS - ATTENTION!"
                    cv2.putText(frame, "Yeux: " + eye_state, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    handle_drowsy_state('closed')
                    
                elif avg_ear < EYE_AR_THRESH_PARTIAL or mar > SMILE_THRESH:
                    eye_state = "PARTIELLEMENT FERMÉS" if avg_ear < EYE_AR_THRESH_PARTIAL else "OUVERTS"
                    smile_state = "Please wake-up !!" if mar > SMILE_THRESH else "Driver focused"
                    cv2.putText(frame, "Yeux: " + eye_state, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    handle_drowsy_state('partial', smile_alert=(mar > SMILE_THRESH))
                    
                else:
                    eye_state = "OUVERTS"
                    smile_state = "Driver focused"
                    cv2.putText(frame, "Yeux: " + eye_state, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    handle_drowsy_state('open')
                
                # Show smile state
                cv2.putText(frame, "Expression: " + smile_state, (10, 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Display metrics
                cv2.putText(frame, f"EAR: {avg_ear:.2f}", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"MAR: {mar:.2f}", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                              
            # Show the video feed
            cv2.imshow("Analyse Faciale", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
    except Exception as e:
        print(f"Erreur lors de l'analyse faciale: {str(e)}")
    finally:
        face_recognizer.stop_cv2_camera()
        cv2.destroyAllWindows()
        cleanup_gpio()

def main():
    try:
        while True:
            print("\n=== Menu de Test ===")
            print("1. Tester la reconnaissance faciale")
            print("2. Tester la détection de somnolence")
            print("3. Tester le détecteur de points de repère facial")
            print("4. Tester toutes les fonctionnalités")
            print("5. Quitter")
            
            choice = input("Choisissez une option (1-5): ")
            
            if choice == '1':
                test_face_recognition()
            elif choice == '2':
                test_drowsiness_detection()
            elif choice == '3':
                test_shape_predictor()
            elif choice == '4':
                print("\nDémarrage des tests complets...")
                test_face_recognition()
                test_drowsiness_detection()
                test_shape_predictor()
                print("\nTous les tests sont terminés.")
            elif choice == '5':
                print("Au revoir!")
                break
            else:
                print("Option invalide. Veuillez choisir entre 1 et 5.")
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()
