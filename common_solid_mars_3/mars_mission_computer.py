# 라이브러리 설치
import random
from pathlib import Path
from datetime import datetime
import json

ENV_SPEC = {
    "mars_base_internal_temperature":   ("°C",  (18.0, 30.0), ),
    "mars_base_external_temperature":   ("°C",  (0.0, 21.0), 1),
    "mars_base_internal_humiddity":     ("%",   (50.0, 60.0), 1),
    "mars_base_external_illuminance":   ("W/m²",())
    "mars_base": ()
    "mars_base": ()
}
# 1. 클래스 정의 더미 센서 제작(DummySensor)
class DummySensor:

# 2. 클래스 정의 미션컴퓨터(Missioncomputer)
