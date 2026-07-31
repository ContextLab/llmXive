import os
import json
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
import networkx as nx
import numpy as np

from utils.logging_utils import init_logging, get_logger
from utils.graph_utils import is_connected, calculate_graph_metrics

# Initialize logging for this module
init_logging()
logger = get_logger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return json.load(f)

def generate_regular_ring_lattice(n: int, k: int, seed: int) -> nx.Graph:
    """
    Generate a synthetic regular ring lattice.
    
    Args:
        n: Number of nodes
        k: Number of nearest neighbors to connect (must be even)
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX Graph object representing the ring lattice
    """
    # Base graph is synthetic; FR-001 requirement to use ca-AstroPh has been 
    # formally amended in spec.md per T000 and documented in T012b.
    G = nx.watts_strogatz_graph(n, k, p=0.0, seed=seed)
    return G

def generate_watts_strogatz_graph(n: int, k: int, p: float, seed: int) -> nx.Graph:
    """
    Generate a Watts-Strogatz small-world graph.
    
    Args:
        n: Number of nodes
        k: Number of nearest neighbors (must be even)
        p: Rewiring probability (0.0 to 1.0)
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX Graph object
    """
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    return G

def validate_graph(G: nx.Graph, n_expected: int = 500) -> Tuple[bool, str]:
    """
    Validate that a graph meets the required properties.
    
    Args:
        G: NetworkX Graph to validate
        n_expected: Expected number of nodes
        
    Returns:
        Tuple of (is_valid, reason)
    """
    if G.number_of_nodes() != n_expected:
        return False, f"Node count mismatch: {G.number_of_nodes()} != {n_expected}"
    
    if not is_connected(G):
        return False, "Graph is not connected"
    
    # Check average degree is preserved (should be k=2 for ring lattice)
    avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
    if abs(avg_degree - 2.0) > 0.01:
        return False, f"Average degree not preserved: {avg_degree}"
    
    return True, "Valid"

