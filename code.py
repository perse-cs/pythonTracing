neighborsx = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'D', 'E'],
    'D': ['B', 'C', 'E'],
    'E': ['C', 'D']
}


def dfs(start):
  # Initialize explored flags
  explored = {vx: False for vx in neighborsx}
  # Stack for DFS
  stack = []
  stack.append(start)

  while stack:
    current = stack.pop()
    if not explored[current]:
      explored[current] = True
      print(current)
      # Push neighbors in given order
      for n in neighborsx[current]:
        if not explored[n]:
          stack.append(n)


dfs('A')
