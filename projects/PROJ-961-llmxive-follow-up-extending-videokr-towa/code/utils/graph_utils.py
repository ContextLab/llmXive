from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, Union

def build_undirected_graph(edges: List[Tuple[Any, Any]]) -> Dict[Any, List[Any]]:
    graph: Dict[Any, List[Any]] = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = []
        if v not in graph:
            graph[v] = []
        graph[u].append(v)
        graph[v].append(u)
    return graph

def build_directed_graph(edges: List[Tuple[Any, Any]]) -> Dict[Any, List[Any]]:
    graph: Dict[Any, List[Any]] = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = []
        graph[u].append(v)
    return graph

def shortest_path_bfs(graph: Dict[Any, List[Any]], start: Any, end: Any) -> Optional[List[Any]]:
    if start not in graph or end not in graph:
        return None
    
    if start == end:
        return [start]
    
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        for neighbor in graph.get(current, []):
            if neighbor == end:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None

def calculate_hop_distance(graph: Dict[Any, List[Any]], start: Any, end: Any) -> Optional[int]:
    path = shortest_path_bfs(graph, start, end)
    if path is None:
        return None
    return len(path) - 1

def get_connected_components(graph: Dict[Any, List[Any]]) -> List[Set[Any]]:
    visited = set()
    components = []
    
    for node in graph:
        if node not in visited:
            component = set()
            queue = deque([node])
            visited.add(node)
            
            while queue:
                current = queue.popleft()
                component.add(current)
                
                for neighbor in graph.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            components.append(component)
    
    return components

def get_hop_distribution(graph: Dict[Any, List[Any]], nodes: List[Any]) -> Dict[int, int]:
    distribution: Dict[int, int] = {}
    
    for i, start in enumerate(nodes):
        for end in nodes[i+1:]:
            dist = calculate_hop_distance(graph, start, end)
            if dist is not None:
                distribution[dist] = distribution.get(dist, 0) + 1
    
    return distribution

def main():
    # Example usage
    edges = [('A', 'B'), ('B', 'C'), ('C', 'D'), ('A', 'E')]
    graph = build_undirected_graph(edges)
    
    print(f"Graph: {graph}")
    print(f"Path A->D: {shortest_path_bfs(graph, 'A', 'D')}")
    print(f"Distance A->D: {calculate_hop_distance(graph, 'A', 'D')}")
    print(f"Components: {get_connected_components(graph)}")

if __name__ == "__main__":
    main()
