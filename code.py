neighbors_exc = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'D', 'E'],
    'D': ['B', 'C', 'E'],
    'E': ['C', 'D']
}


def dfs(start):
  # Initialize explored flags
  explored = {v: False for v in neighbors_exc}
  # Stack for DFS
  stack = []
  stack.append(start)

  while stack:
    current = stack.pop()
    if not explored[current]:
      explored[current] = True
      print(current)
      # Push neighbors in given order
      for n in neighbors_exc[current]:
        if not explored[n]:
          stack.append(n)


dfs('A')
