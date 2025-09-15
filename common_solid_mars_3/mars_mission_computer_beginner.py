# mars_mission_computer_beginner.py
# ─────────────────────────────────────────────────────────
# 초급자 버전(간단/짧게): 문제1~3 + (문제4: 쓰레드만)
# 표준 라이브러리만 사용
# 실행 예)
#   python mars_mission_computer_beginner.py p1
#   python mars_mission_computer_beginner.py p2
#   python mars_mission_computer_beginner.py p3
#   python mars_mission_computer_beginner.py p4-threads
# 종료: p2/p4-threads 모드에서 터미널에 q + Enter
# ─────────────────────────────────────────────────────────

import json
import os
import platform
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
import subprocess

# ───────── 문제 공통: 환경 항목 스펙 ─────────
ENV_SPEC = {
    "mars_base_internal_temperature": ("°C",   (18.0, 30.0), 1),
    "mars_base_external_temperature": ("°C",   (0.0, 21.0),  1),
    "mars_base_internal_humidity":    ("%",    (50.0, 60.0), 1),
    "mars_base_external_illuminance": ("W/m²", (500.0, 715.0), 0),
    "mars_base_internal_co2":         ("%",    (0.02, 0.10), 3),
    "mars_base_internal_oxygen":      ("%",    (4.0, 7.0),   2),
}

# 저장될 폴더 설정
LOG_DIR = Path("logs")

# 자동화 주기 상수화
SENSOR_PERIOD_SEC = 5.0
INFO_PERIOD_SEC   = 20.0


# ───────── 문제 1: 더미 센서 ─────────
class DummySensor:
    """
    난수로 환경값을 만들어 보관/제공하는 더미 센서.
    """
    def __init__(self):
        # 상태(state): 최신 값 보관. 처음엔 None
        self.env_values = {k: None for k in ENV_SPEC}

    def set_env(self) -> None:
        """
        ENV_SPEC 범위에서 난수 생성 → 상태 갱신
        dict형태의 key,value값을 순회하기 용이하게 items()사용.
        """
        for key, (_unit, (lo, hi), nd) in ENV_SPEC.items():
            val = round(random.uniform(lo, hi), nd)
            if nd == 0:
                val = int(val)
            self.env_values[key] = val

    def get_env(self, *, log: bool = False) -> dict:
        """
        현재 스냅샷 반환(+옵션: 로그 1줄 기록)
        """
        snap = dict(self.env_values)
        if log:
            try:
                LOG_DIR.mkdir(parents=True, exist_ok=True)
                rec = {"ts": now_iso(), "type": "sensor", "data": snap}
                with (LOG_DIR / f"env_{datetime.now():%Y%m%d}.log").open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception as e:
                print(json_dumps({"ts": now_iso(), "type": "warn", "msg": f"log failed: {e}"}))
        return snap

# ───────── 문제 2/3: 미션 컴퓨터 ─────────
class MissionComputer:
    """
    센서 수집(주기), 시스템 정보/부하 출력.
    """
    def __init__(self, name="runComputer"):
        self.name = name
        self.sensor = DummySensor()
        self.env_values = {k: None for k in ENV_SPEC}

    # 문제 2: 5초 주기 수집(JSON), q로 종료
    def get_sensor_data(self, period_sec: float = 5.0, stop_event: Event | None = None) -> None:
        # time 모듈의 단조 시계 함수(경과 시간 측정을 위해 사용)
        next_tick = time.monotonic()
        while True:
            if stop_event and stop_event.is_set():
                print(json_dumps({"ts": now_iso(), "type": "system", "msg": "stop sensor"}))
                break
            self.sensor.set_env()
            snap = self.sensor.get_env(log=True)
            self.env_values.update(snap)
            out = {"ts": now_iso(), "node": self.name, "type": "sensor", "data": snap}
            print(json_dumps(out))
            
            next_tick += period_sec
            remaining = next_tick - time.monotonic()
            if remaining > 0:
                if stop_event and stop_event.is_set():
                    break
                # time 모듈로 현재 실행 중인 쓰레드를 지정한 (Seconds)만큼 정지.
                time.sleep(remaining)

    # 문제 3-1: 시스템 정보
    def get_mission_computer_info(self) -> dict:
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "cpu_cores": os.cpu_count(),
        }
        out = {"ts": now_iso(), "node": self.name, "type": "info", "data": info}
        print(json_dumps(out))
        return info

    # 문제 3-2: 시스템 부하(간단/초급자 버전)
    def get_mission_computer_load(self) -> dict:
        # 쉬운 근사치: loadavg(1분)/코어수 → 대략 CPU 사용률(%)
        cpu_pct = None
        mem_pct = None
        try:
            # hasattr 객체에 속성 이름이 있는지 불리언으로 확인.
            if hasattr(os, "getloadavg"):
                la1, _la5, _la15 = os.getloadavg()  # macOS/Linux
                cores = os.cpu_count() or 1
                cpu_pct = round(min(100.0, (la1 / cores) * 100.0), 1)
        except Exception:
            pass

        if platform.system() == "Darwin":
            mem_pct = _mac_memory_percent()

        load = {"cpu_percent": cpu_pct, "memory_percent": mem_pct}
        out = {"ts": now_iso(), "node": self.name, "type": "load", "data": load}

        print(json_dumps(out))

        return load
    
