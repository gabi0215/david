"""
design_dome.py
- 문제1: 인화성 지수 정렬/필터 + CSV/이진 저장
- 문제2: 반구 돔 표면적/무게 계산(sphere_area) + 반복 CLI
- 문제3: NumPy로 부품 평균/필터 + CSV 저장/전치
제약: 외부 패키지는 금지(NumPy만 허용), 모든 파일처리 예외처리, 출력은 소수점 3자리
"""
import zipfile
import csv, pickle
from pathlib import Path
from math import pi
import numpy as np

# 프로젝트 루트
BASE = Path(__file__).resolve().parent

MATERIAL_DENSITY = {"glass":2.4,"aluminum":2.7,"carbon_steel":7.85} # g/cm^3
MARS_G = 0.38

OUT_DIR = (Path(__file__).parent / "result").resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 전역: 마지막 결과 저장 (과제 조건)
LAST_RESULT = {"material": None, "diameter": None, "thickness": None,
               "area_m2": None, "weight_kg": None}

# 영문 재질 -> 한글 라벨
MATERIAL_KO = {"glass": "유리", "aluminum": "알루미늄", "carbon_steel": "탄소강"}

# 데이터 부품관리 평균 값에 대한 재사용성을 위한 상수 선언입니다.
PART_STRENGTH_MAX = 50

def extract_zip(zip_path, result_dir=None):
    """zip파일 예외처리 및 압축해제 함수입니다.

    Raises:
        FileNotFoundError: _description_
        IsADirectoryError: _description_

    Returns:
        _type_: _description_
    """
    zp = Path(zip_path)
    base_result = Path(result_dir) if result_dir else Path.cwd()
    if not zp.exists(): raise FileNotFoundError(f"ZIP파일을 찾을 수 없습니다. :{zp}")
    if not zp.is_file(): raise IsADirectoryError(f"경로 확인 필요! :{zp}")

    extract_dir = base_result / "mars_base"
    extract_dir.mkdir(parents=True, exist_ok=True)

    def _skip(name: str) -> bool:
        return (name.startswith('__MACOSX/') or
                name.endswith('.DS_Store') or
                '/._' in name or
                Path(name).name.startswith('._'))
    
    with zipfile.ZipFile(zp, "r") as zf:
        names = [n for n in zf.namelist() if not _skip(n)]
        for n in names:
            zf.extract(n, extract_dir)
        print(f"-------압축해제완료-------->{extract_dir}")
        print("\n".join(names))
        print(f" 압축 해제된 파일 수: {len(names)}")

    return extract_dir

def find_file(name: str) -> Path:
    """BASE / BASE/mars_base에서 재귀 검색(case-insensitive).
    macOS 메타파일/폴더는 무시."""
    targets = [BASE, BASE / "mars_base"]
    target_lower = name.lower()

    def _skip(p: Path) -> bool:
        return (
            "__MACOSX" in p.parts
            or p.name.startswith("._")
            or p.name == ".DS_Store"
        )

    # 1) 최상위 정확 매치
    for d in targets:
        p = d / name
        if p.is_file():
            return p

    # 2) 재귀(case-insensitive) 매치
    for d in targets:
        if d.exists():
            for q in d.rglob("*"):
                if q.is_file() and not _skip(q) and q.name.lower() == target_lower:
                    return q
    # 찾을 수 없을 시
    raise FileNotFoundError(
        f"{name} not found. searched: {', '.join(str(d) for d in targets)}")

def print_csv_raw(csv_path: Path) -> None:
    """CSV 원본 그대로 출력하는 함수입니다.

    Args:
        csv_path (Path)
    """
    try:
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            print("\n ======================원본 CSV 전체 출력 ===========================")
            print(f.read().rstrip())
    except OSError as e:
        print(f"[읽기오류] {csv_path} : {e}")
    except UnicodeDecodeError:
        # BOM없으면 재시도 처리
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            print("\n ======================원본 CSV 전체 출력 ===========================")
            print(f.read().rstrip())

def print_rows_plain(rows: list[dict], title: str, limit: int | None = None) -> None:
    """dict 형태가 아닌 한줄로 출력

    Args:
        rows (list[dict]): _description_
        title (str): _description_
        limit (int | None, optional): _description_. Defaults to None.
    """
    if not rows:
        print(f"\n{title}\n(비어있음)")
        return
    header = list(rows[0].keys())
    print(f"\n{title} ===")
    print(", ".join(header))  # 헤더
    data = rows if limit is None else rows[:limit]
    def _fmt(v):
        try:
            return f"{float(v):.3f}"
        except Exception: return str(v)
    for r in data:
        line = ", ".join(_fmt(r.get(k, "")) for k in header)
        print(line)

