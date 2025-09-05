list_a = [0, 1, 2, 3, 4, 5, 6, 7]
print(list_a)

list_a.extend(list_a)
print(list_a)

list_a.append(10)
print(list_a)

list_a.insert(3, 0)
print(list_a)

list_a.remove(3)
print(list_a)

list_a.pop(3)
print(list_a)

list_a.pop()
print(list_a)

del list_a[:5]
print(list_a)

del list_a[3:]
print(list_a)

list_a.clear()
print(list_a)