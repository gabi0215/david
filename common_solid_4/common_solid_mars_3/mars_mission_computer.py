
# 실행 예)
#   python mars_mission_computer.py p1 -> 센서 1회 + 로그파일 생성
#   python mars_mission_computer.py p2 -> 5초마다 출력, 5분 유지 시 sensor_avg5m 추가
#   python mars_mission_computer.py p3 -> JSON에서 cpu_type, memory_total 확인
#   python mars_mission_computer.py p4-threads 세 메서드 동시 동작 
#   python mars_mission_computer.py p4-procs 세 프로세스 동작
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
from multiprocessing import Process, Event as MpEvent

# psutil
try:
    import psutil
except Exception:
    psutil = None

# ───────── 문제 공통: 환경 항목 스펙 ─────────
ENV_SPEC = {
    "mars_base_internal_temperature": ("°C",   (18.0, 30.0), 1),
    "mars_base_external_temperature": ("°C",   (0.0, 21.0),  1),
    "mars_base_internal_humidity":    ("%",    (50.0, 60.0), 1),
    "mars_base_external_illuminance": ("W/m²", (500.0, 715.0), 0),
    "mars_base_internal_co2":         ("%",    (0.02, 0.1), 3),
    "mars_base_internal_oxygen":      ("%",    (4.0, 7.0),   2),
}

# 저장될 폴더 설정
LOG_DIR = Path("logs")

# 자동화 주기 상수화
SENSOR_PERIOD_SEC = 5.0
INFO_PERIOD_SEC   = 20.0

# 보너스 과제
SETTINGS_PATH = Path('setting.txt')

USAGE = "Usage: python mars_mission_computer.py [p1|p2|p3|p4-threads|p4-procs]"

def load_settings() -> dict[str, set[str]]:
    """
    setting.txt를 읽어 섹션별 허용 키 집합을 만든다.
    파일이 없거나 비어 있으면 모든 키 허용(빈 집합은 '전체 허용' 의미).
    형식 예)
      sensor=mars_base_internal_temperature,mars_base_external_temperature
      info=os,os_release
      load=cpu_percent,memory_percent
    """
    allow = {'sensor': set(), 'info': set(), 'load': set()}

    try:
        if not SETTINGS_PATH.exists():
            return allow  # 전체 허용
        
        for line in SETTINGS_PATH.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            key, csv = line.split('=', 1)
            key = key.strip().lower()

            if key in allow:
                vals = {t.strip() for t in csv.split(',') if t.strip()}
                allow[key] = vals

    except Exception:
        # 설정 파싱 실패 시 안전하게 전체 허용
        return {'sensor': set(), 'info': set(), 'load': set()}
    return allow

def filter_dict(data: dict, allow: set[str]) -> dict:
    """
    allow가 비어있으면 data 그대로.
    비어있지 않으면 allow에 포함된 키만 남겨 반환.
    """
    if not allow:
        return dict(data)
    return {k: v for k, v in data.items() if k in allow}

    
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

def _get_total_memory_bytes() -> int | None:
    """총 물리 메모리 바이트(가능하면). 실패 시 None"""
    # 1) psutil 우선
    if psutil is not None:
        try:
            return int(psutil.virtual_memory().total)
        except Exception:
            pass
    # 2) macOS: sysctl
    if sys.platform == "darwin":
        import subprocess
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()
            return int(out)
        except Exception:
            return None
    # 3) Linux: /proc/meminfo
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb * 1024
        except Exception:
            return None
    # 4) Windows: ctypes
    if os.name == "nt":
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        try:
            stat = MEMORYSTATUSEX(); stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return int(stat.ullTotalPhys)
        except Exception:
            return None
    return None


