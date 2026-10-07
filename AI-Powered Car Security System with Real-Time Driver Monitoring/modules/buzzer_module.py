import RPi.GPIO as GPIO
import time
import threading

# Buzzer pin setup
BUZZER_PIN = 25  # GPIO pin number
_is_initialized = False

def init_buzzer():
    """Initialize the buzzer. Must be called before using any other functions."""
    global _is_initialized, pwm
    if not _is_initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        pwm = GPIO.PWM(BUZZER_PIN, 1000)  # 1000 Hz frequency
        _is_initialized = True

def cleanup():
    """Clean up GPIO. Call this when done using the buzzer."""
    global _is_initialized
    if _is_initialized:
        GPIO.cleanup(BUZZER_PIN)
        _is_initialized = False

def _check_init():
    if not _is_initialized:
        raise RuntimeError("Buzzer not initialized. Call init_buzzer() first.")

def buzzer_on():
    """Turn on the buzzer."""
    _check_init()
    GPIO.output(BUZZER_PIN, GPIO.HIGH)

def buzzer_off():
    """Turn off the buzzer."""
    _check_init()
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def short_beep(duration=0.2):
    """Make a short beep."""
    _check_init()
    buzzer_on()
    time.sleep(duration)
    buzzer_off()

def long_beep(duration=1.0, pause=1.0, count=1):
    """Make one or more long beeps.
    
    Args:
        duration: Length of each beep in seconds
        pause: Pause between beeps in seconds
        count: Number of beeps to make
    """
    _check_init()
    for _ in range(count):
        buzzer_on()
        time.sleep(duration)
        buzzer_off()
        if _ < count - 1:  # Don't pause after the last beep
            time.sleep(pause)

def continuous_beep():
    """Beep continuously until stopped."""
    global running
    _check_init()
    buzzer_on()
    while running:
        time.sleep(0.1)  # Small sleep to prevent CPU hogging
    buzzer_off()

# Global variables for thread control
running = True
current_thread = None
counter = 0

def stop_current_thread():
    """Stop the current alert thread if one is running."""
    global current_thread
    if current_thread is not None:
        current_thread.join()
    current_thread = None

def alert_first():
    """First level alert - short beeps."""
    global running
    while running:
        if counter == 1:
            short_beep()
        time.sleep(1)

def alert_second():
    """Second level alert - long beeps."""
    global running
    while running:
        if counter == 2:
            long_beep()
        time.sleep(1)

def alert_third():
    """Third level alert - continuous beep."""
    global running
    while running:
        if counter == 3:
            continuous_beep()
        time.sleep(1)

def start_alert_thread():
    """Start the appropriate alert thread based on counter value."""
    global current_thread
    if not _is_initialized:
        init_buzzer()
    
    if counter == 1:
        stop_current_thread()
        current_thread = threading.Thread(target=alert_first)
        current_thread.start()
    elif counter == 2:
        stop_current_thread()
        current_thread = threading.Thread(target=alert_second)
        current_thread.start()
    elif counter == 3:
        stop_current_thread()
        current_thread = threading.Thread(target=alert_third)
        current_thread.start()

def stop_alerts():
    """Stop all alerts and cleanup."""
    global running
    running = False
    stop_current_thread()
    buzzer_off()

if __name__ == '__main__':
    # Test code
    try:
        print("Initializing buzzer...")
        init_buzzer()
        
        print("Testing short beep...")
        short_beep()
        time.sleep(1)
        
        print("Testing long beep...")
        long_beep(duration=0.5, count=2)
        time.sleep(1)
        
        print("Testing continuous beep for 2 seconds...")
        running = True
        t = threading.Thread(target=continuous_beep)
        t.start()
        time.sleep(2)
        running = False
        t.join()
        
        print("Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        stop_alerts()
        cleanup()