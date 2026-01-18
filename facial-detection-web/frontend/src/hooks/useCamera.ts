import { useState, useCallback, useRef, useEffect } from 'react';

interface CameraState {
  isActive: boolean;
  error: string | null;
  devices: MediaDeviceInfo[];
  selectedDeviceId: string | null;
}

interface UseCameraReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  state: CameraState;
  startCamera: (deviceId?: string) => Promise<void>;
  stopCamera: () => void;
  switchCamera: (deviceId: string) => Promise<void>;
  captureFrame: () => ImageData | null;
}

export function useCamera(): UseCameraReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [state, setState] = useState<CameraState>({
    isActive: false,
    error: null,
    devices: [],
    selectedDeviceId: null,
  });

  const getDevices = useCallback(async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter((d) => d.kind === 'videoinput');
      setState((prev) => ({ ...prev, devices: videoDevices }));
      return videoDevices;
    } catch (error) {
      console.error('Failed to enumerate devices:', error);
      return [];
    }
  }, []);

  const startCamera = useCallback(async (deviceId?: string) => {
    try {
      // Stop existing stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      const constraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 },
          facingMode: 'user',
          ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const selectedId = stream.getVideoTracks()[0]?.getSettings()?.deviceId || null;

      setState((prev) => ({
        ...prev,
        isActive: true,
        error: null,
        selectedDeviceId: selectedId,
      }));

      // Get updated device list
      await getDevices();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to start camera';
      setState((prev) => ({
        ...prev,
        isActive: false,
        error: message,
      }));
      console.error('Camera error:', error);
    }
  }, [getDevices]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setState((prev) => ({
      ...prev,
      isActive: false,
      error: null,
    }));
  }, []);

  const switchCamera = useCallback(async (deviceId: string) => {
    await startCamera(deviceId);
  }, [startCamera]);

  const captureFrame = useCallback((): ImageData | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || !state.isActive) {
      return null;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return null;
    }

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Mirror the image (horizontal flip)
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);

    return ctx.getImageData(0, 0, canvas.width, canvas.height);
  }, [state.isActive]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Get devices on mount
  useEffect(() => {
    getDevices();
  }, [getDevices]);

  return {
    videoRef,
    canvasRef,
    state,
    startCamera,
    stopCamera,
    switchCamera,
    captureFrame,
  };
}
