"""
Graph utility functions for shortest path calculations and graph analysis.
"""
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, Union


def build_undirected_graph(edges: List[Tuple[Any, Any]]) -> Dict[Any, Set[Any]]:
    """
    Build an undirected graph from a list of edges.
    
    Args:
        edges (List[Tuple[Any, Any]]): List of edge tuples (node1, node2).
        
    Returns:
        Dict[Any, Set[Any]]: Adjacency list representation of the graph.
    """
    graph: Dict[Any, Set[Any]] = {}
    
    for node1, node2 in edges:
        if node1 not in graph:
            graph[node1] = set()
        if node2 not in graph:
            graph[node2] = set()
        
        graph[node1].add(node2)
        graph[node2].add(node1)
    
    return graph


def build_directed_graph(edges: List[Tuple[Any, Any]]) -> Dict[Any, Set[Any]]:
    """
    Build a directed graph from a list of edges.
    
    Args:
        edges (List[Tuple[Any, Any]]): List of edge tuples (source, target).
        
    Returns:
        Dict[Any, Set[Any]]: Adjacency list representation of the graph.
    """
    graph: Dict[Any, Set[Any]] = {}
    
    for source, target in edges:
        if source not in graph:
            graph[source] = set()
        if target not in graph:
            graph[target] = set()
        
        graph[source].add(target)
    
    return graph


def shortest_path_bfs(
    graph: Dict[Any, Set[Any]],
    start: Any,
    end: Any
) -> Optional[List[Any]]:
    """
    Find the shortest path between two nodes using BFS.
    
    Args:
        graph (Dict[Any, Set[Any]]): Adjacency list representation of the graph.
        start (Any): Start node.
        end (Any): End node.
        
    Returns:
        Optional[List[Any]]: Shortest path as a list of nodes, or None if no path exists.
    """
    if start == end:
        return [start]
    
    if start not in graph or end not in graph:
        return None
    
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        # Sort neighbors for lexicographic tie-breaking
        neighbors = sorted(graph.get(current, []))
        
        for neighbor in neighbors:
            if neighbor == end:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None


def calculate_hop_distance(
    graph: Dict[Any, Set[Any]],
    start: Any,
    end: Any
) -> Optional[int]:
    """
    Calculate the hop distance between two nodes.
    
    Args:
        graph (Dict[Any, Set[Any]]): Adjacency list representation of the graph.
        start (Any): Start node.
        end (Any): End node.
        
    Returns:
        Optional[int]: Number of hops, or None if no path exists.
    """
    path = shortest_path_bfs(graph, start, end)
    if path is None:
        return None
    return len(path) - 1


def get_connected_components(graph: Dict[Any, Set[Any]]) -> List[Set[Any]]:
    """
    Find all connected components in an undirected graph.
    
    Args:
        graph (Dict[Any, Set[Any]]): Adjacency list representation of the graph.
        
    Returns:
        List[Set[Any]]: List of sets, each containing nodes in a connected component.
    """
    visited: Set[Any] = set()
    components: List[Set[Any]] = []
    
    for node in graph:
        if node not in visited:
            component: Set[Any] = set()
            queue = deque([node])
            
            while queue:
                current = queue.popleft()
                if current not in visited:
                    visited.add(current)
                    component.add(current)
                    
                    for neighbor in graph.get(current, []):
                        if neighbor not in visited:
                            queue.append(neighbor)
            
            components.append(component)
    
    return components


def get_hop_distribution(
    graph: Dict[Any, Set[Any]],
    nodes: List[Any]
) -> Dict[int, int]:
    """
    Calculate the distribution of hop distances between all pairs of nodes.
    
    Args:
        graph (Dict[Any, Set[Any]]): Adjacency list representation of the graph.
        nodes (List[Any]): List of nodes to consider.
        
    Returns:
        Dict[int, int]: Dictionary mapping hop distance to count.
    """
    distribution: Dict[int, int] = {}
    
    for i, node1 in enumerate(nodes):
        for node2 in nodes[i+1:]:
            distance = calculate_hop_distance(graph, node1, node2)
            if distance is not None:
                distribution[distance] = distribution.get(distance, 0) + 1
    
    return distribution


def main() -> None:
    """Main entry point for graph utilities module."""
    pass


if __name__ == "__main__":
    main()
