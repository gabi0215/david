from flask import Flask, request, render_template
import os # 파일 경로 생성, 파일 존재 여부 확인
from io import BytesIO # io.ByesIO()사용 시 gTTs 의 오디오 데이터를 파일로 저장하지 않고 사용가능.
from gtts import gTTS
import base64 # 바이너리 데이터를 텍스트로 변환(image,오디오 등 HTML에 직접 삽입 시 사용)
import io
import datetime
import traceback

app = Flask(__name__)

# 유효한 언어 목록(변수명은 PEP8가이드)
VALID_LANGS = {'ko', 'en', 'ja', 'es'}

@app.route("/", methods=["GET", "POST"])

def index():
    # 사용자 요청 전에 아무것도 없는 초기값을 설정합니다.
    # base64로 인코딩된 음성데이터를 담습니다.
    audio_data = None
    # 입력이 없거나 오류 발생 시 보여줄 에러메세지를 저장합니다.
    error = None
    filename = None
    # 요청 방식이 POST인지 확인하는 조건문입니다.
    if request.method == "POST":
        input_text = request.form.get("input_text", "").strip()
        lang = request.form.get("lang", "ko")

        # 입력 검증 보너스 구현부분
        if not input_text:
            error = "텍스트를 입력해주세요!!"
        elif lang not in VALID_LANGS:
            error = f"지원하지 않는 언어입니다: {lang}"
        else:
            try:
                tts = gTTS(text=input_text, lang=lang)
                # 메모리 상에서 사용할수 있는 이진 파일 객체 생성
                fp = io.BytesIO()
                # fp 라는 메모리 파일에 mp3 형식으로 음성데이터 저장.
                tts.write_to_fp(fp)
                # 초기 세팅
                fp.seek(0)

                # base64 인코딩
                audio_data = base64.b64encode(fp.read()).decode("utf-8")

                # mp3 저장
                # os.path.join()를 사용하면 운영체제에 맞는 구분자를 자동으로 처리해줍니다.
                filename = f"tts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                with open(os.path.join("static", filename), "wb") as f:
                    fp.seek(0)
                    f.write(fp.read())

                # 로그 저장
                # 쓰기 모드로 txt파일을 열고 append 모드로 이어서 쓰고 멀티바이트 문자가 깨지지않게 인코딩 설정을 합니다.
                with open("input_log.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(f"{datetime.datetime.now()} - 입력: {input_text} / 언어: {lang}\n")

            except Exception as e:
                traceback.print_exc()
                error = f"TTS 변환 실패: {str(e)}"

    return render_template("index.html", audio = audio_data, error = error, filename = filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
