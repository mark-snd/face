import { useEffect, useRef } from 'react';
import type { DetectionResult, DetectionState } from '@/types';

interface VideoPreviewProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  state: DetectionState;
  latestResult: DetectionResult | null;
  showLandmarks?: boolean;
  showFaceBox?: boolean;
}

export function VideoPreview({
  videoRef,
  state,
  latestResult,
  showLandmarks = true,
  showFaceBox = true,
}: VideoPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const draw = () => {
      if (video.readyState >= 2) {
        // Set canvas size
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw mirrored video
        ctx.save();
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0);
        ctx.restore();

        // Draw overlays if detection result exists
        if (latestResult && state.isFaceDetected) {
          // Mirror coordinates for drawing
          const mirrorX = (x: number) => canvas.width - x;

          // Draw face box
          if (showFaceBox) {
            const box = latestResult.faceBox;
            ctx.strokeStyle = state.isDrowsy ? '#ef4444' : state.isYawning ? '#f97316' : '#22c55e';
            ctx.lineWidth = 3;
            ctx.strokeRect(
              mirrorX(box.x + box.width),
              box.y,
              box.width,
              box.height
            );
          }

          // Draw landmarks
          if (showLandmarks && latestResult.landmarks) {
            ctx.fillStyle = '#3b82f6';

            // Draw eye landmarks (indices 36-47)
            for (let i = 36; i < 48; i++) {
              const point = latestResult.landmarks[i];
              if (point) {
                ctx.beginPath();
                ctx.arc(mirrorX(point.x), point.y, 2, 0, Math.PI * 2);
                ctx.fill();
              }
            }

            // Draw mouth landmarks (indices 48-67)
            ctx.fillStyle = '#ec4899';
            for (let i = 48; i < 68; i++) {
              const point = latestResult.landmarks[i];
              if (point) {
                ctx.beginPath();
                ctx.arc(mirrorX(point.x), point.y, 2, 0, Math.PI * 2);
                ctx.fill();
              }
            }
          }
        }
      }

      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [videoRef, state, latestResult, showLandmarks, showFaceBox]);

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      {/* Hidden video element */}
      <video
        ref={videoRef}
        className="hidden"
        playsInline
        muted
      />

      {/* Canvas for rendering */}
      <canvas
        ref={canvasRef}
        className="w-full rounded-lg shadow-lg"
      />

      {/* Alert overlay */}
      {(state.isDrowsy || state.isYawning) && (
        <div
          className={`absolute inset-0 rounded-lg flex items-center justify-center ${
            state.isDrowsy
              ? 'bg-red-500/30 animate-pulse-fast'
              : 'bg-orange-500/30'
          }`}
        >
          <div className="text-white text-4xl font-bold drop-shadow-lg">
            {state.isDrowsy ? '졸음 감지!' : '하품 감지!'}
          </div>
        </div>
      )}

      {/* No face detected indicator */}
      {state.isDetecting && !state.isFaceDetected && (
        <div className="absolute inset-0 rounded-lg flex items-center justify-center bg-gray-900/50">
          <div className="text-white text-xl">
            얼굴을 감지하지 못했습니다
          </div>
        </div>
      )}

      {/* Model loading indicator */}
      {!state.isModelLoaded && (
        <div className="absolute inset-0 rounded-lg flex items-center justify-center bg-gray-900/70">
          <div className="text-white text-xl flex items-center gap-3">
            <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            모델 로딩 중...
          </div>
        </div>
      )}
    </div>
  );
}
