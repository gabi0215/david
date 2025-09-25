# log 파일의 전체 내역을 출력
# 로그 파일(mission_computer_main.log) 읽기
# 전체 내용을 출력
# 필요한 필터링 및 시간순 정렬
# JSON 저장 (mission_computer_main.json)

# 구현에 필요한 라이브러리를 호출합니다.
import csv
import os
from datetime import datetime
# from dotenv import load_dotenv
import json
from pathlib import path

# .env 파일 로드
load_dotenv()

# 환경 변수에서 경로 불러오기
FILEPATH = os.getenv("LOG_FILE")
RESULT = os.getenv("RESULT")

def require_env():
    '''
    이 함수는 env내부에 값이 없을 경우를 대비한 함수입니다.
    '''
    empty = []
    if not FILEPATH:
        empty.append("LOG_FILE")
    if not RESULT:
        empty.append("RESULT")
    if empty:
        raise RuntimeError(f".env에 {', '.join(empty)} 변수가 없습니다.")

def read_log_file(FILEPATH):
    '''
    1. log file read + 예외 처리
    csv.DictReader ,을 기준으로 자동인식 후 parsing
    '''
    logs = []
    try:
        with open(FILEPATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
            return logs
    except FileNotFoundError:
        print(f"log파일을 찾을 수 없습니다.: {FILEPATH}")
    except UnicodeDecodeError:
        print("디코딩 오류 에러 발생! UTF-8 인코딩 확인해주세요")
    return []

def sort_log_datetime(logs):
    '''
    timestamp 필드 기준으로 시간 역순 정렬을 위한 함수입니다.
    '''
    try:
        return sorted(
            logs,
            key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
    except Exception as e:
        print("정렬 도중 오류 발생:", e)
        return logs

def convert_list_to_dict(logs):
    return {i: log for i, log in enumerate(logs)}

def save_to_json(data):
    '''
    결과물을 현재 시간을 기준으로 저장하는 함수입니다.
    '''
    # 현재 시간을 기반 파일 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 확장자 분리
    base, ext = os.path.splitext(RESULT)

    # 새로운 파일명 조합
    new_filename = f"{base}_{timestamp}{ext}"
    
    # 폴더가 없다면 자동생성
    os.makedirs(os.path.dirname(new_filename), exist_ok=True)
    
    # 저장
    with open(new_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"JSON 저장 완료 -> {new_filename}")

if __name__ == "__main__":
    logs = read_log_file(FILEPATH)

    print("\n① 로그 전체 출력:")
    for log in logs:
        print(log)

    if logs:
        print("\n② 시간 기준 역순 정렬된 로그 출력문입니다.")
        sorted_logs = sort_log_datetime(logs)
        for log in sorted_logs:
            print(log)

        print("\n③ 리스트를 딕셔너리로 변환한 결과:")
        log_dict = convert_list_to_dict(sorted_logs)
        for k, v in log_dict.items():
            print(f"{k}: {v}")

        print("\n④ JSON으로 저장:")
        save_to_json(log_dict)

    else:
        print("⚠️ 로그 데이터가 없어서 이후 작업을 건너뜁니다.")
