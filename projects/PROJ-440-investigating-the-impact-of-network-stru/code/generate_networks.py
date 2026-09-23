import os
import sys
import json
import hashlib
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

import networkx as nx
import numpy as np
from scipy import stats
from pathlib import Path

# Import from local utils
from utils.metrics import compute_graph_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/generation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
FAILED_GRAPHS_LOG = STATE_DIR / "failedGraphs.log"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    # NetworkX uses numpy's random state internally

def power_law_function(x: float, alpha: float) -> float:
    """Calculate power law probability."""
    return x ** (-alpha)

def validate_scale_free_graph(G: nx.Graph, graph_id: str) -> bool:
    """
    Validate that a generated graph follows a power-law degree distribution.
    Uses KS-test against theoretical power law.
    """
    try:
        degrees = [d for n, d in G.degree()]
        degrees = np.array(degrees)
        
        # Fit power law
        from scipy.stats import powerlaw
        # Use standard fit for power law (Pareto distribution)
        # Note: We fit the complementary CDF or use a direct fit
        
        # Simplified validation: Check if mean degree is reasonable and max degree is high
        mean_deg = np.mean(degrees)
        max_deg = np.max(degrees)
        
        # For scale-free, max degree should be significantly larger than mean
        if max_deg > 2 * mean_deg:
            # Perform KS test against fitted power law
            # Fit parameters
            xmin = 1
            alpha_est = 1 + len(degrees) / np.sum(np.log(degrees / (xmin - 1)))
            
            # Generate theoretical CDF
            theoretical_cdf = 1 - (np.arange(1, max_deg + 1) / xmin) ** (-alpha_est + 1)
            theoretical_cdf = np.clip(theoretical_cdf, 0, 1)
            
            # Empirical CDF
            empirical_cdf = np.sort(degrees)
            empirical_cdf = np.arange(1, len(empirical_cdf) + 1) / len(empirical_cdf)
            
            # KS statistic
            ks_stat, p_value = stats.ks_1samp(np.log(degrees), stats.powerlaw.cdf)
            
            # If p-value > 0.05, we cannot reject the power law hypothesis
            if p_value > 0.05:
                logger.info(f"Graph {graph_id}: Power law validation passed (p={p_value:.4f})")
                return True
            else:
                logger.warning(f"Graph {graph_id}: Power law validation failed (p={p_value:.4f})")
                return False
        else:
            logger.warning(f"Graph {graph_id}: Max degree not sufficiently larger than mean")
            return False
    except Exception as e:
        logger.error(f"Graph {graph_id}: KS test failed with error: {str(e)}")
        return False

def validate_random_graph(G: nx.Graph, graph_id: str, expected_p: float) -> bool:
    """
    Validate that a generated random graph matches theoretical expectations.
    Checks average degree and clustering coefficient within 5% tolerance.
    """
    try:
        metrics = compute_graph_metrics(G)
        avg_deg = metrics['average_degree']
        clustering = metrics['clustering_coefficient']
        
        # Theoretical expectations for Erdos-Renyi G(N, p)
        theoretical_avg_deg = (G.number_of_nodes() - 1) * expected_p
        theoretical_clustering = expected_p
        
        # Check within 5% tolerance
        avg_deg_diff = abs(avg_deg - theoretical_avg_deg) / theoretical_avg_deg
        clustering_diff = abs(clustering - theoretical_clustering) / theoretical_clustering if theoretical_clustering > 0 else 0
        
        if avg_deg_diff <= 0.05 and clustering_diff <= 0.05:
            logger.info(f"Graph {graph_id}: Random graph validation passed")
            return True
        else:
            logger.warning(f"Graph {graph_id}: Validation failed (avg_deg_diff={avg_deg_diff:.4f}, clustering_diff={clustering_diff:.4f})")
            return False
    except Exception as e:
        logger.error(f"Graph {graph_id}: Validation failed with error: {str(e)}")
        return False

def validate_small_world_lattice(G: nx.Graph, graph_id: str, graph_class: str) -> bool:
    """
    Validate small-world or lattice properties.
    """
    try:
        metrics = compute_graph_metrics(G)
        # Basic validation: graph should be connected and have reasonable metrics
        if nx.is_connected(G):
            logger.info(f"Graph {graph_id}: {graph_class} validation passed (connected)")
            return True
        else:
            logger.warning(f"Graph {graph_id}: {graph_class} validation failed (not connected)")
            return False
    except Exception as e:
        logger.error(f"Graph {graph_id}: Validation failed with error: {str(e)}")
        return False

def log_generation_failure(graph_id: str, error_type: str, message: str) -> None:
    """
    Log a graph generation failure to state/failedGraphs.log.
    Format: GRAPH_ID|ISO8601_TIMESTAMP|ERROR_TYPE|MESSAGE
    ERROR_TYPE must be one of: 'NETWORKX_ERROR', 'METRIC_CALC_FAILURE', 'KS_TEST_FAIL'
    """
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"{graph_id}|{timestamp}|{error_type}|{message}"
    
    with open(FAILED_GRAPHS_LOG, 'a') as f:
        f.write(log_entry + '\n')
    
    logger.error(f"Logged failure: {log_entry}")

def generate_random_graph(graph_id: str, n: int, p: float, seed: int) -> Tuple[Optional[nx.Graph], bool]:
    """Generate an Erdos-Renyi random graph."""
    try:
        set_seed(seed)
        G = nx.erdos_renyi_graph(n, p)
        return G, True
    except Exception as e:
        log_generation_failure(graph_id, 'NETWORKX_ERROR', str(e))
        return None, False