# ───────── 문제 1: 더미 센서 ─────────
class DummySensor:
    """
    난수로 환경값을 만들어 보관/제공하는 더미 센서.
    """
    def __init__(self):
        # 상태(state): 최신 값 보관. 처음엔 None
        self.env_values = {k: None for k in ENV_SPEC}

    # def set_env(self) -> None:
    #     """
    #     ENV_SPEC 범위에서 난수 생성 → 상태 갱신
    #     dict형태의 key,value값을 순회하기 용이하게 items()사용.
    #     """
        
    #     # # 튜플 언패킹
    #     # for key, (_unit, (lo, hi), nd) in ENV_SPEC.items():
    #     #     val = round(random.uniform(lo, hi), nd)
    #     #     if nd == 0:
    #     #         val = int(val)
    #     #     self.env_values[key] = val

    def set_env(self) -> None:
        """
        ENV_SPEC에 정의된 범위로 난수를 만들어 self.env_values에 저장합니다.
        (튜플 언패킹 사용 안 함: 모두 인덱싱으로 풀어서 접근)
        """
        # ENV_SPEC은 dict이므로 dict를 그대로 돌면 '키'만 순회합니다.
        for key in ENV_SPEC:
            # 1) 키로부터 값(spec)을 꺼냅니다.
            spec = ENV_SPEC[key]  # spec은 ('단위', (하한, 상한), 소수자리) 모양의 튜플

            # 2) spec 튜플을 인덱스로 각각 뽑습니다. (언패킹 대신 인덱싱)
            # unit   = spec[0]      # 예: "W/m²" (이번 함수에서는 쓰지 않지만 의미상 보관)
            bounds = spec[1]      # 예: (500.0, 715.0)
            nd     = spec[2]      # 예: 0  (정수처럼 표현하고 싶을 때 0)

            # 3) 범위 튜플(bounds)에서도 인덱스로 하한/상한을 뽑습니다.
            lo = bounds[0]
            hi = bounds[1]

            # 4) random.uniform(lo, hi): [lo, hi] 사이 '실수' 난수 생성 (표준 라이브러리 random 모듈)
            val = random.uniform(lo, hi)

            # 5) round(val, nd): 소수점 nd자리까지 반올림 (내장 함수)
            val = round(val, nd)

            # 6) nd가 0이라면 정수로 저장하고 싶다는 정책 → int()로 캐스팅 (내장 함수)
            #    (출력에서만 정수처럼 보이게 하고 싶다면 이 블록을 빼세요)
            if nd == 0:
                val = int(val)

            # 7) 완성된 값을 상태 딕셔너리에 저장
            self.env_values[key] = val


    def get_env(self, *, log: bool = False) -> dict:
        """
        현재 스냅샷 반환(+옵션: 로그 1줄 기록)
        """
        snap = dict(self.env_values)
        # 만약 상위폴더(log)가 없다면 생성 있다면 에러 없이 통과
        if log:
            try:
                LOG_DIR.mkdir(parents=True, exist_ok=True)
                # 로그 레코드 저장될 때마다의 상태 기준이므로 복사본이 들어가야함.
                rec = {"ts": now_iso(), "type": "sensor", "data": snap}
                # 파일이름의 형태 지정 및 열고 append모드, 인코딩 지정  후
                # 별칭 지정 및 비ASCII문자(W/m²) 등의 한글,기호를 이스케이프 하지 않고 그대로 기록
                with (LOG_DIR / f"env_{datetime.now():%Y%m%d}.log").open("a", encoding="utf-8") as f:
                    json.dump(rec, f, ensure_ascii=False)
                    f.write("\n")
            
            except Exception as e:
                print(json_dumps({"ts": now_iso(), "type": "warn", "msg": f"log failed: {e}"}))
        return snap

