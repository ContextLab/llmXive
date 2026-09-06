from __future__ import annotations

import json
import logging
import os
import random
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

import networkx as nx
import numpy as np

from utils.logging_utils import get_logger, log_operation
from utils.graph_utils import is_connected, calculate_graph_metrics

# Initialize logger tolerant of call signatures
logger = get_logger("generate_topology")

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def generate_regular_ring_lattice(n: int, k: int, seed: int) -> nx.Graph:
    """
    Generate a synthetic regular ring lattice.
    
    Args:
        n: Number of nodes
        k: Each node is joined with its k nearest neighbors
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph object
    """
    # Using networkx's built-in function which creates a regular ring lattice
    # when p=0. We set p=0 explicitly to ensure it is a regular ring.
    G = nx.watts_strogatz_graph(n, k, 0.0, seed=seed)
    return G

def generate_watts_strogatz_graph(n: int, k: int, p: float, seed: int) -> nx.Graph:
    """
    Generate a Watts-Strogatz small-world graph.
    
    Args:
        n: Number of nodes
        k: Initial number of neighbors (must be even)
        p: Rewiring probability
        seed: Random seed
    
    Returns:
        NetworkX Graph object
    """
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    return G

def validate_graph(G: nx.Graph, n: int) -> Tuple[bool, str]:
    """
    Validate graph properties.
    
    Args:
        G: NetworkX Graph
        n: Expected number of nodes
    
    Returns:
        Tuple (is_valid, message)
    """
    if G.number_of_nodes() != n:
        return False, f"Node count mismatch: expected {n}, got {G.number_of_nodes()}"
    
    if not is_connected(G):
        return False, "Graph is not connected"
    
    return True, "Valid"

def compute_graph_checksum(G: nx.Graph) -> str:
    """
    Compute a deterministic checksum of the graph structure.
    
    Args:
        G: NetworkX Graph
    
    Returns:
        SHA256 hex digest string
    """
    # Sort nodes and edges for deterministic serialization
    nodes = sorted(G.nodes())
    edges = sorted(tuple(sorted(e)) for e in G.edges())
    
    # Create a string representation
    data = f"nodes:{nodes};edges:{edges}"
    return hashlib.sha256(data.encode()).hexdigest()

def save_graph_and_metadata(
    G: nx.Graph, 
    topology_id: int, 
    p: float, 
    seed: int, 
    output_dir: str,
    metadata_list: list
) -> str:
    """
    Save graph to gpickle and update metadata list.
    
    Args:
        G: NetworkX Graph
        topology_id: Unique ID for this topology
        p: Rewiring probability
        seed: Random seed used
        output_dir: Directory to save files
        metadata_list: List to append metadata to
    
    Returns:
        Path to the saved gpickle file
    """
    filename = f"topology_{topology_id}_p{p:.2f}_seed_{seed}.gpickle"
    filepath = os.path.join(output_dir, filename)
    
    nx.write_gpickle(G, filepath)
    
    # Compute checksum
    checksum = compute_graph_checksum(G)
    
    # Calculate metrics
    metrics = calculate_graph_metrics(G)
    
    metadata = {
        "topology_id": topology_id,
        "p": p,
        "seed": seed,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "avg_degree": float(metrics.get("average_degree", 0.0)),
        "clustering_coefficient": float(metrics.get("clustering_coefficient", 0.0)),
        "checksum": checksum,
        "file_path": filepath
    }
    
    metadata_list.append(metadata)
    
    return filepath