def _to_float(x: str) -> float:
    """인화성 정렬 및 필터 + 저장

    Args:
        x (str): 실수형으로 변환

    Returns:
        변환 실패해도 멈추지않고 실행.

    except: 실패 시 'nan'으로 대체.
    """
    try:
        return float(x)
    except Exception:
        return float("nan")

def load_inventory(p: Path) -> list[dict]:
    rows = []

    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows

def convert_csv(csv_path: Path | str | None = None, out_dir: Path = OUT_DIR):
    danger_csv_path = out_dir / "Mars_Base_Inventory_danger.csv"
    bin_path = out_dir / "Mars_Base_Inventory_List.bin"
    
    try:
        if csv_path:
            src = Path(csv_path)
        else:
            try:
                src = find_file("Mars_Base_Inventory_List.csv")
            except FileNotFoundError:
                zip_path = BASE / "mars_base.zip"
                if zip_path.exists():
                    extract_zip(zip_path, BASE)
                    src = find_file("Mars_Base_Inventory_List.csv")
                else:
                    raise

        rows = load_inventory(src)
        if not rows:
            print("CSV에 데이터가 없습니다."); return [], [], []
        
        for r in rows: 
            r["Flammability"] = _to_float(r.get("Flammability",""))
        rows.sort(
            key=lambda r: (r["Flammability"] if isinstance(r["Flammability"], float) else -1),
            reverse=True)
        
        danger = [r for r in rows if isinstance(r["Flammability"], float) and r["Flammability"]>=0.7]
        
        # 저장 (CSV) - 소수점 3자리 고정
        with open(danger_csv_path, "w", encoding="utf-8-sig", newline="") as f:
            fieldnames = list(rows[0].keys())
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in danger:
                r_out = dict(r)
                # 오탈자 수정 + 숫자일 때만 포맷팅
                if isinstance(r_out.get("Flammability"), float):
                    r_out["Flammability"] = f"{r_out['Flammability']:.3f}"
                w.writerow(r_out)

        # 보너스: 이진 저장/복구
        with open(bin_path, "wb") as f: pickle.dump(rows, f)
        with open(bin_path, "rb") as f: restored = pickle.load(f)
        print(f"\n위험 {len(danger)}건 저장 -> {danger_csv_path.name} / 정렬본BIN -> {bin_path.name}")
        return rows, danger, restored
    
    except FileNotFoundError:
        print("CSV 파일을 찾을 수 없습니다."); return [], [], []
    except Exception as e:
        print(f"오류: {e}"); return [], [], []

def sphere_area(diameter_m: float, material: str, thickness_cm: float=1.0) -> tuple[float,float]:
    """반구 곡면적[m^2], 화성 중력 반영 무게[kg]"""
    
    if diameter_m<=0 or thickness_cm<=0:
        raise ValueError("지름/두께는 0보다 커야 합니다.")
    
    mkey = material.strip().lower()
    if mkey not in MATERIAL_DENSITY:
        raise ValueError("material은 glass/aluminum/carbon_steel 중 하나")
    
    r = diameter_m/2.0
    curved_area_m2 = 2*pi*(r**2)
    vol_cm3 = (curved_area_m2*1e4) * thickness_cm
    mass_kg = vol_cm3*MATERIAL_DENSITY[mkey]/1000.0
    weight_mars = mass_kg*MARS_G
    
    return round(curved_area_m2,3), round(weight_mars,3)

def _pretty_int_or_3(x: float) -> str:
    """정수면 '10', 아니면 '10.500'처럼 3자리 고정"""
    return str(int(x)) if float(x).is_integer() else f"{x:.3f}"

def mars_structure_program():
    print("Mars 돔 설계 계산기 (반구 곡면=2πr², 종료: q)")
    while True:
        s = input("지름(m)을 입력하세요 (종료:q): ").strip()
        if s.lower() in {"q", "quit", "exit"}:
            break
        try:
            d = float(s)
            if d <= 0:
                raise ValueError("지름은 0보다 커야 합니다.")

            m = input("재질(glass/aluminum/carbon_steel): ").strip().lower()
            if m not in MATERIAL_DENSITY:
                raise ValueError("재질은 glass/aluminum/carbon_steel 중 하나여야 합니다.")

            t_in = input("두께(cm, 기본 1): ").strip()
            t = 1.0 if not t_in else float(t_in)
            if t <= 0:
                raise ValueError("두께는 0보다 커야 합니다.")

            # 반구 곡면
            area_m2, weight_kg = sphere_area(d, m, t)  # 이미 2πr²/0.38 반영 함수

            # 전역 저장 (과제 조건)
            LAST_RESULT.update({
                "material": m, "diameter": d, "thickness": t,
                "area_m2": area_m2, "weight_kg": weight_kg
            })

            # 예시 형식에 맞춘 출력(⇒, 면적/무게 3자리, 지름/두께는 정수면 정수)
            print(f"재질 ⇒ {MATERIAL_KO[m]}, "
                  f"지름 ⇒ {_pretty_int_or_3(d)}, "
                  f"두께 ⇒ {_pretty_int_or_3(t)}, "
                  f"면적 ⇒ {area_m2:.3f}, "
                  f"화성 유효중량 ⇒ {weight_kg:.3f} kg")
        except Exception as e:
            print(f"입력 오류: {e}")

