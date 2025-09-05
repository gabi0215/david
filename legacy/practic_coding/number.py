numbers = [273, 103, 5, 32, 65, 9, 72, 800, 99]

for number in numbers:
    if number > 100:
        print("- 100 이상의 수:", number)

for hol in numbers:
    if hol % 2 == 0:
        print(f"{hol}은 짝수입니다.")
    else:
        print(f"{hol}은 홀수입니다.")

for number in numbers:
    length = len(str(number))

    if length == 1:
        print(f"{number}은 한 자리수 입니다.")

    elif length == 2:
        print(f"{number}은 두 자리수 입니다.")
    
    else:
        print(f"{number}은 세 자리수 입니다.")

