import os
import sys
import json
import hashlib
import argparse
import logging
import numpy as np
import networkx as nx
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
SEED_BASE = 42
TOLERANCE_PERCENT = 0.05  # 5% tolerance for theoretical validation

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    import random
    random.seed(seed)

def power_law_function(k: float, gamma: float) -> float:
    """
    Probability density function for power-law distribution.
    P(k) ~ k^(-gamma)
    """
    if k < 1:
        return 0.0
    return k ** (-gamma)

def validate_scale_free(graph: nx.Graph, gamma: float = 2.5) -> Dict[str, Any]:
    """
    Validate that a graph's degree distribution follows a power law.
    Uses Kolmogorov-Smirnov test against a power-law distribution.
    """
    degrees = [d for n, d in graph.degree()]
    if len(degrees) < 2:
        return {"valid": False, "ks_stat": 0.0, "p_value": 0.0, "message": "Insufficient data"}

    # Fit power law parameters
    try:
        # Use scipy.stats to fit power law (approximation)
        # Note: For rigorous power-law fitting, powerlaw package is preferred,
        # but we use scipy for standard library compatibility
        shape, loc, scale = stats.powerlaw.fit(degrees)
        
        # Perform KS test
        ks_stat, p_value = stats.kstest(degrees, 'powerlaw', args=(shape, loc, scale))
        
        is_valid = p_value > 0.05
        return {
            "valid": is_valid,
            "ks_stat": float(ks_stat),
            "p_value": float(p_value),
            "fitted_gamma": float(shape),
            "message": f"Power law fit {'accepted' if is_valid else 'rejected'} (p={p_value:.3f})"
        }
    except Exception as e:
        return {"valid": False, "ks_stat": 0.0, "p_value": 0.0, "message": f"Fit failed: {str(e)}"}

def validate_random_graph(graph: nx.Graph, expected_avg_degree: float, expected_clustering: float) -> Dict[str, Any]:
    """
    Validate that a random graph's metrics are within 5% of theoretical expectations.
    
    For Erdős-Rényi random graphs G(n, p):
    - Expected average degree: <k> = (n-1)p ≈ np
    - Expected clustering coefficient: C ≈ p = <k>/(n-1) ≈ <k>/n
    
    Args:
        graph: NetworkX graph to validate
        expected_avg_degree: Theoretical average degree
        expected_clustering: Theoretical clustering coefficient
        
    Returns:
        Dictionary with validation results
    """
    n = graph.number_of_nodes()
    if n == 0:
        return {"valid": False, "message": "Graph has no nodes"}
        
    actual_avg_degree = sum(dict(graph.degree()).values()) / n
    actual_clustering = nx.average_clustering(graph)
    
    # Calculate deviations
    degree_deviation = abs(actual_avg_degree - expected_avg_degree) / expected_avg_degree if expected_avg_degree > 0 else 0
    clustering_deviation = abs(actual_clustering - expected_clustering) / expected_clustering if expected_clustering > 0 else 0
    
    # Check if within 5% tolerance
    degree_ok = degree_deviation <= TOLERANCE_PERCENT
    clustering_ok = clustering_deviation <= TOLERANCE_PERCENT
    is_valid = degree_ok and clustering_ok
    
    result = {
        "valid": is_valid,
        "expected_avg_degree": float(expected_avg_degree),
        "actual_avg_degree": float(actual_avg_degree),
        "degree_deviation_pct": float(degree_deviation * 100),
        "expected_clustering": float(expected_clustering),
        "actual_clustering": float(actual_clustering),
        "clustering_deviation_pct": float(clustering_deviation * 100),
        "degree_status": "PASS" if degree_ok else "FAIL",
        "clustering_status": "PASS" if clustering_ok else "FAIL",
        "message": (
            f"Random graph validation: "
            f"Degree {degree_status} ({actual_avg_degree:.2f} vs {expected_avg_degree:.2f}), "
            f"Clustering {clustering_status} ({actual_clustering:.4f} vs {expected_clustering:.4f})"
        )
    }
    
    if not is_valid:
        logger.warning(f"Random graph validation failed: {result['message']}")
    else:
        logger.info(f"Random graph validation passed: {result['message']}")
        
    return result

