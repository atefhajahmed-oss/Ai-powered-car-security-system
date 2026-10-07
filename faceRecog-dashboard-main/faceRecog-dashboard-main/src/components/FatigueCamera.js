import React, { useState, useRef, useEffect, useCallback } from 'react';

// Inline styles
const styles = {
  container: {
    width: '100%',
    margin: '0',
    padding: '0',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  videoContainer: {
    position: 'relative',
    width: '100%',
    flex: '1 1 auto',
    minHeight: '600px',
    backgroundColor: '#000',
    borderRadius: '8px',
    overflow: 'hidden',
    margin: '0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mjpegImage: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    display: 'block',
    maxWidth: '100%',
    maxHeight: '100vh',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    color: '#fff',
    zIndex: 10,
  },
  errorOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    color: '#ff6b6b',
    padding: '20px',
    textAlign: 'center',
    zIndex: 10,
  },
  statusOverlay: {
    position: 'absolute',
    top: '10px',
    left: '10px',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    color: '#fff',
    padding: '10px',
    borderRadius: '4px',
    zIndex: 11,
  },
  statusItem: {
    margin: '5px 0',
    fontSize: '14px',
  },
  warning: {
    color: '#ff4444',
    fontWeight: 'bold',
  },
  refreshButton: {
    marginTop: '10px',
    padding: '5px 10px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};

const FatigueCamera = ({ onStatusUpdate }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [timestamp, setTimestamp] = useState(Date.now());
  const [status, setStatus] = useState({
    ear: 0,
    mar: 0,
    angle: 0,
    warning: '',
    blink_count: 0,
    is_yawning: false,
    fps: 0,
  });
  
  const imgRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  const statusIntervalRef = useRef(null);
  const isMountedRef = useRef(true);
  const retryCountRef = useRef(0);
  const frameCountRef = useRef(0);
  const frameTimesRef = useRef([]);
  const lastFrameTimeRef = useRef(0);
  const MAX_RETRIES = 5;

  // Base URL for the API - using the Flask server's default port for fatigue detection
  const API_BASE_URL = 'http://localhost:5001';
  const videoFeedUrl = `${API_BASE_URL}/video_feed?t=${timestamp}`;
  const statusUrl = `${API_BASE_URL}/status`;

  // Calculate FPS based on frame times
  const calculateFps = useCallback((currentTime) => {
    // Keep track of frame times for the last second
    const now = currentTime || performance.now();
    const frameTimes = frameTimesRef.current;
    
    // Add current frame time
    frameTimes.push(now);
    
    // Remove frames older than 1 second
    while (frameTimes.length > 0 && now - frameTimes[0] > 1000) {
      frameTimes.shift();
    }
    
    // Calculate FPS
    const fps = frameTimes.length > 1 ? 
      Math.round((frameTimes.length - 1) * 1000 / (now - frameTimes[0])) : 
      0;
    
    lastFrameTimeRef.current = now;
    frameCountRef.current++;
    
    return fps;
  }, []);

  // Fetch fatigue detection status from the server
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(statusUrl);
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      
      if (isMountedRef.current) {
        setStatus(prev => ({
          ...prev,
          ...data
        }));
        
        // Notify parent component if needed
        if (onStatusUpdate) {
          onStatusUpdate(data);
        }
      }
    } catch (error) {
      console.log('[FatigueCamera] Error fetching status:', error);
    }
  }, [onStatusUpdate, statusUrl]);

  // Handle successful image load
  const handleImageLoaded = useCallback(() => {
    const now = performance.now();
    const fps = calculateFps(now);
    
    if (!isStreaming) {
      console.log('[FatigueCamera] Image loaded successfully');
      setIsStreaming(true);
      setError(null);
      retryCountRef.current = 0; // Reset retry counter on success
      
      // Start polling for status updates
      fetchStatus();
      statusIntervalRef.current = setInterval(fetchStatus, 100);
      
      // Log initial FPS after a short delay to allow it to stabilize
      setTimeout(() => {
        console.log(`[FatigueCamera] Stream running at ${fps} FPS`);
      }, 1000);
    }
  }, [isStreaming, calculateFps, fetchStatus]);

  // Handle image loading errors
  const handleImageError = useCallback((e) => {
    console.log('[FatigueCamera] Error loading image:', e);
    setIsStreaming(false);
    
    if (retryCountRef.current < MAX_RETRIES) {
      const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 10000);
      console.log(`[FatigueCamera] Retrying in ${delay}ms (attempt ${retryCountRef.current + 1}/${MAX_RETRIES})`);
      
      setError(`Connection lost. Attempting to reconnect (${retryCountRef.current + 1}/${MAX_RETRIES})...`);
      
      retryTimeoutRef.current = setTimeout(() => {
        setTimestamp(Date.now()); // Force refresh
        retryCountRef.current++;
      }, delay);
    } else {
      setError([
        'Failed to connect to the fatigue detection server. Please check:',
        `1. The fatigue detection server is running at ${API_BASE_URL}`,
        '2. No other application is using the camera',
        '3. The camera is properly connected'
      ].join('\n'));
    }
  }, [API_BASE_URL]);

  // Handle retry button click
  const handleRetry = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    setError(null);
    setTimestamp(Date.now());
    retryCountRef.current = 0;
  }, []);

  // Handle refresh button click
  const handleRefresh = useCallback(() => {
    setTimestamp(Date.now());
  }, []); 

  // Clean up on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
      }
    };
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.videoContainer}>
        <img
          ref={imgRef}
          src={videoFeedUrl}
          alt="Fatigue Detection Feed"
          style={styles.mjpegImage}
          onLoad={handleImageLoaded}
          onError={handleImageError}
        />
        
        {/* Loading overlay */}
        {!isStreaming && !error && (
          <div style={styles.loadingOverlay}>
            <div>Connecting to fatigue detection server...</div>
          </div>
        )}
        
        {/* Error overlay */}
        {error && (
          <div style={styles.errorOverlay}>
            <div style={styles.errorContent}>
              <p style={{ marginBottom: '16px', whiteSpace: 'pre-line' }}>{error}</p>
              <button 
                onClick={handleRetry}
                style={{
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginTop: '16px'
                }}
              >
                Retry
              </button>
            </div>
          </div>
        )}
        
        {/* Status overlay */}
        {isStreaming && !error && (
          <div style={styles.statusOverlay}>
            <div style={styles.statusItem}>
              <strong>EAR:</strong> {status.ear.toFixed(3)}
            </div>
            <div style={styles.statusItem}>
              <strong>MAR:</strong> {status.mar.toFixed(3)}
            </div>
            <div style={styles.statusItem}>
              <strong>Angle:</strong> {status.angle.toFixed(1)}°
            </div>
            <div style={styles.statusItem}>
              <strong>Blinks:</strong> {status.blink_count}
            </div>
            <div style={styles.statusItem}>
              <strong>Yawning:</strong> {status.is_yawning ? 'Yes' : 'No'}
            </div>
            <div style={styles.statusItem}>
              <strong>FPS:</strong> {Math.round(status.fps)}
            </div>
            {status.warning && (
              <div style={{ ...styles.statusItem, ...styles.warning }}>
                {status.warning}
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Refresh button */}
      <div style={{ textAlign: 'right', marginTop: '8px' }}>
        <button 
          onClick={handleRefresh}
          style={styles.refreshButton}
          title="Refresh stream"
        >
          Refresh
        </button>
      </div>
    </div>
  );
};

export default FatigueCamera;
