# Example list to sort
lst = [-1, 9, 8, 5, 6]

# Insertion sort (inline, no function)
for outer_pointer in range(2, len(lst)):
    current_value = lst[outer_pointer]
    inner_pointer = outer_pointer - 1

    while inner_pointer >= 0 and lst[inner_pointer] > current_value:
        lst[inner_pointer + 1] = lst[inner_pointer]
        inner_pointer -= 1

    lst[inner_pointer + 1] = current_value

print(lst)
