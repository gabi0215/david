# 모든 연산을 별도의 함수로 정의합니다.
def add(a,b):
        return a + b
def subtract(a,b):
        return a - b
def multiply(a,b):
        return a * b
def divide(a,b):
        if b == 0:
            return "Error: Division by zero."
        return a / b

# 계산기 함수입니다.
def calculator():
    try:
        a = float(input("Enter first number: "))
    except ValueError:
        print("Invalid input for number.")
        return
    
    try:
        b = float(input("Enter Second number: "))
    except ValueError:
        print("Invalid input for number")
        return
    # 조건은 숫자를 2개 받아야하고 int로 받아와야하며 다른 인자가 들어올 경우 예외처리를 해야하는 조건이 있습니다.

    # int를 a,b에 변수에 받고 나면 연산자를 입력 받아야합니다.
    operator = input("Enter operator (+, -, *, /): ")

    # 모든 연산을 각각의 함수를 호출해서 진행합니다.
    if operator == "+":
        result = add(a, b)
    elif operator == "-":
        result = subtract(a, b)
    elif operator == "*":
        result = multiply(a, b)
    elif operator == "/":
        result = divide(a, b)
    else:
        print("Invalid operator.")
        return
    # 문자열이면 에러 메세지 출력, 숫자라면 result를 출력.
    if isinstance(result, str):
         print(result)
    else:
         print("Result:", result)

# 보너스 과제 함수입니다.
def expression_calculator():
    expression = input("Enter expression (ex: 3 + 3): ")
    parts = expression.split() # 공백 포함이라는 조건이 있어 strip은 사용하지 않고 split하였습니다.

    # 공백 2개가 없으면 예외 처리
    if len(parts) != 3:
        print("Invalid expression format.")
        return

    # 각 부분을 변수로 저장
    a_str, operator, b_str = parts

    # 일반 계산기와 동일하게 정수가 아닌 str이 들어오면 메시지 출력 후 종료.
    try:
        a = float(a_str)
        b = float(b_str)
    except ValueError:
        print("Invalid number.")
        return

    if operator == "+":
        result = add(a, b)
    elif operator == "-":
        result = subtract(a, b)
    elif operator == "*":
        result = multiply(a, b)
    elif operator == "/":
        result = divide(a, b)
    else:
        print("Invalid operator.")
        return

    # 파이썬 내장 함수를 사용하여 해당 값이 특정 타입인지 확인합니다.
    if isinstance(result, str):
        print(result)
    else:
        print("Result:", result)

# practic_06을 위해 우선순위를 결정하여 계산하는 함수를 구현했습니다.
def priority_calculator():
    expression = input("Enter expression (ex: 3 + 3 * 5 - 2): ")
    tokens = expression.split()

    # 입력이 공백이라면 탈출.
    if len(tokens) % 2 == 0:
        print("Invalid input")
        return
    # 입력 시 연산자가 없이 숫자만 입력되었을 예외처리 로직
    if not any(op in tokens for op in ["+", "-", "*", "/"]):
        print("연산자가 하나도 없습니다.")
        return
    
    # 0부터 2칸씩 이동하면서 i값을 가져오고 숫자 부분만 골라서 float로 변환합니다.
    try:
        for i in range(0, len(tokens), 2):
            tokens[i] = float(tokens[i])
    except ValueError:
        print("Invalid input.")
        return
    
    i = 1 # 인덱스 1부터 시작(tokens[1]은 연산자 위치)
    while i < len(tokens) -1: # 범위 초과 방지
        op = tokens[i]
        if op == "*" or op == "/":
            a = tokens[i - 1]
            b = tokens[i + 1]
            result = multiply(a,b) if op == "*" else divide(a, b)
            if isinstance(result, str):
                print(result)
                return
            tokens[i - 1:i + 2] = [result] # 계산된 3개를 하나의 값으로 리스트에서 치환.
            i = 1 # 연산 처리가 끝났고 리스트가 바뀌었고, 다시 처음부터 검사
        else: # 연산자가 아니라면 다음 연산자로 이동
            i += 2

    result = tokens[0] # 첫 숫자를 시작값으로 저장
    i = 1
    while i < len(tokens) - 1: # 연산자와와 오르쪽 숫자 처리용 반복
        op = tokens[i] # op 연산자, b: 다음 숫자
        b = tokens[i + 1]
        # 누적 계산
        if op == "+":
            result = add(result, b)
        elif op == "-":
            result = subtract(result, b)
        # 다음 연산자와 숫자 위치로 이동
        i += 2

    print("Result:", result)

# 보너스 과제에 괄호까지 처리하는 추가 함수구현해보기

# 코드 재사용성을 위해서 모드 자체를 선택할 수 있도록 구현했습니다.
if __name__ == "__main__":
    print("계산기 모드를 선택해주세요!")
    print("1. 기본 계산기 (숫자 2개만 입력하여 연산합니다.)")
    print("2. 수식 계산기 (a + b 형식)")
    print("3. 우선순위 수식 계산기(공백 기준, *, / > +, -)")
    # print("4. 괄호 포함 우선순위 계산기")
    mode = input("Enter mode (1 ~ 3): ")

    if mode == "1":
        calculator()
    elif mode == "2":
        expression_calculator()
    elif mode == "3":
        priority_calculator()
    # elif mode == "4":
    #     priority_calculator_bonus()
    else:
         print("Invalid mode.")