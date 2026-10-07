import React, { useState, useRef, useEffect, useCallback } from 'react';

const Camera = ({ onFaceDetected, mode = 'face' }) => {
  const API_BASE_URL = mode === 'blink' ? 'http://localhost:5002' : 'http://localhost:5000';
  const MAX_RETRIES = 5;
  
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [fps, setFps] = useState(0);
  const [timestamp, setTimestamp] = useState(Date.now());
  
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef(null);
  const frameTimesRef = useRef([]);
  const isMountedRef = useRef(true);
  const wsRef = useRef(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Calculate FPS
  const calculateFps = useCallback(() => {
    const now = Date.now();
    const frameTimes = frameTimesRef.current;
    
    // Remove frames older than 1 second
    while (frameTimes.length > 0 && now - frameTimes[0] > 1000) {
      frameTimes.shift();
    }
    
    // Add current frame time
    frameTimes.push(now);
    
    // Calculate FPS
    const currentFps = frameTimes.length;
    setFps(currentFps);
    return currentFps;
  }, []);

  // Handle image load
  const handleImageLoad = useCallback(() => {
    if (!isStreaming) {
      setIsStreaming(true);
      retryCountRef.current = 0;
      setError(null);
    }
    calculateFps();
  }, [isStreaming, calculateFps]);

  // Handle image errors
  const handleImageError = useCallback((e) => {
    console.log('[Camera] Error loading image:', e);
    setIsStreaming(false);
    
    if (!isMountedRef.current) return;
    
    if (retryCountRef.current < MAX_RETRIES) {
      const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 10000);
      console.log(`[Camera] Retrying in ${delay}ms (attempt ${retryCountRef.current + 1}/${MAX_RETRIES})`);
      
      setError(`Connection lost. Attempting to reconnect (${retryCountRef.current + 1}/${MAX_RETRIES})...`);
      
      retryTimeoutRef.current = setTimeout(() => {
        if (isMountedRef.current) {
          setTimestamp(Date.now());
          retryCountRef.current++;
        }
      }, delay);
    } else {
      const errorMessages = [
        'Failed to connect to the video feed. Please check:',
        `1. The ${mode} server is running at ${API_BASE_URL}`,
        '2. The correct port is being used (5000 for face, 5002 for blink)',
        '3. No other application is using the camera',
        '4. The camera is properly connected',
        '5. The server allows CORS requests from this origin'
      ];
      setError(errorMessages.join('\n'));
    }
  }, [API_BASE_URL, mode]);

  // WebSocket for face detection data
  useEffect(() => {
    if (mode !== 'face') return;

    const wsUrl = `ws://localhost:5000/ws/face_detection`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('[Camera] WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && onFaceDetected) {
          onFaceDetected(data);
        }
      } catch (e) {
        console.log('[Camera] Error parsing WebSocket message:', e);
      }
    };

    wsRef.current.onerror = (error) => {
      console.log('[Camera] WebSocket error:', error);
    };

    wsRef.current.onclose = () => {
      console.log('[Camera] WebSocket disconnected');
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [mode, onFaceDetected]);

  // Video feed URL with timestamp to prevent caching
  const videoFeedUrl = `${API_BASE_URL}/video_feed?t=${timestamp}`;

  return (
    <div className="relative w-full h-full bg-black rounded-lg overflow-hidden">
      {error ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black bg-opacity-80 text-white p-4 text-center">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium mb-2">Connection Error</h3>
          <p className="text-sm text-gray-300 whitespace-pre-line mb-4">{error}</p>
          <button
            onClick={() => {
              setTimestamp(Date.now());
              setError(null);
              retryCountRef.current = 0;
            }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md text-sm font-medium"
          >
            Retry Connection
          </button>
        </div>
      ) : (
        <div className="relative w-full h-full">
          <img
            src={videoFeedUrl}
            alt="Video Feed"
            className="w-full h-full object-contain"
            onLoad={handleImageLoad}
            onError={handleImageError}
          />
          <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
            {fps} FPS
          </div>
        </div>
      )}
    </div>
  );
};

export default Camera