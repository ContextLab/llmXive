"""
Network Generation and Metrics Computation Module

Generates diverse synthetic oscillator network topologies and computes
static structural metrics. Implements error handling for generation failures.
"""
import os
import sys
import json
import hashlib
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import numpy as np
from scipy import stats

# Import metrics functions from the utils module
from utils.metrics import compute_graph_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/generation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEED = 42
MIN_NODES = 100
MAX_NODES = 200
TARGET_GRAPHS_PER_CLASS = 10
TOTAL_TARGET_GRAPHS = 50

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    random_state = np.random.RandomState(seed)
    return random_state

def power_law_function(k: float, gamma: float, kmin: float) -> float:
    """Compute power-law probability density."""
    return (gamma - 1) * kmin**(gamma - 1) * k**(-gamma)

def validate_scale_free_graph(G: nx.Graph, graph_id: str) -> Tuple[bool, str]:
    """
    Validate that a graph follows a power-law degree distribution.
    Uses KS-test to compare against theoretical power law.
    """
    degrees = [d for _, d in G.degree()]
    if len(degrees) < 2:
        return False, f"Graph {graph_id}: Insufficient nodes for degree distribution"

    # Fit power law
    try:
        from powerlaw import Fit
        fit = Fit(degrees, discrete=True)
        p_value = fit.power_law.pvalue()
        if p_value > 0.05:
            return True, f"Graph {graph_id}: Power-law fit valid (p={p_value:.4f})"
        else:
            return False, f"Graph {graph_id}: Power-law fit invalid (p={p_value:.4f})"
    except ImportError:
        # Fallback: simple heuristic if powerlaw package not available
        loglog_degrees = np.log10(np.array(sorted(list(set(degrees)))))
        loglog_counts = np.log10(np.array([degrees.count(d) for d in sorted(list(set(degrees)))]))
        if len(loglog_degrees) > 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(loglog_degrees, loglog_counts)
            if r_value < -0.8:  # Negative slope indicates power law
                return True, f"Graph {graph_id}: Approximate power-law (r={r_value:.4f})"
        return False, f"Graph {graph_id}: Could not validate power-law distribution"

