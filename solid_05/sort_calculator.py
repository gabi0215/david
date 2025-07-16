# 정렬 프로그램을 구현하기 위한 코드입니다.

# 입력을 처리 할 함수입니다.
def get_number_list():
    try:
        user_input = input("Enter numbers separated by spaces: ").strip()
        
        # 입력이 비어 있는 경우 예외 발생(reaise 강제로)
        if not user_input:
            raise ValueError
        
        # 문자열을 나눠줍니다.
        str_list = user_input.split()

        # flaot으로 변환(예외처리 포함)
        number_list = [float(num) for num in str_list]

        return number_list
    
    except ValueError:
        print("Invalid input.")
    return

# 선택 정렬 알고리즘 함수입니다.
def sort_numbers(arr):
    x = len(arr)
    for i in range(x):
        min_index = i
        for j in range(i + 1,x):
            if arr[j] < arr[min_index]:
                min_index = j
        arr[i], arr[min_index] = arr[min_index], arr[i]
    return arr    

# 메인으로 실행되는 함수입니다. 중복된 숫자를 정렬하게 된다면 중복도 제거합니다.
def main():
    numbers = get_number_list()
    if numbers is not None:
        # 중복제거
        delete_numbers = list(set(numbers))

        # 정렬
        sorted_numbers = sort_numbers(delete_numbers)
        print("sorted:", " ".join(f"{num:.1f}" for num in sorted_numbers))

if __name__ == "__main__":
    main()