"""
Serialization module for network ensembles.

This module handles the serialization of generated network instances and their
associated structural metrics to disk, including the generation of SHA-256
checksums for data integrity verification (Principle V).

Dependencies:
    - code/generate_networks.py (for network generation logic if needed, though
      this module focuses on saving existing objects)
    - code/utils/metrics.py (for metric calculation if not pre-calculated)
    - code/utils/checksums.py (for SHA-256 generation)
"""
import os
import json
import hashlib
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional

import networkx as nx
import numpy as np

# Import from project utilities
from utils.checksums import calculate_sha256
from utils.metrics import calculate_structural_metrics


def serialize_network_to_graphml(graph: nx.Graph, output_path: Path) -> None:
    """
    Serialize a NetworkX graph to GraphML format.

    Args:
        graph: The NetworkX graph instance to serialize.
        output_path: The file path where the GraphML file will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, str(output_path))


def serialize_metrics_to_json(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Serialize a dictionary of metrics to a JSON file.

    Args:
        metrics: The dictionary containing structural metrics.
        output_path: The file path where the JSON file will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, default=str)


def process_and_serialize_networks(
    networks: List[nx.Graph],
    seeds: List[int],
    topology_types: List[str],
    base_output_dir: Path,
    metrics_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Process a list of network instances, calculate metrics, and serialize them.

    This function performs the following steps for each network:
    1. Ensures the network is connected (or handles components).
    2. Calculates structural metrics (assortativity, path length, etc.).
    3. Saves the network as a GraphML file.
    4. Saves the metrics as a JSON file.
    5. Generates a checksum for both files.

    Args:
        networks: List of NetworkX graph instances.
        seeds: List of integer seeds corresponding to each network.
        topology_types: List of string topology type names (e.g., 'erdos_renyi').
        base_output_dir: Root directory for saving network files.
        metrics_dir: Optional specific directory for metrics. If None, uses base_output_dir/metrics.

    Returns:
        A list of dictionaries containing metadata about the serialized files and checksums.
    """
    if len(networks) != len(seeds) or len(networks) != len(topology_types):
        raise ValueError("networks, seeds, and topology_types must have the same length.")

    if metrics_dir is None:
        metrics_dir = base_output_dir / "metrics"

    base_output_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    serialized_manifest = []

    for i, (graph, seed, topology) in enumerate(zip(networks, seeds, topology_types)):
        # Define file paths
        graph_filename = f"network_{topology}_seed_{seed}.graphml"
        metrics_filename = f"metrics_{seed}.json"
        checksum_filename = f"checksums_{seed}.json"

        graph_path = base_output_dir / graph_filename
        metrics_path = metrics_dir / metrics_filename
        checksum_path = base_output_dir / checksum_filename

        # 1. Calculate metrics (re-using logic from T013/T005)
        # Note: T013 logic is assumed to be in utils.metrics or similar, but we re-calculate
        # here to ensure the saved JSON is fresh and consistent with the saved graph.
        # We use the calculate_structural_metrics from utils.metrics as per API surface.
        # However, utils.metrics.calculate_structural_metrics expects a graph.
        try:
            # Calculate metrics for the largest connected component if disconnected
            if not nx.is_connected(graph):
                # For disconnected graphs, we analyze the largest component for global metrics
                # but note this in the metadata
                largest_cc = max(nx.connected_components(graph), key=len)
                subgraph = graph.subgraph(largest_cc).copy()
                metrics = calculate_structural_metrics(subgraph)
                metrics['is_connected'] = False
                metrics['largest_component_size'] = len(largest_cc)
                metrics['total_nodes'] = graph.number_of_nodes()
            else:
                metrics = calculate_structural_metrics(graph)
                metrics['is_connected'] = True
                metrics['largest_component_size'] = graph.number_of_nodes()
                metrics['total_nodes'] = graph.number_of_nodes()
        except Exception as e:
            # Fallback for specific metric calculation errors (e.g., isolated nodes in assortativity)
            metrics = {
                'error': str(e),
                'is_connected': nx.is_connected(graph) if graph.number_of_nodes() > 1 else True,
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges()
            }
            metrics['total_nodes'] = metrics['nodes']
            metrics['largest_component_size'] = metrics['nodes']

        # Add metadata
        metrics['seed'] = seed
        metrics['topology'] = topology
        metrics['filename'] = graph_filename

        # 2. Serialize Network to GraphML
        serialize_network_to_graphml(graph, graph_path)

        # 3. Serialize Metrics to JSON
        serialize_metrics_to_json(metrics, metrics_path)

        # 4. Generate Checksums
        graph_checksum = calculate_sha256(graph_path)
        metrics_checksum = calculate_sha256(metrics_path)

        checksum_data = {
            'seed': seed,
            'topology': topology,
            'files': {
                'graph': {
                    'path': str(graph_path),
                    'checksum': graph_checksum
                },
                'metrics': {
                    'path': str(metrics_path),
                    'checksum': metrics_checksum
                }
            }
        }

        # Save checksums to a local JSON file for this seed
        with open(checksum_path, 'w', encoding='utf-8') as f:
            json.dump(checksum_data, f, indent=2)

        # Add to manifest
        serialized_manifest.append(checksum_data)

    return serialized_manifest


def main():
    """
    Main entry point for the serialization script.

    This function is intended to be called after network generation (T012)
    and metric calculation (T013) logic is available. It assumes that
    network objects and their seeds are available in memory or loaded from
    a temporary state. For the purpose of this task, we demonstrate the
    serialization logic by generating a small set of networks on the fly
    to ensure the output files are created as required by T014.
    """
    import random
    from generate_networks import set_global_seed, generate_erdos_renyi, generate_barabasi_albert, generate_watts_strogatz

    print("Starting network serialization process (T014)...")

    # Configuration for demonstration
    # In a full pipeline, these would be loaded from the previous step's output
    num_instances = 3
    n_nodes = 500
    base_seed = 42

    # Directories
    output_dir = Path("data/raw/networks")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate a small set of networks to demonstrate serialization
    # This ensures we have real data to serialize, not just a stub
    networks = []
    seeds = []
    types = []

    for i in range(num_instances):
        seed = base_seed + i
        set_global_seed(seed)
        topo_type = ['erdos_renyi', 'barabasi_albert', 'watts_strogatz'][i % 3]

        if topo_type == 'erdos_renyi':
            g = generate_erdos_renyi(n=n_nodes, p=0.01, seed=seed)
        elif topo_type == 'barabasi_albert':
            g = generate_barabasi_albert(n=n_nodes, m=3, seed=seed)
        else:
            g = generate_watts_strogatz(n=n_nodes, k=4, p=0.1, seed=seed)

        networks.append(g)
        seeds.append(seed)
        types.append(topo_type)

    # Process and serialize
    manifest = process_and_serialize_networks(
        networks=networks,
        seeds=seeds,
        topology_types=types,
        base_output_dir=output_dir
    )

    # Save the master manifest
    manifest_path = output_dir / "serialization_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"Successfully serialized {len(manifest)} networks to {output_dir}")
    print(f"Manifest saved to {manifest_path}")
    print("Checksums generated for all files.")


if __name__ == "__main__":
    main()
