import os
import sys
import json
import hashlib
import argparse
import logging
import random
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import numpy as np
from scipy import stats
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(nx, 'set_seed'):
        nx.set_seed(seed)

def power_law_function(k: float, gamma: float) -> float:
    """Calculate probability density for a power law distribution."""
    if k < 1:
        return 0.0
    return (gamma - 1) * (k ** (-gamma))

def validate_scale_free_graph(G: nx.Graph, N: int) -> Dict[str, Any]:
    """
    Validate that a graph follows a power-law degree distribution.
    Returns a dict with validation status and p-value.
    """
    degrees = [d for _, d in G.degree()]
    # Fit power law
    try:
        # Use scipy stats for fitting if possible, or manual fit
        # Here we use a simple Kolmogorov-Smirnov test against a theoretical power law
        # We fit the exponent gamma using MLE for simplicity
        gamma_est = 1 + N / (N * np.log(np.mean(degrees)) - np.sum(np.log(degrees)))
        
        # Generate theoretical distribution
        theoretical_cdf = []
        ks_stat, p_value = stats.kstest(degrees, lambda x: 1 - (x / min(degrees)) ** (-gamma_est + 1) if x >= min(degrees) else 0)
        
        return {
            "is_valid": p_value > 0.05,
            "p_value": p_value,
            "gamma_estimate": gamma_est
        }
    except Exception as e:
        logger.warning(f"Validation failed for scale-free graph: {e}")
        return {
            "is_valid": False,
            "p_value": 0.0,
            "error": str(e)
        }

def validate_random_graph(G: nx.Graph, N: int, p: float) -> Dict[str, Any]:
    """
    Validate that a random graph matches theoretical expectations.
    Checks average degree and clustering coefficient within 5% of theoretical.
    """
    try:
        avg_degree = sum(dict(G.degree()).values()) / N
        theoretical_avg_degree = (N - 1) * p
        
        clustering = nx.average_clustering(G)
        theoretical_clustering = p
        
        degree_diff = abs(avg_degree - theoretical_avg_degree) / theoretical_avg_degree if theoretical_avg_degree > 0 else 0
        cluster_diff = abs(clustering - theoretical_clustering) / theoretical_clustering if theoretical_clustering > 0 else 0
        
        is_valid = (degree_diff < 0.05) and (cluster_diff < 0.05)
        
        return {
            "is_valid": is_valid,
            "degree_diff": degree_diff,
            "cluster_diff": cluster_diff,
            "avg_degree": avg_degree,
            "theoretical_avg_degree": theoretical_avg_degree,
            "clustering": clustering,
            "theoretical_clustering": theoretical_clustering
        }
    except Exception as e:
        logger.warning(f"Validation failed for random graph: {e}")
        return {
            "is_valid": False,
            "error": str(e)
        }

def validate_small_world_lattice(G: nx.Graph, graph_class: str) -> Dict[str, Any]:
    """
    Validate Small-World or Lattice graph properties.
    Small-World: High clustering, low path length.
    Lattice: Regular degree, high path length.
    """
    try:
        clustering = nx.average_clustering(G)
        path_length = nx.average_shortest_path_length(G)
        degrees = [d for _, d in G.degree()]
        degree_std = np.std(degrees)
        
        is_valid = False
        message = ""
        
        if graph_class == "small_world":
            # Small-world should have high clustering and relatively low path length
            # Heuristic: clustering > 0.1 and path_length < N/2
            is_valid = (clustering > 0.1) and (path_length < len(G) / 2)
            message = f"Small-world check: clustering={clustering:.4f}, path_length={path_length:.4f}"
        elif graph_class == "lattice":
            # Lattice should have low degree variance (regular) and higher path length
            is_valid = (degree_std < 0.5) and (path_length > len(G) / 4)
            message = f"Lattice check: degree_std={degree_std:.4f}, path_length={path_length:.4f}"
        
        return {
            "is_valid": is_valid,
            "clustering": clustering,
            "path_length": path_length,
            "degree_std": degree_std,
            "message": message
        }
    except Exception as e:
        logger.warning(f"Validation failed for {graph_class} graph: {e}")
        return {
            "is_valid": False,
            "error": str(e)
        }

