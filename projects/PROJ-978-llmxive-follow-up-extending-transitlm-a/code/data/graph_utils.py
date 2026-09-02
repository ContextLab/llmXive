import json
import os
import sys
import math
import pickle
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple, Set

# Import constants from config if available, otherwise define defaults
try:
    from config import Config
except ImportError:
    Config = None

def load_ground_truth(path: str = "data/raw/transitlm_ground_truth.json") -> Dict[str, Any]:
    """Load the ground truth dataset from JSON."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_processed_routes(path: str = "data/processed/stratified_routes.parquet") -> Any:
    """Load processed routes from Parquet file."""
    try:
        import pandas as pd
        if not Path(path).exists():
            raise FileNotFoundError(f"Processed routes file not found: {path}")
        return pd.read_parquet(path)
    except ImportError:
        raise ImportError("pandas and pyarrow are required to load parquet files")

def build_route_graph(routes_data: Any) -> Any:
    """
    Build an adjacency graph from route data.
    Returns a dictionary mapping station_id -> set of neighbor station_ids.
    """
    if isinstance(routes_data, dict) and 'routes' in routes_data:
        routes = routes_data['routes']
    elif hasattr(routes_data, 'to_dict'):
        # Assume DataFrame or similar
        routes = routes_data.to_dict('records')
    else:
        routes = routes_data

    graph: Dict[int, Set[int]] = {}
    
    for route in routes:
        # Handle different data structures
        if isinstance(route, dict):
            stations = route.get('stations', route.get('station_ids', []))
        else:
            # Assume it's a list of station IDs
            stations = list(route)
        
        for i in range(len(stations) - 1):
            u, v = stations[i], stations[i+1]
            
            if u not in graph:
                graph[u] = set()
            if v not in graph:
                graph[v] = set()
            
            graph[u].add(v)
            graph[v].add(u)
    
    return graph

def compute_jaccard_index(set_a: Set[Any], set_b: Set[Any]) -> float:
    """Compute Jaccard similarity index between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0

