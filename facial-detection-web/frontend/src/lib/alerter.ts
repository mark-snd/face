export class Alerter {
  private audioContext: AudioContext | null = null;
  private lastAlertTime = 0;
  private cooldown: number;

  constructor(cooldownSeconds = 3) {
    this.cooldown = cooldownSeconds * 1000;
  }

  private initAudioContext(): void {
    if (!this.audioContext) {
      this.audioContext = new AudioContext();
    }
  }

  async playAlert(frequency = 800, duration = 0.3): Promise<void> {
    const now = Date.now();
    if (now - this.lastAlertTime < this.cooldown) {
      return;
    }

    this.initAudioContext();
    if (!this.audioContext) return;

    this.lastAlertTime = now;

    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.5, this.audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(
      0.01,
      this.audioContext.currentTime + duration
    );

    oscillator.start(this.audioContext.currentTime);
    oscillator.stop(this.audioContext.currentTime + duration);
  }

  async playDrowsyAlert(): Promise<void> {
    await this.playAlert(800, 0.5);
    setTimeout(() => this.playAlert(1000, 0.3), 200);
  }

  async playYawnAlert(): Promise<void> {
    await this.playAlert(600, 0.3);
  }

  async requestNotificationPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }

    return false;
  }

  showNotification(title: string, body: string): void {
    if (Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon: '/favicon.ico',
        tag: 'drowsy-alert',
        requireInteraction: true,
      });
    }
  }

  setCooldown(seconds: number): void {
    this.cooldown = seconds * 1000;
  }
}

export const alerter = new Alerter();
