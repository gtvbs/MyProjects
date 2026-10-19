
import array

ARRAY = array.array('i', [1, 2,9, 10, 3, 4, 5])

ARRAY.append(6)

ARRAY = sorted(ARRAY)
print(ARRAY)
