import platform
import time

# Initialize IS_RASPBERRY_PI first
IS_RASPBERRY_PI = platform.system() == 'Linux' and platform.machine().startswith('arm')

__all__ = [
    'IS_RASPBERRY_PI',
    'init_gpio',
    'control_face_led',
    'reset_leds',
    'handle_drowsy_state',
    'cleanup_gpio'
]

# Only import GPIO if on Raspberry Pi
GPIO = None
if IS_RASPBERRY_PI:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("Warning: RPi.GPIO module not found. GPIO functionality will be disabled.")
        IS_RASPBERRY_PI = False

# LED pins
FACE_LED_PIN = 17    # LED for face detection
GREEN_LED_PIN = 23   # LED for open eyes
YELLOW_LED_PIN = 24  # LED for partial closed eyes
RED_LED_PIN = 18     # LED for closed eyes
BUZZER_PIN = 25      # Buzzer pin
RELAY_PIN = 4        # Relay pin synchronized with face LED

_gpio_initialized = False
_pwm = None  # For buzzer PWM control

def init_gpio():
    """Initialize all GPIO pins if not already initialized."""
    global _gpio_initialized, _pwm
    if not IS_RASPBERRY_PI:
        return
        
    if not _gpio_initialized:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup LED pins
        GPIO.setup(FACE_LED_PIN, GPIO.OUT)
        GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
        GPIO.setup(YELLOW_LED_PIN, GPIO.OUT)
        GPIO.setup(RED_LED_PIN, GPIO.OUT)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        GPIO.setup(RELAY_PIN, GPIO.OUT)
        
        # Initialize all pins to LOW
        GPIO.output(FACE_LED_PIN, GPIO.LOW)
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        GPIO.output(RELAY_PIN, GPIO.LOW)
        
        # Initialize buzzer PWM
        _pwm = GPIO.PWM(BUZZER_PIN, 1000)  # 1000 Hz frequency
        _pwm.start(0)  # Start with 0% duty cycle
        
        _gpio_initialized = True

def cleanup_gpio():
    """Clean up GPIO resources."""
    global _gpio_initialized, _pwm
    if IS_RASPBERRY_PI and _gpio_initialized:
        if _pwm:
            _pwm.stop()
        reset_leds()
        GPIO.cleanup()
        _gpio_initialized = False

def control_face_led(state):
    """Control face LED and synchronized relay.
    
    Args:
        state: True to turn on, False to turn off
    """
    if IS_RASPBERRY_PI and _gpio_initialized:
        GPIO.output(FACE_LED_PIN, state)
        GPIO.output(RELAY_PIN, state)  # Relay mirrors face LED state

def reset_leds():
    """Turn off all LEDs."""
    if IS_RASPBERRY_PI and _gpio_initialized:
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        control_face_led(False)

def _beep(duration=0.1, frequency=1000):
    """Internal function to make the buzzer beep."""
    if IS_RASPBERRY_PI and _gpio_initialized and _pwm:
        _pwm.ChangeFrequency(frequency)
        _pwm.ChangeDutyCycle(50)  # 50% duty cycle
        time.sleep(duration)
        _pwm.ChangeDutyCycle(0)

def handle_drowsy_state(state, smile_alert=False):
    """Handle LED and buzzer patterns based on eye state and smile.
    
    Args:
        state: 'closed', 'partial', or 'open'
        smile_alert: True if smile indicates wake-up needed
    """
    if not IS_RASPBERRY_PI or not _gpio_initialized:
        return
        
    reset_leds()
    
    if state == 'closed':
        # Red LED blink with continuous long beep
        GPIO.output(RED_LED_PIN, GPIO.HIGH)
        _beep(duration=1.0, frequency=2000)
        time.sleep(0.5)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        
    elif state == 'partial' or smile_alert:
        # Yellow LED blink with short beep
        GPIO.output(YELLOW_LED_PIN, GPIO.HIGH)
        _beep(duration=0.2, frequency=1500)
        time.sleep(0.3)
        GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        
    else:  # open and focused
        # Green LED gentle blink, no buzzer
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)