def validate_small_world_lattice(graph: nx.Graph, graph_class: str) -> Dict[str, Any]:
    """
    Validate Small-World and Lattice graphs based on average path length.
    
    Small-World: High clustering, low path length (compared to lattice)
    Lattice: Regular degree, high path length (scales with n)
    
    Args:
        graph: NetworkX graph to validate
        graph_class: Either "small_world" or "lattice"
        
    Returns:
        Dictionary with validation results
    """
    n = graph.number_of_nodes()
    if n == 0:
        return {"valid": False, "message": "Graph has no nodes"}
        
    avg_path_length = nx.average_shortest_path_length(graph)
    clustering = nx.average_clustering(graph)
    
    # Theoretical expectations (approximate)
    if graph_class == "lattice":
        # For a 2D lattice (n = L^2), path length scales as L ~ sqrt(n)
        # For 1D ring lattice, path length scales as n/4
        # Using 1D approximation: <L> ≈ n/4
        theoretical_path_length = n / 4.0
        # High clustering expected for lattice (close to 1 for 1D ring)
        theoretical_clustering = 0.75  # Approximate for 1D ring with k=4
        
        path_deviation = abs(avg_path_length - theoretical_path_length) / theoretical_path_length
        clustering_deviation = abs(clustering - theoretical_clustering) / theoretical_clustering if theoretical_clustering > 0 else 0
        
        # Lattice should have high path length and high clustering
        path_ok = path_deviation <= TOLERANCE_PERCENT
        clustering_ok = clustering_deviation <= TOLERANCE_PERCENT
        
    elif graph_class == "small_world":
        # Small-world: path length should be much lower than lattice
        # Typically scales logarithmically: <L> ~ ln(n)
        theoretical_path_length = np.log(n) * 2  # Approximate
        # Should have relatively high clustering (similar to lattice)
        theoretical_clustering = 0.5  # Approximate
        
        path_deviation = abs(avg_path_length - theoretical_path_length) / theoretical_path_length
        clustering_deviation = abs(clustering - theoretical_clustering) / theoretical_clustering if theoretical_clustering > 0 else 0
        
        # Small-world should have low path length and high clustering
        path_ok = path_deviation <= TOLERANCE_PERCENT
        clustering_ok = clustering_deviation <= TOLERANCE_PERCENT
    else:
        return {"valid": False, "message": f"Unknown graph class: {graph_class}"}
    
    is_valid = path_ok and clustering_ok
    
    result = {
        "valid": is_valid,
        "graph_class": graph_class,
        "n": n,
        "avg_path_length": float(avg_path_length),
        "theoretical_path_length": float(theoretical_path_length),
        "path_deviation_pct": float(path_deviation * 100),
        "clustering": float(clustering),
        "theoretical_clustering": float(theoretical_clustering),
        "clustering_deviation_pct": float(clustering_deviation * 100),
        "path_status": "PASS" if path_ok else "FAIL",
        "clustering_status": "PASS" if clustering_ok else "FAIL",
        "message": (
            f"{graph_class.capitalize()} validation: "
            f"Path length {path_status} ({avg_path_length:.2f} vs {theoretical_path_length:.2f}), "
            f"Clustering {clustering_status} ({clustering:.4f} vs {theoretical_clustering:.4f})"
        )
    }
    
    if not is_valid:
        logger.warning(f"{graph_class.capitalize()} validation failed: {result['message']}")
    else:
        logger.info(f"{graph_class.capitalize()} validation passed: {result['message']}")
        
    return result

def generate_random_graph(n: int, p: float, seed: int) -> nx.Graph:
    """Generate an Erdős-Rényi random graph G(n, p)."""
    set_seed(seed)
    G = nx.erdos_renyi_graph(n, p, seed=seed)
    return G

def generate_scale_free_graph(n: int, m: int, seed: int) -> nx.Graph:
    """Generate a Barabási-Albert scale-free graph."""
    set_seed(seed)
    G = nx.barabasi_albert_graph(n, m, seed=seed)
    return G