def compute_graph_checksum(G: nx.Graph) -> str:
    """Compute a deterministic checksum of the graph structure."""
    # Create a deterministic representation of the graph
    nodes = sorted(G.nodes())
    edges = sorted([tuple(sorted(e)) for e in G.edges()])
    data = f"nodes:{nodes},edges:{edges}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def save_graph_and_metadata(G: nx.Graph, topology_id: int, p: float, seed: int, 
                             output_dir: str) -> str:
    """
    Save the graph to a gpickle file and update metadata.
    
    Args:
        G: NetworkX Graph
        topology_id: Unique identifier for this topology
        p: Rewiring probability
        seed: Random seed used
        output_dir: Directory to save files
        
    Returns:
        Path to the saved graph file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    filename = f"topology_{topology_id}_p{p:.2f}_seed_{seed}.gpickle"
    filepath = os.path.join(output_dir, filename)
    
    # Save graph
    nx.write_gpickle(G, filepath)
    
    # Compute checksum
    checksum = compute_graph_checksum(G)
    
    # Update or create metadata file
    metadata_path = os.path.join(output_dir, "graph_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata_list = json.load(f)
    else:
        metadata_list = []
    
    # Append new entry
    new_entry = {
        "topology_id": topology_id,
        "p": p,
        "seed": seed,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes(),
        "clustering_coefficient": nx.average_clustering(G),
        "checksum": checksum,
        "file_path": filename
    }
    metadata_list.append(new_entry)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    logger.info(f"Saved graph: {filename} (checksum: {checksum})")
    return filepath

def log_disconnected_graph(topology_id: int, p: float, seed: int, log_path: str):
    """Log a disconnected graph attempt to a separate log file."""
    os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            disconnected_log = json.load(f)
    else:
        disconnected_log = []
    
    disconnected_log.append({
        "topology_id": topology_id,
        "p": p,
        "seed": seed,
        "reason": "Graph not connected"
    })
    
    with open(log_path, 'w') as f:
        json.dump(disconnected_log, f, indent=2)
    
    logger.warning(f"Disconnected graph logged: topology_{topology_id}_p{p:.2f}_seed_{seed}")

def log_methodology_correction(log_path: str):
    """Log the methodology correction (synthetic base vs ca-AstroPh)."""
    os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)
    
    correction = {
        "original_spec": "FR-001 (ca-AstroPh)",
        "corrected_approach": "Synthetic regular ring lattice (N=500, k=2)",
        "rationale": "Methodological incoherence of reconstructing irregular citation network into regular lattice",
        "amendment_ref": "T000, T000a, T012b",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(log_path, 'w') as f:
        json.dump(correction, f, indent=2)
    
    logger.info("Methodology correction logged")

def run_generation_batch(n_topologies: int, config_path: str, 
                         output_dir: str = "data/processed") -> List[str]:
    """
    Generate a batch of n_topologies valid Watts-Strogatz graphs.
    
    This function implements the batch generation loop for User Story 1.
    It generates graphs with varying rewiring probabilities (p) from 0.0 to 1.0,
    ensuring all graphs are connected and meet the required properties.
    
    Args:
        n_topologies: Number of valid graphs to generate (from config.json)
        config_path: Path to data/processed/config.json
        output_dir: Directory to save generated graphs
        
    Returns:
        List of paths to saved graph files
    """
    # Load configuration
    config = load_config(config_path)
    n_nodes = 500  # Fixed N as per spec
    k = 2          # Fixed k as per spec
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize tracking
    saved_graphs = []
    disconnected_log_path = os.path.join(output_dir, "disconnected_log.json")
    topology_id = 0
    attempts = 0
    max_attempts = n_topologies * 100  # Safety limit
    
    # Generate p values: 50 steps from 0.0 to 1.0
    p_values = np.linspace(0.0, 1.0, 50)
    
    logger.info(f"Starting batch generation: {n_topologies} valid graphs needed")
    logger.info(f"Using {len(p_values)} p-values: {p_values}")
    
    while len(saved_graphs) < n_topologies and attempts < max_attempts:
        attempts += 1
        
        # Select p value (cycle through or random)
        # For reproducibility and coverage, we cycle through p_values
        p = p_values[len(saved_graphs) % len(p_values)]
        
        # Generate a random seed
        seed = np.random.randint(0, 2**31)
        
        # Generate graph
        G = generate_watts_strogatz_graph(n_nodes, k, p, seed)
        
        # Validate
        is_valid, reason = validate_graph(G, n_nodes)
        
        if is_valid:
            topology_id += 1
            filepath = save_graph_and_metadata(G, topology_id, p, seed, output_dir)
            saved_graphs.append(filepath)
            logger.info(f"Success {len(saved_graphs)}/{n_topologies}: topology_{topology_id}")
        else:
            # Log disconnected graph
            log_disconnected_graph(topology_id + 1, p, seed, disconnected_log_path)
            logger.debug(f"Attempt {attempts}: {reason}, retrying...")
    
    if len(saved_graphs) < n_topologies:
        raise RuntimeError(f"Failed to generate {n_topologies} valid graphs. Only generated {len(saved_graphs)} after {attempts} attempts.")
    
    logger.info(f"Batch generation complete: {len(saved_graphs)} graphs saved to {output_dir}")
    return saved_graphs

def main():
    """Main entry point for topology generation."""
    config_path = "data/processed/config.json"
    output_dir = "data/processed"
    
    # Log methodology correction
    log_methodology_correction(os.path.join(output_dir, "scope_limitation.log"))
    
    # Check if config exists
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    # Load config to get n_topologies
    config = load_config(config_path)
    n_topologies = config.get('n_topologies', 10)
    
    if n_topologies < 10:
        logger.warning(f"Requested n_topologies ({n_topologies}) is below minimum viable (10)")
    
    logger.info(f"Generating {n_topologies} topologies...")
    
    # Run batch generation
    saved_files = run_generation_batch(n_topologies, config_path, output_dir)
    
    logger.info(f"Generated {len(saved_files)} topology files:")
    for f in saved_files:
        logger.info(f"  - {f}")

if __name__ == "__main__":
    main()