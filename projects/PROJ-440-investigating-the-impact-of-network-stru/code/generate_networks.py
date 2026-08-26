import os
import sys
import json
import hashlib
import argparse
import logging
import random
import numpy as np
import networkx as nx
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Configure logging for error handling visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/generation_errors.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(nx, 'set_random_seed'):
        nx.set_random_seed(seed)

def power_law_function(k: float, gamma: float = 2.5) -> float:
    """Calculate probability for power law distribution."""
    return k ** (-gamma)

def validate_scale_free_graph(G: nx.Graph, id_str: str) -> bool:
    """
    Validate that a graph follows a power-law degree distribution.
    Uses KS-test against a power law model.
    """
    degrees = [d for _, d in G.degree()]
    if len(degrees) < 10:
        logger.warning(f"Graph {id_str} has too few nodes for valid power-law fit.")
        return False

    # Fit power law parameters using scipy or simple regression on log-log
    # Using a simple approach: fit slope on log-log
    log_k = np.log([d for d in degrees if d > 0])
    log_p = np.log([1.0/len(degrees)] * len(degrees)) # Uniform probability for simplicity in check, or use actual counts

    # More robust: use powerlaw library if available, else simple KS test on degrees
    # Here we perform a KS test against a theoretical power law generated from fitted parameters
    try:
        # Fit gamma using MLE approximation
        # p(k) ~ k^-gamma
        # Simple estimator: gamma = 1 + N / sum(log(k/k_min))
        k_min = min(degrees)
        if k_min <= 1: k_min = 2
        gamma_est = 1 + len(degrees) / np.sum(np.log(np.array(degrees) / k_min))

        # Generate synthetic data from fitted power law
        # We use inverse transform sampling for power law: k = k_min * (1 - U)^(1/(1-gamma))
        u = np.random.rand(len(degrees))
        synthetic_degrees = k_min * (u) ** (1 / (1 - gamma_est))
        
        # Perform KS test
        ks_stat, p_value = stats.ks_2samp(degrees, synthetic_degrees)
        
        if p_value < 0.05:
            logger.warning(f"Graph {id_str} failed power-law validation (p={p_value:.4f}).")
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating scale-free graph {id_str}: {e}")
        return False

def validate_random_graph(G: nx.Graph, id_str: str, N: int, p: float) -> bool:
    """
    Validate random graph metrics against theoretical expectations.
    Theoretical clustering C ≈ p, average degree k ≈ p(N-1).
    """
    try:
        avg_degree = np.mean([d for _, d in G.degree()])
        theoretical_degree = p * (N - 1)
        
        clustering = nx.average_clustering(G)
        theoretical_clustering = p

        degree_diff = abs(avg_degree - theoretical_degree) / theoretical_degree
        cluster_diff = abs(clustering - theoretical_clustering) / theoretical_clustering

        if degree_diff > 0.05:
            logger.warning(f"Graph {id_str} average degree deviation: {degree_diff:.2%} (Expected: {theoretical_degree:.2f}, Got: {avg_degree:.2f})")
            return False
        
        if cluster_diff > 0.05:
            logger.warning(f"Graph {id_str} clustering deviation: {cluster_diff:.2%} (Expected: {theoretical_clustering:.2f}, Got: {clustering:.2f})")
            return False

        return True
    except Exception as e:
        logger.error(f"Error validating random graph {id_str}: {e}")
        return False

def validate_small_world_lattice(G: nx.Graph, id_str: str, graph_type: str) -> bool:
    """
    Validate Small-World and Lattice graphs.
    Small-World: High clustering, low path length.
    Lattice: Regular degree, high path length.
    """
    try:
        clustering = nx.average_clustering(G)
        try:
            path_length = nx.average_shortest_path_length(G)
        except nx.NetworkXError:
            # Disconnected graph
            logger.warning(f"Graph {id_str} is disconnected.")
            return False

        if graph_type == "small_world":
            # Heuristic: clustering should be significantly higher than random (approx 1/N)
            # and path length should be relatively low (log N)
            if clustering < 0.1:
                logger.warning(f"Graph {id_str} (Small-World) clustering too low: {clustering:.4f}")
                return False
            if path_length > 10: # Arbitrary threshold for N=100
                logger.warning(f"Graph {id_str} (Small-World) path length too high: {path_length:.4f}")
                return False
        elif graph_type == "lattice":
            # Lattice should have high path length relative to N
            if path_length < 5:
                logger.warning(f"Graph {id_str} (Lattice) path length too low: {path_length:.4f}")
                return False
            # Check regularity
            degrees = [d for _, d in G.degree()]
            if max(degrees) != min(degrees):
                logger.warning(f"Graph {id_str} (Lattice) is not regular.")
                return False

        return True
    except Exception as e:
        logger.error(f"Error validating {graph_type} graph {id_str}: {e}")
        return False

def generate_random_graph(N: int, p: float, seed: int, id_str: str) -> Optional[nx.Graph]:
    set_seed(seed)
    try:
        G = nx.erdos_renyi_graph(N, p, seed=seed)
        if not validate_random_graph(G, id_str, N, p):
            logger.error(f"Generation validation failed for {id_str}. Excluding from dataset.")
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate random graph {id_str}: {e}")
        return None

def generate_scale_free_graph(N: int, m: int, seed: int, id_str: str) -> Optional[nx.Graph]:
    set_seed(seed)
    try:
        G = nx.barabasi_albert_graph(N, m, seed=seed)
        if not validate_scale_free_graph(G, id_str):
            logger.error(f"Generation validation failed for {id_str}. Excluding from dataset.")
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate scale-free graph {id_str}: {e}")
        return None