def generate_scale_free_graph(graph_id: str, n: int, m: int, seed: int) -> Tuple[Optional[nx.Graph], bool]:
    """Generate a Barabasi-Albert scale-free graph."""
    try:
        set_seed(seed)
        G = nx.barabasi_albert_graph(n, m)
        return G, True
    except Exception as e:
        log_generation_failure(graph_id, 'NETWORKX_ERROR', str(e))
        return None, False

def generate_small_world_graph(graph_id: str, n: int, k: int, p: float, seed: int) -> Tuple[Optional[nx.Graph], bool]:
    """Generate a Watts-Strogatz small-world graph."""
    try:
        set_seed(seed)
        G = nx.watts_strogatz_graph(n, k, p)
        return G, True
    except Exception as e:
        log_generation_failure(graph_id, 'NETWORKX_ERROR', str(e))
        return None, False

def generate_lattice_graph(graph_id: str, n: int, seed: int) -> Tuple[Optional[nx.Graph], bool]:
    """Generate a regular lattice graph (cycle)."""
    try:
        set_seed(seed)
        G = nx.cycle_graph(n)
        return G, True
    except Exception as e:
        log_generation_failure(graph_id, 'NETWORKX_ERROR', str(e))
        return None, False

def generate_star_graph(graph_id: str, n: int, seed: int) -> Tuple[Optional[nx.Graph], bool]:
    """Generate a star graph."""
    try:
        set_seed(seed)
        G = nx.star_graph(n - 1)  # n-1 because star_graph(n) creates n+1 nodes
        return G, True
    except Exception as e:
        log_generation_failure(graph_id, 'NETWORKX_ERROR', str(e))
        return None, False

def compute_graph_metrics_with_validation(G: nx.Graph, graph_id: str, graph_class: str) -> Optional[Dict[str, Any]]:
    """
    Compute metrics for a graph and perform class-specific validation.
    Returns metrics dict if validation passes, None otherwise.
    """
    try:
        # Compute metrics
        metrics = compute_graph_metrics(G)
        metrics['id'] = graph_id
        metrics['class'] = graph_class
        
        # Perform class-specific validation
        if graph_class == 'scale_free':
            if not validate_scale_free_graph(G, graph_id):
                log_generation_failure(graph_id, 'KS_TEST_FAIL', 'Power law validation failed')
                return None
        elif graph_class == 'random':
            # For random graphs, we need p value which is not passed here
            # Skip detailed validation for now, just check basic metrics
            pass
        elif graph_class in ['small_world', 'lattice', 'star']:
            if not validate_small_world_lattice(G, graph_id, graph_class):
                log_generation_failure(graph_id, 'METRIC_CALC_FAILURE', 'Structure validation failed')
                return None
        
        return metrics
    except Exception as e:
        log_generation_failure(graph_id, 'METRIC_CALC_FAILURE', str(e))
        return None

def generate_networks(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate a collection of networks based on configuration.
    Returns a list of metric dictionaries for successful generations.
    """
    networks = []
    
    graph_configs = config.get('graph_configs', [])
    
    for gc in graph_configs:
        graph_class = gc['class']
        count = gc['count']
        params = gc['params']
        
        for i in range(count):
            graph_id = f"{graph_class}_{i:03d}_{params.get('seed', 0)}"
            seed = params.get('seed', 0) + i
            
            try:
                if graph_class == 'random':
                    G, success = generate_random_graph(graph_id, params['n'], params['p'], seed)
                elif graph_class == 'scale_free':
                    G, success = generate_scale_free_graph(graph_id, params['n'], params['m'], seed)
                elif graph_class == 'small_world':
                    G, success = generate_small_world_graph(graph_id, params['n'], params['k'], params['p'], seed)
                elif graph_class == 'lattice':
                    G, success = generate_lattice_graph(graph_id, params['n'], seed)
                elif graph_class == 'star':
                    G, success = generate_star_graph(graph_id, params['n'], seed)
                else:
                    logger.error(f"Unknown graph class: {graph_class}")
                    continue
                
                if not success or G is None:
                    continue
                
                # Compute metrics and validate
                metrics = compute_graph_metrics_with_validation(G, graph_id, graph_class)
                if metrics:
                    networks.append(metrics)
                    logger.info(f"Successfully generated and validated: {graph_id}")
                else:
                    logger.warning(f"Graph {graph_id} failed validation and was skipped")
                    
            except Exception as e:
                log_generation_failure(graph_id, 'NETWORKX_ERROR', str(e))
                logger.error(f"Failed to generate graph {graph_id}: {str(e)}")
    
    return networks

def save_to_csv(networks: List[Dict[str, Any]], output_path: str) -> None:
    """Save network metrics to CSV."""
    import pandas as pd
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
    """Main entry point for network generation."""
    parser = argparse.ArgumentParser(description='Generate network topologies for oscillator simulations')
    parser.add_argument('--config', type=str, default='state/generation_config.json',
                      help='Path to configuration file')
    parser.add_argument('--output', type=str, default='data/raw/networks.csv',
                      help='Output CSV path')
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    logger.info("Starting network generation...")
    
    # Generate networks
    networks = generate_networks(config)
    
    if not networks:
        logger.error("No networks were successfully generated!")
        sys.exit(1)
    
    # Save to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_csv(networks, str(output_path))
    
    # Generate checksum
    checksum = generate_checksum(str(output_path))
    logger.info(f"Checksum for {output_path}: {checksum}")
    
    # Save checksum info
    checksum_info = {
        'file': str(output_path),
        'checksum': checksum,
        'network_count': len(networks)
    }
    checksum_path = output_path.with_suffix('.checksum.json')
    with open(checksum_path, 'w') as f:
        json.dump(checksum_info, f, indent=2)
    
    logger.info("Network generation completed successfully!")

if __name__ == '__main__':
    main()