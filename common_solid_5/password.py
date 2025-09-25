"""
door_hacking.py
- 문제 1: ZIP 암호 풀기 (brute force + 멀티프로세스 보너스)
- 문제 2: 카이사르 암호 해독 (brute force + 사전 기반 자동 중단 보너스)
제약: zipfile 외의 외부 라이브러리 사용 불가
"""

import zipfile
import string
import itertools
import time
from pathlib import Path
from multiprocessing import Pool, cpu_count


# ───────── 문제 1: ZIP 암호 풀기 ─────────
def _try_password(args):
    """병렬 탐색용 내부 함수"""
    zip_path, pwd = args
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(path="unlocked", pwd=pwd.encode("utf-8"))
        return pwd
    except Exception:
        return None


def unlock_zip(zip_path: str, out_dir: str = ".", use_parallel: bool = False) -> None:
    """ZIP 파일 암호를 brute force로 푸는 함수"""
    charset = string.digits + string.ascii_lowercase
    start_time = time.time()
    password_file = Path("password.txt")

    if use_parallel:
        print("[INFO] 멀티프로세스로 암호 탐색 시작")
        pool = Pool(processes=cpu_count())
        tasks = (("emergency_storage_key.zip", "".join(p))
                 for p in itertools.product(charset, repeat=6))
        for attempt, result in enumerate(pool.imap_unordered(_try_password, tasks), 1):
            if result:
                elapsed = time.time() - start_time
                print(f"[SUCCESS] 암호 발견: {result}")
                print(f"총 시도 횟수: {attempt}, 소요 시간: {elapsed:.2f}초")
                with open(password_file, "w", encoding="utf-8") as f:
                    f.write(result)
                pool.terminate()
                return
            if attempt % 50000 == 0:
                elapsed = time.time() - start_time
                print(f"[TRY] {attempt}회 시도, 진행시간 {elapsed:.2f}초")
        pool.close()
        pool.join()
    else:
        attempt = 0
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for pwd_tuple in itertools.product(charset, repeat=6):
                    attempt += 1
                    pwd = "".join(pwd_tuple)
                    try:
                        zf.extractall(path=out_dir, pwd=pwd.encode("utf-8"))
                        elapsed = time.time() - start_time
                        print(f"[SUCCESS] 암호 발견: {pwd}")
                        print(f"총 시도 횟수: {attempt}, 소요 시간: {elapsed:.2f}초")
                        with open(password_file, "w", encoding="utf-8") as f:
                            f.write(pwd)
                        return
                    except Exception:
                        if attempt % 100000 == 0:
                            elapsed = time.time() - start_time
                            print(f"[TRY] {attempt}회 시도, 진행시간 {elapsed:.2f}초")
            print("암호를 찾지 못했습니다.")
        except FileNotFoundError:
            print(f"[ERROR] ZIP 파일을 찾을 수 없음: {zip_path}")
        except zipfile.BadZipFile:
            print(f"[ERROR] 올바른 ZIP 파일이 아님: {zip_path}")


# ───────── 문제 2: 카이사르 암호 해독 ─────────
def caesar_cipher_decode(target_text: str, dictionary: list[str] | None = None) -> None:
    """카이사르 암호 해독: 0~25 자리수 이동, 사전 기반 자동 멈춤 지원"""
    alphabet = string.ascii_lowercase
    result_file = Path("result.txt")

    for shift in range(26):
        decoded = []
        for ch in target_text:
            if ch.islower():
                idx = (alphabet.index(ch) - shift) % 26
                decoded.append(alphabet[idx])
            elif ch.isupper():
                idx = (alphabet.index(ch.lower()) - shift) % 26
                decoded.append(alphabet[idx].upper())
            else:
                decoded.append(ch)
        line = "".join(decoded)
        print(f"[{shift:02}] {line}")

        # 보너스: 사전 단어 매칭 → 자동 중단
        if dictionary:
            for word in dictionary:
                if word.lower() in line.lower():
                    print(f"[AUTO-DECODE] 사전 단어 '{word}' 발견 → shift={shift}")
                    with open(result_file, "w", encoding="utf-8") as f:
                        f.write(line)
                    return

    # 사용자 수동 선택
    try:
        num = int(input("정답으로 보이는 shift 번호를 입력하세요: ").strip())
        if 0 <= num < 26:
            decoded = []
            for ch in target_text:
                if ch.islower():
                    idx = (alphabet.index(ch) - num) % 26
                    decoded.append(alphabet[idx])
                elif ch.isupper():
                    idx = (alphabet.index(ch.lower()) - num) % 26
                    decoded.append(alphabet[idx].upper())
                else:
                    decoded.append(ch)
            final_text = "".join(decoded)
            with open(result_file, "w", encoding="utf-8") as f:
                f.write(final_text)
            print(f"[RESULT] result.txt 파일에 저장 완료")
        else:
            print("잘못된 번호 입력")
    except Exception:
        print("입력 오류 발생")


# ───────── 실행 예시 ─────────
if __name__ == "__main__":
    print("=== 문제 1: ZIP 암호 풀기 ===")
    unlock_zip("emergency_storage_key.zip", out_dir="unlocked", use_parallel=True)

    print("\n=== 문제 2: 카이사르 암호 해독 ===")
    try:
        with open("password.txt", "r", encoding="utf-8") as f:
            cipher_text = f.read().strip()
            # 간단한 사전 예시
            dict_words = ["secret", "mars", "key", "password"]
            caesar_cipher_decode(cipher_text, dictionary=dict_words)
    except FileNotFoundError:
        print("[ERROR] password.txt 파일을 찾을 수 없습니다.")
