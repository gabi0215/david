"""mission_computer_main.log 분석 스크립트

기능:
  ① 로그 파일 원본을 출력
  ② timestamp 기준 역순 정렬하여 출력
  ③ 리스트를 딕셔너리로 변환하여 출력
  ④ JSON 파일로 저장 (동명이면 덮어쓰지 않도록 타임스탬프를 붙여 저장)

제약사항:
  - Python 3.x, PEP 8 일부 준수, 함수별 독스트링 포함
  - UTF-8 / UTF-8-SIG 인코딩 지원
  - CSV 구분자 자동 추정(csv.Sniffer), 실패 시 엑셀 기본 Dialect
"""

# 구현에 필요한 라이브러리를 호출합니다.
import csv
import re
import json
from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from sys import argv

# 위험 키워드 정의
RISK_KEYWORDS = ("폭발", "누출", "고온", "Oxygen")

# import os
# LOG_ENV = "LOG_FILE"
# RESULT_ENV = "RESULT"

# def require_env() -> tuple[Path, Path]:
#     '''이 함수는 환경 변수의 유효성을 검사하고 경로를 반환합니다.
#     '''
#     log_file = os.getenv(LOG_ENV)
#     result_file = os.getenv(RESULT_ENV)

#     missing = [name for name, val in [(LOG_ENV, log_file), (RESULT_ENV, result_file)] if not val]
#     if missing:
#         # 환경 변수 없으면 강제 오류
#         raise RuntimeError(f".env에 {', '.join(missing)} 변수가 없습니다.")
    
#     return Path(log_file), Path(result_file)

def require_env() -> tuple[Path, Path]:
    '''(.env 미사용) CLI 인자 또는 기본값으로 경로 반환
    사용법: python main.py [로그파일경로] [결과경로(디렉터리 또는 .json)]
    '''
    base = Path.cwd()
    log = Path(argv[1]) if len(argv) > 1 else base / "mission_computer_main.log"
    out = Path(argv[2]) if len(argv) > 2 else base / "result"

    # 홈(~) 확장 + 절대경로 정규화 (협업/클론 환경에서도 안전)
    log = log.expanduser().resolve()
    out = out.expanduser().resolve()
    return log, out

def read_log_file(path: Path) -> list[dict[str, Any]]:
    '''
    Args:
    구현 기능
    - log file read 리스트 형태로 반환
    - 인코딩은 utf-8 -> 실패하면 utf-8-sig로 재시도 구현
    - csv.Sniffer 사용. 구분자 자동 추정(, ; | TAB)
    - 모든 문자열 k/v 값에 대해 공백제거 -> .strip()
    - csv.DictReader:  콤마를 기준 가정, Sniffer로 구분자 추정
    
    - path : CSV 파일 경로
    '''
    # 1. 파일 존재 검증 후 없다면 예외 발생
    # 2. main에서 사용자의 직관적인 메세지 처리.
    if not path.exists():
        raise FileNotFoundError(f"로그 파일을 찾을 수 없습니다.: {path}")
    
    # 인코딩 시도
    for enc in ("utf-8","utf-8-sig"):
        try:
            with path.open('r', encoding=enc, newline="") as f:
                # 구분자 추정(,/;/tab/파이프)
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
                except csv.Error:
                    # 추정 실패 시 콤마 기본
                    dialect = csv.get_dialect('excel') # 실패 시 기본값 세팅

                reader = csv.DictReader(f, dialect=dialect)
                rows: list[dict[str, Any]] = []
                for i, row in enumerate(reader, start=1):
                    # 키/값 str이면 좌우 공백 제거
                    clean = {
                        (k.strip() if isinstance(k, str) else k):
                        (v.strip() if isinstance(v, str) else v)
                        for k, v in row.items()
                    }
                    clean["orig_idx"] = i   # ← 원본 CSV의 1-based 행 번호
                    rows.append(clean)
                return rows
        except UnicodeDecodeError:
            continue

    # 모든 인코딩 시도 실패.
    raise UnicodeDecodeError("utf-8/utf-8-sig", b"", 0, 1, "지원 인코딩으로 디코딩 실패")

def sort_log_datetime(logs):
    '''
    Args:
    - timestamp 필드 기준으로 시간 역순 정렬을 위한 함수입니다.
    - (YYYY-MM-DD HH:MM:SS) 기준 역순 정렬
    '''
    def key(row: dict[str, Any]):
        ts = parse_ts_safe(row.get("timestamp"))
        return ts or datetime.min   # 파싱 실패 시 안전하게 최소값
    try:
        return sorted(logs, key=key, reverse=True)
    except Exception:
        return logs