def log_disconnected_graph(p: float, seed: int, log_file: str, output_dir: str):
    """Log disconnected graph attempts to a specific file."""
    log_path = os.path.join(output_dir, "disconnected_log.json")
    
    entry = {
        "p": p,
        "seed": seed,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Read existing log if exists
    existing = []
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []
    
    existing.append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(existing, f, indent=2)

def log_methodology_correction(output_dir: str):
    """Log the methodology correction (synthetic ring lattice) to a file."""
    log_path = os.path.join(output_dir, "methodology_correction.json")
    
    correction = {
        "source": "FR-001 (Original) vs T000a (Correction)",
        "original_requirement": "Use ca-AstroPh citation network",
        "corrected_requirement": "Generate synthetic regular ring lattice (N=500, k=2)",
        "reason": "Reconstructing an irregular citation network into a regular ring lattice is methodologically incoherent. The Watts-Strogatz model requires a regular ring base.",
        "verified_by": "T000a (Spec Verification)"
    }
    
    with open(log_path, 'w') as f:
        json.dump(correction, f, indent=2)

def generate_batch(
    n_topologies: int, 
    config_path: str,
    n_nodes: int = 500,
    k_neighbors: int = 2
) -> List[str]:
    """
    Generate a batch of N valid (connected) Watts-Strogatz graphs.
    
    Logic:
    1. Read n_topologies from config.json.
    2. Generate a list of p values based on n_topologies count.
    3. Loop to generate valid graphs. Retry up to MAX_RETRIES for each p.
    4. Skip p if MAX_RETRIES reached, log warning.
    5. Stop when n_topologies valid graphs are saved or p-values exhausted.
    
    Args:
        n_topologies: Target number of valid topologies to generate
        config_path: Path to data/processed/config.json
        n_nodes: Number of nodes (default 500)
        k_neighbors: Number of neighbors (default 2)
    
    Returns:
        List of paths to saved .gpickle files
    """
    # Load config
    config = load_config(config_path)
    
    # Determine sampling strategy for p values
    if n_topologies >= 10:
        # Systematic coverage
        p_values = np.linspace(0.0, 1.0, n_topologies).tolist()
    else:
        # Fixed representative set truncated
        fixed_p = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        p_values = fixed_p[:n_topologies]
    
    # Record this in config for audit (update the loaded config dict)
    config["sampling_p_values"] = p_values
    
    # Save updated config back
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    output_dir = os.path.dirname(config_path)
    metadata_list = []
    saved_paths = []
    MAX_RETRIES = 10
    
    log_methodology_correction(output_dir)
    
    topology_id = 0
    
    for p in p_values:
        logger.info(f"Attempting to generate connected graph for p={p:.2f}")
        found_for_p = False
        
        for retry in range(MAX_RETRIES):
            seed = random.randint(0, 2**32 - 1)
            try:
                # Generate graph
                G = generate_watts_strogatz_graph(n_nodes, k_neighbors, p, seed)
                
                # Validate
                is_valid, msg = validate_graph(G, n_nodes)
                
                if is_valid:
                    path = save_graph_and_metadata(
                        G, topology_id, p, seed, output_dir, metadata_list
                    )
                    saved_paths.append(path)
                    topology_id += 1
                    found_for_p = True
                    logger.info(f"Saved topology_{topology_id-1} (p={p:.2f}, seed={seed})")
                    
                    if len(saved_paths) >= n_topologies:
                        break
                else:
                    # Log disconnected attempt
                    log_disconnected_graph(p, seed, output_dir, output_dir)
                    logger.warning(f"Graph disconnected for p={p:.2f}, seed={seed} (retry {retry+1}/{MAX_RETRIES})")
                    
            except Exception as e:
                logger.error(f"Error generating graph for p={p:.2f}, seed={seed}: {e}")
                log_disconnected_graph(p, seed, output_dir, output_dir)
        
        if not found_for_p:
            logger.warning(f"Failed to generate connected graph for p={p:.2f} after {MAX_RETRIES} retries. Skipping.")
        
        if len(saved_paths) >= n_topologies:
            break
    
    # Save metadata
    metadata_path = os.path.join(output_dir, "graph_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    logger.info(f"Batch generation complete. Saved {len(saved_paths)} topologies.")
    return saved_paths

def main():
    """Main entry point for batch generation."""
    config_path = "data/processed/config.json"
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    config = load_config(config_path)
    n_topologies = config.get("n_topologies", 10)
    
    logger.info(f"Starting batch generation for {n_topologies} topologies...")
    
    paths = generate_batch(n_topologies, config_path)
    
    logger.info(f"Generation finished. Total files: {len(paths)}")

if __name__ == "__main__":
    main()