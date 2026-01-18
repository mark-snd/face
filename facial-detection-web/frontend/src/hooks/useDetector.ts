import { useState, useCallback, useRef, useEffect } from 'react';
import { faceDetector } from '@/lib/detector';
import { alerter } from '@/lib/alerter';
import type { DetectionResult, DetectionState, DetectionConfig, DEFAULT_CONFIG } from '@/types';

interface UseDetectorOptions {
  config?: Partial<DetectionConfig>;
  onDrowsy?: (result: DetectionResult) => void;
  onYawn?: (result: DetectionResult) => void;
  onDetection?: (result: DetectionResult) => void;
}

interface UseDetectorReturn {
  state: DetectionState;
  isModelLoaded: boolean;
  loadModels: () => Promise<void>;
  startDetection: (videoElement: HTMLVideoElement) => void;
  stopDetection: () => void;
  updateConfig: (config: Partial<DetectionConfig>) => void;
  latestResult: DetectionResult | null;
}

const DEFAULT_DETECTION_CONFIG: DetectionConfig = {
  earThreshold: 0.22,
  marThreshold: 0.6,
  drowsyTime: 2.0,
  yawnTime: 1.0,
  alertCooldown: 3.0,
};

export function useDetector(options: UseDetectorOptions = {}): UseDetectorReturn {
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [latestResult, setLatestResult] = useState<DetectionResult | null>(null);
  const [state, setState] = useState<DetectionState>({
    isModelLoaded: false,
    isDetecting: false,
    isFaceDetected: false,
    currentEAR: 0,
    currentMAR: 0,
    isDrowsy: false,
    isYawning: false,
    currentEmotion: 'neutral',
    emotionConfidence: 0,
    eyesClosedDuration: 0,
    mouthOpenDuration: 0,
  });

  const configRef = useRef<DetectionConfig>({
    ...DEFAULT_DETECTION_CONFIG,
    ...options.config,
  });
  const animationFrameRef = useRef<number | null>(null);
  const eyesClosedStartRef = useRef<number | null>(null);
  const mouthOpenStartRef = useRef<number | null>(null);
  const lastDrowsyAlertRef = useRef<number>(0);
  const lastYawnAlertRef = useRef<number>(0);

  const loadModels = useCallback(async () => {
    try {
      await faceDetector.initialize();
      setIsModelLoaded(true);
      setState((prev) => ({ ...prev, isModelLoaded: true }));
      await alerter.requestNotificationPermission();
    } catch (error) {
      console.error('Failed to load models:', error);
      throw error;
    }
  }, []);

  const processDetection = useCallback(
    (result: DetectionResult | null) => {
      const now = Date.now();
      const config = configRef.current;

      if (!result) {
        setState((prev) => ({
          ...prev,
          isFaceDetected: false,
          currentEAR: 0,
          currentMAR: 0,
        }));
        eyesClosedStartRef.current = null;
        mouthOpenStartRef.current = null;
        return;
      }

      setLatestResult(result);
      options.onDetection?.(result);

      const { ear, mar, dominantEmotion, confidence } = result;

      // Eye closure detection
      let eyesClosedDuration = 0;
      let isDrowsy = false;

      if (ear < config.earThreshold) {
        if (eyesClosedStartRef.current === null) {
          eyesClosedStartRef.current = now;
        }
        eyesClosedDuration = (now - eyesClosedStartRef.current) / 1000;

        if (eyesClosedDuration >= config.drowsyTime) {
          isDrowsy = true;
          if (now - lastDrowsyAlertRef.current > config.alertCooldown * 1000) {
            lastDrowsyAlertRef.current = now;
            alerter.playDrowsyAlert();
            alerter.showNotification('졸음 감지!', '잠시 휴식이 필요합니다.');
            options.onDrowsy?.(result);
          }
        }
      } else {
        eyesClosedStartRef.current = null;
      }

      // Yawn detection
      let mouthOpenDuration = 0;
      let isYawning = false;

      if (mar > config.marThreshold) {
        if (mouthOpenStartRef.current === null) {
          mouthOpenStartRef.current = now;
        }
        mouthOpenDuration = (now - mouthOpenStartRef.current) / 1000;

        if (mouthOpenDuration >= config.yawnTime) {
          isYawning = true;
          if (now - lastYawnAlertRef.current > config.alertCooldown * 1000) {
            lastYawnAlertRef.current = now;
            alerter.playYawnAlert();
            options.onYawn?.(result);
          }
        }
      } else {
        mouthOpenStartRef.current = null;
      }

      setState((prev) => ({
        ...prev,
        isFaceDetected: true,
        currentEAR: ear,
        currentMAR: mar,
        isDrowsy,
        isYawning,
        currentEmotion: dominantEmotion,
        emotionConfidence: confidence,
        eyesClosedDuration,
        mouthOpenDuration,
      }));
    },
    [options]
  );

  const startDetection = useCallback(
    (videoElement: HTMLVideoElement) => {
      if (!isModelLoaded) {
        console.warn('Models not loaded yet');
        return;
      }

      setState((prev) => ({ ...prev, isDetecting: true }));
      let isRunning = true;

      const detect = async () => {
        if (!isRunning) return;

        if (videoElement.readyState >= 2) {
          const result = await faceDetector.detect(videoElement);
          processDetection(result);
        }

        if (isRunning) {
          // Request next frame immediately after detection completes
          animationFrameRef.current = requestAnimationFrame(detect);
        }
      };

      detect();

      // Store cleanup function
      const originalStop = stopDetection;
      return () => {
        isRunning = false;
        originalStop();
      };
    },
    [isModelLoaded, processDetection]
  );

  const stopDetection = useCallback(() => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    setState((prev) => ({ ...prev, isDetecting: false }));
    eyesClosedStartRef.current = null;
    mouthOpenStartRef.current = null;
  }, []);

  const updateConfig = useCallback((newConfig: Partial<DetectionConfig>) => {
    configRef.current = { ...configRef.current, ...newConfig };
    if (newConfig.alertCooldown !== undefined) {
      alerter.setCooldown(newConfig.alertCooldown);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return {
    state,
    isModelLoaded,
    loadModels,
    startDetection,
    stopDetection,
    updateConfig,
    latestResult,
  };
}
