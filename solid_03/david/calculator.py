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
        a = int(input("Enter first number: "))
    except ValueError:
        print("Invalid input for number.")
        return
    
    try:
        b = int(input("Enter Second number: "))
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
    expression = input("Enter expression: ")
    parts = expression.split() # 공백 포함이라는 조건이 있어 strip은 사용하지 않고 split하였습니다.

    # 공백 2개가 없으면 예외 처리
    if len(parts) != 3:
        print("Invalid expression format.")
        return

    # 각 부분을 변수로 저장
    a_str, operator, b_str = parts

    # 일반 계산기와 동일하게 정수가 아닌 str이 들어오면 메시지 출력 후 종료.
    try:
        a = int(a_str)
        b = int(b_str)
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

# 코드 재사용성을 위해서 모드 자체를 선택할 수 있도록 구현했습니다.
if __name__ == "__main__":
    print("계산기 모드를 선택해주세요!")
    print("1. 일반 계산기 (숫자 2개만 입력하여 연산합니다.)")
    print("2. 문자열 수식 계산기 (숫자 1 또는 2)")
    mode = input("Enter mode (1 or 2): ")

    if mode == "1":
        calculator()
    elif mode == "2":
        expression_calculator()
    else:
         print("Invalid mode selection.")