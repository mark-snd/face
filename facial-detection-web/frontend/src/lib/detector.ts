import * as faceapi from '@vladmandic/face-api';
import type { Point, DetectionResult, Emotions } from '@/types';

export class FaceDetector {
  private isLoaded = false;
  private modelPath = '/models';

  async initialize(modelPath?: string): Promise<void> {
    if (this.isLoaded) return;

    if (modelPath) {
      this.modelPath = modelPath;
    }

    try {
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(this.modelPath),
        faceapi.nets.faceLandmark68Net.loadFromUri(this.modelPath),
        faceapi.nets.faceExpressionNet.loadFromUri(this.modelPath),
      ]);
      this.isLoaded = true;
      console.log('Face detection models loaded successfully');
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
    if (!this.isLoaded) {
      console.warn('Models not loaded yet');
      return null;
    }

    const detection = await faceapi
      .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({
        inputSize: 416,
        scoreThreshold: 0.5,
      }))
      .withFaceLandmarks()
      .withFaceExpressions();

    if (!detection) {
      return null;
    }

    const landmarks = detection.landmarks;
    const leftEye = landmarks.getLeftEye();
    const rightEye = landmarks.getRightEye();
    const mouth = landmarks.getMouth();

    const ear = this.calculateEAR(leftEye, rightEye);
    const mar = this.calculateMAR(mouth);

    const emotions = detection.expressions as unknown as Emotions;
    const dominantEmotion = this.getDominantEmotion(emotions);

    return {
      ear,
      mar,
      emotions,
      dominantEmotion: dominantEmotion.emotion,
      confidence: dominantEmotion.confidence,
      landmarks: landmarks.positions.map((p) => ({ x: p.x, y: p.y })),
      faceBox: {
        x: detection.detection.box.x,
        y: detection.detection.box.y,
        width: detection.detection.box.width,
        height: detection.detection.box.height,
      },
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

  private calculateMAR(mouth: Point[]): number {
    // Mouth landmark indices (12 points for outer lip):
    // 0-5: upper lip, 6-11: lower lip
    // Using specific points for vertical/horizontal measurements
    const A = this.euclidean(mouth[2], mouth[10]); // vertical 1
    const B = this.euclidean(mouth[4], mouth[8]);  // vertical 2
    const C = this.euclidean(mouth[3], mouth[9]);  // vertical 3
    const D = this.euclidean(mouth[0], mouth[6]);  // horizontal
    return (A + B + C) / (2.0 * D);
  }

  private euclidean(p1: Point, p2: Point): number {
    return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
  }

  private getDominantEmotion(emotions: Emotions): {
    emotion: string;
    confidence: number;
  } {
    const entries = Object.entries(emotions) as [string, number][];
    const sorted = entries.sort((a, b) => b[1] - a[1]);
    return {
      emotion: sorted[0][0],
      confidence: sorted[0][1],
    };
  }
}

export const faceDetector = new FaceDetector();
