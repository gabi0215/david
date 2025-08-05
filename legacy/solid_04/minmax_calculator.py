# 최소값, 최대값을 출력하는 프로그램 함수입니다.
def minmax_calculator():
    # 1. 입력을 받아옵니다. 받아온 입력을 input_list라는 변수에 공백 기준으로 나누어서 리스트화 해줍니다.
    try:
        input_str = input("Enter numbers separated by space: ")
        input_list = input_str.split()

    # 2. 리스트 컴프리헨션 - [표현식 for 변수 in 반복가능한객체 if 조건] - 
        numbers = [float(x) for x in input_list]
    #--------------------------------
    # 2-1 일반적인 for문
    # numbers = []
    # for x in input_list:
    #     numbers.append(float(x))
    # -------------------------------
    # 3. 내장함수 없이 수동으로 비교해야합니다.
        minimum = numbers[0]
        maximum = numbers[0]
        # 인덱스 위치부터 전체
        for num in numbers[1:]:
            if num < minimum:
                minimum = num
            if num > maximum:
                maximum = num
    # 결과를 출력합니다.
        print(f"Min: {minimum}, Max = {maximum}")

    # 숫자가 아닐 때 예외 처리를 해줍니다.
    except ValueError:
        print("Invalid input")

if __name__ == "__main__":
    minmax_calculator()