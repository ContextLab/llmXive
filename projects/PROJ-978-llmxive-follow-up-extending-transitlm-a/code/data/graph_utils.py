import json
import os
import sys
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, DefaultDict
from collections import defaultdict

# Ensure we can import from the project root if run as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_env_config


def load_processed_routes(filepath: str) -> List[Dict[str, Any]]:
    """
    Load the preprocessed routes from a JSON file.
    Expected format: List of routes, where each route is a list of station names.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed routes file not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def build_route_graph(routes: List[List[str]]) -> Dict[str, Set[str]]:
    """
    Build a local adjacency graph from a list of routes.
    Returns an adjacency list where keys are stations and values are sets of connected stations.
    Only considers consecutive stations in routes as edges.
    """
    graph: DefaultDict[str, Set[str]] = defaultdict(set)
    
    for route in routes:
        if len(route) < 2:
            continue
        
        for i in range(len(route) - 1):
            from_station = route[i]
            to_station = route[i + 1]
            
            # Add directed edges (undirected graph logic for overlap check)
            graph[from_station].add(to_station)
            graph[to_station].add(from_station)
    
    return dict(graph)


def load_ground_truth(filepath: str) -> Set[Tuple[str, str]]:
    """
    Load ground truth edges from a JSON file.
    Expected format: List of dicts with 'from', 'to', 'count'.
    Returns a set of normalized edges (tuple of sorted station names).
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    edges = set()
    for edge_data in data:
        from_st = edge_data['from']
        to_st = edge_data['to']
        # Normalize edge to be order-independent for overlap comparison
        normalized_edge = tuple(sorted([from_st, to_st]))
        edges.add(normalized_edge)
    
    return edges


def compute_edge_overlap(
    built_graph: Dict[str, Set[str]], 
    ground_truth_edges: Set[Tuple[str, str]]
) -> float:
    """
    Compute the edge overlap percentage between the built graph and ground truth.
    Overlap = (Number of edges in built graph that exist in ground truth) / (Total unique edges in built graph)
    Note: If built graph has 0 edges, returns 0.0.
    """
    built_edges = set()
    for from_st, to_sts in built_graph.items():
        for to_st in to_sts:
            normalized = tuple(sorted([from_st, to_st]))
            built_edges.add(normalized)
    
    if len(built_edges) == 0:
        return 0.0
    
    overlapping_edges = built_edges.intersection(ground_truth_edges)
    overlap_ratio = len(overlapping_edges) / len(built_edges)
    
    return overlap_ratio


