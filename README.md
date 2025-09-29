# ai-codyssey
- Github과 Codyssey를 연동하기 위해 만들어진 Repository입니다.
- 혁신과정을 위한 david 저장소로 새롭게 만들어 진행합니다.

## 🐍 Python 가상환경 세팅 및 실행 안내
이 저장소는 Python 기반으로 동작합니다.아래의 과정을 통해 개발 환경을 세팅하고 스크립트를 실행할 수 있습니다.

###
✅ 1. Python 버전 확인

python3 --version

권장 버전: Python 3.8 이상

pyenv --version

###
✅ 2. 가상환경 생성 (처음 한 번만)

pyenv virtual 3.11.8 가상환경이름

python 버전을 설정하여 가상환경을 세팅합니다.

###
✅ 3. 가상환경 활성화

▸ macOS / Linux

pyenv activate 가상환경이름

가상환경이름\사용자명 % 

프론트에 (가상환경이름)처럼 표시되면 가상환경 활성화 완료!

###
✅ 4. 패키지 설치

pip install -r requirements.txt

프로젝트 실행에 필요한 모든 패키지가 자동 설치됩니다.

###
✅ 5. 스크립트 실행 예시

python solid_01/python_test.py

실행하고자 하는 파일 경로에 맞게 수정해서 실행하세요.

# 🚩 가상환경 종료 (선택)
```
pyenv deactivate 가상환경이름
ㄴ
📦 requirements.txt 생성 방법 (개발자용)

새로 패키지를 설치했다면 다음 명령으로 requirements.txt를 업데이트 해주세요.

pip freeze > requirements.txt
```
###
# 🚫 .gitignore 설정 권장
```
가상환경 폴더는 Git에 업로드하지 않도록 .gitignore 파일에 다음 내용을 추가하세요:

가상환경이름/
__pycache__/
```
# 📙 참고
```
requirements.txt 파일은 Python 환경 설정을 공유하기 위한 하드웨어 파일입니다.

협업 시 환경 불일치를 방지하기 위해 필요합니다.

가상환경을 코드와 함께 관리하면 재설정이 필요 없는 효율적인 개발이 가능합니다.

# 🍽️ 메뉴 화면 추가 프로젝트 (GitHub 협업 과제)

이 프로젝트는 GitHub 협업 실습의 일환으로, 웹 페이지에 메뉴 화면을 추가하고 GitHub의 이슈, 브랜치, PR(Pull Request) 관리 기능을 실습하는 데 목적이 있습니다.
```
## 📁 프로젝트 구조
```
common_solid_01/    
├── app.py # Flask 애플리케이션 진입점  
├── templates/  
└── menu.html # 메뉴 페이지 (아메리카노, 라떼, 녹차 버튼 포함)

common_solid_04/    
├── common_solid_mars # Hello_mars.py 진입점    
├── common_solid_mars_2 # desing_dome.py 진입점   
└── common_solid_mars_3 # mars_mission_computer.py 진입점   

common_solid_05/    
├── make_calculator # calculator.py 진입점  
├── password_solid  # password.py 진입점    
    └── password.py     
    └── emergency_storage_key.zip       
    └── unlocked
```
## 🛠️ 사용 방법

1. 저장소 클론:
    ```bash
    git clone https://github.com/<사용자명>/<저장소명>.git
    cd <저장소명>
    ```
2. 가상환경세팅
    ```
    프로젝트 실행 시!
    pyenv activate "지정한 가상환경명"
    - requiremnet.txt로 가상환경 세팅 후 실행해주세요.
    └── password.py -> pyenv virtualenv 3.11.8 password_solid
    └── calculator.py -> pyenv virtualenv 3.11.8 calculator
        └── pyenv activate "지정하기"
    ```

## ✍️ 작성자

- 이름: 이승갑
- 과제명: GitHub 협업 환경 구성 및 기능 구현 실습