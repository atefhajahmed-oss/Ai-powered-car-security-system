from modules.keypad_module import *
import time
from modules.I2C_LCD_driver import *
from modules.Face_recognition import *
from modules.drowsiness_detection import *
from modules.shared import *

# Configuration par défaut
secret_code = "4789"

# Initialisation des composants selon la plateforme
try:
    import RPi.GPIO as GPIO
    first_alert_pin = 17
    second_alert_pin = 27
    third_alert_pin = 22
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(first_alert_pin, GPIO.OUT)
    GPIO.setup(second_alert_pin, GPIO.OUT)
    GPIO.setup(third_alert_pin, GPIO.OUT)
    USE_GPIO = True
    
    # Initialisation des périphériques Raspberry Pi
    mylcd = lcd()
    keypad = Keypad(secret_code)
except ImportError:
    print("GPIO non disponible - Mode simulation")
    USE_GPIO = False
    # Simulation des composants pour le développement
    class DummyLCD:
        def lcd_display_string(self, text, line=1, pos=0):
            print(f"LCD Line {line}: {text}")
        def lcd_clear(self):
            print("LCD Clear")
            
    class DummyKeypad:
        def __init__(self, code):
            self.code = code
            self.current_input = ""
        def get_input(self):
            # Simulation d'entrée pour le test
            return input("Entrez une touche (0-9, *, #, A-D): ")
        def reset_input(self):
            self.current_input = ""
            
    mylcd = DummyLCD()
    keypad = DummyKeypad(secret_code)

def check_PIN():

    

    st = True  # State flag indicating if we are expecting the PIN
    passwd = ""  # Variable to store the entered password
    print("To start engine, please enter pin: ")
    mylcd.lcd_display_string("Please enter pin: ")
    keypad.reset_input()
    try:
        while True:
            user_input = keypad.get_input()
            
            if user_input:  # Process input only if it's not empty
                if user_input == '*' and st:
                    print("Resetting input... ENTER PIN again.")
                    st = False
                    passwd = ""
                    keypad.reset_input()

                elif user_input == 'C'and st :
                    if (passwd):
                        passwd = passwd[:-1]
                    print(f"current input: {user_input}, password: {passwd}")
                    
                elif user_input == 'D' and st:
                    print(f"Password entered: {passwd}")
                    if passwd == secret_code:
                        print("Engine Started!")
                        mylcd.lcd_display_string("Engin Started")
                        sleep(1)
                        mylcd.lcd_clear()
                        mylcd.lcd_display_string("Drive safe")
                        return
                        passwd = ""
                    else:
                        print("Wrong password.")
                        mylcd.lcd_display_string("Wrong PIN")
                        sleep(1);
                        mylcd.lcd_clear()
                        mylcd.lcd_display_string("Please enter pin: ")
                        passwd = ""
                    keypad.reset_input()
                
                elif st:  # If in password-entry mode, accumulate characters
                    passwd += user_input
                    print(f"Current input: {user_input}, Password so far: {passwd}")
                    mylcd.lcd_display_string(f"{len(passwd)*'*'}",2,0)
                
                else:
                    print(f"Unrecognized input: {user_input}")
                
                # Reset input buffer
                keypad.reset_input()
            
            time.sleep(0.1)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        print("\nStopping keypad...")
        keypad.stop_keypad()

def set_alert(level):
    if not USE_GPIO:
        print(f"Simulation - Niveau d'alerte : {level}")
        return
        
    if level == 1:
        GPIO.output(first_alert_pin, GPIO.HIGH)
        GPIO.output(second_alert_pin, GPIO.LOW)
        GPIO.output(third_alert_pin, GPIO.LOW)
    elif level == 2:
        GPIO.output(first_alert_pin, GPIO.LOW)
        GPIO.output(second_alert_pin, GPIO.HIGH)
        GPIO.output(third_alert_pin, GPIO.LOW)
    elif level == 3:
        GPIO.output(first_alert_pin, GPIO.LOW)
        GPIO.output(second_alert_pin, GPIO.LOW)
        GPIO.output(third_alert_pin, GPIO.HIGH)
    else:
        GPIO.output(first_alert_pin, GPIO.LOW)
        GPIO.output(second_alert_pin, GPIO.LOW)
        GPIO.output(third_alert_pin, GPIO.LOW)

def main():
    try:
        print("Démarrage de la détection de somnolence...")
        detect = drowsiness()
        counter = 0
        first_alert = False
        second_alert = False
        third_alert = False
        
        while True:
            if detect.detect_drowsiness_state():
                counter += 1
            else:
                counter = 0
                set_alert(0)
                first_alert = False
                second_alert = False
                third_alert = False
                
            if counter == 1 and not first_alert:
                first_alert = True
                print("Première alerte activée")
                set_alert(1)
            elif counter == 2 and not second_alert:
                second_alert = True
                print("Deuxième alerte activée")
                set_alert(2)
            elif counter == 3 and not third_alert:
                third_alert = True
                print("Véhicule arrêté")
                set_alert(3)
                break
                
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur")
    finally:
        if USE_GPIO:
            set_alert(0)
            GPIO.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    if check_PIN():
        main()
