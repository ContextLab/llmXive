"""
Network Feature Engineering Module.

This module computes network-based features for misinformation cascades.
All features are derived from pre-cascade historical network context to avoid circularity.

Input Sources:
  - Historical network files (JSON) specified in --input
  - Cascade data (JSON) specified in --cascade

Transformation Steps:
  1. Load historical network structures
  2. Extract cascade nodes
  3. Compute degree distribution moments (mean, variance, skewness)
  4. Compute clustering coefficient
  5. Compute mean betweenness centrality
  6. Aggregate features per cascade

Output Files:
  - Intermediate network features CSV (specified in --output)
  - Logs written to pipeline.log
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import networkx as nx

from pipeline.utils import set_global_seed, setup_logger


def load_historical_networks(network_paths: list) -> dict:
    """
    Load historical network graphs from JSON files.

    Args:
        network_paths: List of paths to JSON network files.

    Returns:
        Dictionary mapping user_id to networkx Graph object.
    """
    networks = {}
    for path in network_paths:
        with open(path, 'r') as f:
            data = json.load(f)
            # Assume JSON format: {"nodes": [...], "edges": [...]}
            G = nx.Graph()
            G.add_nodes_from(data.get('nodes', []))
            G.add_edges_from(data.get('edges', []))
            # Store under a representative ID or path hash if needed
            networks[path] = G
    return networks


def compute_degree_moments(G: nx.Graph) -> dict:
    """
    Compute moments of the degree distribution.

    Args:
        G: Networkx graph.

    Returns:
        Dictionary with mean, variance, and skewness of degrees.
    """
    degrees = [d for n, d in G.degree()]
    if not degrees:
        return {'mean_degree': 0.0, 'var_degree': 0.0, 'skew_degree': 0.0}

    mean_deg = np.mean(degrees)
    var_deg = np.var(degrees)
    skew_deg = 0.0
    if var_deg > 0:
        skew_deg = np.mean(((np.array(degrees) - mean_deg) / np.sqrt(var_deg)) ** 3)

    return {
        'mean_degree': float(mean_deg),
        'var_degree': float(var_deg),
        'skew_degree': float(skew_deg)
    }


def compute_clustering_coefficient(G: nx.Graph) -> float:
    """
    Compute the average clustering coefficient of the graph.

    Args:
        G: Networkx graph.

    Returns:
        Average clustering coefficient.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    return nx.average_clustering(G)


def compute_mean_betweenness(G: nx.Graph) -> float:
    """
    Compute the mean betweenness centrality of nodes in the graph.

    Args:
        G: Networkx graph.

    Returns:
        Mean betweenness centrality.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    betweenness = nx.betweenness_centrality(G)
    if not betweenness:
        return 0.0
    return float(np.mean(list(betweenness.values())))


def extract_cascade_nodes(cascade_path: str) -> list:
    """
    Extract node IDs from a cascade JSON file.

    Args:
        cascade_path: Path to cascade JSON file.

    Returns:
        List of node IDs in the cascade.
    """
    with open(cascade_path, 'r') as f:
        data = json.load(f)
        nodes = data.get('nodes', [])
        # Assume nodes are either dicts with 'node_id' or just strings/integers
        if nodes and isinstance(nodes[0], dict):
            return [n['node_id'] for n in nodes]
        return nodes


def process_cascades(cascade_paths: list, network_paths: list, output_path: str, logger: logging.Logger):
    """
    Process multiple cascades and compute network features.

    Args:
        cascade_paths: List of paths to cascade JSON files.
        network_paths: List of paths to historical network JSON files.
        output_path: Path to write the output CSV.
        logger: Logger instance for recording progress.
    """
    # Log input parameters
    logger.info(f"Processing {len(cascade_paths)} cascades from: {cascade_paths}")
    logger.info(f"Using {len(network_paths)} historical network files: {network_paths}")
    logger.info(f"Output will be written to: {output_path}")

    networks = load_historical_networks(network_paths)
    logger.info("Loaded historical networks successfully.")

    # For simplicity, we assume one network per cascade or a single global network.
    # In a real scenario, we'd map cascades to specific networks.
    # Here we use the first network if available, or a combined network.
    combined_G = nx.Graph()
    for G in networks.values():
        combined_G = nx.compose(combined_G, G)

    logger.info(f"Combined historical network has {combined_G.number_of_nodes()} nodes and {combined_G.number_of_edges()} edges.")

    results = []
    for c_path in cascade_paths:
        cascade_id = Path(c_path).stem
        logger.info(f"Processing cascade: {cascade_id}")

        nodes = extract_cascade_nodes(c_path)
        if not nodes:
            logger.warning(f"No nodes found in cascade {cascade_id}, skipping.")
            continue

        # Extract subgraph of historical network for these nodes
        sub_G = combined_G.subgraph(nodes)

        # Compute features
        deg_moments = compute_degree_moments(sub_G)
        clustering = compute_clustering_coefficient(sub_G)
        betweenness = compute_mean_betweenness(sub_G)

        results.append({
            'cascade_id': cascade_id,
            'mean_degree': deg_moments['mean_degree'],
            'var_degree': deg_moments['var_degree'],
            'skew_degree': deg_moments['skew_degree'],
            'clustering_coeff': clustering,
            'mean_betweenness': betweenness
        })

    # Write to CSV
    import csv
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Feature extraction complete. Wrote {len(results)} rows to {output_path}")


def main():
    """Main entry point for network feature extraction."""
    parser = argparse.ArgumentParser(description='Compute network features for cascades.')
    parser.add_argument('--input', type=str, required=True, nargs='+',
                        help='Paths to cascade JSON files.')
    parser.add_argument('--network', type=str, required=True, nargs='+',
                        help='Paths to historical network JSON files.')
    parser.add_argument('--output', type=str, required=True,
                        help='Path for output CSV file.')
    parser.add_argument('--seed', type=int, default=12345,
                        help='Random seed for reproducibility.')
    parser.add_argument('--log', type=str, default='pipeline.log',
                        help='Path to log file.')

    args = parser.parse_args()

    # Setup logging and seed
    logger = setup_logger(args.log)
    set_global_seed(args.seed)
    logger.info("Starting network feature extraction.")
    logger.info(f"Input cascades: {args.input}")
    logger.info(f"Input networks: {args.network}")
    logger.info(f"Output file: {args.output}")

    try:
        process_cascades(args.input, args.network, args.output, logger)
        logger.info("Network feature extraction completed successfully.")
    except Exception as e:
        logger.error(f"Error during feature extraction: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