def generate_small_world_graph(n: int, k: int, p: float, seed: int) -> nx.Graph:
    """Generate a Watts-Strogatz small-world graph."""
    set_seed(seed)
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    return G

def generate_lattice_graph(n: int, k: int, seed: int) -> nx.Graph:
    """Generate a 1D ring lattice graph (regular graph)."""
    set_seed(seed)
    # Create a 1D ring lattice with n nodes and k nearest neighbors
    G = nx.random_regular_graph(k, n, seed=seed)
    return G

def generate_star_graph(n: int, seed: int) -> nx.Graph:
    """Generate a star graph."""
    set_seed(seed)
    G = nx.star_graph(n - 1)  # n-1 leaves + 1 center = n nodes
    return G

def compute_graph_metrics(graph: nx.Graph, graph_id: str, graph_class: str) -> Dict[str, Any]:
    """Compute comprehensive metrics for a graph."""
    n = graph.number_of_nodes()
    m = graph.number_of_edges()
    
    # Basic metrics
    avg_degree = sum(dict(graph.degree()).values()) / n if n > 0 else 0
    clustering = nx.average_clustering(graph)
    
    # Average path length (handle disconnected graphs)
    try:
        avg_path_length = nx.average_shortest_path_length(graph)
    except nx.NetworkXError:
        # Graph might be disconnected
        avg_path_length = float('inf')
    
    # Degree distribution stats
    degrees = [d for n, d in graph.degree()]
    degree_stats = {
        "min": min(degrees) if degrees else 0,
        "max": max(degrees) if degrees else 0,
        "mean": float(np.mean(degrees)) if degrees else 0,
        "std": float(np.std(degrees)) if degrees else 0
    }
    
    return {
        "id": graph_id,
        "class": graph_class,
        "n": n,
        "m": m,
        "avg_degree": float(avg_degree),
        "clustering_coefficient": float(clustering),
        "avg_path_length": float(avg_path_length) if not np.isinf(avg_path_length) else -1,
        "degree_stats": degree_stats,
        "is_connected": nx.is_connected(graph)
    }

def generate_networks(
    n_per_class: int = 10,
    n_range: Tuple[int, int] = (100, 200),
    seed_base: int = SEED_BASE
) -> List[Dict[str, Any]]:
    """
    Generate diverse synthetic oscillator network topologies.
    
    Args:
        n_per_class: Number of graphs to generate per class
        n_range: Range of node counts (min, max)
        seed_base: Base seed for reproducibility
        
    Returns:
        List of dictionaries containing graph metrics and validation results
    """
    graph_classes = ["random", "scale_free", "small_world", "lattice", "star"]
    all_graphs = []
    seed_counter = 0
    
    for graph_class in graph_classes:
        for i in range(n_per_class):
            seed = seed_base + seed_counter
            seed_counter += 1
            
            # Random node count within range
            n = np.random.randint(n_range[0], n_range[1] + 1)
            graph_id = f"{graph_class}_{n}_{i:03d}"
            
            try:
                # Generate graph based on class
                if graph_class == "random":
                    p = 0.1  # Connection probability
                    G = generate_random_graph(n, p, seed)
                    
                    # Theoretical expectations for G(n, p)
                    expected_avg_degree = (n - 1) * p
                    expected_clustering = p
                    
                    # Validate against theory
                    validation = validate_random_graph(G, expected_avg_degree, expected_clustering)
                    metrics = compute_graph_metrics(G, graph_id, graph_class)
                    metrics["validation"] = validation
                    metrics["validation_passed"] = validation["valid"]
                    
                elif graph_class == "scale_free":
                    m = 2  # Number of edges to attach from new node
                    G = generate_scale_free_graph(n, m, seed)
                    
                    # Validate power law
                    validation = validate_scale_free(G)
                    metrics = compute_graph_metrics(G, graph_id, graph_class)
                    metrics["validation"] = validation
                    metrics["validation_passed"] = validation["valid"]
                    
                elif graph_class == "small_world":
                    k = 4  # Each node connected to k nearest neighbors
                    p_rewire = 0.1  # Rewiring probability
                    G = generate_small_world_graph(n, k, p_rewire, seed)
                    
                    # Validate small-world properties
                    validation = validate_small_world_lattice(G, "small_world")
                    metrics = compute_graph_metrics(G, graph_id, graph_class)
                    metrics["validation"] = validation
                    metrics["validation_passed"] = validation["valid"]
                    
                elif graph_class == "lattice":
                    k = 4  # Regular degree
                    G = generate_lattice_graph(n, k, seed)
                    
                    # Validate lattice properties
                    validation = validate_small_world_lattice(G, "lattice")
                    metrics = compute_graph_metrics(G, graph_id, graph_class)
                    metrics["validation"] = validation
                    metrics["validation_passed"] = validation["valid"]
                    
                elif graph_class == "star":
                    G = generate_star_graph(n, seed)
                    # Star graph validation (optional, no strict theoretical bounds here)
                    metrics = compute_graph_metrics(G, graph_id, graph_class)
                    metrics["validation"] = {"valid": True, "message": "Star graph (no strict validation)"}
                    metrics["validation_passed"] = True
                    
                else:
                    logger.error(f"Unknown graph class: {graph_class}")
                    continue
                
                all_graphs.append(metrics)
                
            except Exception as e:
                logger.error(f"Failed to generate graph {graph_id}: {str(e)}")
                # Exclude failed graphs from final set (as per T016)
                continue
    
    logger.info(f"Successfully generated {len(all_graphs)} graphs")
    return all_graphs

