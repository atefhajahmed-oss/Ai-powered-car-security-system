import RPi.GPIO as GPIO
from threading import Thread, Event 
import time


class Keypad(Thread):
    def __init__(self, secret_code):
        super().__init__()
        self.L1 = 5
        self.L2 = 6
        self.L3 = 13
        self.L4 = 19
        self.C1 = 12
        self.C2 = 16
        self.C3 = 20
        self.C4 = 21

        self.keypad_pressed = -1
        self.secret_code = secret_code
        self.input = ""

        # Thread control flags
        self.running = Event()
        self.stop_event = Event()

        # GPIO setup
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.L1, GPIO.OUT)
        GPIO.setup(self.L2, GPIO.OUT)
        GPIO.setup(self.L3, GPIO.OUT)
        GPIO.setup(self.L4, GPIO.OUT)

        GPIO.setup(self.C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(self.C1, GPIO.RISING, callback=self.keypad_callback)
        GPIO.add_event_detect(self.C2, GPIO.RISING, callback=self.keypad_callback)
        GPIO.add_event_detect(self.C3, GPIO.RISING, callback=self.keypad_callback)
        GPIO.add_event_detect(self.C4, GPIO.RISING, callback=self.keypad_callback)

    def keypad_callback(self, channel):
        """Callback to detect key presses."""
        if self.keypad_pressed == -1:
            self.keypad_pressed = channel

    def set_all_lines(self, state):
        """Set all lines to a specific state."""
        GPIO.output(self.L1, state)
        GPIO.output(self.L2, state)
        GPIO.output(self.L3, state)
        GPIO.output(self.L4, state)

    # def check_special_keys(self):
    #     """Checks for special keys."""
    #     GPIO.output(self.L3, GPIO.HIGH)

    #     if GPIO.input(self.C4) == 1:  # 'C' key resets input
    #         print("Input reset!")
    #         self.input = ""
    #         return True

    #     GPIO.output(self.L3, GPIO.LOW)
    #     GPIO.output(self.L1, GPIO.HIGH)

    #     if GPIO.input(self.C4) == 1:  # '*' key triggers action
    #         print("Special key '*' detected!")
    #         return True

    #     GPIO.output(self.L1, GPIO.LOW)
    #     return False

    def read_line(self, line, characters):
        """Reads the key pressed in a line and appends it to the input."""
        GPIO.output(line, GPIO.HIGH)
        if GPIO.input(self.C1) == 1:
            self.input = characters[0]
        if GPIO.input(self.C2) == 1:
            self.input = characters[1]
        if GPIO.input(self.C3) == 1:
            self.input = characters[2]
        if GPIO.input(self.C4) == 1:
            self.input = characters[3]
        GPIO.output(line, GPIO.LOW)

    def get_input(self):
        """Returns the current input."""
        return self.input

    def reset_input(self):
        """Resets the input string."""
        self.input = ""

    def start_keypad(self):
        """Starts the keypad thread."""
        self.running.set()
        self.stop_event.clear()
        self.start()

    def stop_keypad(self):
        """Stops the keypad thread."""
        self.running.clear()
        self.stop_event.set()
        self.join()
        GPIO.cleanup()

    def run(self):
        """Main thread loop."""
        try:
            while not self.stop_event.is_set():
                if self.keypad_pressed != -1:
                    self.set_all_lines(GPIO.HIGH)
                    if GPIO.input(self.keypad_pressed) == 0:
                        self.keypad_pressed = -1
                    else:
                        time.sleep(0.1)
                else:
                    # if not self.check_special_keys():
                    self.read_line(self.L1, ["1", "2", "3", "A"])
                    self.read_line(self.L2, ["4", "5", "6", "B"])
                    self.read_line(self.L3, ["7", "8", "9", "C"])
                    self.read_line(self.L4, ["*", "0", "#", "D"])
                    time.sleep(0.1)
                    # else:
                        # time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nKeypad thread interrupted!")



        
        
"""if __name__ == "__main__":
    secret_code = "4789"
    keypad = Keypad(secret_code)

    print("Starting keypad...")
    keypad.start_keypad()

    st = False  # State flag indicating if we are expecting the PIN
    passwd = ""  # Variable to store the entered password

    try:
        while True:
            user_input = keypad.get_input()
            
            if user_input:  # Process input only if it's not empty
                if user_input == '#':
                    print("To start engine, please enter pin: ")
                    keypad.reset_input()
                    st = True
                    passwd = ""  # Reset password entry for a fresh start
                
                elif user_input == '*' and st
                .
                :
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
                        print("Access granted!")
                        st = False
                        passwd = ""
                    else:
                        print("Wrong password.")
                        passwd = ""
                    keypad.reset_input()
                
                elif st:  # If in password-entry mode, accumulate characters
                    passwd += user_input
                    print(f"Current input: {user_input}, Password so far: {passwd}")
                
                else:
                    print(f"Unrecognized input: {user_input}")
                
                # Reset input buffer
                keypad.reset_input()
            
            time.sleep(0.1)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        print("\nStopping keypad...")
        keypad.stop_keypad()
"""
