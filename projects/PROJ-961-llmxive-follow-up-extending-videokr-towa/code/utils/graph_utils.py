"""
Module: graph_utils

Purpose:
    Provides graph algorithms and utilities, including BFS shortest path,
    connected components, and hop distance calculations.

Functions:
    - build_undirected_graph: Builds an undirected graph from edges.
    - build_directed_graph: Builds a directed graph from edges.
    - shortest_path_bfs: Finds the shortest path using BFS.
    - calculate_hop_distance: Calculates distance between nodes.
    - get_connected_components: Finds connected components.
    - get_hop_distribution: Calculates hop distribution.
    - main: Entry point for the script.
"""
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, Union

def build_undirected_graph(edges: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    """
    Builds an undirected graph from a list of edges.

    Args:
        edges (List[Tuple[str, str]]): List of (u, v) edges.

    Returns:
        Dict[str, List[str]]: Adjacency list.
    """
    graph = {}
    for u, v in edges:
        graph.setdefault(u, []).append(v)
        graph.setdefault(v, []).append(u)
    return graph

def build_directed_graph(edges: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    """
    Builds a directed graph from a list of edges.

    Args:
        edges (List[Tuple[str, str]]): List of (u, v) edges.

    Returns:
        Dict[str, List[str]]: Adjacency list.
    """
    graph = {}
    for u, v in edges:
        graph.setdefault(u, []).append(v)
    return graph

def shortest_path_bfs(graph: Dict[str, List[str]], start: str, end: str) -> Optional[List[str]]:
    """
    Finds the shortest path between two nodes using BFS.

    Args:
        graph (Dict[str, List[str]]): Graph adjacency list.
        start (str): Start node.
        end (str): End node.

    Returns:
        Optional[List[str]]: Path as a list of nodes, or None if no path.
    """
    if start == end:
        return [start]
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        node, path = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None

def calculate_hop_distance(graph: Dict[str, List[str]], start: str, end: str) -> int:
    """
    Calculates the hop distance between two nodes.

    Args:
        graph (Dict[str, List[str]]): Graph.
        start (str): Start node.
        end (str): End node.

    Returns:
        int: Distance in hops, or -1 if no path.
    """
    path = shortest_path_bfs(graph, start, end)
    if path is None:
        return -1
    return len(path) - 1

def get_connected_components(graph: Dict[str, List[str]]) -> List[Set[str]]:
    """
    Finds all connected components in the graph.

    Args:
        graph (Dict[str, List[str]]): Graph.

    Returns:
        List[Set[str]]: List of sets of nodes.
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

def get_hop_distribution(graph: Dict[str, List[str]], nodes: List[str]) -> Dict[int, int]:
    """
    Calculates the distribution of hop distances between a set of nodes.

    Args:
        graph (Dict[str, List[str]]): Graph.
        nodes (List[str]): List of nodes.

    Returns:
        Dict[int, int]: Distribution of hops.
    """
    dist_counts = {}
    for i, n1 in enumerate(nodes):
        for n2 in nodes[i+1:]:
            d = calculate_hop_distance(graph, n1, n2)
            if d > 0:
                dist_counts[d] = dist_counts.get(d, 0) + 1
    return dist_counts

def main():
    """
    Main entry point for the graph_utils script.
    Demonstrates basic functionality.
    """
    edges = [("A", "B"), ("B", "C"), ("C", "D")]
    graph = build_undirected_graph(edges)
    path = shortest_path_bfs(graph, "A", "D")
    print(f"Shortest path A->D: {path}")

if __name__ == "__main__":
    main()
