import os
import sys
import json
import hashlib
import argparse
import logging
import random
from typing import Dict, List, Tuple, Optional, Any, Set

import numpy as np
import networkx as nx
from scipy import stats
from scipy.stats import kstest

# Import existing utilities
from code.utils.metrics import (
    compute_clustering_coefficient,
    compute_average_path_length,
    compute_degree_distribution_stats,
    compute_graph_metrics,
)
from code.utils.checksums import generate_checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# --- Core Generation Functions (Existing) ---

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(np.random, 'default_rng'):
        # For newer numpy versions
        pass
    logger.info(f"Random seed set to {seed}")

def power_law_function(x: float, alpha: float, xmin: float) -> float:
    """Calculate the probability density for a power law distribution."""
    if x < xmin:
        return 0.0
    return (alpha - 1) * xmin ** (alpha - 1) * x ** (-alpha)

def validate_scale_free(graph: nx.Graph, alpha: float = 2.5, xmin: int = 1) -> bool:
    """
    Validate if a graph's degree distribution follows a power law.
    Uses KS-test. Returns True if p-value > 0.05.
    """
    degrees = [d for _, d in graph.degree()]
    degrees = [d for d in degrees if d >= xmin]
    if len(degrees) < 10:
        logger.warning("Not enough nodes with degree >= xmin for KS-test.")
        return False

    # Fit power law parameters
    try:
        # Using a simple fit or assuming fixed alpha for validation context
        # For rigorous validation, we'd use powerlaw package, but here we use scipy
        # We compare empirical CDF to theoretical CDF
        empirical_cdf, bins = np.histogram(degrees, bins='auto', density=True)
        # Theoretical CDF for power law P(X>=x) = (x/xmin)^(1-alpha)
        # PDF = (alpha-1)/xmin * (x/xmin)^(-alpha)
        # We will perform a simple KS test against the theoretical distribution
        
        # Construct theoretical distribution for KS test
        # We need to normalize the theoretical PDF over the range of data
        theoretical_pdf = np.array([power_law_function(b, alpha, xmin) for b in bins[:-1]])
        
        # Normalize
        if np.sum(theoretical_pdf) > 0:
            theoretical_pdf /= np.sum(theoretical_pdf)
        
        # KS Test
        # Note: scipy.stats.kstest expects a CDF or a distribution string.
        # We will construct a custom CDF function.
        def theoretical_cdf(x):
            if x < xmin:
                return 0.0
            return 1.0 - (xmin / x) ** (alpha - 1)
        
        ks_stat, p_value = kstest(degrees, theoretical_cdf)
        logger.debug(f"KS-test for scale-free: stat={ks_stat:.4f}, p-value={p_value:.4f}")
        return p_value > 0.05
    except Exception as e:
        logger.warning(f"Validation failed for scale-free check: {e}")
        return False

def validate_random_graph(graph: nx.Graph, N: int) -> bool:
    """
    Validate if a graph is approximately Erdos-Renyi.
    Checks if degree distribution is binomial (approximated by normal for large N).
    Tolerance: mean degree within 5% of expected.
    """
    degrees = [d for _, d in graph.degree()]
    mean_deg = np.mean(degrees)
    expected_deg = (N - 1) * 0.1 # Assuming p=0.1 for ER generation in generate_random_graph
    
    # Simple tolerance check
    if expected_deg == 0:
        return False
    
    tolerance = 0.05
    diff = abs(mean_deg - expected_deg) / expected_deg
    logger.debug(f"Random graph validation: mean={mean_deg:.2f}, expected={expected_deg:.2f}, diff={diff:.2%}")
    return diff <= tolerance

def generate_random_graph(N: int, p: float = 0.1, seed: Optional[int] = None) -> nx.Graph:
    """Generate an Erdos-Renyi random graph."""
    if seed is not None:
        set_seed(seed)
    G = nx.erdos_renyi_graph(N, p)
    return G

def generate_scale_free_graph(N: int, m: int = 2, seed: Optional[int] = None) -> nx.Graph:
    """Generate a Barabasi-Albert scale-free graph."""
    if seed is not None:
        set_seed(seed)
    G = nx.barabasi_albert_graph(N, m)
    return G

def generate_small_world_graph(N: int, k: int = 4, p: float = 0.1, seed: Optional[int] = None) -> nx.Graph:
    """Generate a Watts-Strogatz small-world graph."""
    if seed is not None:
        set_seed(seed)
    G = nx.watts_strogatz_graph(N, k, p)
    return G

def generate_lattice_graph(N: int, dims: int = 2, seed: Optional[int] = None) -> nx.Graph:
    """Generate a 2D or 3D grid graph."""
    if seed is not None:
        set_seed(seed)
    if dims == 2:
        root = int(np.sqrt(N))
        G = nx.grid_2d_graph(root, root)
        G = nx.convert_node_labels_to_integers(G)
    else:
        # Fallback for 3D if N is a perfect cube, else 2D
        root = int(np.cbrt(N))
        if root**3 == N:
            G = nx.grid_3d_graph(root, root, root)
            G = nx.convert_node_labels_to_integers(G)
        else:
            root = int(np.sqrt(N))
            G = nx.grid_2d_graph(root, root)
            G = nx.convert_node_labels_to_integers(G)
    return G

