"""
Network Generation Module.

Generates synthetic oscillator network topologies (Random, Scale-Free, Small-World, Lattice, Star)
and computes static structural metrics.
"""
import os
import sys
import json
import hashlib
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import networkx as nx
from scipy import stats

# Import from local utils as per API surface
from utils.metrics import (
    compute_clustering_coefficient,
    compute_average_path_length,
    compute_degree_distribution_stats,
    compute_graph_metrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_NODES = 100
MAX_NODES = 200
MIN_GRAPHS_PER_CLASS = 10
TOTAL_GRAPHS_TARGET = 50
RANDOM_SEED_BASE = 42
FAILED_LOG_PATH = "state/failedGraphs.log"
OUTPUT_PATH = "data/raw/networks.csv"


def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    # NetworkX uses numpy random internally for most generators


def power_law_function(x: float, gamma: float, xmin: float) -> float:
    """Power law probability density function helper."""
    if x < xmin:
        return 0.0
    return (gamma - 1) * (xmin ** (gamma - 1)) * (x ** -gamma)


def validate_scale_free_graph(G: nx.Graph) -> Tuple[bool, str]:
    """
    Validate that a graph follows a power-law degree distribution.
    Uses KS-test against a power-law model.
    """
    degrees = [d for n, d in G.degree()]
    if len(degrees) < 10:
        return False, "Insufficient degrees for validation"

    # Fit power law
    # Using a simple heuristic: fit gamma and xmin
    # For robustness, we use a simplified fit or assume standard parameters for generation
    # Here we perform a KS-test comparing empirical CDF to theoretical power law
    
    # Estimate parameters (simplified for validation)
    # In a full implementation, one might use the powerlaw package
    # We will fit gamma via MLE approximation for integer degrees >= 1
    degrees_arr = np.array(degrees)
    xmin = 1.0 # Minimum degree is at least 1 for connected graphs usually
    # MLE for gamma: gamma = 1 + n / sum(log(x_i / xmin))
    # Filter out zeros if any (disconnected nodes)
    valid_degrees = degrees_arr[degrees_arr >= 1]
    if len(valid_degrees) == 0:
        return False, "No valid degrees >= 1"
    
    gamma_est = 1.0 + len(valid_degrees) / np.sum(np.log(valid_degrees / xmin))
    
    # Generate theoretical CDF
    # Theoretical P(X <= x) = 1 - (x/xmin)^(1-gamma)
    max_deg = int(np.max(valid_degrees))
    x_vals = np.arange(1, max_deg + 1)
    # CDF of power law: 1 - (x/xmin)^(1-gamma)
    # Note: This is for continuous approximation. Discrete correction is complex.
    # We'll use a simplified KS test on the sorted degrees
    
    empirical_cdf = np.arange(1, len(valid_degrees) + 1) / len(valid_degrees)
    theoretical_cdf = 1 - (x_vals[:len(valid_degrees)] / xmin) ** (1 - gamma_est)
    
    # Ensure theoretical_cdf doesn't exceed 1 due to float issues
    theoretical_cdf = np.clip(theoretical_cdf, 0, 1)
    
    # KS Statistic
    ks_stat, p_value = stats.ks_2samp(valid_degrees, np.random.power(1/gamma_est, len(valid_degrees)) * max_deg) 
    # The above synthetic generation for KS is a proxy. 
    # Let's do a direct KS on the empirical vs theoretical CDF of the power law
    
    # Correct approach for discrete data comparison without external package:
    # Compare sorted data to expected order statistics or use a chi-square binning.
    # For this task, we assume if gamma is in a reasonable range (2.0 - 3.5) and p-value of a fit is > 0.05
    # We will perform a simplified check:
    
    # 1. Check if gamma is reasonable
    if not (2.0 <= gamma_est <= 3.5):
        return False, f"Estimated gamma {gamma_est:.2f} outside typical range [2.0, 3.5]"

    # 2. Perform KS test against a theoretical power law distribution
    # We construct the theoretical CDF values for the observed data points
    # P(X <= x) = 1 - (x/xmin)^(1-gamma)
    theoretical_probs = 1 - (valid_degrees / xmin) ** (1 - gamma_est)
    theoretical_probs = np.clip(theoretical_probs, 0, 1)
    
    # Sort empirical CDF (already sorted by definition of valid_degrees sorted)
    # Actually, valid_degrees is not sorted.
    sorted_degrees = np.sort(valid_degrees)
    empirical_cdf_vals = np.arange(1, len(sorted_degrees) + 1) / len(sorted_degrees)
    theoretical_cdf_vals = 1 - (sorted_degrees / xmin) ** (1 - gamma_est)
    theoretical_cdf_vals = np.clip(theoretical_cdf_vals, 0, 1)
    
    d = np.max(np.abs(empirical_cdf_vals - theoretical_cdf_vals))
    # Approximate p-value for KS test (n is large)
    # p = 2 * exp(-2 * d^2 * n) is for one sample against continuous distribution
    n = len(sorted_degrees)
    p_val_approx = 2 * np.exp(-2 * (d ** 2) * n)
    
    if p_val_approx > 0.05:
        return True, f"Power-law fit p={p_val_approx:.4f}"
    else:
        return False, f"Power-law fit failed (p={p_val_approx:.4f})"


def validate_random_graph(G: nx.Graph, p: float) -> Tuple[bool, str]:
    """
    Validate random graph metrics against theoretical expectations.
    Checks average degree and clustering coefficient within 5%.
    """
    n = G.number_of_nodes()
    if n < 2:
        return False, "Graph too small"
    
    # Theoretical average degree: k = (n-1)*p
    theoretical_k = (n - 1) * p
    actual_k = np.mean([d for n, d in G.degree()])
    
    # Theoretical clustering: C = p
    theoretical_c = p
    actual_c = nx.average_clustering(G)
    
    # Check within 5%
    k_diff = abs(actual_k - theoretical_k) / theoretical_k if theoretical_k > 0 else 0
    c_diff = abs(actual_c - theoretical_c) / theoretical_c if theoretical_c > 0 else 0
    
    if k_diff <= 0.05 and c_diff <= 0.05:
        return True, f"Metrics within 5% (k_diff={k_diff:.4f}, c_diff={c_diff:.4f})"
    else:
        return False, f"Metrics deviation > 5% (k_diff={k_diff:.4f}, c_diff={c_diff:.4f})"


def validate_small_world_lattice(G: nx.Graph, class_name: str) -> Tuple[bool, str]:
    """
    Validate small-world or lattice properties.
    For small-world: High clustering, low path length compared to random.
    For lattice: High clustering, high path length.
    """
    # Basic check: graph is connected
    if not nx.is_connected(G):
        return False, "Graph is not connected"
    
    clustering = nx.average_clustering(G)
    path_len = nx.average_shortest_path_length(G)
    
    if class_name == "small_world":
        # Small world should have high clustering and relatively low path length
        # Heuristic: clustering > 0.1 and path_len < n/5
        n = G.number_of_nodes()
        if clustering > 0.1 and path_len < n / 5:
            return True, f"Small-world properties met (C={clustering:.3f}, L={path_len:.3f})"
        else:
            return False, f"Small-world properties not met (C={clustering:.3f}, L={path_len:.3f})"
    elif class_name == "lattice":
        # Lattice should have high clustering
        if clustering > 0.5:
            return True, f"Lattice properties met (C={clustering:.3f})"
        else:
            return False, f"Lattice properties not met (C={clustering:.3f})"
    
    return True, "Validation skipped"


def log_generation_failure(graph_id: str, error_type: str, message: str) -> None:
    """Log a generation failure to state/failedGraphs.log."""
    timestamp = datetime.now().isoformat()
    log_entry = f"{graph_id}|{timestamp}|{error_type}|{message}\n"
    
    os.makedirs(os.path.dirname(FAILED_LOG_PATH), exist_ok=True)
    with open(FAILED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)
    logger.error(f"Logged failure: {log_entry.strip()}")


def generate_random_graph(graph_id: str, seed: int) -> Optional[Dict[str, Any]]:
    """Generate an Erdos-Renyi random graph."""
    try:
        n = np.random.randint(MIN_NODES, MAX_NODES + 1)
        p = 0.05 # Fixed probability for consistency
        G = nx.erdos_renyi_graph(n, p, seed=seed)
        
        # Validate
        valid, msg = validate_random_graph(G, p)
        if not valid:
            log_generation_failure(graph_id, "VALIDATION_FAIL", msg)
            return None
        
        metrics = compute_graph_metrics(G)
        metrics['id'] = graph_id
        metrics['class'] = 'random'
        metrics['theoretical_match'] = 'passed' if valid else 'failed'
        metrics['status'] = 'valid'
        return metrics
    except Exception as e:
        log_generation_failure(graph_id, "NETWORKX_ERROR", str(e))
        return None


def generate_scale_free_graph(graph_id: str, seed: int) -> Optional[Dict[str, Any]]:
    """Generate a Barabasi-Albert scale-free graph."""
    try:
        n = np.random.randint(MIN_NODES, MAX_NODES + 1)
        m = 3 # Number of edges to attach from a new node
        G = nx.barabasi_albert_graph(n, m, seed=seed)
        
        # Validate
        valid, msg = validate_scale_free_graph(G)
        if not valid:
            log_generation_failure(graph_id, "VALIDATION_FAIL", msg)
            return None
        
        metrics = compute_graph_metrics(G)
        metrics['id'] = graph_id
        metrics['class'] = 'scale_free'
        metrics['theoretical_match'] = 'passed' if valid else 'failed'
        metrics['status'] = 'valid'
        return metrics
    except Exception as e:
        log_generation_failure(graph_id, "NETWORKX_ERROR", str(e))
        return None


def generate_small_world_graph(graph_id: str, seed: int) -> Optional[Dict[str, Any]]:
    """Generate a Watts-Strogatz small-world graph."""
    try:
        n = np.random.randint(MIN_NODES, MAX_NODES + 1)
        k = 4 # Each node connected to k nearest neighbors in ring lattice
        p_rewire = 0.1 # Probability of rewiring
        G = nx.watts_strogatz_graph(n, k, p_rewire, seed=seed)
        
        # Ensure connected (sometimes rewiring disconnects)
        if not nx.is_connected(G):
            # Try to reconnect or regenerate (simplified: just check again)
            # For robustness, we might retry, but here we log failure if not connected
            log_generation_failure(graph_id, "VALIDATION_FAIL", "Graph not connected after generation")
            return None

        valid, msg = validate_small_world_lattice(G, "small_world")
        if not valid:
            log_generation_failure(graph_id, "VALIDATION_FAIL", msg)
            return None
        
        metrics = compute_graph_metrics(G)
        metrics['id'] = graph_id
        metrics['class'] = 'small_world'
        metrics['theoretical_match'] = 'passed' if valid else 'failed'
        metrics['status'] = 'valid'
        return metrics
    except Exception as e:
        log_generation_failure(graph_id, "NETWORKX_ERROR", str(e))
        return None


def generate_lattice_graph(graph_id: str, seed: int) -> Optional[Dict[str, Any]]:
    """Generate a 2D grid graph (Lattice)."""
    try:
        # Target N nodes, find closest square root for grid
        target_n = np.random.randint(MIN_NODES, MAX_NODES + 1)
        side = int(np.sqrt(target_n))
        n = side * side
        if n < MIN_NODES: n = MIN_NODES # Fallback
        
        G = nx.grid_2d_graph(int(np.sqrt(n)), int(np.sqrt(n)))
        # Flatten nodes to 1D if needed, but metrics work on 2D tuples
        
        valid, msg = validate_small_world_lattice(G, "lattice")
        if not valid:
            log_generation_failure(graph_id, "VALIDATION_FAIL", msg)
            return None
        
        metrics = compute_graph_metrics(G)
        metrics['id'] = graph_id
        metrics['class'] = 'lattice'
        metrics['theoretical_match'] = 'passed' if valid else 'failed'
        metrics['status'] = 'valid'
        return metrics
    except Exception as e:
        log_generation_failure(graph_id, "NETWORKX_ERROR", str(e))
        return None


def generate_star_graph(graph_id: str, seed: int) -> Optional[Dict[str, Any]]:
    """Generate a Star graph."""
    try:
        n = np.random.randint(MIN_NODES, MAX_NODES + 1)
        G = nx.star_graph(n - 1) # star_graph(n) creates n+1 nodes (0 center, 1..n leaves)
        
        # Star graphs are always connected
        metrics = compute_graph_metrics(G)
        metrics['id'] = graph_id
        metrics['class'] = 'star'
        metrics['theoretical_match'] = 'N/A' # No specific theoretical test for star in this context
        metrics['status'] = 'valid'
        return metrics
    except Exception as e:
        log_generation_failure(graph_id, "NETWORKX_ERROR", str(e))
        return None


def compute_graph_metrics_with_validation(G: nx.Graph, class_name: str) -> Dict[str, Any]:
    """Wrapper to compute metrics and handle specific validation if needed."""
    # This function is mostly covered by the specific generators, 
    # but kept for consistency with the API surface description.
    metrics = compute_graph_metrics(G)
    return metrics


def generate_networks() -> List[Dict[str, Any]]:
    """Main generation loop to create 50+ networks."""
    results = []
    generators = {
        'random': generate_random_graph,
        'scale_free': generate_scale_free_graph,
        'small_world': generate_small_world_graph,
        'lattice': generate_lattice_graph,
        'star': generate_star_graph
    }
    
    graphs_per_class = TOTAL_GRAPHS_TARGET // len(generators)
    if graphs_per_class < MIN_GRAPHS_PER_CLASS:
        graphs_per_class = MIN_GRAPHS_PER_CLASS
    
    logger.info(f"Generating {graphs_per_class} graphs per class...")
    
    for class_name, gen_func in generators.items():
        count = 0
        attempts = 0
        max_attempts = graphs_per_class * 5 # Allow retries
        
        while count < graphs_per_class and attempts < max_attempts:
            attempts += 1
            graph_id = f"graph_{class_name}_{count:04d}"
            seed = RANDOM_SEED_BASE + attempts
            
            result = gen_func(graph_id, seed)
            if result:
                results.append(result)
                count += 1
                logger.info(f"Generated {class_name} graph {count}/{graphs_per_class}")
            else:
                logger.warning(f"Failed to generate {class_name} graph {count}/{graphs_per_class} (attempt {attempts})")
        
        if count < graphs_per_class:
            logger.error(f"Failed to generate enough {class_name} graphs. Generated {count}/{graphs_per_class}")
    
    return results


def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save data to CSV."""
    import csv
    
    if not data:
        logger.error("No data to save.")
        return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} records to {filepath}")


def generate_checksum(filepath: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate synthetic networks.")
    parser.add_argument('--output', default=OUTPUT_PATH, help='Output CSV path')
    args = parser.parse_args()
    
    set_seed(RANDOM_SEED_BASE)
    
    data = generate_networks()
    save_to_csv(data, args.output)
    
    checksum = generate_checksum(args.output)
    logger.info(f"Output file checksum: {checksum}")


if __name__ == "__main__":
    main()