def generate_random_graph(N: int, p: float, seed: int) -> nx.Graph:
    """Generate an Erdos-Renyi random graph."""
    set_seed(seed)
    G = nx.erdos_renyi_graph(N, p)
    return G

def generate_scale_free_graph(N: int, m: int, seed: int) -> nx.Graph:
    """Generate a Barabasi-Albert scale-free graph."""
    set_seed(seed)
    G = nx.barabasi_albert_graph(N, m)
    return G

def generate_small_world_graph(N: int, k: int, p: float, seed: int) -> nx.Graph:
    """Generate a Watts-Strogatz small-world graph."""
    set_seed(seed)
    G = nx.watts_strogatz_graph(N, k, p)
    return G

def generate_lattice_graph(N: int, k: int, seed: int) -> nx.Graph:
    """Generate a regular lattice graph (k-regular ring lattice)."""
    set_seed(seed)
    G = nx.random_regular_graph(k, N)
    return G

def generate_star_graph(N: int, seed: int) -> nx.Graph:
    """Generate a star graph."""
    set_seed(seed)
    G = nx.star_graph(N - 1)
    return G

def compute_graph_metrics(G: nx.Graph, graph_id: str, graph_class: str) -> Dict[str, Any]:
    """Compute all structural metrics for a graph."""
    N = G.number_of_nodes()
    E = G.number_of_edges()
    
    # Basic metrics
    avg_degree = sum(dict(G.degree()).values()) / N if N > 0 else 0
    clustering = nx.average_clustering(G)
    
    # Path length (handle disconnected graphs)
    try:
        path_length = nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        # Graph is disconnected, use largest connected component
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        path_length = nx.average_shortest_path_length(subgraph) if len(subgraph) > 1 else 0
    
    # Degree distribution stats
    degrees = [d for _, d in G.degree()]
    degree_mean = np.mean(degrees)
    degree_std = np.std(degrees)
    degree_max = max(degrees) if degrees else 0
    degree_min = min(degrees) if degrees else 0
    
    # Validation results
    validation = {}
    if graph_class == "random":
        validation = validate_random_graph(G, N, avg_degree / (N - 1))
    elif graph_class == "scale_free":
        validation = validate_scale_free_graph(G, N)
    elif graph_class in ["small_world", "lattice"]:
        validation = validate_small_world_lattice(G, graph_class)
    
    return {
        "id": graph_id,
        "class": graph_class,
        "N": N,
        "E": E,
        "avg_degree": avg_degree,
        "clustering_coefficient": clustering,
        "average_path_length": path_length,
        "degree_mean": degree_mean,
        "degree_std": degree_std,
        "degree_max": degree_max,
        "degree_min": degree_min,
        "validation": validation
    }

