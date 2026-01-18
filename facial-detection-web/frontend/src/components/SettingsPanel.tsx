import { useState } from 'react';
import type { DetectionConfig } from '@/types';

interface SettingsPanelProps {
  config: DetectionConfig;
  onConfigChange: (config: Partial<DetectionConfig>) => void;
  devices: MediaDeviceInfo[];
  selectedDeviceId: string | null;
  onDeviceChange: (deviceId: string) => void;
}

export function SettingsPanel({
  config,
  onConfigChange,
  devices,
  selectedDeviceId,
  onDeviceChange,
}: SettingsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between text-white hover:bg-gray-700 transition-colors"
      >
        <span className="font-semibold">설정</span>
        <svg
          className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Content */}
      {isOpen && (
        <div className="p-4 border-t border-gray-700 space-y-4">
          {/* Camera selection */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              카메라 선택
            </label>
            <select
              value={selectedDeviceId || ''}
              onChange={(e) => onDeviceChange(e.target.value)}
              className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {devices.map((device) => (
                <option key={device.deviceId} value={device.deviceId}>
                  {device.label || `카메라 ${device.deviceId.slice(0, 8)}`}
                </option>
              ))}
            </select>
          </div>

          {/* EAR Threshold */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              EAR 임계값: {config.earThreshold.toFixed(2)}
            </label>
            <input
              type="range"
              min="0.15"
              max="0.30"
              step="0.01"
              value={config.earThreshold}
              onChange={(e) =>
                onConfigChange({ earThreshold: parseFloat(e.target.value) })
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>민감</span>
              <span>둔감</span>
            </div>
          </div>

          {/* MAR Threshold */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              MAR 임계값: {config.marThreshold.toFixed(2)}
            </label>
            <input
              type="range"
              min="0.4"
              max="0.8"
              step="0.05"
              value={config.marThreshold}
              onChange={(e) =>
                onConfigChange({ marThreshold: parseFloat(e.target.value) })
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>민감</span>
              <span>둔감</span>
            </div>
          </div>

          {/* Drowsy Time */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              졸음 감지 시간: {config.drowsyTime.toFixed(1)}초
            </label>
            <input
              type="range"
              min="1.0"
              max="5.0"
              step="0.5"
              value={config.drowsyTime}
              onChange={(e) =>
                onConfigChange({ drowsyTime: parseFloat(e.target.value) })
              }
              className="w-full"
            />
          </div>

          {/* Yawn Time */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              하품 감지 시간: {config.yawnTime.toFixed(1)}초
            </label>
            <input
              type="range"
              min="0.5"
              max="3.0"
              step="0.5"
              value={config.yawnTime}
              onChange={(e) =>
                onConfigChange({ yawnTime: parseFloat(e.target.value) })
              }
              className="w-full"
            />
          </div>

          {/* Alert Cooldown */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              알림 간격: {config.alertCooldown.toFixed(1)}초
            </label>
            <input
              type="range"
              min="1.0"
              max="10.0"
              step="1.0"
              value={config.alertCooldown}
              onChange={(e) =>
                onConfigChange({ alertCooldown: parseFloat(e.target.value) })
              }
              className="w-full"
            />
          </div>
        </div>
      )}
    </div>
  );
}
