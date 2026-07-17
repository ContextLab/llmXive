"""
Graph utilities for the llmXive pipeline.

Provides Breadth-First Search (BFS) based shortest path logic
for unweighted graphs, handling disconnected components gracefully.
"""
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Type alias for graph representation: Node -> List of Neighbors
Graph = Dict[Any, List[Any]]


def build_undirected_graph(edges: List[Tuple[Any, Any]]) -> Graph:
    """
    Builds an undirected graph from a list of edge tuples.
    
    Args:
        edges: List of (source, target) tuples.
    
    Returns:
        A dictionary mapping each node to a list of its neighbors.
    """
    graph: Graph = {}
    
    for src, tgt in edges:
        if src not in graph:
            graph[src] = []
        if tgt not in graph:
            graph[tgt] = []
        
        # Avoid duplicate edges if the input contains them
        if tgt not in graph[src]:
            graph[src].append(tgt)
        if src not in graph[tgt]:
            graph[tgt].append(src)
    
    return graph


def build_directed_graph(edges: List[Tuple[Any, Any]]) -> Graph:
    """
    Builds a directed graph from a list of edge tuples.
    
    Args:
        edges: List of (source, target) tuples.
    
    Returns:
        A dictionary mapping each node to a list of its outgoing neighbors.
    """
    graph: Graph = {}
    
    for src, tgt in edges:
        if src not in graph:
            graph[src] = []
        if tgt not in graph:
            graph[tgt] = [] # Ensure targets exist as keys even if they have no outgoing edges
        
        if tgt not in graph[src]:
            graph[src].append(tgt)
    
    return graph


def shortest_path_bfs(
    graph: Graph,
    start: Any,
    end: Any
) -> Tuple[Optional[List[Any]], int]:
    """
    Finds the shortest path between two nodes in an unweighted graph using BFS.
    
    Handles disconnected graphs by returning (None, -1) if no path exists
    or if either node is missing from the graph.
    
    Args:
        graph: The graph dictionary (Node -> List[Neighbors]).
        start: The starting node.
        end: The target node.
    
    Returns:
        A tuple (path, distance):
            - path: A list of nodes representing the shortest path, or None if no path exists.
            - distance: The number of edges in the path, or -1 if no path exists.
    """
    # Handle edge cases
    if start not in graph or end not in graph:
        return None, -1
    
    if start == end:
        return [start], 0
    
    # BFS initialization
    queue: deque = deque([(start, [start])])
    visited: Set[Any] = {start}
    
    while queue:
        current_node, path = queue.popleft()
        
        # Explore neighbors
        neighbors = graph.get(current_node, [])
        for neighbor in neighbors:
            if neighbor == end:
                final_path = path + [neighbor]
                return final_path, len(final_path) - 1
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    # No path found (disconnected components)
    return None, -1


def calculate_hop_distance(
    graph: Graph,
    start: Any,
    end: Any
) -> int:
    """
    Calculates the shortest hop distance between two nodes.
    
    Convenience wrapper around `shortest_path_bfs` that returns only the distance.
    
    Args:
        graph: The graph dictionary.
        start: The starting node.
        end: The target node.
    
    Returns:
        The number of hops (edges) between start and end, or -1 if disconnected.
    """
    _, distance = shortest_path_bfs(graph, start, end)
    return distance


def get_connected_components(graph: Graph) -> List[Set[Any]]:
    """
    Identifies all connected components in the graph.
    
    Treats the graph as undirected for this operation (ignores edge direction).
    
    Args:
        graph: The graph dictionary.
    
    Returns:
        A list of sets, where each set contains the nodes of a connected component.
    """
    visited: Set[Any] = set()
    components: List[Set[Any]] = []
    
    # Ensure we check every node, even isolated ones
    all_nodes = set(graph.keys())
    
    for node in all_nodes:
        if node not in visited:
            component: Set[Any] = set()
            stack = [node]
            
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    component.add(current)
                    
                    # Add neighbors (treating as undirected)
                    # Note: In a directed graph stored as adjacency list, 
                    # we only traverse outgoing edges here. 
                    # If true undirected connectivity is needed on a directed graph,
                    # we would need to build a reverse map or traverse both ways.
                    # For standard "connected components" on directed graphs, 
                    # we usually mean "weakly connected components" (ignoring direction).
                    
                    neighbors = graph.get(current, [])
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            stack.append(neighbor)
                    
                    # Also check incoming edges if we want strict weak connectivity
                    # and the graph is directed. Since our Graph type is just Node->List,
                    # we assume the input graph for this function is already undirected
                    # or we are only checking reachability in the provided direction.
                    # To be safe for "disconnected graphs" in the context of BFS,
                    # we assume the graph passed is the undirected version built by build_undirected_graph.
            
            components.append(component)
    
    return components

def get_hop_distribution(
    graph: Graph,
    start_nodes: List[Any],
    end_nodes: List[Any]
) -> Dict[int, int]:
    """
    Calculates the distribution of shortest path distances between pairs of nodes.
    
    Args:
        graph: The graph dictionary.
        start_nodes: List of starting nodes.
        end_nodes: List of target nodes.
    
    Returns:
        A dictionary mapping hop distance -> count of pairs with that distance.
        Distances of -1 (disconnected) are excluded from the distribution.
    """
    distribution: Dict[int, int] = {}
    
    # Assuming 1:1 pairing or iterating all pairs? 
    # Based on typical usage (e.g., question entities to answer entities), 
    # we assume parallel lists or specific pairs. 
    # Here we implement 1:1 pairing if lengths match, else warn.
    if len(start_nodes) != len(end_nodes):
        raise ValueError("start_nodes and end_nodes must have the same length for 1:1 pairing.")
    
    for src, tgt in zip(start_nodes, end_nodes):
        dist = calculate_hop_distance(graph, src, tgt)
        if dist != -1:
            distribution[dist] = distribution.get(dist, 0) + 1
    
    return distribution