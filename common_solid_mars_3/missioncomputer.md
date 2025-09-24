# class
```
__init__ 자동생성자

객체가 호출될 때 자동으로 생성됩니다.
class를 통해 생성된 객체는 인스턴스라고 합니다..
정의 시 self를 제외한 인자와 동일하게 값을 줘야 동작합니다.
인자가 맞지 않으면 필요한 인자를 갯수만큼을 똑같이 달라고 오류메세지가 발생합니다.
```

### 멤버 변수
```
class 생성 시 사용된 self.변수 등을 멤버 변수라고 합니다.
class 외부에서도 멤버 변수는 사용이 가능합니다. 
이 말은 즉, class를 통해 생성된 객체에 멤버 변수를 추가적으로 정의 할 수 있음을 뜻합니다.
(다만, 기존에 생성된 클래스에는 멤버 변수 추가없이 지정한 것만 가능합니다.)
```

# random
- random.uniform
- 

# datetime

# json

# time
사용자가 시간의 시간 변경 또는 NTP 동기화가 되면 time.time의 경우는 꼬일 수도 있음.
- time.monotonic : 시스템의 시각 변경 등에 영향을 받지 않고 시간의 증가만 하므로 타임아웃/주기/실행에 대해 안전함.
- time.monotonic()
- time.sleep()

# APsscheduler(Advanced Python Scheduler)

단일 실행, 인터벌 실행, 크론 스타일 실행 등 다양한 방식으로 작업을 예약이 가능하며, 백그라운드 작업등을 쉽게 처리할 수 있도록 도와주며, 웹 애플리케이션, 대규모 시스템, 배치 작업 처리 등 다양한 환경에서 활용됩니다.

### 주요 기능
- 다양한 작업 스케줄링 옵션(일회성, 반복, 크론)
- 동기 및 비동기 작업 실행 지원
- 여러 작업 저장소 지원(메모리, SQLAlchemy, MongoDB, Redis 등)
- 타임존 설정 및 여름시간(Daylight Saving Time) 고려
- 이벤트 리스너와 후크를 통한 작업 실행 모니터링

### 설치 방법
```pip install apscheduler```

### 예제 코드

```
from apscheduler.schedulers.background 
import BackgroundScheduler

def hello():
    print("Hello World!")

# 스케줄러 생성 및 작업 추가
scheduler = BackgroundScheduler()
scheduler.add_job(hello, 'interval', seconds=30)
- 매 30초마다 hello 함수 실행

# 스케줄러 시작
scheduler.start()

# 프로그램이 종료되지 않도록 대기
try:
    while True:
        time.sleep(2)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()

```

# 로직 구조 생각해보기
문제 1번에서 DummySensor라는 클래스는 정해진 딕셔너리 형태의 내부에 해당 키값의 고유 값들이 각자 정해진 범위들 안에서
난수를 생성해야합니다. 이를 위해서는 DummySensor class가 자기 자신을 인스턴스화하여 호출할 수 있도록 ENV_SPEC이 반복가능한 자료구조이므로

# Event
스레드간에 공유하는 플래그
```
stop_event.set() : 강제 종료가 아닌 종료 요청
stop_event.is_set() : 비차단 상태 점검 함수 -> True라면 종료신호,False라면 계속 진행.-> 플래그 ON인지 즉시 확인
is_set()은 루프안에서 상태만 빠르게 사용할 때 사용합니다.
stop_event.wait() : 신호가 오기 전까지 대기, 신호가 오면 즉시 사용
stop_event.clear() : 플래그OFF(다시 진행 가능)
d

여러 스레드가 하나의 이벤트를 공유한다면 set() 한번으로 전부에게 정지신호를 보낼수있음.
! 프로세스 간 제어가 필요 시 Threading.Event 가 아닌 multiprocessing.Event를 사용해야합니다.
```

# psutil