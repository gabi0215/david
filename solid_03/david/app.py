from flask import Flask, request, Response # Response를 통해 브라우저에 오디어 데이터를 직접 전달 가능
import os # os.getenv 환경변수 설정
from io import BytesIO
from gtts import gTTS

# 환경변수로부터 기본 언어 설정
DEFAULT_LANG = os.getenv('DEFAULT_LANG', 'ko')
app = Flask(__name__)

# "/" 경로에 GET 요청이 오면 실행되고 request.args.get 통해 쿼리 파라미터 언어를 받아옵니다.
@app.route("/")
def home():

    text = "Hello, DevOps"

    lang = request.args.get('lang', DEFAULT_LANG)
    fp = BytesIO()
    gTTS(text, "com", lang).write_to_fp(fp)
    # gTTS로 텍스트를 음성변환 후 메모리 버퍼에 저장
    # 페이지 전달없이 바로 재생
    return Response(fp.getvalue(), mimetype='audio/mpeg') 

if __name__ == '__main__':
    app.run('0.0.0.0', 8080)