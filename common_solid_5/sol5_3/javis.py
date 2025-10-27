import os
import sounddevice as sd# 마이크로부터 소리받기, 스피커로 소리 내보내기
import soundfile as sf # 녹음된 데이터를 파일로 저장하거나 읽기
from datetime import datetime
import csv
import whisper

# 녹음 설정
RECORD_SECONDS = 10  # 녹음 시간 (초)
SAMPLE_RATE = 44100  # 샘플링 레이트(1초에 몇번 잘랐는가?) sounddevice 또는 pyaudio 라이브러리의 경우 이 값을 알아야 녹음 세팅을 정확히 가능해짐.
CHANNELS = 2  # 채널 수
RECORD_DIR = 'records'

# records 폴더 없으면 생성
os.makedirs(RECORD_DIR, exist_ok=True)

def record_audio():
    print('녹음을 시작합니다...')
    recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS)
    sd.wait()  # 녹음 끝날 때까지 대기
    filename = datetime.now().strftime('%Y%m%d-%H%M%S') + '.wav'
    filepath = os.path.join(RECORD_DIR, filename)
    # soundfile 라이브러리로 파일을 저장합니다.
    sf.write(filepath, recording, SAMPLE_RATE)
    print(f'녹음이 완료되었습니다: {filepath}')
    return filepath

def speech_to_text(filepath):
    model = whisper.load_model('base')
    result = model.transcribe(filepath, language='ko')
    text = result['text']
    print('인식된 텍스트:', text)

    # 결과 CSV 저장
    csv_filename = os.path.splitext(os.path.basename(filepath))[0] + '.csv'
    csv_path = os.path.join(RECORD_DIR, csv_filename)
    # os.path.basename(filepath) -> 파일 경로에서 파일의 이름만 추출
    # os.path.splittext(filename) -> 추출 된 파일 이름에서 확장자를 분리(리턴 값은 이름, 확장자) 형태의 튜플
    with open(csv_path, mode='w', encoding='utf-8', newline='') as f:
        # 해당 경로의 인코딩형태 쓰기모드 등을 지정
        writer = csv.writer(f)
        writer.writerow(['Time', 'Text'])
        writer.writerow([datetime.now().strftime('%H:%M:%S'), text])
        # append를 사용할 경우 줄바꿈 쉼표 따옴표 등의 문자 처리에서 오류가 발생 할 수 있음.
    print(f'CSV 저장 완료: {csv_path}')

def search_keyword_in_csvs(keyword):
    print(f'\n🔍 키워드 "{keyword}" 검색 결과:\n')
    found = False
    # records 폴더 내부 파일 목록 불러오기
    for filename in os.listdir(RECORD_DIR):
        if filename.endswith('.csv'):
            # 파일 확장자명이 .csv면 처리
            path = os.path.join(RECORD_DIR, filename)
            with open(path, encoding='utf-8') as f:
                reader = csv.reader(f) # csv형식으로 읽을 수 있게 만들기
                next(reader)  # 첫 줄 Time, Text 헤더 건너뜀
                for row in reader:
                    time, text = row
                    if keyword in text:
                        print(f'📁 파일: {filename}')
                        print(f'⏰ 시간: {time}')
                        print(f'🗣️ 내용: {text}\n')
                        found = True
    if not found:
        print('⚠️ 해당 키워드가 포함된 텍스트를 찾지 못했습니다.')
    print('🔚 검색 종료')

if __name__ == '__main__':
    audio_path = record_audio()
    speech_to_text(audio_path)

    # 검색어 입력을 받습니다.
    keyword = input('\n 검색할 키워드를 입력하시오: ')
    search_keyword_in_csvs(keyword)