def generate_networks(
    n_per_class: int = 10,
    N_min: int = 100,
    N_max: int = 200,
    base_seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate diverse synthetic oscillator network topologies.
    
    Args:
        n_per_class: Number of graphs to generate per class (default 10)
        N_min: Minimum number of nodes
        N_max: Maximum number of nodes
        base_seed: Base random seed for reproducibility
    
    Returns:
        List of dictionaries containing graph metrics and validation results
    """
    graph_classes = [
        ("random", "random"),
        ("scale_free", "scale_free"),
        ("small_world", "small_world"),
        ("lattice", "lattice"),
        ("star", "star")
    ]
    
    results = []
    failed_generations = []
    
    current_seed = base_seed
    
    for class_name, graph_type in graph_classes:
        for i in range(n_per_class):
            graph_id = f"{class_name}_{i:03d}"
            N = np.random.randint(N_min, N_max + 1)
            
            try:
                if graph_type == "random":
                    p = 0.1  # Connection probability
                    G = generate_random_graph(N, p, current_seed)
                elif graph_type == "scale_free":
                    m = 3  # Number of edges to attach from a new node
                    G = generate_scale_free_graph(N, m, current_seed)
                elif graph_type == "small_world":
                    k = 4  # Each node has k nearest neighbors
                    p_sw = 0.1  # Rewiring probability
                    G = generate_small_world_graph(N, k, p_sw, current_seed)
                elif graph_type == "lattice":
                    k = 4  # Regular degree
                    G = generate_lattice_graph(N, k, current_seed)
                elif graph_type == "star":
                    G = generate_star_graph(N, current_seed)
                else:
                    raise ValueError(f"Unknown graph type: {graph_type}")
                
                # Compute metrics
                metrics = compute_graph_metrics(G, graph_id, class_name)
                
                # Log validation result
                if not metrics["validation"].get("is_valid", True):
                    logger.warning(
                        f"Graph {graph_id} ({class_name}) failed validation: "
                        f"{metrics['validation'].get('message', 'Unknown reason')}"
                    )
                
                results.append(metrics)
                current_seed += 1
                
            except Exception as e:
                logger.error(f"Failed to generate graph {graph_id} ({class_name}): {e}")
                failed_generations.append({
                    "id": graph_id,
                    "class": class_name,
                    "error": str(e)
                })
                # Continue to next graph - exclude failed ones from final set
                continue
    
    if failed_generations:
        logger.warning(
            f"Total failed generations: {len(failed_generations)}. "
            f"These graphs have been excluded from the final dataset."
        )
    
    return results

def save_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save network metrics to a CSV file."""
    if not results:
        raise ValueError("No results to save.")
    
    # Flatten validation data
    flattened_results = []
    for r in results:
        row = {
            "id": r["id"],
            "class": r["class"],
            "N": r["N"],
            "E": r["E"],
            "avg_degree": r["avg_degree"],
            "clustering_coefficient": r["clustering_coefficient"],
            "average_path_length": r["average_path_length"],
            "degree_mean": r["degree_mean"],
            "degree_std": r["degree_std"],
            "degree_max": r["degree_max"],
            "degree_min": r["degree_min"]
        }
        # Add validation fields
        val = r.get("validation", {})
        row["validation_is_valid"] = val.get("is_valid", False)
        row["validation_p_value"] = val.get("p_value", 0.0)
        row["validation_error"] = val.get("error", "")
        flattened_results.append(row)
    
    df = pd.DataFrame(flattened_results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} networks to {output_path}")

def generate_checksum(file_path: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for network generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic oscillator networks")
    parser.add_argument("--n-per-class", type=int, default=10, help="Number of graphs per class")
    parser.add_argument("--n-min", type=int, default=100, help="Minimum number of nodes")
    parser.add_argument("--n-max", type=int, default=200, help="Maximum number of nodes")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--output", type=str, default="data/raw/networks.csv", help="Output CSV path")
    parser.add_argument("--checksum-output", type=str, default="state/networks_checksum.txt", help="Checksum output path")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    logger.info(f"Generating networks: {args.n_per_class} per class, N=[{args.n_min}, {args.n_max}]")
    
    results = generate_networks(
        n_per_class=args.n_per_class,
        N_min=args.n_min,
        N_max=args.n_max,
        base_seed=args.seed
    )
    
    if not results:
        logger.error("No graphs were successfully generated. Exiting.")
        sys.exit(1)
    
    save_to_csv(results, args.output)
    
    # Generate checksum
    checksum = generate_checksum(args.output)
    checksum_path = args.checksum_output
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {args.output}\n")
    
    logger.info(f"Checksum generated: {checksum}")
    logger.info(f"Network generation complete. {len(results)} graphs saved.")

if __name__ == "__main__":
    main()