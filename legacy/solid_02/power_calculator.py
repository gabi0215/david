def calculator():
    try:
        number = float(input("Enter number: "))
    except ValueError:
        print("Invalid number input.")
        return
    # 사용자로부터 숫자를 입력받을 때 예외 처리를 위한 코드입니다.
    # return은 에러가 났으면 계산을 진행하지 않고 함수를 종료합니다.

    try:
        exponent = int(input("Enter exponent: "))
    except ValueError:
        print("Invalid exponent input.")
        return
    # 사용자로부터 지수를 입력받을 때 예외 처리를 위한 코드입니다.
    
    result = 1.0 # 결과를 담을 변수입니다. 초기값은 곱셈 항등원인 1.0입니다.

    for _ in range(abs(exponent)):
        result *= number
    # result = result * number 의 축약형입니다.
    # 반복 변수 이름이 없으므로 언더바를 사용했습니다.
    # abs() 항상 양수로 절대값을 반환하게 하는 내장함수입니다.

    if exponent < 0:
        result = 1 / result
    # 지수가 음수일 때

    print("Result:", result)
    # 최종 계산된 결과를 출렵합니다.

if __name__ == "__main__":
    calculator()
