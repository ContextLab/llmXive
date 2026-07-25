"""Graph utility functions for pathfinding and analysis."""
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, Union

def build_undirected_graph(edges: List[Tuple[str, str]]) -> Dict[str, Set[str]]:
    """Build an undirected graph from a list of edges."""
    graph: Dict[str, Set[str]] = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = set()
        if v not in graph:
            graph[v] = set()
        graph[u].add(v)
        graph[v].add(u)
    return graph

def build_directed_graph(edges: List[Tuple[str, str]]) -> Dict[str, Set[str]]:
    """Build a directed graph from a list of edges."""
    graph: Dict[str, Set[str]] = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = set()
        graph[u].add(v)
        if v not in graph:
            graph[v] = set()
    return graph

def shortest_path_bfs(graph: Dict[str, Set[str]], start: str, end: str) -> Optional[List[str]]:
    """Find the shortest path between two nodes using BFS.

    Args:
        graph: The graph as an adjacency list.
        start: The starting node.
        end: The ending node.

    Returns:
        A list of nodes representing the shortest path, or None if no path exists.
    """
    if start not in graph or end not in graph:
        return None

    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        node, path = queue.popleft()
        if node == end:
            return path

        for neighbor in sorted(graph[node]):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None

def calculate_hop_distance(graph: Dict[str, Set[str]], start: str, end: str) -> Optional[int]:
    """Calculate the hop distance between two nodes.

    Args:
        graph: The graph as an adjacency list.
        start: The starting node.
        end: The ending node.

    Returns:
        The number of hops between start and end, or None if no path exists.
    """
    path = shortest_path_bfs(graph, start, end)
    if path is None:
        return None
    return len(path) - 1

def get_connected_components(graph: Dict[str, Set[str]]) -> List[Set[str]]:
    """Find all connected components in an undirected graph."""
    visited: Set[str] = set()
    components: List[Set[str]] = []

    for node in graph:
        if node not in visited:
            component: Set[str] = set()
            queue = deque([node])
            while queue:
                current = queue.popleft()
                if current not in visited:
                    visited.add(current)
                    component.add(current)
                    for neighbor in graph[current]:
                        if neighbor not in visited:
                            queue.append(neighbor)
            components.append(component)

    return components

def get_hop_distribution(graph: Dict[str, Set[str]], component: Optional[Set[str]] = None) -> Dict[int, int]:
    """Calculate the distribution of hop distances in a graph component.

    Args:
        graph: The graph as an adjacency list.
        component: An optional set of nodes defining a component.

    Returns:
        A dictionary mapping hop distance to count.
    """
    if component is None:
        component = set(graph.keys())

    hop_counts: Dict[int, int] = {}
    nodes = list(component)

    for i, start in enumerate(nodes):
        for end in nodes[i + 1:]:
            distance = calculate_hop_distance(graph, start, end)
            if distance is not None:
                hop_counts[distance] = hop_counts.get(distance, 0) + 1

    return hop_counts