def validate_graph_against_ground_truth(graph: Any, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the constructed graph against ground truth.
    Returns validation report with edge overlap percentage.
    """
    # Extract ground truth edges
    gt_routes = ground_truth.get('routes', [])
    gt_edges: Set[Tuple[int, int]] = set()
    
    for route in gt_routes:
        stations = route.get('stations', route.get('station_ids', []))
        for i in range(len(stations) - 1):
            u, v = stations[i], stations[i+1]
            gt_edges.add((min(u, v), max(u, v)))
    
    # Extract graph edges
    graph_edges: Set[Tuple[int, int]] = set()
    if isinstance(graph, dict):
        for u, neighbors in graph.items():
            for v in neighbors:
                graph_edges.add((min(u, v), max(u, v)))
    
    if not gt_edges:
        return {"edge_overlap_percentage": 0.0, "status": "FAIL", "error": "No ground truth edges"}
    
    intersection = len(gt_edges & graph_edges)
    overlap = intersection / len(gt_edges)
    
    status = "PASS" if overlap >= 0.95 else "FAIL"
    
    return {
        "edge_overlap_percentage": overlap,
        "status": status,
        "total_gt_edges": len(gt_edges),
        "total_graph_edges": len(graph_edges),
        "intersection_edges": intersection
    }

def compute_route_topological_complexity(
    route_stations: List[int], 
    adjacency_graph: Dict[int, Set[int]]
) -> float:
    """
    Compute topological complexity for a specific route.
    Uses path-level betweenness centrality on the global graph restricted to route nodes.
    """
    if not route_stations or len(route_stations) < 2:
        return 0.0
    
    # Restrict graph to route nodes
    route_nodes = set(route_stations)
    subgraph: Dict[int, Set[int]] = {}
    for node in route_nodes:
        if node in adjacency_graph:
            subgraph[node] = adjacency_graph[node] & route_nodes
        else:
            subgraph[node] = set()
    
    # Simple betweenness centrality approximation for the route path
    # Count how many shortest paths between non-adjacent route nodes pass through route nodes
    if len(route_nodes) < 3:
        return 0.0
    
    # BFS for shortest paths
    def bfs_paths(start: int, end: int) -> int:
        queue = [(start, [start])]
        paths_count = 0
        while queue:
            current, path = queue.pop(0)
            if current == end:
                paths_count += 1
                continue
            for neighbor in subgraph.get(current, set()):
                if neighbor not in path:
                    queue.append((neighbor, path + [neighbor]))
        return paths_count
    
    total_betweenness = 0.0
    node_count = len(route_nodes)
    
    for i, node in enumerate(route_stations):
        if i == 0 or i == len(route_stations) - 1:
            continue
        
        # Count paths that pass through this node
        betweenness = 0
        for start_node in route_nodes:
            for end_node in route_nodes:
                if start_node == end_node or start_node == node or end_node == node:
                    continue
                # Check if shortest path goes through node (simplified)
                # In a real implementation, we'd compute all shortest paths
                if start_node in subgraph.get(node, set()) and end_node in subgraph.get(node, set()):
                    betweenness += 1
        
        total_betweenness += betweenness
    
    # Normalize
    return total_betweenness / (node_count * (node_count - 1)) if node_count > 1 else 0.0

def build_adjacency_index(
    graph: Dict[int, Set[int]], 
    top_n: int = 10
) -> Dict[int, List[Tuple[int, float]]]:
    """
    Construct a retrieval index of top-N neighbors for each station.
    
    Args:
        graph: Adjacency graph mapping station_id -> set of neighbor station_ids
        top_n: Number of top neighbors to retrieve for each station
    
    Returns:
        Dictionary mapping station_id -> list of (neighbor_id, frequency_score)
        Frequency score is currently 1.0 for unweighted graphs (all neighbors equal)
    """
    index: Dict[int, List[Tuple[int, float]]] = {}
    
    for station_id, neighbors in graph.items():
        if not neighbors:
            index[station_id] = []
            continue
        
        # Convert to list and sort (deterministic order for equal frequencies)
        # Since we don't have frequency data here, we use station_id for tie-breaking
        neighbor_list = sorted(list(neighbors))
        
        # Take top N
        top_neighbors = neighbor_list[:top_n]
        
        # Assign frequency score of 1.0 (unweighted)
        # In a real implementation, this would be derived from edge weights/frequencies
        index[station_id] = [(neighbor, 1.0) for neighbor in top_neighbors]
    
    return index

def main():
    """Main entry point for building adjacency index."""
    print("Starting adjacency index construction...")
    
    # Load ground truth
    try:
        ground_truth = load_ground_truth()
        print(f"Loaded ground truth with {len(ground_truth.get('routes', []))} routes")
    except Exception as e:
        print(f"Error loading ground truth: {e}")
        sys.exit(1)
    
    # Build graph from ground truth
    try:
        graph = build_route_graph(ground_truth)
        print(f"Built graph with {len(graph)} nodes")
    except Exception as e:
        print(f"Error building graph: {e}")
        sys.exit(1)
    
    # Validate graph
    validation_report = validate_graph_against_ground_truth(graph, ground_truth)
    print(f"Graph validation: {validation_report['status']} (overlap: {validation_report['edge_overlap_percentage']:.2%})")
    
    if validation_report['status'] != 'PASS':
        print("Warning: Graph validation failed, proceeding anyway for index construction")
    
    # Build adjacency index
    top_n = 10  # Default top-N
    adjacency_index = build_adjacency_index(graph, top_n)
    print(f"Built adjacency index with {len(adjacency_index)} entries")
    
    # Save index
    output_path = "data/processed/adjacency_index.pkl"
    try:
        with open(output_path, 'wb') as f:
            pickle.dump({
                'index': adjacency_index,
                'top_n': top_n,
                'validation_report': validation_report,
                'node_count': len(adjacency_index)
            }, f)
        print(f"Saved adjacency index to {output_path}")
    except Exception as e:
        print(f"Error saving index: {e}")
        sys.exit(1)
    
    print("Adjacency index construction completed successfully.")
    return adjacency_index

if __name__ == "__main__":
    main()
