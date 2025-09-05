a_of_a = [
    [1, 2, 3],
    [4, 5, 6,7],
    [8, 9]
]

for number in a_of_a:
    for inner in number:
        print(inner)

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
output = [[], [], []]

for number in numbers:
    output[number % 3].append(number)

print(output)