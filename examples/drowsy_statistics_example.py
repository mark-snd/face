"""
졸림 감지 통계 수집 예제
========================
졸림/하품 이벤트를 수집하여 통계를 분석하고
리포트를 생성하는 예제입니다.

사용법:
1. 터미널 1에서 main.py 실행
2. 터미널 2에서 이 스크립트 실행
"""

import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

PIPE_PATH = "/tmp/face_status_pipe"
STATS_FILE = "drowsy_statistics.json"


class DrowsyStatistics:
    def __init__(self):
        self.events = []
        self.session_start = datetime.now()
        self.load_stats()

    def load_stats(self):
        """저장된 통계 로드"""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r') as f:
                    data = json.load(f)
                    self.events = data.get('events', [])
                    print(f"기존 통계 로드: {len(self.events)}개 이벤트")
            except:
                self.events = []

    def save_stats(self):
        """통계 저장"""
        with open(STATS_FILE, 'w') as f:
            json.dump({'events': self.events}, f, indent=2)

    def add_event(self, event_type):
        """이벤트 추가"""
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'hour': datetime.now().hour
        }
        self.events.append(event)
        self.save_stats()
        return event

    def get_session_stats(self):
        """현재 세션 통계"""
        session_events = [
            e for e in self.events
            if datetime.fromisoformat(e['timestamp']) >= self.session_start
        ]

        drowsy = sum(1 for e in session_events if e['type'] == 'DROWSY')
        yawn = sum(1 for e in session_events if e['type'] == 'YAWN')

        duration = datetime.now() - self.session_start
        minutes = int(duration.total_seconds() / 60)

        return {
            'duration_minutes': minutes,
            'drowsy_count': drowsy,
            'yawn_count': yawn,
            'total_events': drowsy + yawn
        }

    def get_hourly_distribution(self):
        """시간대별 이벤트 분포"""
        hourly = defaultdict(lambda: {'DROWSY': 0, 'YAWN': 0})

        for event in self.events:
            hour = event.get('hour', 0)
            event_type = event['type']
            hourly[hour][event_type] += 1

        return dict(hourly)

    def get_today_stats(self):
        """오늘의 통계"""
        today = datetime.now().date()
        today_events = [
            e for e in self.events
            if datetime.fromisoformat(e['timestamp']).date() == today
        ]

        drowsy = sum(1 for e in today_events if e['type'] == 'DROWSY')
        yawn = sum(1 for e in today_events if e['type'] == 'YAWN')

        return {'drowsy': drowsy, 'yawn': yawn, 'total': drowsy + yawn}

    def print_report(self):
        """통계 리포트 출력"""
        session = self.get_session_stats()
        today = self.get_today_stats()
        hourly = self.get_hourly_distribution()

        print("\n" + "=" * 50)
        print("📊 졸림 감지 통계 리포트")
        print("=" * 50)

        # 현재 세션
        print("\n[ 현재 세션 ]")
        print(f"  경과 시간: {session['duration_minutes']}분")
        print(f"  졸림 감지: {session['drowsy_count']}회")
        print(f"  하품 감지: {session['yawn_count']}회")

        # 오늘 누적
        print("\n[ 오늘 누적 ]")
        print(f"  졸림 감지: {today['drowsy']}회")
        print(f"  하품 감지: {today['yawn']}회")
        print(f"  총 이벤트: {today['total']}회")

        # 시간대별 분포
        print("\n[ 시간대별 분포 ]")
        for hour in sorted(hourly.keys()):
            data = hourly[hour]
            total = data['DROWSY'] + data['YAWN']
            bar = "█" * min(total, 20)
            print(f"  {hour:02d}시: {bar} ({data['DROWSY']}D/{data['YAWN']}Y)")

        # 피로도 분석
        print("\n[ 피로도 분석 ]")
        if session['total_events'] == 0:
            print("  ✅ 양호: 졸림/하품 없음")
        elif session['total_events'] < 3:
            print("  ⚠️  주의: 약간의 피로 징후")
        elif session['total_events'] < 6:
            print("  🟠 경고: 피로 누적 - 휴식 권장")
        else:
            print("  🔴 위험: 심한 피로 - 즉시 휴식 필요!")

        print("\n" + "=" * 50)


def main():
    print("╔══════════════════════════════════════╗")
    print("║    졸림 감지 통계 수집 예제          ║")
    print("╚══════════════════════════════════════╝")
    print()
    print(f"통계 파일: {STATS_FILE}")
    print(f"파이프 경로: {PIPE_PATH}")
    print("main.py를 먼저 실행하세요!")
    print()
    print("명령어: 'r' + Enter = 리포트 출력")
    print("-" * 50)

    stats = DrowsyStatistics()
    stats.print_report()

    print("\n이벤트 대기 중...")

    with open(PIPE_PATH, 'r') as pipe:
        while True:
            event = pipe.readline().strip()
            if event in ("DROWSY", "YAWN"):
                timestamp = datetime.now().strftime("%H:%M:%S")
                stats.add_event(event)

                session = stats.get_session_stats()
                print(f"[{timestamp}] {event} | "
                      f"세션: {session['drowsy_count']}D/{session['yawn_count']}Y | "
                      f"경과: {session['duration_minutes']}분")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("오류: Named Pipe를 찾을 수 없습니다.")
        print("main.py를 먼저 실행하세요.")
    except KeyboardInterrupt:
        print("\n\n최종 리포트:")
        stats = DrowsyStatistics()
        stats.print_report()
        print("프로그램 종료")
