"""
Metrics calculation module for the llmXive follow-up project.
"""
import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import networkx as nx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_graph_from_json(file_path: Path) -> nx.DiGraph:
    """Load a graph from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    G = nx.DiGraph()
    G.add_nodes_from(data.get('nodes', []))
    G.add_edges_from(data.get('edges', []))
    return G

def calculate_global_connectivity(G: nx.DiGraph) -> float:
    """Calculate global connectivity (edges / possible edges)."""
    n = G.number_of_nodes()
    if n < 2:
        return 0.0
    possible_edges = n * (n - 1) / 2
    actual_edges = G.number_of_edges()
    if possible_edges == 0:
        return 0.0
    return actual_edges / possible_edges

def calculate_average_branching_factor(G: nx.DiGraph) -> float:
    """Calculate average branching factor (sum(out-degrees) / N)."""
    n = G.number_of_nodes()
    if n == 0:
        return 0.0
    total_out_degree = sum(d for n, d in G.out_degree())
    return total_out_degree / n

def process_batch(graphs_dir: Path, output_file: Path):
    """Process all graphs in a directory and write metrics to CSV."""
    graphs_dir = Path(graphs_dir)
    output_file = Path(output_file)
    
    results = []
    
    # Get all JSON files in the directory
    graph_files = list(graphs_dir.glob("*.json"))
    
    if not graph_files:
        logger.warning(f"No JSON files found in {graphs_dir}")
        # Write empty CSV with headers
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['trajectory_id', 'global_connectivity', 'avg_branching_factor'])
            writer.writeheader()
        return

    for graph_file in graph_files:
        traj_id = graph_file.stem
        try:
            G = load_graph_from_json(graph_file)
            connectivity = calculate_global_connectivity(G)
            branching = calculate_average_branching_factor(G)
            
            results.append({
                'trajectory_id': traj_id,
                'global_connectivity': connectivity,
                'avg_branching_factor': branching
            })
        except Exception as e:
            logger.error(f"Error processing {graph_file}: {e}")
            continue
    
    # Write results to CSV
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['trajectory_id', 'global_connectivity', 'avg_branching_factor']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Wrote {len(results)} rows to {output_file}")

def main():
    """Main entry point for metrics calculation."""
    graphs_dir = Path("data/processed/graphs")
    output_file = Path("data/processed/metrics.csv")
    process_batch(graphs_dir, output_file)

if __name__ == "__main__":
    main()
