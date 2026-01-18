import { useState, useEffect, useCallback } from 'react';
import { useCamera } from '@/hooks/useCamera';
import { useDetector } from '@/hooks/useDetector';
import { useWebSocket } from '@/hooks/useWebSocket';
import { VideoPreview } from '@/components/VideoPreview';
import { StatusDashboard } from '@/components/StatusDashboard';
import { SettingsPanel } from '@/components/SettingsPanel';
import type { DetectionConfig, DetectionResult } from '@/types';

const DEFAULT_CONFIG: DetectionConfig = {
  earThreshold: 0.22,
  marThreshold: 0.6,
  drowsyTime: 2.0,
  yawnTime: 1.0,
  alertCooldown: 3.0,
};

export default function App() {
  const [config, setConfig] = useState<DetectionConfig>(DEFAULT_CONFIG);
  const [isRunning, setIsRunning] = useState(false);

  const { videoRef, state: cameraState, startCamera, stopCamera, switchCamera } = useCamera();

  const handleDrowsy = useCallback((result: DetectionResult) => {
    wsActions.sendEvent({
      type: 'DROWSY',
      timestamp: Date.now(),
      ear: result.ear,
      emotion: result.dominantEmotion,
    });
  }, []);

  const handleYawn = useCallback((result: DetectionResult) => {
    wsActions.sendEvent({
      type: 'YAWN',
      timestamp: Date.now(),
      mar: result.mar,
      emotion: result.dominantEmotion,
    });
  }, []);

  const {
    state: detectorState,
    isModelLoaded,
    loadModels,
    startDetection,
    stopDetection,
    updateConfig,
    latestResult,
  } = useDetector({
    config,
    onDrowsy: handleDrowsy,
    onYawn: handleYawn,
  });

  const wsActions = useWebSocket({
    onMessage: (data) => {
      console.log('WebSocket message:', data);
    },
  });

  // Load models on mount
  useEffect(() => {
    loadModels().catch(console.error);
  }, [loadModels]);

  const handleStart = async () => {
    try {
      await startCamera();
      setIsRunning(true);
    } catch (error) {
      console.error('Failed to start:', error);
    }
  };

  const handleStop = () => {
    stopDetection();
    stopCamera();
    setIsRunning(false);
  };

  // Start detection when camera is active and models are loaded
  useEffect(() => {
    if (isRunning && cameraState.isActive && isModelLoaded && videoRef.current) {
      startDetection(videoRef.current);
    }
  }, [isRunning, cameraState.isActive, isModelLoaded, videoRef, startDetection]);

  const handleConfigChange = (newConfig: Partial<DetectionConfig>) => {
    setConfig((prev) => ({ ...prev, ...newConfig }));
    updateConfig(newConfig);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">얼굴 표정 & 졸음 감지</h1>
          <div className="flex items-center gap-2">
            {wsActions.state.isConnected && (
              <span className="text-xs text-green-400 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-400 rounded-full" />
                서버 연결됨
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video preview */}
          <div className="lg:col-span-2 space-y-4">
            <VideoPreview
              videoRef={videoRef}
              state={detectorState}
              latestResult={latestResult}
            />

            {/* Controls */}
            <div className="flex justify-center gap-4">
              {!isRunning ? (
                <button
                  onClick={handleStart}
                  disabled={!isModelLoaded}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-semibold transition-colors"
                >
                  {isModelLoaded ? '시작' : '모델 로딩 중...'}
                </button>
              ) : (
                <button
                  onClick={handleStop}
                  className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-semibold transition-colors"
                >
                  중지
                </button>
              )}
            </div>

            {/* Error message */}
            {cameraState.error && (
              <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-400">
                <strong>오류:</strong> {cameraState.error}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <StatusDashboard state={detectorState} config={config} />
            <SettingsPanel
              config={config}
              onConfigChange={handleConfigChange}
              devices={cameraState.devices}
              selectedDeviceId={cameraState.selectedDeviceId}
              onDeviceChange={switchCamera}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 py-2 px-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-gray-400">
          <span>웹 기반 얼굴 표정 & 졸음 감지 시스템</span>
          <span>face-api.js + React</span>
        </div>
      </footer>
    </div>
  );
}
