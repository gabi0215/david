# print(1)
# print(1+1)
# print(1-1)
# print(type(1.1))

import math
import random

print('math.sqrt(4):', (math.sqrt(4))) # math의 sqrt 제곱근 구하는 코드
print('math.pow(2,3):', (math.pow(2,3))) # math의 제곱 하는 pow 코드

print('random.random():', random.random())

value = random.random()

print('random.random():', value, 'type:', type(value))
print(f"random.random(): {value}, type: {type(value)}")

print("""
hello
world
""")
print("hello\nworld\n!")

print(f"random.random(): \n{value}, type: {type(value)}")
print("len('hello world'*500'):", len('hello world'*500))
print("len('hello world'*500'):", type('hello world'*500))
print("'hello world'.replace('hello world', 'hi! 32seuol':", 'hello world'.replace('hello world', 'hi! 32seuol'))