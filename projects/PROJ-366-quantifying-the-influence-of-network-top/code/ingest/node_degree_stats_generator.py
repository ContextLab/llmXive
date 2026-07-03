"""
Node degree statistics generator for aggregated graph analysis.

This module computes global statistics across multiple graphs to
understand the typical coordination environment in amorphous silicon.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List
from collections import Counter

logger = logging.getLogger(__name__)

def load_graphs(graph_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all graph files from a directory.
    
    Args:
        graph_dir: Directory containing graph files
        
    Returns:
        List of graph dictionaries
    """
    graphs = []
    
    # Load JSON files
    for json_file in graph_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            graphs.append(json.load(f))
    
    # Load pickle files
    for pickle_file in graph_dir.glob("*.pkl"):
        with open(pickle_file, 'rb') as f:
            graphs.append(pickle.load(f))
    
    logger.info(f"Loaded {len(graphs)} graphs from {graph_dir}")
    return graphs

def calculate_global_degree_distribution(graphs: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Calculate the global degree distribution across all graphs.
    
    Args:
        graphs: List of graph dictionaries
        
    Returns:
        Dictionary mapping degree to count
    """
    all_degrees = []
    
    for graph in graphs:
        edges = graph.get("edges", [])
        nodes = graph.get("nodes", [])
        n_nodes = len(nodes) if nodes else graph.get("metadata", {}).get("n_nodes", 0)
        
        if n_nodes == 0:
            continue
        
        # Calculate degrees
        degrees = [0] * n_nodes
        for edge in edges:
            i, j = edge[0], edge[1]
            if i < n_nodes and j < n_nodes:
                degrees[i] += 1
                degrees[j] += 1
        
        all_degrees.extend(degrees)
    
    return dict(Counter(all_degrees))

def compute_mode_and_stats(degree_distribution: Dict[int, int]) -> Dict[str, Any]:
    """
    Compute mode and summary statistics from degree distribution.
    
    Args:
        degree_distribution: Dictionary mapping degree to count
        
    Returns:
        Dictionary with mode, mean, std, min, max
    """
    if not degree_distribution:
        return {
            "mode": 0,
            "mean": 0.0,
            "std": 0.0,
            "min": 0,
            "max": 0,
            "total_nodes": 0
        }
    
    # Expand distribution to list of degrees
    degrees = []
    for deg, count in degree_distribution.items():
        degrees.extend([deg] * count)
    
    total_nodes = len(degrees)
    mode = Counter(degrees).most_common(1)[0][0]
    mean = sum(degrees) / total_nodes
    variance = sum((d - mean) ** 2 for d in degrees) / total_nodes
    std = variance ** 0.5
    
    return {
        "mode": mode,
        "mean": float(mean),
        "std": float(std),
        "min": min(degrees),
        "max": max(degrees),
        "total_nodes": total_nodes
    }

def main():
    """Main entry point for statistics generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate node degree statistics")
    parser.add_argument("--input", type=Path, required=True, help="Input directory with graph files")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON file for statistics")
    
    args = parser.parse_args()
    
    # Load graphs
    graphs = load_graphs(args.input)
    
    if not graphs:
        logger.error("No graphs found in input directory")
        return
    
    # Calculate global distribution
    global_dist = calculate_global_degree_distribution(graphs)
    
    # Compute stats
    stats = compute_mode_and_stats(global_dist)
    stats["degree_distribution"] = global_dist
    
    # Save output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved statistics to {args.output}")
    logger.info(f"Mode: {stats['mode']}, Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")

if __name__ == "__main__":
    main()