# ───────── 유틸 ─────────
def now_iso() -> str:
    """
    현재 로컬 시각을 가져옵니다.
    초 단위까지의 ISO 8601 문자열을 반환합니다.

    Returns:
        str: ISO 8601 string (e.g., "2025-09-12T18:42:03")
    """
    return datetime.now().isoformat(timespec="seconds")

def json_dumps(obj: dict) -> str:
    """딕셔너리를 JSON 문자열로 직렬화한다.

    Args:
        obj (dict): JSON으로 직렬화할 딕셔너리(내부 값은 JSON 직렬화 가능해야 함).

    Returns:
        str: 비ASCII 문자를 이스케이프하지 않는(JSON 그대로 유지) JSON 문자열.
    """
    return json.dumps(obj, ensure_ascii=False)

def run_threads() -> None:
    """
    문제4: 쓰레드 3개(info/load 20초, sensor 5초)
    """
    mc = MissionComputer("runComputer")
    stop = Event()

    def info_loop():
        period = INFO_PERIOD_SEC
        next_tick = time.monotonic()
        while not stop.is_set():
            mc.get_mission_computer_info()
            next_tick += period
            remaining = next_tick - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)

    def load_loop():
        period = INFO_PERIOD_SEC
        next_tick = time.monotonic()
        while not stop.is_set():
            mc.get_mission_computer_load()
            next_tick += period
            remaining = next_tick - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)

    def sensor_loop():
        mc.get_sensor_data(period_sec=SENSOR_PERIOD_SEC, stop_event=stop)

    t1 = Thread(target=info_loop, daemon=True)
    t2 = Thread(target=load_loop, daemon=True)
    t3 = Thread(target=sensor_loop, daemon=True)
    t1.start(); t2.start(); t3.start()

    print("Threads running. Stop with 'q' + Enter.")
    try:
        while True:
            cmd = sys.stdin.readline().strip().lower()
            if cmd == "q":
                break
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        t1.join(timeout=2); t2.join(timeout=2); t3.join(timeout=2)
        print("All threads stopped.")

def _mac_memory_percent() -> float | None:
    """
    vm_stat/sysctl 기반 macOS 메모리 사용률(%) 근사치. 실패 시 None.
    """
    try:
        pagesize = int(subprocess.check_output(["sysctl", "-n", "hw.pagesize"]).decode().strip())
        out = subprocess.check_output(["vm_stat"]).decode()

        def get_pages(prefix: str) -> int:
            for line in out.splitlines():
                if line.startswith(prefix):
                    # 예: "Pages active: 12345."
                    v = line.split(":", 1)[1].strip().strip(".").replace(",", "")
                    return int(v)
            return 0

        free = get_pages("Pages free")
        active = get_pages("Pages active")
        inactive = get_pages("Pages inactive")
        speculative = get_pages("Pages speculative")
        wired = get_pages("Pages wired down") or get_pages("Pages wired")  # 버전별 표기 차이
        compressed = get_pages("Pages occupied by compressor")

        total_pages = free + active + inactive + speculative + wired + compressed
        
        if total_pages == 0:
            return None
        
        used_pages = active + inactive + speculative + wired + compressed
        pct = round((used_pages / total_pages) * 100.0, 1)
        return max(0.0, min(100.0, pct))
    
    except Exception:
        return None

# ───────── 메인 ─────────
def main(argv: list[str]) -> None:
    mode = (argv[1] if len(argv) > 1 else "p1").lower()

    if mode == "p1":
        # 문제1 테스트: 센서 1회 생성/출력(+로그)
        ds = DummySensor()
        ds.set_env()
        snap = ds.get_env(log=True)
        for k, v in snap.items():
            unit = ENV_SPEC[k][0]
            print(f"{k}: {v} {unit}")
        print(json_dumps({"ts": now_iso(), "msg": "p1 done"}))

    elif mode == "p2":
        # 문제2 실행: 5초마다 JSON 출력, q로 종료
        mc = MissionComputer("runComputer")
        stop = Event()
        th = Thread(target=mc.get_sensor_data, kwargs={"period_sec": 5.0, "stop_event": stop}, daemon=True)
        th.start()
        print("Sensor loop running. Stop with 'q' + Enter.")
        try:
            while True:
                if sys.stdin.readline().strip().lower() == "q":
                    break
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            th.join(timeout=2)
            print("Sensor loop stopped.")

    elif mode == "p3":
        # 문제3 실행: 시스템 정보/부하 1회 출력
        mc = MissionComputer("runComputer")
        mc.get_mission_computer_info()
        mc.get_mission_computer_load()

    elif mode == "p4-threads":
        # 문제4(간단): 쓰레드 3개 동시 실행
        run_threads()

    else:
        print("Usage: python mars_mission_computer_beginner.py [p1|p2|p3|p4-threads]")

if __name__ == "__main__":
    main(sys.argv)
