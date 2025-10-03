# calculator.py — 한 파일 제출용 (PyQt6 우선, 미설치 시 PyQt5 폴백)
from __future__ import annotations

import math
import sys

# ───────────────── PyQt 호환 임포트 (6 → 5 폴백) ─────────────────
try:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QKeySequence, QShortcut
    from PyQt6.QtWidgets import (
        QApplication,
        QDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenuBar,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    def align_right():
        return Qt.AlignmentFlag.AlignRight

    PYQT_VER = 6
except Exception:  # PyQt5 fallback
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QKeySequence, QShortcut
    from PyQt5.QtWidgets import (
        QApplication,
        QDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenuBar,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    def align_right():
        return Qt.AlignRight

    PYQT_VER = 5


# ───────────────── iPhone 톤 전역 스타일시트 ─────────────────
APP_QSS = """
/* 배경 */
QMainWindow, QWidget { background: #1C1C1E; color: #FFFFFF; }

/* 디스플레이 */
QLineEdit{
  background:#000000; color:#FFFFFF; border:1px solid #2C2C2E;
  padding:10px; font-size:22px; border-radius:8px;
}

/* 버튼 공통(배경은 역할 규칙이 덮어씀) */
QPushButton{
  min-width:64px; min-height:64px; font-size:22px;
  border-radius:32px; border:0px; color:#FFFFFF;
}

/* ───── 역할별 기본 색 (아이폰 톤) ───── */
QPushButton[role="num"]{ background:#3A3A3C; }                 /* 숫자키/점 */
QPushButton[role="fn"] { background:#A5A5A5; color:#000000; }  /* C, +/- , % */
QPushButton[role="op"] { background:#FF9F0A; color:#FFFFFF; }  /* / * - +    */
QPushButton[role="eq"] { background:#FF9F0A; color:#FFFFFF; }  /* =          */

/* 0 버튼: 가로로 긴 알약 */
QPushButton[wide="true"]{
  min-width:140px; border-radius:32px; padding-left:24px;
}

/* ───── 역할별 hover/pressed (전역 hover/pressed 금지) ───── */
QPushButton[role="num"]:hover   { background:#4A4A4C; }
QPushButton[role="num"]:pressed { background:#2A2A2C; }

QPushButton[role="fn"]:hover    { background:#B5B5B5; color:#000000; }
QPushButton[role="fn"]:pressed  { background:#8F8F8F; color:#000000; }

QPushButton[role="op"]:hover,
QPushButton[role="eq"]:hover    { background:#FFB340; color:#FFFFFF; }
QPushButton[role="op"]:pressed,
QPushButton[role="eq"]:pressed  { background:#CC7F00; color:#FFFFFF; }

/* 상단 모드바(세그먼트) */
#modeBar QPushButton{
  background:#2C2C2E; color:#FFFFFF; border-radius:14px; min-height:34px; font-size:16px;
}
#modeBar QPushButton:checked{ background:#FF9F0A; color:#FFFFFF; }
"""


# ───────────────── 모드 정의 ─────────────────
class Mode:
    BASIC = "basic"
    ENGINEERING = "engineering"


# ───────────────── 계산 로직(기본) ─────────────────
class Calculator:
    """
    초보자 친화: 상태 기반 사칙연산 계산기.
    - add/subtract/multiply/divide 메서드 (요구사항)
    - reset, negative_positive, percent
    - 연속 계산(= 누를 때)
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.current = "0"   # 표시 문자열(입력 중)
        self.acc = None      # 누적값(float)
        self.op = None       # 직전 연산자('+','-','*','/')
        self.just_eval = False  # = 직후 숫자 입력 시 클리어

    # 입력(숫자/소수점)
    def input_digit(self, ch: str) -> str:
        if self.just_eval:
            self.current = "0"
            self.just_eval = False
        if ch == ".":
            if "." not in self.current:
                self.current += "."
            return self.current
        if self.current == "0":
            self.current = ch
        else:
            self.current += ch
        return self.current

    def negative_positive(self) -> str:
        if self.current.startswith("-"):
            self.current = self.current[1:]
        else:
            if self.current != "0":
                self.current = "-" + self.current
        return self.current

    def percent(self) -> str:
        try:
            v = float(self.current) / 100.0
            self.current = self._fmt(v)
        except ValueError:
            pass
        return self.current

    # ── 요구: 연산 메서드 ──
    def add(self):      self._set_op("+")
    def subtract(self): self._set_op("-")
    def multiply(self): self._set_op("*")
    def divide(self):   self._set_op("/")

    def equals(self) -> str:
        self._eval_pending()
        self.op = None
        self.just_eval = True
        self.current = self._fmt(self.acc if self.acc is not None else 0.0)
        return self.current

    # 내부 유틸
    def _set_op(self, op: str):
        if self.acc is None:
            try:
                self.acc = float(self.current)
            except ValueError:
                self.acc = 0.0
        else:
            self._eval_pending()
        self.op = op
        self.current = "0"

    def _eval_pending(self):
        if self.op is None:
            return
        try:
            b = float(self.current)
        except ValueError:
            b = 0.0
        a = self.acc if self.acc is not None else 0.0
        if self.op == "+":   self.acc = a + b
        elif self.op == "-": self.acc = a - b
        elif self.op == "*": self.acc = a * b
        elif self.op == "/": self.acc = 0.0 if b == 0.0 else a / b

    @staticmethod
    def _fmt(x: float) -> str:
        return f"{x:.12g}"


# ───────────────── 안전 수식 평가(공학용) ─────────────────
def safe_eval(expr: str) -> float:
    """
    공학용: math 화이트리스트만 허용. (라디안)
    허용: 사칙, 괄호, **, 단항±, 상수/함수
    """
    allowed = {
        "pi": math.pi, "e": math.e,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "abs": abs,
    }
    return eval(expr, {"__builtins__": None}, allowed)


# ───────────────── UI: 기본 계산기 ─────────────────
class BasicCalculatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.cal = Calculator()

        self.disp = QLineEdit("0")
        self.disp.setReadOnly(True)
        self.disp.setAlignment(align_right())

        grid = QGridLayout(self)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.setContentsMargins(24, 12, 24, 24)

        # 표시창
        grid.addWidget(self.disp, 0, 0, 1, 4)

        # 버튼들 (iPhone 톤에 맞춘 role/wide)
        btns = [
            (self._make_btn("C",   role="fn",  handler=self.on_click), 1,0),
            (self._make_btn("+/-", role="fn",  handler=self.on_click), 1,1),
            (self._make_btn("%",   role="fn",  handler=self.on_click), 1,2),
            (self._make_btn("/",   role="op",  handler=self.on_click), 1,3),

            (self._make_btn("7",   role="num", handler=self.on_click), 2,0),
            (self._make_btn("8",   role="num", handler=self.on_click), 2,1),
            (self._make_btn("9",   role="num", handler=self.on_click), 2,2),
            (self._make_btn("*",   role="op",  handler=self.on_click), 2,3),

            (self._make_btn("4",   role="num", handler=self.on_click), 3,0),
            (self._make_btn("5",   role="num", handler=self.on_click), 3,1),
            (self._make_btn("6",   role="num", handler=self.on_click), 3,2),
            (self._make_btn("-",   role="op",  handler=self.on_click), 3,3),

            (self._make_btn("1",   role="num", handler=self.on_click), 4,0),
            (self._make_btn("2",   role="num", handler=self.on_click), 4,1),
            (self._make_btn("3",   role="num", handler=self.on_click), 4,2),
            (self._make_btn("+",   role="op",  handler=self.on_click), 4,3),

            (self._make_btn("0",   role="num", wide=True, handler=self.on_click), 5,0,1,2),
            (self._make_btn(".",   role="num", handler=self.on_click), 5,2),
            (self._make_btn("=",   role="eq",  handler=self.on_click), 5,3),
        ]
        for item in btns:
            btn, r, c, *span = item
            rs, cs = (span + [1, 1])[:2]
            grid.addWidget(btn, r, c, rs, cs)

    def _make_btn(self, text, role="num", wide=False, handler=None):
        b = QPushButton(text)
        b.setProperty("role", role)
        if wide:
            b.setProperty("wide", True)
        if handler:
            b.clicked.connect(lambda _, t=text: handler(t))
        return b

    def on_click(self, t: str):
        if t.isdigit() or t == ".":
            self.disp.setText(self.cal.input_digit(t)); return
        if t == "C":
            self.cal.reset(); self.disp.setText(self.cal.current); return
        if t == "+/-":
            self.disp.setText(self.cal.negative_positive()); return
        if t == "%":
            self.disp.setText(self.cal.percent()); return
        if t in {"+", "-", "*", "/"}:
            {"+": self.cal.add, "-": self.cal.subtract,
             "*": self.cal.multiply, "/": self.cal.divide}[t]()
            self.disp.setText(self.cal.current); return
        if t == "=":
            self.disp.setText(self.cal.equals()); return


# ───────────────── UI: 공학용 계산기(확장) ─────────────────
class EngineeringCalculatorWidget(BasicCalculatorWidget):
    def __init__(self):
        super().__init__()
        grid: QGridLayout = self.layout()  # type: ignore

        extra = [
            ("(", 6, 0, "fn"), (")", 6, 1, "fn"), ("π", 6, 2, "fn"), ("e", 6, 3, "fn"),
            ("x²", 7, 0, "op"), ("√x", 7, 1, "op"), ("1/x", 7, 2, "op"), ("·", 7, 3, "fn"),
            ("sin", 8, 0, "op"), ("cos", 8, 1, "op"), ("tan", 8, 2, "op"), ("· ", 8, 3, "fn"),
            ("sinh", 9, 0, "op"), ("cosh", 9, 1, "op"), ("tanh", 9, 2, "op"), ("·  ", 9, 3, "fn"),
        ]
        for text, r, c, role in extra:
            btn = self._make_btn(text, role=role, handler=self.on_extra)
            btn.setMinimumHeight(52)
            if text.strip("·").strip() == "":
                btn.setEnabled(False)
            grid.addWidget(btn, r, c)

    def on_extra(self, t: str):
        s = self.disp.text()
        if t == "π":  self.disp.setText(self._append(s, "pi"));  return
        if t == "e":  self.disp.setText(self._append(s, "e"));   return
        if t == "(":  self.disp.setText(s + "(");                 return
        if t == ")":  self.disp.setText(s + ")");                 return
        if t == "x²": self.disp.setText(f"({s})**2");             return
        if t == "√x": self.disp.setText(f"sqrt({s})");            return
        if t == "1/x":self.disp.setText(f"(1/({s}))");            return
        if t in {"sin","cos","tan","sinh","cosh","tanh"}:
            self.disp.setText(f"{t}({s})");                       return

    @staticmethod
    def _append(base: str, token: str) -> str:
        return token if base == "0" else base + token

    def on_click(self, t: str):
        if t == "=":
            expr = self.disp.text()
            try:
                val = safe_eval(expr)
                self.disp.setText(Calculator._fmt(val))
                self.cal.just_eval = True
            except Exception:
                self.disp.setText("0")
                self.cal.reset()
            return
        super().on_click(t)


# ───────────────── 터미널 입력 리스너(선택) ─────────────────
class StdinWatcher(QThread):
    switch = pyqtSignal(str)  # "basic" or "engineering"

    def run(self):
        if not (sys.stdin and sys.stdin.isatty()):
            return
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            s = line.strip()
            if s == "1": self.switch.emit(Mode.BASIC)
            elif s == "2": self.switch.emit(Mode.ENGINEERING)


# ───────────────── 메인 윈도우(즉시 전환 버튼/단축키/터미널) ─────────────────
class MainWindow(QMainWindow):
    def __init__(self, start_mode: str):
        super().__init__()
        self.stack = QStackedWidget()
        self.basic = BasicCalculatorWidget()
        self.engineering = EngineeringCalculatorWidget()
        self.stack.addWidget(self.basic)        # 0
        self.stack.addWidget(self.engineering)  # 1

        # 상단 모드바(세그먼트)
        bar = QWidget(); bar.setObjectName("modeBar")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(12, 8, 12, 8)
        bar_lay.setSpacing(12)
        self.btn_basic = QPushButton("Basic")
        self.btn_eng = QPushButton("Engineering")
        for b in (self.btn_basic, self.btn_eng): b.setCheckable(True)
        self.btn_basic.clicked.connect(lambda: self._click_mode(Mode.BASIC))
        self.btn_eng.clicked.connect(lambda: self._click_mode(Mode.ENGINEERING))

        bar_lay.addWidget(self.btn_basic); bar_lay.addWidget(self.btn_eng)

        # 중앙 배치: (모드바) + (스택)
        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(bar)
        v.addWidget(self.stack)
        self.setCentralWidget(central)

        self._make_menu_shortcuts()
        self.set_mode(start_mode)
        self.setWindowTitle("Calculator")

        # 터미널 리스너(있을 때만)
        self._stdin = StdinWatcher()
        self._stdin.switch.connect(self.set_mode)
        try: self._stdin.setDaemon(True)
        except Exception: pass
        self._stdin.start()

    def _click_mode(self, mode: str):
        self.set_mode(mode)

    def _make_menu_shortcuts(self):
        mb = QMenuBar(self)
        self.setMenuBar(mb)
        m = mb.addMenu("Mode")
        a1 = m.addAction("Basic"); a2 = m.addAction("Engineering")
        a1.triggered.connect(lambda: self.set_mode(Mode.BASIC))
        a2.triggered.connect(lambda: self.set_mode(Mode.ENGINEERING))
        # 메뉴 단축키
        a1.setShortcut(QKeySequence("Ctrl+1"))
        a2.setShortcut(QKeySequence("Ctrl+2"))
        # 전역 단축키(포커스 무관)
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.set_mode(Mode.BASIC))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.set_mode(Mode.ENGINEERING))
        # macOS(⌘)
        QShortcut(QKeySequence("Meta+1"), self, activated=lambda: self.set_mode(Mode.BASIC))
        QShortcut(QKeySequence("Meta+2"), self, activated=lambda: self.set_mode(Mode.ENGINEERING))

    def set_mode(self, mode: str):
        self.stack.setCurrentIndex(0 if mode == Mode.BASIC else 1)
        self.btn_basic.setChecked(mode == Mode.BASIC)
        self.btn_eng.setChecked(mode == Mode.ENGINEERING)


# ───────────────── 실행 후 숫자 입력(초기 1회) ─────────────────
def prompt_for_mode_console() -> str:
    while True:
        s = input("\n모드 선택: [1] 기본  [2] 공학  (기본=1): ").strip() or "1"
        if s in {"1", "2"}:
            return Mode.BASIC if s == "1" else Mode.ENGINEERING
        print("잘못된 입력입니다. 1 또는 2를 입력하세요.")


class ModeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("모드 선택")
        self.chosen = Mode.BASIC
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("모드를 선택하세요"))
        b1 = QPushButton("1) 기본 계산기"); b2 = QPushButton("2) 공학용 계산기")
        lay.addWidget(b1); lay.addWidget(b2)
        b1.clicked.connect(lambda: self._choose(Mode.BASIC))
        b2.clicked.connect(lambda: self._choose(Mode.ENGINEERING))
    def _choose(self, mode: str):
        self.chosen = mode
        self.accept()


def choose_mode_interactive(app) -> str:
    try:
        if sys.stdin and sys.stdin.isatty():
            return prompt_for_mode_console()
    except Exception:
        pass
    dlg = ModeDialog(); dlg.exec()
    return dlg.chosen


# ───────────────── 엔트리 포인트 ─────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)  # iPhone 톤 스타일 적용

    start_mode = choose_mode_interactive(app)  # 초기 1회 선택
    mw = MainWindow(start_mode)
    mw.show()
    try:
        sys.exit(app.exec())
    except AttributeError:
        sys.exit(app.exec_())
