import os
import sys
import json
import hashlib
import argparse
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx
import numpy as np
from scipy import stats

# Import metrics from the utils module as per API surface
from utils.metrics import (
    compute_clustering_coefficient,
    compute_average_path_length,
    compute_degree_distribution_stats,
    compute_graph_metrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(np.random, 'default_rng'):
        np.random.default_rng(seed)

def power_law_function(k: float, gamma: float) -> float:
    """Calculate probability density for power-law distribution."""
    return (gamma - 1) * (k ** -gamma)

def validate_scale_free_graph(G: nx.Graph, target_gamma: float = 2.5) -> Tuple[bool, float]:
    """
    Validate if a graph follows a power-law degree distribution.
    Returns (is_valid, p_value).
    """
    degrees = [d for n, d in G.degree()]
    # Fit power law
    try:
        # Use scipy stats to fit power law
        # We use the continuous power law approximation for simplicity
        # In practice, networkx-algorithms or powerlaw package is better,
        # but we stick to standard libs as per requirements
        degree_counts = np.bincount(degrees)
        non_zero_indices = np.where(degree_counts > 0)[0]
        if len(non_zero_indices) < 2:
            return False, 0.0

        # Extract degrees for KS-test
        observed_degrees = np.repeat(non_zero_indices, degree_counts[non_zero_indices])
        
        # Fit parameters
        # Simplified MLE for power law exponent
        if len(observed_degrees) == 0:
            return False, 0.0
        
        xmin = min(observed_degrees)
        if xmin <= 1:
            xmin = 2 # Power law defined for k >= 1 usually, but discrete needs care
        
        # Estimate gamma using MLE approximation for discrete power law
        # gamma = 1 + n / (sum(ln(k_i / (k_min - 0.5))))
        # Using a simplified continuous approximation for stability
        if np.all(observed_degrees <= 0):
            return False, 0.0
            
        gamma_est = 1.0 + len(observed_degrees) / np.sum(np.log(observed_degrees / (xmin - 0.5)))
        
        # Generate theoretical distribution for KS test
        # We compare empirical CDF against theoretical CDF
        theoretical_cdf = []
        observed_cdf = []
        ks_stat, p_value = 0.0, 1.0
        
        try:
            # Use Kolmogorov-Smirnov test
            # Fit a power law distribution using scipy's powerlaw (if available) or custom
            # Since scipy.stats.powerlaw is not standard for this specific use case (it's for [0,1]),
            # we use a custom KS test against the fitted parameters
            
            # Sort observed degrees
            sorted_degrees = np.sort(observed_degrees)
            n = len(sorted_degrees)
            
            # Empirical CDF
            ecdf = np.arange(1, n+1) / n
            
            # Theoretical CDF for discrete power law P(X <= k) = 1 - (k/xmin)^(1-gamma) approx
            # This is a simplification. For rigorous testing, use the 'powerlaw' package.
            # Here we use a standard KS test against a fitted Pareto distribution as proxy
            # for the power law tail, which is standard in many physics contexts.
            
            # Fit Pareto (shifted)
            # scipy.stats.pareto
            # Shape parameter b = gamma - 1
            # scale = xmin
            shape = gamma_est - 1
            if shape <= 0:
                return False, 0.0
                
            # We perform KS test against the fitted Pareto distribution
            # Note: Pareto is continuous, degrees are discrete. 
            # For a robust check, we accept if p > 0.05.
            ks_stat, p_value = stats.kstest(sorted_degrees, 'pareto', args=(shape, 0, xmin))
            
        except Exception as e:
            logger.warning(f"KS-test failed for scale-free validation: {e}")
            return False, 0.0

        return p_value > 0.05, p_value

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, 0.0

def validate_random_graph(G: nx.Graph, p: float, N: int) -> Tuple[bool, bool]:
    """
    Validate random graph metrics against theoretical expectations.
    Returns (avg_degree_match, clustering_match).
    """
    metrics = compute_graph_metrics(G)
    avg_degree = metrics['average_degree']
    clustering = metrics['clustering_coefficient']
    
    # Theoretical values for Erdos-Renyi G(N, p)
    theoretical_avg_degree = (N - 1) * p
    theoretical_clustering = p
    
    # Check within 5%
    avg_match = abs(avg_degree - theoretical_avg_degree) < 0.05 * theoretical_avg_degree
    clust_match = abs(clustering - theoretical_clustering) < 0.05 * theoretical_clustering
    
    return avg_match, clust_match

def validate_small_world_lattice(G: nx.Graph, graph_class: str) -> bool:
    """
    Placeholder for specific validation of small-world or lattice properties.
    For now, just checks basic connectivity.
    """
    return nx.is_connected(G)

def generate_random_graph(N: int, p: float, seed: int) -> nx.Graph:
    """Generate an Erdos-Renyi random graph."""
    set_seed(seed)
    G = nx.erdos_renyi_graph(N, p, seed=seed)
    return G

def generate_scale_free_graph(N: int, m: int, seed: int) -> nx.Graph:
    """Generate a Barabasi-Albert scale-free graph."""
    set_seed(seed)
    G = nx.barabasi_albert_graph(N, m, seed=seed)
    return G

def generate_small_world_graph(N: int, k: int, p: float, seed: int) -> nx.Graph:
    """Generate a Watts-Strogatz small-world graph."""
    set_seed(seed)
    G = nx.watts_strogatz_graph(N, k, p, seed=seed)
    # Ensure connectivity for simulation stability if possible
    if not nx.is_connected(G) and N > 1:
        # If disconnected, try to rewire or warn. 
        # For this task, we might just accept it and let the simulation handle it,
        # or re-generate. We'll rely on the simulation's error handling for disconnected components
        # or ensure k is large enough.
        pass
    return G

def generate_lattice_graph(N: int, seed: int) -> nx.Graph:
    """Generate a 1D ring lattice."""
    set_seed(seed)
    # Create a cycle graph as a simple lattice
    G = nx.cycle_graph(N)
    return G

def generate_star_graph(N: int, seed: int) -> nx.Graph:
    """Generate a star graph."""
    set_seed(seed)
    G = nx.star_graph(N - 1)
    return G

def compute_graph_metrics(G: nx.Graph) -> Dict[str, Any]:
    """
    Compute standard metrics for a graph.
    Returns a dictionary of metrics.
    """
    try:
        metrics = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'average_degree': np.mean([d for n, d in G.degree()]),
            'clustering_coefficient': nx.average_clustering(G),
            'average_path_length': nx.average_shortest_path_length(G) if nx.is_connected(G) else float('inf'),
            'diameter': nx.diameter(G) if nx.is_connected(G) else float('inf'),
        }
        
        # Degree distribution stats
        degrees = [d for n, d in G.degree()]
        metrics['degree_std'] = np.std(degrees)
        metrics['max_degree'] = max(degrees) if degrees else 0
        metrics['min_degree'] = min(degrees) if degrees else 0
        
        return metrics
    except Exception as e:
        logger.error(f"Error computing metrics: {e}")
        return {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'average_degree': 0.0,
            'clustering_coefficient': 0.0,
            'average_path_length': float('inf'),
            'diameter': float('inf'),
            'degree_std': 0.0,
            'max_degree': 0,
            'min_degree': 0,
        }

