"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import components with SSR disabled
const Camera = dynamic(
  () => import('./Camera'),
  { ssr: false, loading: () => <div>Loading Camera...</div> }
);

const FatigueCamera = dynamic(
  () => import('./FatigueCamera'),
  { ssr: false, loading: () => <div>Loading Fatigue Detection...</div> }
);

const CombinedCamera = dynamic(
  () => import('./CombinedCamera'),
  { ssr: false, loading: () => <div>Loading Combined View...</div> }
);

import Header from "./Header";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const TABS = [
  { id: 'combined', label: 'Combined View' },
  { id: 'face', label: 'Face Recognition' },
  { id: 'blink', label: 'Blink Detection' },
  { id: 'tiredness', label: 'Tiredness Detection' },
];

const MetricsChart = ({ data, title, color = 'rgb(79, 70, 229)' }) => {
  const chartData = {
    labels: data.map((_, i) => i + 1),
    datasets: [
      {
        label: title,
        data: data,
        borderColor: color,
        backgroundColor: `${color}20`,
        tension: 0.4,
        fill: true,
      },
    ],
  };
  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true } },
    animation: { duration: 0 },
  };
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
      <div className="h-32">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};

const Dashboard = () => {
  console.log('[Dashboard] Rendering Dashboard component');
  
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState('face');
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fatigueStatus, setFatigueStatus] = useState({
    ear: 0,
    mar: 0,
    angle: 0,
    warning: '',
    blink_count: 0,
    is_yawning: false,
    fps: 0,
  });
  
  useEffect(() => {
    console.log('[Dashboard] Component mounted');
    setMounted(true);
    
    return () => {
      console.log('[Dashboard] Component unmounting');
      setMounted(false);
    };
  }, []);

  const [metrics, setMetrics] = useState({
    faceDetected: false,
    faceName: 'Unknown',
    faceConfidence: 0,
    lastFaceUpdate: null,
    blinkCount: 0,
    blinkRate: 0,
    ear: 0,
    mar: 0,
    isTired: false,
    recognitionStatus: 'inactive',
  });
  const [history, setHistory] = useState({
    ear: Array(30).fill(0),
    mar: Array(30).fill(0),
    blinks: Array(30).fill(0),
  });
  const metricsInterval = useRef(null);

  // Handle face detection events from the Camera component
  const handleFaceDetected = (faceData) => {
    setMetrics(prev => ({
      ...prev,
      faceDetected: faceData.face_detected || false,
      faceName: faceData.name || 'Unknown',
      faceConfidence: faceData.confidence || 0,
      lastFaceUpdate: new Date().toISOString(),
      blinkCount: faceData.blink_count || prev.blinkCount,
      ear: faceData.eye_aspect_ratio || prev.ear,
      mar: faceData.mouth_aspect_ratio || prev.mar,
    }));
  };
  
  // Handle fatigue detection status updates
  const handleFatigueStatusUpdate = (status) => {
    setFatigueStatus(prev => ({
      ...prev,
      ...status
    }));
    
    // Update metrics based on fatigue status
    setMetrics(prev => ({
      ...prev,
      blinkCount: status.blink_count || prev.blinkCount,
      ear: status.ear || prev.ear,
      mar: status.mar || prev.mar,
      isTired: !!status.warning,
    }));
    
    // Update history with new data
    setHistory(prev => ({
      ear: [...prev.ear.slice(1), status.ear || 0],
      mar: [...prev.mar.slice(1), status.mar || 0],
      blinks: [...prev.blinks.slice(1), status.blink_count || 0]
    }));
  };

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // First check if backend is responsive
        const statusRes = await fetch('http://localhost:5000/status').catch(() => ({ ok: false }));
        const isBackendUp = statusRes.ok;
        setIsBackendConnected(isBackendUp);

        if (isBackendUp) {
          let metricsData = {};
          
          // Try to get metrics from the status endpoint first
          if (statusRes.ok) {
            metricsData = await statusRes.json();
            
            // Update metrics with the data from the backend
            setMetrics(prev => ({
              ...prev,
              blinkCount: metricsData.blink_count || 0,
              ear: 0, // Not available in status
              mar: 0, // Not available in status
              isTired: false, // Not available in status
              faceDetected: (metricsData.face_count || 0) > 0,
              faceName: metricsData.unique_people > 0 ? 'Recognized' : 'Unknown',
              faceConfidence: (metricsData.face_count || 0) > 0 ? 100 : 0,
              recognitionStatus: 'active'
            }));
            
            // Update history with dummy data since we don't have real metrics
            setHistory(prev => ({
              ear: [...prev.ear.slice(1), Math.random() * 0.2 + 0.1],
              mar: [...prev.mar.slice(1), Math.random() * 0.3 + 0.1],
              blinks: [...prev.blinks.slice(1), 0] // No blink count in status
            }));
          }
        } else {
          setError('Failed to connect to the face recognition service');
        }
      } catch (error) {
        console.log('[Dashboard] Error in fetchMetrics:', error);
        setIsBackendConnected(false);
        setLoading(false);
        setError(`Error: ${error.message}`);
      }
    };

    // Initial fetch
    console.log('[Dashboard] Starting initial metrics fetch');
    fetchMetrics();
    
    // Set up polling
    console.log('[Dashboard] Setting up metrics polling interval');
    metricsInterval.current = setInterval(fetchMetrics, 5000);

    return () => {
      console.log('[Dashboard] Cleaning up metrics interval');
      if (metricsInterval.current) {
        clearInterval(metricsInterval.current);
      }
    };
  }, [mounted]);

  const toggleRecognition = async () => {
    const newStatus = metrics.recognitionStatus === 'active' ? 'inactive' : 'active';
    // In a real implementation, you would call an API endpoint here
    // For now, we'll just toggle the local state
    setMetrics(prev => ({ ...prev, recognitionStatus: newStatus }));
    
    // Optional: Show a toast or notification
    console.log(`Recognition ${newStatus}`);
  };


  // Check backend connection
  const checkBackend = useCallback(async () => {
    try {
      const [faceStatus, blinkStatus] = await Promise.allSettled([
        fetch('http://localhost:5000/status').then(res => res.ok && res.json()),
        fetch('http://localhost:5002/status').then(res => res.ok && res.json())
      ]);
      
      const isFaceServiceUp = faceStatus.status === 'fulfilled' && faceStatus.value !== false;
      const isBlinkServiceUp = blinkStatus.status === 'fulfilled' && blinkStatus.value !== false;
      
      setIsBackendConnected(isFaceServiceUp && isBlinkServiceUp);
      
      if (!isFaceServiceUp) {
        console.log('Face recognition service is not available');
      }
      if (!isBlinkServiceUp) {
        console.log('Blink detection service is not available');
      }
      
      // Update metrics if face service is up
      if (isFaceServiceUp) {
        setMetrics(prev => ({
          ...prev,
          recognitionStatus: faceStatus.value?.status || 'inactive'
        }));
      }
      return { isFaceServiceUp, isBlinkServiceUp };
    } catch (error) {
      console.log('Error connecting to backend:', error);
      setIsBackendConnected(false);
      return { isFaceServiceUp: false, isBlinkServiceUp: false };
    }
  }, []);

  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, 5000);

    return () => clearInterval(interval);
  }, []);

  // Loading state for client-side mounting
  if (!mounted) {
    if (loading) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      );
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8 overflow-x-auto">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
              <div className="flex items-center ml-4">
                <div className={`w-2 h-2 rounded-full mr-2 ${isBackendConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isBackendConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </nav>
          </div>

          <div className="mt-6">
            {activeTab === 'combined' && <CombinedCamera />}
            {activeTab === 'face' && <Camera onFaceDetected={handleFaceDetected} mode="face" />}
            {activeTab === 'blink' && <FatigueCamera onStatusUpdate={handleFatigueStatusUpdate} mode="blink" />}
            {activeTab === 'tiredness' && (
              <div className="p-8 text-center text-gray-500">
                <p className="text-lg font-medium">Tiredness Detection</p>
                <p className="mt-2">This feature is coming soon.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