def generate_small_world_graph(N: int, k: int, p: float, seed: int, id_str: str) -> Optional[nx.Graph]:
    set_seed(seed)
    try:
        G = nx.watts_strogatz_graph(N, k, p, seed=seed)
        if not validate_small_world_lattice(G, id_str, "small_world"):
            logger.error(f"Generation validation failed for {id_str}. Excluding from dataset.")
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate small-world graph {id_str}: {e}")
        return None

def generate_lattice_graph(N: int, k: int, seed: int, id_str: str) -> Optional[nx.Graph]:
    set_seed(seed)
    try:
        # Create a 1D ring lattice
        G = nx.watts_strogatz_graph(N, k, 0, seed=seed)
        if not validate_small_world_lattice(G, id_str, "lattice"):
            logger.error(f"Generation validation failed for {id_str}. Excluding from dataset.")
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate lattice graph {id_str}: {e}")
        return None

def generate_star_graph(N: int, seed: int, id_str: str) -> Optional[nx.Graph]:
    set_seed(seed)
    try:
        G = nx.star_graph(N-1)
        # Star graph validation: one node with degree N-1, others 1
        degrees = [d for _, d in G.degree()]
        if max(degrees) != N-1 or min(degrees) != 1:
            logger.error(f"Star graph {id_str} structure invalid.")
            return None
        return G
    except Exception as e:
        logger.error(f"Failed to generate star graph {id_str}: {e}")
        return None

def compute_graph_metrics(G: nx.Graph, graph_class: str, graph_id: str) -> Dict[str, Any]:
    """Compute metrics for a single graph."""
    try:
        n = G.number_of_nodes()
        m = G.number_of_edges()
        avg_degree = 2 * m / n if n > 0 else 0
        
        clustering = nx.average_clustering(G)
        
        try:
            path_length = nx.average_shortest_path_length(G)
        except nx.NetworkXError:
            path_length = float('inf') # Handle disconnected

        # Degree distribution stats
        degrees = [d for _, d in G.degree()]
        degree_stats = {
            "min": min(degrees) if degrees else 0,
            "max": max(degrees) if degrees else 0,
            "mean": float(np.mean(degrees)) if degrees else 0,
            "std": float(np.std(degrees)) if degrees else 0
        }

        return {
            "id": graph_id,
            "class": graph_class,
            "N": n,
            "avg_degree": avg_degree,
            "clustering": clustering,
            "path_length": path_length,
            "degree_min": degree_stats["min"],
            "degree_max": degree_stats["max"],
            "degree_mean": degree_stats["mean"],
            "degree_std": degree_stats["std"]
        }
    except Exception as e:
        logger.error(f"Error computing metrics for {graph_id}: {e}")
        return None

def generate_networks(
    num_per_class: int = 10,
    n_range: Tuple[int, int] = (100, 200),
    base_seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Generate networks across 5 classes.
    Returns: (list of metric dicts, list of failed IDs)
    """
    networks = []
    failed_ids = []
    current_seed = base_seed

    classes_config = {
        "random": {"generator": generate_random_graph, "params": {"p": 0.1}},
        "scale_free": {"generator": generate_scale_free_graph, "params": {"m": 3}},
        "small_world": {"generator": generate_small_world_graph, "params": {"k": 4, "p": 0.1}},
        "lattice": {"generator": generate_lattice_graph, "params": {"k": 4}},
        "star": {"generator": generate_star_graph, "params": {}}
    }

    for cls_name, config in classes_config.items():
        for i in range(num_per_class):
            N = np.random.randint(n_range[0], n_range[1] + 1)
            graph_id = f"{cls_name}_{N}_{current_seed}"
            
            generator = config["generator"]
            params = config["params"].copy()
            params.update({"N": N, "seed": current_seed, "id_str": graph_id})

            logger.info(f"Generating {cls_name} graph {graph_id} (N={N})...")
            
            G = generator(**params)
            
            if G is None:
                failed_ids.append(graph_id)
                continue

            metrics = compute_graph_metrics(G, cls_name, graph_id)
            if metrics:
                networks.append(metrics)
            else:
                failed_ids.append(graph_id)
                logger.error(f"Metrics computation failed for {graph_id}, excluding.")

            current_seed += 1

    return networks, failed_ids

def save_to_csv(networks: List[Dict[str, Any]], output_path: str) -> None:
    """Save network metrics to CSV."""
    import pandas as pd
    if not networks:
        logger.error("No networks to save.")
        return
    
    df = pd.DataFrame(networks)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(networks)} networks to {output_path}")

def generate_checksum(file_path: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Generate oscillator network topologies.")
    parser.add_argument("--output", type=str, default="data/raw/networks.csv", help="Output CSV path")
    parser.add_argument("--per_class", type=int, default=10, help="Number of graphs per class")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    logger.info("Starting network generation...")
    networks, failed_ids = generate_networks(num_per_class=args.per_class, base_seed=args.seed)

    if failed_ids:
        logger.warning(f"Generation failed for {len(failed_ids)} graphs. IDs logged to error log.")
        logger.warning(f"Failed IDs: {', '.join(failed_ids)}")
    
    if not networks:
        logger.critical("No valid networks generated. Aborting.")
        sys.exit(1)

    save_to_csv(networks, args.output)
    
    # Generate checksum
    checksum = generate_checksum(args.output)
    checksum_path = args.output + ".sha256"
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {os.path.basename(args.output)}\n")
    logger.info(f"Checksum saved to {checksum_path}")

    # Log summary
    logger.info(f"Successfully generated {len(networks)} networks.")
    logger.info(f"Failed generations: {len(failed_ids)}")

if __name__ == "__main__":
    main()
