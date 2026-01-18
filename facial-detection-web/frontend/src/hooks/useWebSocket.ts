import { useState, useCallback, useRef, useEffect } from 'react';
import type { DetectionEvent } from '@/types';

interface WebSocketState {
  isConnected: boolean;
  error: string | null;
  reconnectAttempts: number;
}

interface UseWebSocketOptions {
  url?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  onMessage?: (data: unknown) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

interface UseWebSocketReturn {
  state: WebSocketState;
  connect: () => void;
  disconnect: () => void;
  sendEvent: (event: DetectionEvent) => void;
  sendMessage: (data: unknown) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/events`,
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    error: null,
    reconnectAttempts: 0,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current !== null) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setState({
          isConnected: true,
          error: null,
          reconnectAttempts: 0,
        });
        onConnect?.();
        console.log('WebSocket connected');
      };

      wsRef.current.onclose = () => {
        setState((prev) => ({
          ...prev,
          isConnected: false,
        }));
        onDisconnect?.();
        console.log('WebSocket disconnected');

        // Auto reconnect
        if (autoReconnect && state.reconnectAttempts < maxReconnectAttempts) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            setState((prev) => ({
              ...prev,
              reconnectAttempts: prev.reconnectAttempts + 1,
            }));
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setState((prev) => ({
          ...prev,
          error: 'WebSocket connection error',
        }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Connection failed';
      setState((prev) => ({
        ...prev,
        error: message,
      }));
    }
  }, [url, autoReconnect, maxReconnectAttempts, reconnectInterval, onMessage, onConnect, onDisconnect, state.reconnectAttempts]);

  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setState({
      isConnected: false,
      error: null,
      reconnectAttempts: 0,
    });
  }, [clearReconnectTimeout]);

  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const sendEvent = useCallback((event: DetectionEvent) => {
    sendMessage({
      ...event,
      timestamp: event.timestamp || Date.now(),
    });
  }, [sendMessage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearReconnectTimeout();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [clearReconnectTimeout]);

  return {
    state,
    connect,
    disconnect,
    sendEvent,
    sendMessage,
  };
}
