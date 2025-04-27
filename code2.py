def collatz(num, count=0):
  count = count + 1
  if num == 1:
    return count
  next_num = (num // 2) if num % 2 == 0 else (3 * num + 1)
  return collatz(next_num, count)


test = 5
print(collatz(test))
