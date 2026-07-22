from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, Union

def build_undirected_graph(
    edges: List[Tuple[str, str]]
) -> Dict[str, List[str]]:
    """
    Build an undirected graph from edges.
    
    Args:
        edges: List of edge tuples.
        
    Returns:
        Adjacency list.
    """
    graph: Dict[str, List[str]] = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = []
        if v not in graph:
            graph[v] = []
        graph[u].append(v)
        graph[v].append(u)
    return graph

def build_directed_graph(
    edges: List[Tuple[str, str]]
) -> Dict[str, List[str]]:
    """
    Build a directed graph from edges.
    
    Args:
        edges: List of edge tuples.
        
    Returns:
        Adjacency list.
    """
    graph: Dict[str, List[str]] = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = []
        graph[u].append(v)
    return graph

def shortest_path_bfs(
    graph: Dict[str, List[str]], 
    start: str, 
    end: str
) -> Optional[int]:
    """
    Find the shortest path length using BFS.
    
    Args:
        graph: The graph adjacency list.
        start: Start node.
        end: End node.
        
    Returns:
        Shortest path length or None if no path.
    """
    if start not in graph or end not in graph:
        return None
        
    queue = deque([(start, 0)])
    visited = {start}
    
    while queue:
        node, dist = queue.popleft()
        if node == end:
            return dist
            
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
                
    return None

def calculate_hop_distance(
    graph: Dict[str, List[str]], 
    start: str, 
    end: str
) -> Optional[int]:
    """
    Calculate hop distance between two nodes.
    
    Args:
        graph: The graph.
        start: Start node.
        end: End node.
        
    Returns:
        Hop distance or None.
    """
    return shortest_path_bfs(graph, start, end)

def get_connected_components(
    graph: Dict[str, List[str]]
) -> List[Set[str]]:
    """
    Get connected components of the graph.
    
    Args:
        graph: The graph.
        
    Returns:
        List of sets of nodes.
    """
    visited = set()
    components = []
    
    for node in graph:
        if node not in visited:
            component = set()
            queue = deque([node])
            visited.add(node)
            
            while queue:
                curr = queue.popleft()
                component.add(curr)
                
                for neighbor in graph.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        
            components.append(component)
            
    return components

def get_hop_distribution(
    graph: Dict[str, List[str]], 
    sample_pairs: List[Tuple[str, str]]
) -> Dict[int, int]:
    """
    Get the distribution of hop distances.
    
    Args:
        graph: The graph.
        sample_pairs: List of (start, end) pairs.
        
    Returns:
        Dictionary of hop counts to frequencies.
    """
    from collections import Counter
    distances = []
    
    for start, end in sample_pairs:
        dist = shortest_path_bfs(graph, start, end)
        if dist is not None:
            distances.append(dist)
            
    return dict(Counter(distances))