def generate_networks(
    num_per_class: int = 10,
    N_min: int = 100,
    N_max: int = 200,
    base_seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate diverse synthetic oscillator network topologies.
    
    Args:
        num_per_class: Number of graphs to generate per class.
        N_min: Minimum number of nodes.
        N_max: Maximum number of nodes.
        base_seed: Base random seed for reproducibility.
        
    Returns:
        List of dictionaries containing graph data and metrics.
    """
    graphs_data = []
    failed_graphs = []
    
    classes = [
        ('random', generate_random_graph, {'p': 0.1}),
        ('scale_free', generate_scale_free_graph, {'m': 3}),
        ('small_world', generate_small_world_graph, {'k': 4, 'p': 0.1}),
        ('lattice', generate_lattice_graph, {}),
        ('star', generate_star_graph, {})
    ]
    
    logger.info(f"Starting generation of {num_per_class} graphs per class.")
    
    for class_name, generator_func, params in classes:
        generated_count = 0
        attempts = 0
        max_attempts = num_per_class * 10  # Prevent infinite loops
        
        while generated_count < num_per_class and attempts < max_attempts:
            attempts += 1
            seed = base_seed + attempts
            N = random.randint(N_min, N_max)
            
            try:
                # Generate graph
                if class_name == 'random':
                    G = generator_func(N, params['p'], seed)
                elif class_name == 'scale_free':
                    G = generator_func(N, params['m'], seed)
                elif class_name == 'small_world':
                    G = generator_func(N, params['k'], params['p'], seed)
                elif class_name == 'lattice':
                    G = generator_func(N, seed)
                elif class_name == 'star':
                    G = generator_func(N, seed)
                else:
                    raise ValueError(f"Unknown class: {class_name}")
                
                # Compute metrics
                metrics = compute_graph_metrics(G)
                
                # Theoretical validation
                validation_status = "valid"
                validation_details = ""
                
                if class_name == 'scale_free':
                    is_valid, p_val = validate_scale_free_graph(G)
                    if not is_valid:
                        validation_status = "invalid_power_law"
                        validation_details = f"KS-test p={p_val:.4f}"
                        # We still include it but flag it, or exclude? 
                        # Task T016 says "exclude from final set" on failure.
                        # However, scale-free generation is probabilistic. 
                        # Let's exclude if it fails the theoretical check.
                        raise ValueError(f"Scale-free validation failed: {validation_details}")
                
                elif class_name == 'random':
                    avg_match, clust_match = validate_random_graph(G, params['p'], N)
                    if not (avg_match and clust_match):
                        validation_status = "invalid_theoretical"
                        validation_details = f"avg_match={avg_match}, clust_match={clust_match}"
                        raise ValueError(f"Random graph validation failed: {validation_details}")
                
                # Add to list
                graph_id = f"{class_name}_{generated_count + 1}_{seed}"
                entry = {
                    'id': graph_id,
                    'class': class_name,
                    'N': N,
                    'seed': seed,
                    'validation_status': validation_status,
                    'validation_details': validation_details,
                    **metrics
                }
                graphs_data.append(entry)
                generated_count += 1
                logger.info(f"Generated {class_name} graph {generated_count}/{num_per_class} (ID: {graph_id})")
                
            except Exception as e:
                # Log the failure with specific graph ID
                failed_id = f"{class_name}_attempt_{attempts}_N_{N}_seed_{seed}"
                logger.error(f"Generation failure for graph ID '{failed_id}': {e}")
                failed_graphs.append({
                    'id': failed_id,
                    'class': class_name,
                    'N': N,
                    'seed': seed,
                    'error': str(e)
                })
                # Exclude from final set (do not append to graphs_data)
                continue
        
        if generated_count < num_per_class:
            logger.warning(f"Failed to generate {num_per_class} graphs for class {class_name}. Generated {generated_count}.")
    
    if failed_graphs:
        logger.warning(f"Total {len(failed_graphs)} graphs failed generation and were excluded.")
    
    return graphs_data, failed_graphs

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save generated network data to CSV."""
    import csv
    
    if not data:
        logger.warning("No data to save.")
        return
    
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} rows to {filepath}")

