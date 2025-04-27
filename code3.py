graph_exc = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D", "E"],
    "D": ["B", "C", "E"],
    "E": ["C", "D"],
}

explored = {v: False for v in graph_exc}
order = []


def dfs_recurse(v):
  explored[v] = True
  order.append(v)                   # EXPLORE v
  for n in sorted(graph_exc[v]):    # ascending order
    if not explored[n]:
      dfs_recurse(n)


dfs_recurse("A")

print(order)
