import type { DetectionState, DetectionConfig } from '@/types';

interface StatusDashboardProps {
  state: DetectionState;
  config: DetectionConfig;
}

export function StatusDashboard({ state, config }: StatusDashboardProps) {
  const formatNumber = (num: number, decimals = 3) => num.toFixed(decimals);

  const getEARStatusColor = () => {
    if (!state.isFaceDetected) return 'text-gray-400';
    if (state.currentEAR < config.earThreshold) return 'text-red-500';
    return 'text-green-500';
  };

  const getMARStatusColor = () => {
    if (!state.isFaceDetected) return 'text-gray-400';
    if (state.currentMAR > config.marThreshold) return 'text-orange-500';
    return 'text-green-500';
  };

  const getEmotionEmoji = (emotion: string) => {
    const emojiMap: Record<string, string> = {
      neutral: '😐',
      happy: '😊',
      frown: '😠',
      surprise: '😲',
    };
    return emojiMap[emotion] || '😐';
  };

  const getEmotionKorean = (emotion: string) => {
    const koreanMap: Record<string, string> = {
      neutral: '무표정',
      happy: '행복',
      frown: '찡그림',
      surprise: '놀람',
    };
    return koreanMap[emotion] || emotion;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 text-white space-y-4">
      <h2 className="text-lg font-semibold border-b border-gray-700 pb-2">
        감지 상태
      </h2>

      {/* Status indicators */}
      <div className="grid grid-cols-2 gap-4">
        {/* EAR */}
        <div className="bg-gray-700 rounded-lg p-3">
          <div className="text-sm text-gray-400 mb-1">EAR (눈 비율)</div>
          <div className={`text-2xl font-mono ${getEARStatusColor()}`}>
            {state.isFaceDetected ? formatNumber(state.currentEAR) : '---'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            임계값: {config.earThreshold}
          </div>
          {state.eyesClosedDuration > 0 && (
            <div className="text-xs text-red-400 mt-1">
              눈 감음: {formatNumber(state.eyesClosedDuration, 1)}초
            </div>
          )}
        </div>

        {/* MAR */}
        <div className="bg-gray-700 rounded-lg p-3">
          <div className="text-sm text-gray-400 mb-1">MAR (입 비율)</div>
          <div className={`text-2xl font-mono ${getMARStatusColor()}`}>
            {state.isFaceDetected ? formatNumber(state.currentMAR) : '---'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            임계값: {config.marThreshold}
          </div>
          {state.mouthOpenDuration > 0 && (
            <div className="text-xs text-orange-400 mt-1">
              입 벌림: {formatNumber(state.mouthOpenDuration, 1)}초
            </div>
          )}
        </div>
      </div>

      {/* Alerts */}
      <div className="flex gap-2">
        <div
          className={`flex-1 text-center py-2 rounded-lg font-semibold ${
            state.isDrowsy
              ? 'bg-red-500 text-white animate-pulse'
              : 'bg-gray-700 text-gray-400'
          }`}
        >
          {state.isDrowsy ? '🚨 졸림 감지!' : '졸림 없음'}
        </div>
        <div
          className={`flex-1 text-center py-2 rounded-lg font-semibold ${
            state.isYawning
              ? 'bg-orange-500 text-white'
              : 'bg-gray-700 text-gray-400'
          }`}
        >
          {state.isYawning ? '🥱 하품 감지!' : '하품 없음'}
        </div>
      </div>

      {/* Emotion */}
      <div className="bg-gray-700 rounded-lg p-3">
        <div className="text-sm text-gray-400 mb-2">감정 인식</div>
        {state.isFaceDetected ? (
          <div className="flex items-center gap-3">
            <span className="text-3xl">
              {getEmotionEmoji(state.currentEmotion)}
            </span>
            <div>
              <div className="font-semibold">
                {getEmotionKorean(state.currentEmotion)}
              </div>
              <div className="text-sm text-gray-400">
                신뢰도: {(state.emotionConfidence * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        ) : (
          <div className="text-gray-500">얼굴 감지 대기 중...</div>
        )}
      </div>

      {/* Detection status */}
      <div className="flex items-center gap-2 text-sm">
        <div
          className={`w-2 h-2 rounded-full ${
            state.isDetecting ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
          }`}
        />
        <span className="text-gray-400">
          {state.isDetecting ? '감지 중' : '대기 중'}
        </span>
        {state.isFaceDetected && (
          <>
            <span className="text-gray-600">|</span>
            <span className="text-green-400">얼굴 감지됨</span>
          </>
        )}
      </div>
    </div>
  );
}
