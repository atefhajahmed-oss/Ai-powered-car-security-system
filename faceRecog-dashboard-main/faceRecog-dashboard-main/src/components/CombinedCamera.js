import React, { useState, useEffect, useRef, useCallback } from 'react';

const CombinedCamera = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  // State for current status and last recognized face
  const [status, setStatus] = useState({
    face_name: 'Unknown',
    confidence: 0,
    blink_count: 0,
    eye_ar: 0,
    is_eyes_closed: false,
    is_yawning: false,
    mar: 0,
    fps: 0,
    timestamp: new Date().toLocaleTimeString(),
    last_recognized: null,      // Store last recognized face
    recognition_count: 0,        // Count of consecutive recognitions
    last_update: Date.now()      // Timestamp of last recognition
  });
  const [hasInitialized, setHasInitialized] = useState(false);
  const [error, setError] = useState(null);
  
  const videoRef = useRef(null);
  const imgRef = useRef(null);
  const reconnectTimeout = useRef(null);
  const frameUpdateInterval = useRef(null);
  const statusInterval = useRef(null);

  // Function to fetch status from the server with face recognition smoothing
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5003/status');
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      
      // Extract the first face data if available
      const faceData = data.faces && data.faces.length > 0 ? data.faces[0] : null;
      
      setStatus(prev => {
        const now = Date.now();
        const timeSinceLastUpdate = now - prev.last_update;
        const RECOGNITION_TIMEOUT = 1000; // 2 seconds timeout for last recognition
        const MIN_CONFIDENCE = 70; // Minimum confidence percentage to consider a recognition valid
        
        let newFaceName = 'Unknown';
        let newConfidence = 0;
        let newLastRecognized = prev.last_recognized;
        let newRecognitionCount = 0;
        
        // If we have face data with good confidence
        if (faceData && faceData.name && faceData.name !== 'Unknown' && 
            (faceData.confidence * 100) >= MIN_CONFIDENCE) {
          
          // If this is the same face as last time, increment counter
          if (faceData.name === prev.last_recognized?.name) {
            newRecognitionCount = (prev.recognition_count || 0) + 1;
          } else {
            newRecognitionCount = 1;
          }
          
          // Update last recognized face
          newLastRecognized = {
            name: faceData.name,
            confidence: faceData.confidence * 100,
            timestamp: now
          };
          
          newFaceName = faceData.name;
          newConfidence = faceData.confidence * 100;
        } 
        // If no face detected or low confidence, but we have a recent recognition
        else if (prev.last_recognized && timeSinceLastUpdate < RECOGNITION_TIMEOUT) {
          newFaceName = prev.last_recognized.name;
          newConfidence = prev.last_recognized.confidence * 0.9; // Slight confidence decay
          newLastRecognized = {
            ...prev.last_recognized,
            confidence: newConfidence
          };
        }
        
        const newStatus = {
          ...prev,
          // Spread the main data
          blink_count: data.blink_count || prev.blink_count,
          eye_ar: data.eye_ar || prev.eye_ar,
          is_eyes_closed: data.is_eyes_closed || prev.is_eyes_closed,
          fps: data.fps || prev.fps,
          // Face recognition data
          face_name: newFaceName,
          confidence: newConfidence,
          // Other face data
          mar: faceData?.mar || prev.mar,
          is_yawning: (faceData?.mar || 0) > 0.9,
          // Tracking data
          last_recognized: newLastRecognized,
          recognition_count: newRecognitionCount,
          last_update: now,
          timestamp: new Date().toLocaleTimeString()
        };
        
        return newStatus;
      });
    } catch (err) {
      console.log('Error fetching status:', err);
    }
  }, []);

  // Function to update the image source
  const updateImage = useCallback(() => {
    if (!imgRef.current) return false;
    
    try {
      // Add timestamp to prevent caching
      const timestamp = new Date().getTime();
      imgRef.current.src = `http://localhost:5003/video_feed?t=${timestamp}`;
      return true;
    } catch (err) {
      console.log('Error updating image:', err);
      return false;
    }
  }, []);

  // Set up image stream with auto-reconnect
  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    console.log('🔌 Setting up image stream');
    
    const handleLoad = () => {
      console.log('✅ Image loaded');
      if (!hasInitialized) {
        setIsLoading(false);
        setConnectionStatus('Connected');
        setHasInitialized(true);
      }
      
      // Clear any existing interval
      if (frameUpdateInterval.current) {
        clearInterval(frameUpdateInterval.current);
      }
      
      // Set up frame updates every 100ms (10fps)
      frameUpdateInterval.current = setInterval(updateImage, 1000);
    };
    
    const handleError = (e) => {
      console.log('❌ Image load error:', e);
      setConnectionStatus('Reconnecting...');
      
      // Only show loading state if we haven't had a successful connection yet
      if (!hasInitialized) {
        setIsLoading(true);
      }
      
      // Clear any existing timeout
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      
      // Try to reconnect after a delay
      reconnectTimeout.current = setTimeout(() => {
        console.log('Attempting to reconnect...');
        updateImage();
      }, 2000); // Increased delay to 2 seconds
    };
    
    // Set up event listeners
    img.addEventListener('load', handleLoad, { once: true });
    img.addEventListener('error', handleError, { once: true });
    
    // Start the stream
    updateImage();
    
    // Set up status polling
    console.log('Setting up status polling');
    statusInterval.current = setInterval(fetchStatus, 1000);
    // Initial fetch after a small delay to ensure component is mounted
    const initialFetch = setTimeout(fetchStatus, 500);
    
    return () => {
      clearTimeout(initialFetch);
    };

    // Cleanup function
    return () => {
      console.log('Cleaning up image stream');
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (frameUpdateInterval.current) {
        clearInterval(frameUpdateInterval.current);
      }
      if (statusInterval.current) {
        clearInterval(statusInterval.current);
      }
      img.removeEventListener('load', handleLoad);
      img.removeEventListener('error', handleError);
    };
  }, []);

  return (
    <div className="flex flex-col h-full bg-gray-100 p-4">
      <div className="flex-1 flex flex-col md:flex-row gap-6">
        {/* Video Feed */}
        <div className="bg-black rounded-lg overflow-hidden relative flex-1">
          <div className="absolute top-4 right-4 z-10">
            <div className="flex items-center bg-black bg-opacity-70 text-white px-3 py-1 rounded-full">
              <div className={`w-2.5 h-2.5 rounded-full mr-2 ${
                connectionStatus === 'Connected' ? 'bg-green-500' : 
                connectionStatus === 'Reconnecting...' ? 'bg-yellow-500' : 
                'bg-red-500'}`}></div>
              <span className="text-xs font-medium">
                {connectionStatus}
              </span>
            </div>
          </div>
          
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70">
              <div className="text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500 mx-auto mb-3"></div>
                <p className="text-white font-medium">{connectionStatus}...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70 text-red-500 p-4">
              <div className="text-center">
                <p className="font-bold">Error</p>
                <p>{error}</p>
                <button 
                  className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </button>
              </div>
            </div>
          )}
          
          <div className="relative w-full h-full">
            <img
              ref={imgRef}
              alt="Video feed"
              className="w-full h-full object-contain"
              style={{ display: isLoading ? 'none' : 'block' }}
            />
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
              </div>
            )}
          </div>
          
          {/* Overlay */}
          <div className="absolute top-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
            Face & Blink Detection
          </div>
        </div>

        {/* Status Panel */}
        <div className="w-full md:w-80 bg-white p-4 rounded-lg shadow-md overflow-y-auto">
          <h2 className="text-lg font-semibold mb-4">Detection Status</h2>
          
          <div className="space-y-4">
            {/* Connection Status */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <h3 className="font-medium text-gray-700 mb-2">Connection</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="text-gray-600">Status:</span>
                <span className="font-medium">
                  {isLoading ? 'Connecting...' : 'Connected'}
                </span>
                <span className="text-gray-600">Last Update:</span>
                <span className="font-mono text-xs">{status.timestamp}</span>
              </div>
            </div>

            {/* Face Recognition */}
            <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">
              <h3 className="font-medium text-blue-700 mb-2 flex items-center">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
                Face Recognition
              </h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="text-blue-600 font-medium">Name:</span>
                <span className="font-medium text-gray-800">
                  {status.face_name || 'Not detected'}
                </span>
                
                <span className="text-blue-600 font-medium">Confidence:</span>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className={`h-2.5 rounded-full ${status.confidence > 70 ? 'bg-green-500' : status.confidence > 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${status.confidence || 0}%` }}
                  ></div>
                </div>
                <span className="text-xs text-gray-500 col-span-2 text-right">
                  {status.confidence ? `${status.confidence.toFixed(1)}%` : '0%'}
                </span>
              </div>
            </div>

            {/* Yawning Detection */}
            <div className={`p-3 rounded-lg border-l-4 ${status.is_yawning ? 'bg-red-50 border-red-500' : 'bg-green-50 border-green-500'}`}>
              <h3 className="font-medium flex items-center">
                <svg className={`w-4 h-4 mr-2 ${status.is_yawning ? 'text-red-700' : 'text-green-700'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                </svg>
                <span className={status.is_yawning ? 'text-red-700' : 'text-green-700'}>
                  {status.is_yawning ? 'Yawning Detected!' : 'No Yawning'}
                </span>
              </h3>
              <div className="mt-2">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Mouth Aspect Ratio:</span>
                  <span className="font-medium">
                    {status.mar ? status.mar.toFixed(2) : 'N/A'}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className={`h-2.5 rounded-full ${status.mar > 0.5 ? 'bg-red-500' : 'bg-green-500'}`}
                    style={{ width: `${Math.min(100, (status.mar || 0) * 100)}%` }}
                  ></div>
                </div>
                <p className="text-xs mt-1 text-gray-600">
                  {status.is_yawning 
                    ? 'Driver may be feeling drowsy. Please take a break.'
                    : 'Driver appears alert and focused.'}
                </p>
              </div>
            </div>

            {/* Blink Detection */}
            <div className="bg-green-50 p-3 rounded-lg">
              <h3 className="font-medium text-green-700 mb-2">Blink Detection</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="text-green-600">Blink Count:</span>
                <span className="font-medium">{status.blink_count}</span>
                
                <span className="text-green-600">EAR:</span>
                <span>{status.ear ? status.ear.toFixed(3) : 'N/A'}</span>
                
                <span className="text-green-600">Eyes Status:</span>
                <span className={status.is_eyes_closed ? 'text-red-600 font-medium' : 'text-green-600'}>
                  {status.is_eyes_closed ? 'CLOSED' : 'Open'}
                </span>
                
                <span className="text-green-600">Yawning:</span>
                <span className={status.is_yawning ? 'text-red-600 font-medium' : 'text-green-600'}>
                  {status.is_yawning ? 'DETECTED' : 'No'}
                </span>
              </div>
            </div>

            {/* Performance */}
            <div className="bg-purple-50 p-3 rounded-lg">
              <h3 className="font-medium text-purple-700 mb-2">Performance</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="text-purple-600">FPS:</span>
                <span className="font-medium">{status.fps || 'N/A'}</span>
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-blue-700">
                    Video feed from the main detection system
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CombinedCamera;