def validate_graph_against_ground_truth(
    routes: List[List[str]], 
    ground_truth_path: str, 
    threshold: float = 0.95
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate the graph built from routes against ground truth.
    Returns a tuple of (is_valid, details_dict).
    is_valid is True if overlap >= threshold.
    """
    built_graph = build_route_graph(routes)
    ground_truth_edges = load_ground_truth(ground_truth_path)
    
    overlap = compute_edge_overlap(built_graph, ground_truth_edges)
    
    # Count unique edges in built graph for reporting
    built_edges = set()
    for from_st, to_sts in built_graph.items():
        for to_st in to_sts:
            normalized = tuple(sorted([from_st, to_st]))
            built_edges.add(normalized)
    
    overlapping_edges = built_edges.intersection(ground_truth_edges)
    
    details = {
        "total_built_edges": len(built_edges),
        "total_ground_truth_edges": len(ground_truth_edges),
        "overlapping_edges": len(overlapping_edges),
        "overlap_ratio": overlap,
        "threshold": threshold,
        "is_valid": overlap >= threshold
    }
    
    return details["is_valid"], details


def compute_path_betweenness_centrality(
    routes: List[List[str]], 
    graph: Optional[Dict[str, Set[str]]] = None
) -> Dict[str, float]:
    """
    Compute betweenness centrality for nodes based on the routes provided.
    This is a simplified version that counts how many routes pass through each node
    as an intermediate node (not start or end).
    
    For a more rigorous betweenness centrality, we would compute shortest paths,
    but given the context of transit routes, counting route passages is a valid proxy.
    """
    if graph is None:
        graph = build_route_graph(routes)
    
    centrality: DefaultDict[str, float] = defaultdict(float)
    total_routes = len(routes)
    
    if total_routes == 0:
        return {}
    
    for route in routes:
        if len(route) < 3:
            continue
        
        # Count intermediate nodes
        for i in range(1, len(route) - 1):
            node = route[i]
            centrality[node] += 1.0
    
    # Normalize by total routes
    normalized_centrality = {
        node: count / total_routes for node, count in centrality.items()
    }
    
    return normalized_centrality


def compute_route_complexity_metrics(
    routes: List[List[str]]
) -> List[Dict[str, Any]]:
    """
    Compute topological complexity metrics for each route.
    Returns a list of dicts with route index, length, and complexity score.
    Complexity score is defined as: (route_length - 1) * betweenness_sum_of_intermediate_nodes
    """
    # First compute betweenness centrality for all nodes
    centrality = compute_path_betweenness_centrality(routes)
    
    metrics = []
    for idx, route in enumerate(routes):
        length = len(route)
        if length < 2:
            metrics.append({
                "route_index": idx,
                "length": length,
                "complexity_score": 0.0,
                "intermediate_nodes": []
            })
            continue
        
        # Sum betweenness of intermediate nodes
        intermediate_nodes = route[1:-1]
        betweenness_sum = sum(centrality.get(node, 0.0) for node in intermediate_nodes)
        
        # Complexity score: number of hops * average betweenness of intermediates
        hops = length - 1
        if hops > 0:
            avg_betweenness = betweenness_sum / hops if hops > 0 else 0.0
            complexity_score = hops * avg_betweenness
        else:
            complexity_score = 0.0
        
        metrics.append({
            "route_index": idx,
            "length": length,
            "complexity_score": complexity_score,
            "intermediate_nodes": intermediate_nodes
        })
    
    return metrics


def compute_topological_metrics_for_all_routes(
    routes: List[List[str]], 
    output_path: str
) -> Dict[str, Any]:
    """
    Compute and save topological metrics for all routes.
    Returns the summary metrics dict.
    """
    graph = build_route_graph(routes)
    centrality = compute_path_betweenness_centrality(routes)
    route_metrics = compute_route_complexity_metrics(routes)
    
    # Compute summary statistics
    avg_length = sum(m["length"] for m in route_metrics) / len(route_metrics) if route_metrics else 0.0
    max_length = max(m["length"] for m in route_metrics) if route_metrics else 0
    min_length = min(m["length"] for m in route_metrics) if route_metrics else 0
    
    avg_complexity = sum(m["complexity_score"] for m in route_metrics) / len(route_metrics) if route_metrics else 0.0
    
    summary = {
        "total_routes": len(routes),
        "avg_route_length": avg_length,
        "max_route_length": max_length,
        "min_route_length": min_length,
        "avg_complexity_score": avg_complexity,
        "num_unique_stations": len(graph),
        "num_unique_edges": len(set(tuple(sorted([a, b])) for a, bs in graph.items() for b in bs)),
        "route_metrics": route_metrics
    }
    
    # Save to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary


def save_topological_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save topological metrics to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def load_topological_metrics(filepath: str) -> Dict[str, Any]:
    """Load topological metrics from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Topological metrics file not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def integrate_topological_metrics(
    route_metrics: List[Dict[str, Any]], 
    output_path: str
) -> None:
    """
    Integrate topological metrics with route data and save.
    This is a placeholder for future integration with model predictions.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(route_metrics, f, indent=2, ensure_ascii=False)


def main():
    """
    Main function to run the graph validation pipeline.
    This script expects:
    1. Preprocessed routes at data/processed/stratified_routes.json (from T006)
    2. Ground truth at data/raw/transitlm_ground_truth.json
    
    It will:
    - Build the adjacency graph from routes
    - Validate against ground truth (>=95% overlap)
    - Save topological metrics
    - Print validation result
    """
    config = get_env_config()
    
    processed_routes_path = Path(config.PROCESSED_ROUTES_PATH)
    ground_truth_path = Path(config.GROUND_TRUTH_PATH)
    topological_metrics_path = Path(config.TOPOLOGICAL_METRICS_PATH)
    
    print(f"Loading processed routes from: {processed_routes_path}")
    routes = load_processed_routes(str(processed_routes_path))
    print(f"Loaded {len(routes)} routes.")
    
    print(f"Loading ground truth from: {ground_truth_path}")
    is_valid, details = validate_graph_against_ground_truth(
        routes, 
        str(ground_truth_path), 
        threshold=0.95
    )
    
    print("\n=== Graph Validation Results ===")
    print(f"Total built edges: {details['total_built_edges']}")
    print(f"Total ground truth edges: {details['total_ground_truth_edges']}")
    print(f"Overlapping edges: {details['overlapping_edges']}")
    print(f"Overlap ratio: {details['overlap_ratio']:.4f} ({details['overlap_ratio']*100:.2f}%)")
    print(f"Threshold: {details['threshold']}")
    print(f"Validation PASSED: {details['is_valid']}")
    
    if not details['is_valid']:
        print("WARNING: Graph validation FAILED. Overlap is below 95%.")
        sys.exit(1)
    
    print("\nComputing topological metrics...")
    summary = compute_topological_metrics_for_all_routes(routes, str(topological_metrics_path))
    print(f"Topological metrics saved to: {topological_metrics_path}")
    print(f"Average route length: {summary['avg_route_length']:.2f}")
    print(f"Average complexity score: {summary['avg_complexity_score']:.4f}")
    
    print("\nGraph validation and metric computation completed successfully.")


if __name__ == "__main__":
    main()