def convert_list_to_dict(logs: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    '''
    Args:
    리스트를 {인덱스: 행} 딕셔너리로 변환
    인덱스 시작 1,지정없으면 0부터 시작함.
    '''
    return {i: log for i, log in enumerate(logs, start=1)}

def save_to_json(data: dict[int, dict[str, Any]] | list[dict[str, Any]], result_path: Path, *, default_stem: str = "mission_computer_main",) -> Path:
    '''
    - JSON 저장(폴더 자동 생성 및 예외 처리 포함)
    - 결과물을 timestamp 기준으로 덮어쓰기 방지하는 함수입니다.
    - 상위 폴더 없으면 자동생성
    - 파일 생성 중 오류 발생하면 메세지 출력 및 예외
    '''
    # 현재 시간을 기반 파일 생성
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = Path(result_path)
    # 확장자가 json이라면 파일로 간주, 아니면 폴더로 간주
    if p.suffix.lower() == ".json":
        base = p.with_suffix(".json")
        base.parent.mkdir(parents=True, exist_ok=True)
        out = base.with_name(f"{base.stem}_{ts}{base.suffix}")

    else:
        p.mkdir(parents=True, exist_ok=True)
        out = p / f"{default_stem}_{ts}.json"
    try:
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        raise OSError(f"결과물 저장 실패: {out} (사유: {e})") from e
    return out

# 사고 분석 보고서
def parse_ts_safe(s: Any) -> datetime | None:
    '''
    문자열을 datatime으로 안전 파싱(형식 다르면 None).
    '''
    if isinstance(s, str):
        try:
            return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return None

def md_escape(text: str) -> str:
    '''
    Markdown 충돌 방지를 위한 간단 이스케이프
    '''
    return text.replace("|", "\|").replace("*", "\*").replace("_", "\_")


def generate_markdown_report(logs: list[dict[str, Any]], out_path: Path = Path("log_analysis.md")) -> Path:
    '''Args:
    log data를 요약 정리하여 log_analysis.md(UTF-8)로 저장합니다.
    '''

    # 타임 레인지
    total = len(logs)
    times: list[datetime] = []
    for row in logs:
        ts = parse_ts_safe(row.get("timestamp"))
        if ts:
            times.append(ts)
    start = min(times).strftime("%Y-%m-%d %H:%M:%S") if times else "N/A"
    end = max(times).strftime("%Y-%m-%d %H:%M:%S") if times else "N/A"

    # 레벨 분포
    level_counts: Counter[str] = Counter()
    for row in logs:
        level = row.get("level") or row.get("event")
        if isinstance(level, str) and level:
            level_counts[level] += 1

    # 위험 키워드 카운트(본문 전체 스캔, 대소문자 무시)
    risk_counter: Counter[str] = Counter()
    joined_fields: list[str] = []
    for row in logs:
        parts = [str(v) for v in row.values() if isinstance(v, (str, int, float))]
        blob = " ".join(parts)
        joined_fields.append(blob)
        lower = blob.lower()
        for kw in RISK_KEYWORDS:
            if kw.lower() in lower:
                risk_counter[kw] += 1
    
    # 최근 건수 설정 가능(샘플로 5개 지정)
    recent = sort_log_datetime(logs)[:5]

    # 간단 가설: 위험 키워드가 다수/연쇄 나오면 패턴 나열
    hypotheses: list[str] = []
    if sum(risk_counter.values()) > 0:
        seq = [kw for blob in joined_fields for kw in RISK_KEYWORDS if kw.lower() in blob.lower()]
        if seq:
            hypotheses.append(f"- 위험 키워드 등장 순서(일부): {', '.join(seq[:10])} ...")
    else:
        hypotheses.append(f"- 위험 키워드 흔적이 없습니다. 설비/센서 이상 또는 로그 누락 가능성을 검토해야합니다.")

    # Markdown 본문 구성
    lines = []
    lines.append("# 사고 원인 분석 보고서(자동생성)")
    lines.append("")
    lines.append(f"- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 로그 총 개수: **{total}**")
    lines.append(f"- 관찰 구간: **{start} ~ {end}**")
    lines.append("")
    lines.append("## 1) 로그 수준(Level) 분포")
    if level_counts:
        for lvl, cnt in level_counts.most_common():
            lines.append(f"- {md_escape(lvl)}: {cnt}")
    else:
        lines.append("- 레벨 정보가 없습니다.")
    lines.append("")
    lines.append("## 2) 위험 키워드 감지")
    if risk_counter:
        for kw, cnt in risk_counter.most_common():
            lines.append(f"- {kw}: {cnt}")
    else:
        lines.append("- 감지된 위험 키워드 없음")
    lines.append("")
    lines.append("## 3) 최근 이벤트 샘플(최대 5건, 역순)")
    if recent:
        for row in recent:
            ts = row.get("timestamp", "N/A")
            lvl = row.get("level", "N/A")
            msg = row.get("message", "")
            msg = md_escape(str(msg))[:200]
            lines.append(f"- [{ts}] ({lvl}) {msg}")
    else:
        lines.append("- 샘플을 표시할 수 없습니다.")
    lines.append("")
    lines.append("## 4) 원인 가설(데이터 기반 단서)")
    lines.extend(hypotheses or ["- 제시할 단서가 부족합니다."])
    lines.append("")
    lines.append("### 5) 데이터 품질 메모")
    lines.append("- 'timestamp' 포맷 불일치/누락 시 정렬 정확도 저하 발생.")
    lines.append("- 레벨/메세지 스키마가 표준화되어 있지 않으면 신뢰도가 떨어질 수 있습니다.")
    lines.append("")

    out_path.write_text("\n".join(map(str,lines)), encoding="utf-8")
    return out_path

def filter_risk_logs(logs: list[dict[str, Any]], result_dir: Path) -> Path:
    '''
    위험 키워드가 포함된 행만 필터링 후 JSON 형식으로 저장합니다.
    '''
    result_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile("|".join(re.escape(k) for k in RISK_KEYWORDS), re.IGNORECASE)
    filtered: list[dict[str, Any]] = []
    for row in logs:
        if any(isinstance(v, str) and pattern.search(v) for v in row.values()):
            filtered.append(row)

    out = result_dir / f"risk_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    return out

def search_json(json_path: Path, query: str) -> list[dict[str, Any]]:
    '''
    생성된 json 형식에서 부분 문자열을 검색합니다.
    '''
    if not json_path.exists():
        print(f"[경고!] JSON 파일이 존재하지 않습니다.: {json_path}")
        return []
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows: Iterable[dict[str, Any]]
    if isinstance(data, dict):
        rows = list(data.values())
    elif isinstance(data, list):
        rows = data
    else:
        print("[주의!] JSON 구조를 해석할 수 없습니다(리스트/딕셔너리만 지원가능).")
        return []
    
    q = query.lower()
    hits: list[dict[str, Any]] = []
    for row in rows:
        if any(isinstance(v, str) and q in v.lower() for v in row.values()):
            hits.append(row)
    return hits
                        

def main() -> None:
    log_path, result_path = require_env()
    print("log 원본 출력: ")
    try:
        logs = read_log_file(log_path)
    except FileNotFoundError as e:
        # 파일 없을 때 처리
        print(f"[입력 오류] {e}")
        return
    except UnicodeDecodeError as e:
        print(f"[인코딩 오류] 디코딩 실패: {e}")
        return
    except Exception as e:
        print(f"[알 수 없는 오류] 로그 읽기 실패: {e}")
        return
    
    if not logs:
        print("log data가 비어 있어 이후 작업을 생략합니다.")
        return
    
    for row in logs:
        print(row)

    # 정렬 후 출력
    print("\n 시간 기준 역순 정렬 로그 출력문!")
    sorted_logs = sort_log_datetime(logs)
    for row in sorted_logs:
        print(row)

    # 리스트 -> 딕셔너리 변환 출력
    print("\n 리스트를 딕셔너리로 변환한 결과: ")
    log_dict = convert_list_to_dict(sorted_logs)
    for k, v in log_dict.items():
        print(f"{k}: {v}")

    print("\n④ JSON으로 저장:")
    out_json = save_to_json(log_dict, result_path, default_stem=Path(log_path).stem)
    print(f"저장 완료: {out_json}")

    print("\n⑤ 사고 분석 보고서(log_analysis.md) 생성:")
    md_path = generate_markdown_report(sorted_logs, Path("log_analysis.md"))
    print(f"보고서 저장 완료: {md_path}")

    print("\n⑥ 위험 키워드 필터 결과 저장:")
    risk_out = filter_risk_logs(sorted_logs, Path(out_json).parent)
    print(f"필터 결과 저장: {risk_out}")

    print("\n⑦ JSON 검색: 검색할 문자열을 입력하세요(엔터=건너뜀)")
    try:
        query = input("> ").strip()
    except EOFError:
        query = ""
    if query:
        hits = search_json(Path(out_json), query)
        print(f"검색 결과: {len(hits)}건")
        for h in hits[:35]:
            print(h)
    else:
        print("검색을 건너뜁니다.")

if __name__ == "__main__":
    main()