# ─────────  미션 컴퓨터 ─────────
class MissionComputer:
    """
    센서 수집(주기), 시스템 정보/부하 출력.
    """
    def __init__(self, name="runComputer"):
        # 노드 식별자 문자열(runComputer)
        self.name = name
        # 실제 센서 대신 난수 값 생성하는 인스턴스
        self.sensor = DummySensor()
        # 최신 센서 스냅샷을 캐시, 초기값은 None, 값이 없는 딕셔너리 새로 만들기
        self.env_values = {k: None for k in ENV_SPEC}
        # 5분 주기
        self._avg_start = time.monotonic()
        # 항목별 합계
        self._avg_sum = {k: 0.0 for k in ENV_SPEC}
        # 샘플 개수
        self._avg_cnt = 0
        # 출력 항목 설정(없으면 전체 허용)
        self._settings = load_settings()  # {'sensor': set(), 'info': set(), 'load': set()}


    # 5초 주기 수집(JSON), q로 종료
    def get_sensor_data(self, period_sec: float = SENSOR_PERIOD_SEC, stop_event: Event | None = None) -> None:
        # 5초 주기는 위에서 상수 선언한 것으로 사용.
        # time 모듈의 단조 시계 함수(경과 시간 측정을 위해 사용)
        next_tick = time.monotonic()
        
        # 루프 시작마다 종료 신호를 확인합니다. -> Event.is_set()이 True라면 정상 종료 로그를 한 줄 찍고 종료.
        while True:
            if stop_event and stop_event.is_set():
                break # 메세지는 메인 종료부에서만 1회 출력(중복 방지)

            # ENV_SPEC범위에서 난수 생성
            self.sensor.set_env()
            # snap 변수의 복사본을 반환하고 1줄로 로깅
            snap = self.sensor.get_env(log=True)
            # 제일 최신 값을 캐시에 반영합니다.
            self.env_values.update(snap)
            
            data_sensor = filter_dict(snap, self._settings.get('sensor', set()))
            out = {"ts": now_iso(), "node": self.name, "type": "sensor", "data": data_sensor}
            print(json_dumps(out))

            # --- 5분 평균 누적/평균/리셋 ---------------------------
            # 1) 합계/개수 누적 (숫자형만)
            for k, v in snap.items():
                if isinstance(v, (int, float)):
                    self._avg_sum[k] += float(v)
            self._avg_cnt += 1

            # 2) 5분(=300초) 경과 시 평균 산출
            elapsed = time.monotonic() - self._avg_start
            if elapsed >= 300.0 and self._avg_cnt > 0:
                avg = {
                    k: round(self._avg_sum[k] / self._avg_cnt, ENV_SPEC[k][2])
                    for k in ENV_SPEC
                }

                # (선택) setting.txt 필터 적용하려면 self._settings 사용: 아래 ②에서 추가
                data_avg = avg if not hasattr(self, "_settings") else filter_dict(
                    avg, self._settings.get('sensor', set())
                )

                print(json_dumps({
                    "ts": now_iso(),
                    "node": self.name,
                    "type": "sensor_avg5m",
                    "window_sec": int(elapsed),
                    "samples": self._avg_cnt,
                    "data": data_avg,
                }))

                # 로그 저장 추가
                try:
                    LOG_DIR.mkdir(parents=True, exist_ok=True)
                    avg_rec = {
                        "ts": now_iso(),
                        "node": self.name,
                        "type": "sensor_avg5m",
                        "window_sec": int(elapsed),
                        "samples": self._avg_cnt,
                        "data": data_avg,
                    }
                    with (LOG_DIR / f"env_avg_{datetime.now():%Y%m%d}.log").open("a", encoding="utf-8") as f:
                        json.dump(avg_rec, f, ensure_ascii=False)
                        f.write(" ")
                except Exception as e:
                    print(json_dumps({"ts": now_iso(), "type": "warn", "msg": f"avg log failed: {e}"}))

                # 3) 버킷 리셋 (다음 5분)
                self._avg_start = time.monotonic()
                self._avg_sum = {k: 0.0 for k in ENV_SPEC}
                self._avg_cnt = 0
            # --------------------------------------------------------

            # 다음 실행 시각을 고정 간격으로 갱신합니다.
            next_tick += period_sec
            remaining = next_tick - time.monotonic()
            
            # 이벤트가 설정되면 즉시 효과. 아니라면 remaining변수만큼 대기
            if remaining > 0:
                if stop_event:
                    stop_event.wait(timeout=remaining)
                    if stop_event.is_set():
                        break
                else:
                    time.sleep(remaining)

    # 시스템 정보
    def get_mission_computer_info(self) -> dict:
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "cpu_type": (platform.processor() or platform.machine() or "unknown"),
            "cpu_cores": os.cpu_count(),
            "memory_total": _get_total_memory_bytes(), # bytes or None
        }

        data_info = filter_dict(info, self._settings.get('info', set()))
        out = {"ts": now_iso(), "node": self.name, "type": "info", "data": data_info}
        print(json_dumps(out))
        
        return data_info

    # 문제 3-2: 시스템 부하(간단/초급자 버전)
    def get_mission_computer_load(self) -> dict:
        # 쉬운 근사치: loadavg(1분)/코어수 → 대략 CPU 사용률(%)
        cpu_pct = None
        mem_pct = None
        # psutil이 잇다면 실시간 수치
        try:
            if psutil is not None:
                cpu_pct = float(psutil.cpu_percent(interval=0.1))
                mem_pct = float(psutil.virtual_memory().percent)
            else:
                # psutil 없을 때 hasattr 객체에 속성 이름이 있는지 불리언으로 확인 후 근사치
                if hasattr(os, "getloadavg"):
                    la1, _la5, _la15 = os.getloadavg()  # macOS/Linux
                    cores = os.cpu_count() or 1
                    cpu_pct = round(min(100.0, (la1 / cores) * 100.0), 1)
                else:
                    cpu_pct = 0.0
                # 메모리 대체: Linux /proc/meminfo, 이외 0.0
                if sys.platform.startswith("linux"):
                    try:
                        meminfo: dict[str, str] = {}
                        with open("/proc/meminfo", "r", encoding="utf-8") as f:
                            for line in f:
                                if ":" in line:
                                    k, v = line.split(":", 1)
                                    meminfo[k.strip()] = v.strip()
                        total_kb = float(meminfo.get("MemTotal", "0  kB").split()[0])
                        avail_kb = float(meminfo.get("MemAvailable", "0 kB").split()[0])
                        if total_kb > 0:
                            used_pct = (1.0 - (avail_kb / total_kb)) * 100.0
                            mem_pct = round(used_pct, 1)
                        else:
                            mem_pct = 0.0
                    except Exception:
                        mem_pct = 0.0
                else:
                    mem_pct = 0.0
        except Exception:
            cpu_pct = 0.0 if cpu_pct is None else cpu_pct
            mem_pct = 0.0 if mem_pct is None else mem_pct

        load = {"cpu_percent": cpu_pct, "memory_percent": mem_pct}
        data_load = filter_dict(load, self._settings.get('load', set()))
        out = {"ts": now_iso(), "node": self.name, "type": "load", "data": data_load}
        print(json_dumps(out))
        return data_load

