```
pip install sounddevice
pip install soundfile
pip install SpeechRecognition

pip install -U openai-whisper

# macOS
brew install ffmpeg
```

# os.path
```
os.path.basename(filepath) -> 파일 경로에서 파일의 이름만 추출
os.path.splittext(filename) -> 추출 된 파일 이름에서 확장자를 분리(리턴 값은 이름, 확장자) 형태의 튜플
```

# csv
```
csv.writer(f) -> csv파일에 데이터를 한 줄씩 쓸 수 있는 객체 생성
csv 형태에 맞게 항목 사이에 자동으로 쉼표를 넣어주기 때문에 writerrow가 편함(문자열 안에 쉼표가 있을 때는 자동으로 따옴표로 감싸서 오류방지
newline='' 과 함 께 사용하면 줄바꿈 깨짐 방지 추가 append로 사용하면 줄바꿈 쉼표 따옴표 등 문자 처리에서 오류 발생 가능성 있음.
```

# whisper
```
numpy 버전이 다를 경우 Pytorch 내부의 numpy 기능과 모듈 호환이 되지 않기 때문에 다운그레이드 해야 사용 가능함.
```