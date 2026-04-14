# Defining the graph exactly with the pseudocode variable names and approach

Graph_exc = ['A', 'B', 'C', 'D', 'E']
Neighbours_exc = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'D', 'E'],
    'D': ['B', 'C', 'E'],
    'E': ['C', 'D']
}

def DFS(Start):
    # Initialize Explored for each v in Graph
    Explored = {}
    for v in Graph_exc:
        Explored[v] = False

    # Stack initialization
    Nodes = []
    Nodes.append(Start)

    # DFS loop
    while len(Nodes) != 0:
        Current = Nodes.pop()
        if Explored[Current] == False:
            Explored[Current] = True
            print(Current)
            for n in Neighbours_exc[Current]:
                if Explored[n] == False:
                    Nodes.append(n)

# Run DFS starting at 'A'
DFS('A')