def run_threads() -> None:
    """
    문제4: 쓰레드 3개(info/load 20초, sensor 5초)
    """
    RunComputer = MissionComputer("runComputer")
    stop = Event()

    def info_loop():
        period = INFO_PERIOD_SEC
        next_tick = time.monotonic()
        while not stop.is_set():
            RunComputer.get_mission_computer_info()
            next_tick += period
            remaining = next_tick - time.monotonic()
            if remaining > 0:
                # Event로 즉시 깨어날 수 있게
                stop.wait(timeout=remaining)
                if stop.is_set():
                    return
                
    def load_loop():
        period = INFO_PERIOD_SEC
        next_tick = time.monotonic()
        while not stop.is_set():
            RunComputer.get_mission_computer_load()
            next_tick += period
            remaining = next_tick - time.monotonic()
            if remaining > 0:
                # q 입력 직후, 주기를 기다리지 않고 즉시 종료
                stop.wait(timeout=remaining)
                if stop.is_set():
                    return

    def sensor_loop():
        RunComputer.get_sensor_data(period_sec=SENSOR_PERIOD_SEC, stop_event=stop)

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
        print("System stopped....")

# def _proc_target(target_name: str, stop: MpEvent) -> None:
#     mc = MissionComputer("runComputer")
#     if target_name == "info":
#         period = INFO_PERIOD_SEC
#         next_tick = time.monotonic()
#         while not stop.is_set():
#             mc.get_mission_computer_info()
#             next_tick += period
#             remain = next_tick - time.monotonic()
#             if remain > 0:
#                 if stop.wait(timeout=remain):
#                     break
#     elif target_name == "load":
#         period = INFO_PERIOD_SEC
#         next_tick = time.monotonic()
#         while not stop.is_set():
#             mc.get_mission_computer_load()
#             next_tick += period
#             remain = next_tick - time.monotonic()
#             if remain > 0:
#                 if stop.wait(timeout=remain):
#                     break
#     else:  # sensor
#         mc.get_sensor_data(period_sec=SENSOR_PERIOD_SEC, stop_event=stop)

def run_procs() -> None:
    stop = MpEvent()
    # 변수명 지정
    RunComputer1 = MissionComputer("runComputer1")
    RunComputer2 = MissionComputer("runComputer2")
    RunComputer3 = MissionComputer("runComputer3")

    procs = [
        Process(target=RunComputer1.get_mission_computer_info, daemon=True),
        Process(target=RunComputer2.get_mission_computer_load, daemon=True),
        Process(target=RunComputer3.get_sensor_data, kwargs={
            "period_sec": SENSOR_PERIOD_SEC, 
            "stop_event": stop}, 
            daemon=True),
    ]

    for p in procs:
        p.start()
    print("Processes running. Stop with 'q' + Enter.")
    try:
        while True:
            cmd = sys.stdin.readline().strip().lower()
            if cmd == "q":
                break
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        for p in procs:
            p.join(timeout=2)
        print("System stopped....")

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
        RunComputer = MissionComputer("runComputer")
        stop = Event()
        th = Thread(target=RunComputer.get_sensor_data, kwargs={
            "period_sec": SENSOR_PERIOD_SEC, 
            "stop_event": stop}, 
            daemon=True)
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
            print("System stopped....")

    elif mode == "p3":
        # 문제3 실행: 시스템 정보/부하 1회 출력
        RunComputer = MissionComputer("runComputer")
        RunComputer.get_mission_computer_info()
        RunComputer.get_mission_computer_load()

    elif mode == "p4-threads":
        # 문제4(간단): 쓰레드 3개 동시 실행
        run_threads()

    elif mode == "p4-procs":
        # 문제4(프로세스): 3개 동시 실행
        run_procs()

    else:
        print(USAGE)

if __name__ == "__main__":
    main(sys.argv)
