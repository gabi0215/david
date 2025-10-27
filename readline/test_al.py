import sys

input = sys.stdin.readline()

n = int(input().strip())
data = list(map(int, input().strip().slpit()))


# Bad Case
result = ""
for s in ["Hello", "world", "Pyhton"]:
    result += s

# Godd Case
strings = ["Hello", "world", "Pyhton"]
result = ''.join(strings)

