// Configuration for the facial recognition dashboard

// API configuration
export const API_BASE_URL = 'http://localhost:5000';

// WebSocket configuration
export const WS_BASE_URL = 'ws://localhost:5000';

// Application settings
export const APP_CONFIG = {
  // Maximum number of retries for failed requests
  MAX_RETRIES: 5,
  
  // Retry delay in milliseconds (will be multiplied by retry count)
  RETRY_DELAY: 1000,
  
  // Timeout for API requests in milliseconds
  API_TIMEOUT: 10000,
  
  // Enable/disable debug mode
  DEBUG: true,
};

// Face detection settings
export const FACE_DETECTION_CONFIG = {
  // Minimum confidence threshold for face detection (0-1)
  MIN_CONFIDENCE: 0.7,
  
  // Maximum number of faces to detect
  MAX_FACES: 10,
  
  // Whether to enable face recognition
  ENABLE_RECOGNITION: true,
};

// Blink detection settings
export const BLINK_DETECTION_CONFIG = {
  // Eye aspect ratio threshold for blink detection
  EAR_THRESHOLD: 0.25,
  
  // Number of consecutive frames below threshold to count as a blink
  EYE_AR_CONSEC_FRAMES: 3,
  
  // Minimum time between blinks in milliseconds
  MIN_BLINK_INTERVAL: 100,
};

export default {
  API_BASE_URL,
  WS_BASE_URL,
  APP_CONFIG,
  FACE_DETECTION_CONFIG,
  BLINK_DETECTION_CONFIG,
};
