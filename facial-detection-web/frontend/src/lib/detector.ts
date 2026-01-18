import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';
import type { Point, DetectionResult, Emotions, BlendshapeScore } from '@/types';

export class FaceDetector {
  private isLoaded = false;
  private modelPath = '/models/face_landmarker.task';
  private wasmPath = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.8/wasm';
  private fallbackModelUrl = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task';
  private landmarker: FaceLandmarker | null = null;

  // MediaPipe Face Mesh landmark indices
  private static LEFT_EYE = [33, 160, 158, 133, 153, 144];
  private static RIGHT_EYE = [362, 385, 387, 263, 373, 380];
  private static MOUTH = {
    left: 61,
    right: 291,
    upper: 13,
    lower: 14,
    upper_left: 81,
    upper_right: 311,
    lower_left: 178,
    lower_right: 402,
  };

  async initialize(modelPath?: string): Promise<void> {
    if (this.isLoaded) return;

    if (modelPath) {
      this.modelPath = modelPath;
    }

    try {
      const filesetResolver = await FilesetResolver.forVisionTasks(this.wasmPath);
      const createLandmarker = (assetPath: string) =>
        FaceLandmarker.createFromOptions(filesetResolver, {
          baseOptions: { modelAssetPath: assetPath },
          outputFaceBlendshapes: true,
          runningMode: 'VIDEO',
          numFaces: 1,
        });

      try {
        this.landmarker = await createLandmarker(this.modelPath);
      } catch (primaryError) {
        console.warn(`MediaPipe model load failed from ${this.modelPath}, trying CDN fallback`, primaryError);
        this.landmarker = await createLandmarker(this.fallbackModelUrl);
      }

      this.isLoaded = true;
      console.log('MediaPipe Face Landmarker loaded successfully');
    } catch (error) {
      console.error('Failed to load face detection models:', error);
      throw new Error('Failed to load face detection models');
    }
  }

  isReady(): boolean {
    return this.isLoaded;
  }

  async detect(
    video: HTMLVideoElement | HTMLCanvasElement
  ): Promise<DetectionResult | null> {
    if (!this.isLoaded || !this.landmarker) {
      console.warn('Models not loaded yet');
      return null;
    }

    const timestampMs = performance.now();
    const result = this.landmarker.detectForVideo(video, timestampMs);

    if (!result || !result.faceLandmarks.length) {
      return null;
    }

    const width = video instanceof HTMLVideoElement ? video.videoWidth : video.width;
    const height = video instanceof HTMLVideoElement ? video.videoHeight : video.height;

    const normalized = result.faceLandmarks[0];
    const landmarks: Point[] = normalized.map((lm) => ({
      x: lm.x * width,
      y: lm.y * height,
    }));

    const leftEye = FaceDetector.LEFT_EYE.map((idx) => landmarks[idx]);
    const rightEye = FaceDetector.RIGHT_EYE.map((idx) => landmarks[idx]);
    const mouth = Object.fromEntries(
      Object.entries(FaceDetector.MOUTH).map(([key, idx]) => [key, landmarks[idx]])
    ) as Record<keyof typeof FaceDetector.MOUTH, Point>;

    const ear = this.calculateEAR(leftEye, rightEye);
    const mar = this.calculateMAR(mouth);

    const blendshapes = this.buildBlendshapes(result);
    const blendshapeMap = Object.fromEntries(blendshapes.map((b) => [b.name, b.score]));
    const { emotion, confidence, emotions } = this.summarizeEmotion(blendshapeMap);

    const blinkScore = this.average([
      blendshapeMap['eyeBlinkLeft'],
      blendshapeMap['eyeBlinkRight'],
    ]);
    const jawOpenScore = blendshapeMap['jawOpen'] ?? 0;

    const faceBox = this.buildBoundingBox(landmarks);

    return {
      ear,
      mar,
      blinkScore,
      jawOpenScore,
      emotions,
      dominantEmotion: emotion,
      confidence,
      blendshapes,
      landmarks,
      faceBox,
    };
  }

  private calculateEAR(leftEye: Point[], rightEye: Point[]): number {
    const leftEAR = this.eyeAspectRatio(leftEye);
    const rightEAR = this.eyeAspectRatio(rightEye);
    return (leftEAR + rightEAR) / 2;
  }

  private eyeAspectRatio(eye: Point[]): number {
    // Eye landmark indices:
    // 0: outer corner, 1: upper outer, 2: upper inner
    // 3: inner corner, 4: lower inner, 5: lower outer
    const A = this.euclidean(eye[1], eye[5]); // vertical 1
    const B = this.euclidean(eye[2], eye[4]); // vertical 2
    const C = this.euclidean(eye[0], eye[3]); // horizontal
    return (A + B) / (2.0 * C);
  }

  private calculateMAR(mouth: Record<string, Point>): number {
    const A = this.euclidean(mouth['upper'], mouth['lower']);
    const B = this.euclidean(mouth['upper_left'], mouth['lower_left']);
    const C = this.euclidean(mouth['upper_right'], mouth['lower_right']);
    const D = this.euclidean(mouth['left'], mouth['right']);
    return D === 0 ? 0 : (A + B + C) / (3.0 * D);
  }

  private euclidean(p1: Point, p2: Point): number {
    return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
  }

  private average(values: Array<number | undefined>): number {
    const filtered = values.filter((v): v is number => typeof v === 'number');
    if (!filtered.length) return 0;
    const sum = filtered.reduce((acc, v) => acc + v, 0);
    return sum / filtered.length;
  }

  private buildBlendshapes(result: ReturnType<FaceLandmarker['detectForVideo']>): BlendshapeScore[] {
    const categories = result?.faceBlendshapes?.[0]?.categories ?? [];
    return categories.map((c) => ({
      name: c.categoryName,
      score: c.score,
    }));
  }

  private summarizeEmotion(blendshapeMap: Record<string, number>): {
    emotion: string;
    confidence: number;
    emotions: Emotions;
  } {
    const happy = this.average([
      blendshapeMap['mouthSmileLeft'],
      blendshapeMap['mouthSmileRight'],
    ]);
    const frown = this.average([
      blendshapeMap['mouthFrownLeft'],
      blendshapeMap['mouthFrownRight'],
      blendshapeMap['browDownLeft'],
      blendshapeMap['browDownRight'],
    ]);
    const surprise = this.average([
      blendshapeMap['jawOpen'],
      blendshapeMap['eyeWideLeft'],
      blendshapeMap['eyeWideRight'],
    ]);
    const neutral = blendshapeMap['mouthClose'] ?? 0;

    const emotions: Emotions = {
      happy,
      frown,
      surprise,
      neutral,
    };

    const sorted = Object.entries(emotions).sort((a, b) => b[1] - a[1]);
    const [emotion, confidence] = sorted[0];
    return { emotion, confidence, emotions };
  }

  private buildBoundingBox(landmarks: Point[]) {
    const xs = landmarks.map((p) => p.x);
    const ys = landmarks.map((p) => p.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
    };
  }
}

export const faceDetector = new FaceDetector();