def generate_checksum(filepath: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic network topologies.")
    parser.add_argument('--num-per-class', type=int, default=10, help='Number of graphs per class')
    parser.add_argument('--N-min', type=int, default=100, help='Minimum nodes')
    parser.add_argument('--N-max', type=int, default=200, help='Maximum nodes')
    parser.add_argument('--seed', type=int, default=42, help='Base seed')
    parser.add_argument('--output', type=str, default='data/raw/networks.csv', help='Output CSV path')
    parser.add_argument('--failed-log', type=str, default='data/raw/failed_generations.json', help='Log for failed graphs')
    args = parser.parse_args()
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.failed_log).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating networks: {args.num_per_class} per class, N=[{args.N_min}, {args.N_max}], seed={args.seed}")
    
    graphs_data, failed_graphs = generate_networks(
        num_per_class=args.num_per_class,
        N_min=args.N_min,
        N_max=args.N_max,
        base_seed=args.seed
    )
    
    # Save successful graphs
    save_to_csv(graphs_data, args.output)
    
    # Save failed graphs to JSON log
    if failed_graphs:
        with open(args.failed_log, 'w') as f:
            json.dump(failed_graphs, f, indent=2)
        logger.info(f"Saved {len(failed_graphs)} failed graph records to {args.failed_log}")
    else:
        # Ensure file exists even if empty to satisfy schema/checksum requirements
        with open(args.failed_log, 'w') as f:
            json.dump([], f)
    
    # Generate checksum
    checksum = generate_checksum(args.output)
    checksum_file = str(Path(args.output).with_suffix('.sha256'))
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {args.output}\n")
    logger.info(f"Checksum saved to {checksum_file}: {checksum}")
    
    print(f"Successfully generated {len(graphs_data)} networks.")
    if failed_graphs:
        print(f"Excluded {len(failed_graphs)} failed generations.")

if __name__ == '__main__':
    main()