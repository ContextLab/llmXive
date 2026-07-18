import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import networkx as nx
from tqdm import tqdm

def load_graph_from_json(file_path: str) -> nx.DiGraph:
    """Load a NetworkX DiGraph from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    G = nx.DiGraph()
    if 'nodes' in data:
        G.add_nodes_from(data['nodes'])
    if 'edges' in data:
        G.add_edges_from(data['edges'])
    return G

def calculate_global_connectivity(G: nx.DiGraph) -> float:
    """
    Calculate normalized Global Connectivity.
    Formula: edges / (N * (N-1))
    Returns 0.0 if N < 2 to avoid division by zero.
    """
    n = G.number_of_nodes()
    if n < 2:
        return 0.0
    num_edges = G.number_of_edges()
    max_edges = n * (n - 1)
    if max_edges == 0:
        return 0.0
    return num_edges / max_edges

def calculate_avg_branching_factor(G: nx.DiGraph) -> float:
    """
    Calculate Average Branching Factor.
    Formula: sum of out-degrees / node count.
    Returns 0.0 if node count is 0.
    """
    n = G.number_of_nodes()
    if n == 0:
        return 0.0
    total_out_degree = sum(d for n, d in G.out_degree())
    return total_out_degree / n

def process_batch(graph_dir: str, output_path: str) -> None:
    """
    Iterate over JSON files in graph_dir, calculate metrics, and write to output_path CSV.
    Includes progress logging using tqdm.
    """
    graph_path = Path(graph_dir)
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph directory not found: {graph_dir}")

    json_files = list(graph_path.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found in {graph_dir}")

    results = []
    
    # Use tqdm to log batch processing progress
    for file_path in tqdm(json_files, desc="Processing graphs"):
        try:
            G = load_graph_from_json(str(file_path))
            connectivity = calculate_global_connectivity(G)
            branching = calculate_avg_branching_factor(G)
            
            results.append({
                'filename': file_path.name,
                'connectivity': connectivity,
                'branching_factor': branching
            })
        except Exception as e:
            # Log error but continue processing other files
            tqdm.write(f"Error processing {file_path.name}: {e}")

    # Write results to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['filename', 'connectivity', 'branching_factor']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    """Entry point for running the metrics calculation batch process."""
    from config import ensure_directories
    ensure_directories()
    
    graph_dir = "data/processed/graphs"
    output_path = "data/processed/metrics.csv"
    
    print(f"Starting batch processing of graphs in {graph_dir}...")
    process_batch(graph_dir, output_path)
    print(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    main()