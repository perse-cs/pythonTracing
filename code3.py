graphx = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D", "E"],
    "D": ["B", "C", "E"],
    "E": ["C", "D"],
}

explored = {vx: False for vx in graphx}
order = []


def dfs_recurse(v):
  explored[v] = True
  order.append(v)                   # EXPLORE v
  for n in sorted(graphx[v]):    # ascending order
    if not explored[n]:
      dfs_recurse(n)


dfs_recurse("A")

print(order)