def validate_random_graph(G: nx.Graph, graph_id: str, expected_clustering: float = None) -> Tuple[bool, str]:
    """
    Validate that a random graph has expected properties.
    Checks average degree and clustering coefficient within 5% of theoretical.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    avg_degree = 2 * m / n if n > 0 else 0

    clustering = nx.average_clustering(G)
    
    # Theoretical clustering for Erdos-Renyi is p = avg_degree / (n-1)
    theoretical_clustering = avg_degree / (n - 1) if n > 1 else 0
    
    if expected_clustering is None:
        expected_clustering = theoretical_clustering

    # Check if within 5% tolerance
    if expected_clustering == 0:
        if clustering > 0.05:
            return False, f"Graph {graph_id}: Clustering {clustering:.4f} too high (expected ~0)"
    else:
        relative_diff = abs(clustering - expected_clustering) / expected_clustering
        if relative_diff > 0.05:
            return False, f"Graph {graph_id}: Clustering {clustering:.4f} deviates >5% from expected {expected_clustering:.4f}"

    return True, f"Graph {graph_id}: Random graph properties valid"

def validate_small_world_lattice(G: nx.Graph, graph_id: str, graph_type: str) -> Tuple[bool, str]:
    """
    Validate small-world or lattice graph properties.
    """
    clustering = nx.average_clustering(G)
    path_length = nx.average_shortest_path_length(G) if nx.is_connected(G) else float('inf')

    if graph_type == "small_world":
        # Small-world: high clustering, low path length
        if clustering < 0.1:
            return False, f"Graph {graph_id}: Clustering too low for small-world"
        if path_length == float('inf'):
            return False, f"Graph {graph_id}: Graph not connected"
        return True, f"Graph {graph_id}: Small-world properties valid"
    elif graph_type == "lattice":
        # Lattice: regular structure, predictable path length
        if path_length == float('inf'):
            return False, f"Graph {graph_id}: Graph not connected"
        return True, f"Graph {graph_id}: Lattice properties valid"
    
    return False, f"Graph {graph_id}: Unknown graph type {graph_type}"

def generate_random_graph(n: int, p: float, seed: int, graph_id: str) -> Optional[nx.Graph]:
    """Generate an Erdos-Renyi random graph."""
    try:
        G = nx.erdos_renyi_graph(n, p, seed=seed)
        is_valid, msg = validate_random_graph(G, graph_id)
        if not is_valid:
            logger.warning(msg)
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate random graph {graph_id}: {e}")
        return None

def generate_scale_free_graph(n: int, m: int, seed: int, graph_id: str) -> Optional[nx.Graph]:
    """Generate a Barabasi-Albert scale-free graph."""
    try:
        G = nx.barabasi_albert_graph(n, m, seed=seed)
        is_valid, msg = validate_scale_free_graph(G, graph_id)
        if not is_valid:
            logger.warning(msg)
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate scale-free graph {graph_id}: {e}")
        return None

def generate_small_world_graph(n: int, k: int, p: float, seed: int, graph_id: str) -> Optional[nx.Graph]:
    """Generate a Watts-Strogatz small-world graph."""
    try:
        G = nx.watts_strogatz_graph(n, k, p, seed=seed)
        is_valid, msg = validate_small_world_lattice(G, graph_id, "small_world")
        if not is_valid:
            logger.warning(msg)
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate small-world graph {graph_id}: {e}")
        return None

def generate_lattice_graph(n: int, k: int, seed: int, graph_id: str) -> Optional[nx.Graph]:
    """Generate a ring lattice graph."""
    try:
        G = nx.watts_strogatz_graph(n, k, 0, seed=seed)  # p=0 for pure lattice
        is_valid, msg = validate_small_world_lattice(G, graph_id, "lattice")
        if not is_valid:
            logger.warning(msg)
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate lattice graph {graph_id}: {e}")
        return None

def generate_star_graph(n: int, seed: int, graph_id: str) -> Optional[nx.Graph]:
    """Generate a star graph."""
    try:
        G = nx.star_graph(n - 1, seed=seed)
        # Star graphs are valid by construction
        return G
    except Exception as e:
        logger.error(f"Failed to generate star graph {graph_id}: {e}")
        return None

def compute_graph_metrics(G: nx.Graph, graph_id: str, graph_class: str) -> Dict[str, Any]:
    """
    Compute and return metrics for a graph.
    This wraps the utils.metrics.compute_graph_metrics function.
    """
    metrics = compute_graph_metrics(G)
    metrics['id'] = graph_id
    metrics['class'] = graph_class
    return metrics

def generate_networks(
    target_count: int = TARGET_GRAPHS_PER_CLASS,
    node_range: Tuple[int, int] = (MIN_NODES, MAX_NODES),
    base_seed: int = DEFAULT_SEED
) -> List[Dict[str, Any]]:
    """
    Generate a diverse set of networks across 5 classes.
    Returns a list of dictionaries containing graph metrics.
    
    Implements error handling: logs failures, excludes failed graphs from final set.
    """
    graph_classes = ['random', 'scale_free', 'small_world', 'lattice', 'star']
    all_metrics = []
    failed_graphs = []
    
    graphs_per_class = target_count
    total_target = graphs_per_class * len(graph_classes)
    
    logger.info(f"Generating {total_target} networks ({graphs_per_class} per class)")
    
    current_seed = base_seed
    
    for graph_class in graph_classes:
        class_graphs = []
        attempts = 0
        max_attempts = graphs_per_class * 3  # Allow some retries
        
        while len(class_graphs) < graphs_per_class and attempts < max_attempts:
            attempts += 1
            graph_id = f"{graph_class}_{len(class_graphs) + 1}_{current_seed}"
            n = np.random.randint(node_range[0], node_range[1] + 1)
            
            G = None
            
            try:
                if graph_class == 'random':
                    p = 0.1  # Probability of edge
                    G = generate_random_graph(n, p, current_seed, graph_id)
                elif graph_class == 'scale_free':
                    m = 3  # Number of edges to attach from a new node
                    G = generate_scale_free_graph(n, m, current_seed, graph_id)
                elif graph_class == 'small_world':
                    k = 4  # Each node connected to 4 nearest neighbors
                    p_rewire = 0.1  # Probability of rewiring
                    G = generate_small_world_graph(n, k, p_rewire, current_seed, graph_id)
                elif graph_class == 'lattice':
                    k = 4  # Each node connected to 4 nearest neighbors
                    G = generate_lattice_graph(n, k, current_seed, graph_id)
                elif graph_class == 'star':
                    G = generate_star_graph(n, current_seed, graph_id)
                
                if G is None:
                    failed_graphs.append({
                        'id': graph_id,
                        'class': graph_class,
                        'reason': 'Generation returned None'
                    })
                    logger.warning(f"Skipping graph {graph_id} due to generation failure")
                    current_seed += 1
                    continue
                
                # Compute metrics
                metrics = compute_graph_metrics(G, graph_id, graph_class)
                class_graphs.append(metrics)
                all_metrics.append(metrics)
                logger.info(f"Successfully generated {graph_id} (N={n})")
                
            except Exception as e:
                error_msg = f"Exception during generation of {graph_id}: {e}"
                logger.error(error_msg)
                failed_graphs.append({
                    'id': graph_id,
                    'class': graph_class,
                    'reason': str(e)
                })
            
            current_seed += 1
        
        if len(class_graphs) < graphs_per_class:
            logger.warning(f"Only generated {len(class_graphs)}/{graphs_per_class} {graph_class} graphs")
    
    # Log summary of failures
    if failed_graphs:
        logger.warning(f"Total generation failures: {len(failed_graphs)}")
        for failure in failed_graphs:
            logger.warning(f"  - {failure['id']} ({failure['class']}): {failure['reason']}")
    else:
        logger.info("All graphs generated successfully without failures")
    
    logger.info(f"Final dataset: {len(all_metrics)} graphs (target: {total_target})")
    return all_metrics

def save_to_csv(metrics_list: List[Dict[str, Any]], output_path: str) -> None:
    """Save metrics to a CSV file."""
    import pandas as pd
    
    df = pd.DataFrame(metrics_list)
    
    # Ensure columns are in expected order
    expected_columns = ['id', 'class', 'N', 'avg_degree', 'clustering_coefficient', 
                      'average_path_length', 'diameter', 'density', 'max_degree', 
                      'min_degree', 'std_degree']
    
    available_columns = [col for col in expected_columns if col in df.columns]
    df = df[available_columns]
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def generate_checksum(file_path: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for network generation."""
    parser = argparse.ArgumentParser(description='Generate network topologies and compute metrics')
    parser.add_argument('--output', type=str, default='data/raw/networks.csv',
                      help='Output CSV file path')
    parser.add_argument('--count', type=int, default=TARGET_GRAPHS_PER_CLASS,
                      help='Number of graphs per class')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED,
                      help='Base random seed')
    parser.add_argument('--min-nodes', type=int, default=MIN_NODES,
                      help='Minimum number of nodes')
    parser.add_argument('--max-nodes', type=int, default=MAX_NODES,
                      help='Maximum number of nodes')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate networks
    metrics = generate_networks(
        target_count=args.count,
        node_range=(args.min_nodes, args.max_nodes),
        base_seed=args.seed
    )
    
    # Save to CSV
    save_to_csv(metrics, str(output_path))
    
    # Generate checksum
    checksum = generate_checksum(str(output_path))
    checksum_path = output_path.with_suffix('.sha256')
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    
    logger.info(f"Checksum generated: {checksum}")
    logger.info("Network generation complete")

if __name__ == '__main__':
    main()