def _parts_to_dict(p: Path) -> dict[str,float]:
    out = {}
    with open(p,"r",encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            name = str(row.get("parts", "")).strip()
            if not name:
                continue
            try:
                value = float(row.get("strength", ""))
            except (TypeError, ValueError):
                value = float("nan")
            out[name] = value
    return out

def analysis_parts():
    p1 = find_file("mars_base_main_parts-001.csv")
    p2 = find_file("mars_base_main_parts-002.csv")
    p3 = find_file("mars_base_main_parts-003.csv")
    
    try:
        arr1,arr2,arr3 = _parts_to_dict(p1),_parts_to_dict(p2),_parts_to_dict(p3)
        names = sorted(set(arr1)|set(arr2)|set(arr3))
        mat = np.vstack([
            np.array([arr1.get(k, np.nan) for k in names], float),
            np.array([arr2.get(k, np.nan) for k in names], float),
            np.array([arr3.get(k, np.nan) for k in names], float),
        ])
        # errstate -> np에서 경고 or 에러 임시 제어 도구
        with np.errstate(all='ignore'):
            avg = np.nanmean(mat, axis=0)
        mask = np.isfinite(avg) & (avg < PART_STRENGTH_MAX)
        
        out_csv = OUT_DIR / "parts_to_work_on.csv"
        try:
            with open(out_csv,"w",encoding="utf-8-sig",newline="") as f:
                w = csv.writer(f); w.writerow(["parts","avg_strength"])
                for name,val in zip(np.array(names)[mask], avg[mask]):
                    w.writerow([name, f"{float(val):.3f}"])
        except OSError as e:
            print(f"[저장 오류] {out_csv}: {e}")
            return

        # 보너스: transpose
        parts2_csv = OUT_DIR / "parts2.csv"
        parts2=[]
        try:
            with open(out_csv, "r", encoding="utf-8-sig", newline="") as f:
                rd = csv.reader(f); next(rd,None)
                for row in rd: parts2.append(row)
            with open(parts2_csv, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(["parts", "avg_strength"])
                w.writerows(parts2)
        except OSError as e:
            print(f"[저장 오류] {parts2_csv}: {e}")
            return
        
        # 전치 행렬 구한 뒤 parts3 저장 및 출력
        parts3 = np.array(parts2, dtype=object).T
        out_csv3 = OUT_DIR / "parts3.csv"
        try:
            with open(out_csv3, "w", encoding="utf-8-sig", newline="") as f:
                w=csv.writer(f)
                for row in parts3: w.writerow(row)
        except OSError as e:
            print(f"[저장 오류] {out_csv3}: {e}")
            return

        # 결과값 출려하기
        print(f"\n================ parts3 전치 행렬 ================")
        for row in parts3:
            print(", ".join(map(str, row)))

        print(f"\n저장 완료 -> {out_csv.name}, {parts2_csv.name}, {out_csv3.name}")
    except FileNotFoundError:
        print(" CSV 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f" 오류: {e}")

if __name__ == "__main__":
    # 1) 파일 찾기(없으면 zip 해제 후 재시도)
    try:
        src = find_file("Mars_Base_Inventory_List.csv")
    except FileNotFoundError:
        zip_path = BASE / "mars_base.zip"
        if zip_path.exists():
            extract_zip(zip_path, BASE)
            src = find_file("Mars_Base_Inventory_List.csv")
        else:
            print("CSV 파일을 찾을 수 없습니다.")
            src = None

    # 2) 원본 그대로 출력 + 정렬/필터/저장/복구
    if src:
        print_csv_raw(src)
        rows, danger, restored = convert_csv(src, out_dir=OUT_DIR)

        # 3) dict 모양 없이 '행 단위'로 깔끔 출력(숫자 3자리)
        print_rows_plain(rows, "==========정렬된 전체 목록(내림차순)============")
        print_rows_plain(danger, "==============위험(Flammability ≥ 0.7) 목록===============")
        print_rows_plain(restored, "=============BIN 복구 확인(상위 20행)=================", limit=20)

    # 필요 시 호출
    analysis_parts()

    try:
        print("\n[Mars 반구체 돔 계산기 실행!] 종료하려면 q를 입력하세요.]")
        mars_structure_program()
    except KeyboardInterrupt:
        print("\n사용자 중단으로 종료합니다.")