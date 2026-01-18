export interface Point {
  x: number;
  y: number;
}

export interface Emotions {
  neutral: number;
  happy: number;
  sad: number;
  angry: number;
  fearful: number;
  disgusted: number;
  surprised: number;
}

export interface DetectionResult {
  ear: number;
  mar: number;
  emotions: Emotions;
  dominantEmotion: string;
  confidence: number;
  landmarks: Point[];
  faceBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface DetectionState {
  isModelLoaded: boolean;
  isDetecting: boolean;
  isFaceDetected: boolean;
  currentEAR: number;
  currentMAR: number;
  isDrowsy: boolean;
  isYawning: boolean;
  currentEmotion: string;
  emotionConfidence: number;
  eyesClosedDuration: number;
  mouthOpenDuration: number;
}

export interface DetectionConfig {
  earThreshold: number;
  marThreshold: number;
  drowsyTime: number;
  yawnTime: number;
  alertCooldown: number;
}

export const DEFAULT_CONFIG: DetectionConfig = {
  earThreshold: 0.22,
  marThreshold: 0.6,
  drowsyTime: 2.0,
  yawnTime: 1.0,
  alertCooldown: 3.0,
};

export interface DetectionEvent {
  type: 'DROWSY' | 'YAWN';
  timestamp: number;
  ear?: number;
  mar?: number;
  emotion?: string;
}
