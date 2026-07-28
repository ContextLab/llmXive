"""
Task T013: Calculate and store structural metrics for generated network instances.

This script reads network instances saved by `generate_networks.py` (in `data/raw/networks/`),
calculates structural metrics (assortativity, average path length, clustering coefficient)
using `utils.metrics`, and saves the results as JSON files named `metrics_{seed}.json`.

Output:
    data/raw/networks/metrics_{seed}.json for each generated network instance.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List

import networkx as nx

# Import existing utility functions
from utils.metrics import (
    calculate_assortativity,
    calculate_average_path_length,
    calculate_clustering_coefficient,
    calculate_structural_metrics,
)


def load_network_from_file(network_path: Path) -> nx.Graph:
    """
    Load a NetworkX graph from a JSON file saved by `save_network`.
    The expected format is a JSON object with 'nodes' and 'edges' lists.
    """
    with open(network_path, 'r') as f:
        data = json.load(f)

    G = nx.Graph()
    G.add_nodes_from(data['nodes'])
    G.add_edges_from(data['edges'])
    return G


def calculate_metrics_for_network(G: nx.Graph, seed: int) -> Dict[str, Any]:
    """
    Calculate structural metrics for a single network instance.
    Returns a dictionary with metrics and metadata.
    """
    metrics = calculate_structural_metrics(G)

    result = {
        'seed': seed,
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'is_connected': nx.is_connected(G),
        'assortativity': metrics['assortativity'],
        'average_path_length': metrics['average_path_length'],
        'clustering_coefficient': metrics['clustering_coefficient'],
        'density': nx.density(G),
        'diameter': nx.diameter(G) if nx.is_connected(G) else None,
    }

    return result


def process_networks_directory(networks_dir: Path, output_dir: Path) -> List[Dict[str, Any]]:
    """
    Process all network JSON files in the specified directory, calculate metrics,
    and save results to individual JSON files in the output directory.
    """
    results = []

    # Find all network JSON files (excluding metrics files)
    network_files = [f for f in networks_dir.glob('network_*.json') if not f.name.startswith('metrics_')]

    if not network_files:
        print(f"No network files found in {networks_dir}")
        return results

    output_dir.mkdir(parents=True, exist_ok=True)

    for network_file in network_files:
        try:
            # Extract seed from filename: network_{seed}.json
            seed = int(network_file.stem.replace('network_', ''))

            print(f"Processing network seed {seed}...")
            G = load_network_from_file(network_file)

            metrics_result = calculate_metrics_for_network(G, seed)
            results.append(metrics_result)

            # Save metrics to individual JSON file
            metrics_file = output_dir / f"metrics_{seed}.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics_result, f, indent=2)

            print(f"  Saved metrics to {metrics_file}")

        except Exception as e:
            print(f"Error processing {network_file}: {e}")
            continue

    return results


def main():
    """
    Main entry point for calculating network metrics.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    networks_dir = project_root / 'data' / 'raw' / 'networks'
    output_dir = networks_dir  # Save metrics in same directory as networks

    if not networks_dir.exists():
        print(f"Error: Networks directory not found: {networks_dir}")
        print("Please run generate_networks.py first to create network instances.")
        return 1

    print(f"Processing networks in: {networks_dir}")
    results = process_networks_directory(networks_dir, output_dir)

    print(f"\nProcessed {len(results)} network instances.")
    print("Metrics saved to:")
    for result in results:
        print(f"  data/raw/networks/metrics_{result['seed']}.json")

    return 0


if __name__ == '__main__':
    exit(main())