def save_to_csv(graphs: List[Dict[str, Any]], output_path: str) -> None:
    """Save generated graphs to CSV file."""
    import csv
    
    if not graphs:
        logger.warning("No graphs to save")
        return
        
    # Flatten nested dictionaries for CSV
    flattened = []
    for g in graphs:
        row = {
            "id": g["id"],
            "class": g["class"],
            "n": g["n"],
            "m": g["m"],
            "avg_degree": g["avg_degree"],
            "clustering_coefficient": g["clustering_coefficient"],
            "avg_path_length": g["avg_path_length"],
            "is_connected": g["is_connected"],
            "validation_passed": g.get("validation_passed", False),
            "validation_message": g.get("validation", {}).get("message", "")
        }
        
        # Add degree stats
        if "degree_stats" in g:
            row["degree_min"] = g["degree_stats"]["min"]
            row["degree_max"] = g["degree_stats"]["max"]
            row["degree_mean"] = g["degree_stats"]["mean"]
            row["degree_std"] = g["degree_stats"]["std"]
        
        flattened.append(row)
    
    # Write to CSV
    fieldnames = list(flattened[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened)
    
    logger.info(f"Saved {len(flattened)} graphs to {output_path}")

def generate_checksum(file_path: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for network generation."""
    parser = argparse.ArgumentParser(description="Generate oscillator network topologies")
    parser.add_argument("--n_per_class", type=int, default=10, help="Number of graphs per class")
    parser.add_argument("--n_min", type=int, default=100, help="Minimum number of nodes")
    parser.add_argument("--n_max", type=int, default=200, help="Maximum number of nodes")
    parser.add_argument("--output", type=str, default="data/raw/networks.csv", help="Output CSV path")
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Generating {args.n_per_class * 5} networks (N={args.n_min}-{args.n_max})")
    
    # Generate networks
    graphs = generate_networks(
        n_per_class=args.n_per_class,
        n_range=(args.n_min, args.n_max),
        seed_base=SEED_BASE
    )
    
    # Save to CSV
    save_to_csv(graphs, args.output)
    
    # Generate checksum
    if os.path.exists(args.output):
        checksum = generate_checksum(args.output)
        checksum_path = args.output + ".sha256"
        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  {os.path.basename(args.output)}\n")
        logger.info(f"Checksum saved to {checksum_path}")
    
    logger.info("Network generation complete")

if __name__ == "__main__":
    main()