def generate_star_graph(N: int, seed: Optional[int] = None) -> nx.Graph:
    """Generate a Star graph."""
    if seed is not None:
        set_seed(seed)
    G = nx.star_graph(N - 1)
    return G

# --- Metric Computation (Existing) ---

def compute_metrics_for_graph(graph: nx.Graph, graph_id: str, class_name: str) -> Dict[str, Any]:
    """Compute all metrics for a single graph and return a dictionary."""
    try:
        metrics = compute_graph_metrics(graph)
        metrics['id'] = graph_id
        metrics['class'] = class_name
        metrics['N'] = graph.number_of_nodes()
        metrics['E'] = graph.number_of_edges()
        return metrics
    except Exception as e:
        logger.error(f"Failed to compute metrics for graph {graph_id}: {e}")
        raise

# --- Main Pipeline with Error Handling (Task T016) ---

def generate_networks(
    output_path: str,
    counts: Dict[str, int],
    seeds: Dict[str, int],
    validation_rules: Dict[str, callable]
) -> List[Dict[str, Any]]:
    """
    Generate networks for all classes, with error handling.
    Returns a list of successfully generated graph records.
    """
    all_records = []
    failed_ids = []

    # Class to generator mapping
    generators = {
        'random': generate_random_graph,
        'scale_free': generate_scale_free_graph,
        'small_world': generate_small_world_graph,
        'lattice': generate_lattice_graph,
        'star': generate_star_graph,
    }

    # Class specific parameters
    params = {
        'random': {'p': 0.1},
        'scale_free': {'m': 2},
        'small_world': {'k': 4, 'p': 0.1},
        'lattice': {'dims': 2},
        'star': {},
    }

    for class_name, count in counts.items():
        logger.info(f"Generating {count} {class_name} graphs...")
        if class_name not in generators:
            logger.error(f"Unknown class: {class_name}")
            continue

        gen_func = generators[class_name]
        class_params = params.get(class_name, {})
        base_seed = seeds.get(class_name, 42)

        for i in range(count):
            graph_id = f"{class_name}_{i:03d}"
            current_seed = base_seed + i
            
            try:
                # 1. Generate
                G = gen_func(N=100, seed=current_seed, **class_params)
                
                # 2. Validate
                validator = validation_rules.get(class_name)
                if validator:
                    if not validator(G, **class_params if class_name == 'random' else {}):
                        logger.warning(f"Validation failed for {graph_id}. Excluding from dataset.")
                        failed_ids.append(graph_id)
                        continue

                # 3. Compute Metrics
                record = compute_metrics_for_graph(G, graph_id, class_name)
                all_records.append(record)
                
            except Exception as e:
                logger.error(f"Generation or processing failed for {graph_id}: {e}")
                failed_ids.append(graph_id)
                # Continue to next graph

    logger.info(f"Generation complete. Success: {len(all_records)}, Failed: {len(failed_ids)}")
    if failed_ids:
        logger.warning(f"Excluded graph IDs: {failed_ids}")
    
    return all_records

def save_to_csv(records: List[Dict[str, Any]], output_path: str) -> None:
    """Save records to CSV and generate checksum."""
    import pandas as pd
    
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(records)} records to {output_path}")
    
    # Generate checksum
    checksum_path = output_path + ".sha256"
    generate_checksum_file(output_path, checksum_path)
    logger.info(f"Generated checksum at {checksum_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate Network Topologies")
    parser.add_argument("--output", type=str, default="data/raw/networks.csv", help="Output CSV path")
    parser.add_argument("--count", type=int, default=10, help="Number of graphs per class")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Configuration
    counts = {
        'random': args.count,
        'scale_free': args.count,
        'small_world': args.count,
        'lattice': args.count,
        'star': args.count,
    }
    seeds = {
        'random': 100,
        'scale_free': 200,
        'small_world': 300,
        'lattice': 400,
        'star': 500,
    }
    
    # Validation rules (partial application of validators with fixed args if needed)
    # For scale_free, we need to pass alpha, xmin. We'll use a wrapper or partial.
    # Here we define simple wrappers or pass defaults in the loop if needed.
    # Since validate_scale_free takes extra args, we wrap it.
    def validate_scale_free_wrapper(G):
        return validate_scale_free(G, alpha=2.5, xmin=1)
    
    def validate_random_wrapper(G):
        return validate_random_graph(G, N=100)

    validation_rules = {
        'random': validate_random_wrapper,
        'scale_free': validate_scale_free_wrapper,
        # Small world, lattice, star don't have strict validation rules in this task scope
    }

    logger.info("Starting network generation pipeline...")
    records = generate_networks(args.output, counts, seeds, validation_rules)
    
    if not records:
        logger.error("No networks were successfully generated.")
        sys.exit(1)

    save_to_csv(records, args.output)
    logger.info("Pipeline finished successfully.")

if __name__ == "__main__":
    main()