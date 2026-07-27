"""
Topology Generation Module for Network Synchronization Study.

This module implements the generation of network topologies using the
Watts-Strogatz small-world model, starting from a synthetic regular ring lattice.
It handles batch generation, validation, metadata logging, and checksum updates.

Note: The base graph is synthetic; FR-001 requirement to use ca-AstroPh has been
formally amended in spec.md per T000 and documented in T012b.
"""

import os
import json
import logging
import time
import hashlib
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import networkx as nx
import numpy as np

# Import from local utils (defined in the project API surface)
from utils.graph_utils import is_connected, calculate_graph_metrics
from utils.logging_utils import init_logging, get_logger, log_warning, log_error
from utils.checksum_utils import compute_file_checksum, write_checksums_file

# Constants
DEFAULT_N_NODES = 500
DEFAULT_K_NEIGHBORS = 2
DEFAULT_SEED = 42
OUTPUT_DIR = Path("data/processed")
METADATA_FILE = OUTPUT_DIR / "graph_metadata.json"
DISCONNECTED_LOG_FILE = OUTPUT_DIR / "disconnected_log.json"
CHECKSUMS_FILE = Path("data/checksums.txt")
METHODOLOGY_LOG = OUTPUT_DIR / "scope_limitation.log"

def init_logging_module():
    """Initialize logging for this module."""
    return init_logging("generate_topology")

def generate_regular_ring_lattice(n: int = DEFAULT_N_NODES, k: int = DEFAULT_K_NEIGHBORS, seed: int = DEFAULT_SEED) -> nx.Graph:
    """
    Generate a synthetic regular ring lattice.

    Args:
        n: Number of nodes.
        k: Each node is connected to k nearest neighbors in ring order.
        seed: Random seed for reproducibility (not used here but kept for API consistency).

    Returns:
        A NetworkX Graph object representing the ring lattice.
    """
    # Base graph is synthetic; FR-001 requirement to use ca-AstroPh has been
    # formally amended in spec.md per T000 and documented in T012b.
    logger = get_logger()
    logger.info(f"Generating synthetic regular ring lattice: N={n}, k={k}, seed={seed}")
    
    G = nx.watts_strogatz_graph(n=n, k=k, p=0.0, seed=seed)
    
    # Verify properties
    assert G.number_of_nodes() == n, f"Expected {n} nodes, got {G.number_of_nodes()}"
    assert G.number_of_edges() == (n * k) // 2, f"Expected {(n * k) // 2} edges, got {G.number_of_edges()}"
    
    logger.info("Regular ring lattice generated successfully.")
    return G

def generate_watts_strogatz_graph(n: int = DEFAULT_N_NODES, k: int = DEFAULT_K_NEIGHBORS, p: float = 0.5, seed: int = DEFAULT_SEED) -> nx.Graph:
    """
    Generate a Watts-Strogatz small-world graph.

    Args:
        n: Number of nodes.
        k: Each node is connected to k nearest neighbors in ring order.
        p: Probability of rewiring each edge.
        seed: Random seed for reproducibility.

    Returns:
        A NetworkX Graph object representing the Watts-Strogatz graph.
    """
    logger = get_logger()
    logger.info(f"Generating Watts-Strogatz graph: N={n}, k={k}, p={p}, seed={seed}")
    
    G = nx.watts_strogatz_graph(n=n, k=k, p=p, seed=seed)
    
    return G

def validate_graph(G: nx.Graph, expected_n: int = DEFAULT_N_NODES) -> Tuple[bool, str]:
    """
    Validate a generated graph.

    Args:
        G: The graph to validate.
        expected_n: Expected number of nodes.

    Returns:
        Tuple of (is_valid, message).
    """
    logger = get_logger()
    
    # Check node count
    if G.number_of_nodes() != expected_n:
        msg = f"Node count mismatch: expected {expected_n}, got {G.number_of_nodes()}"
        logger.error(msg)
        return False, msg
    
    # Check connectivity
    if not is_connected(G):
        msg = f"Graph is disconnected (nodes={G.number_of_nodes()}, edges={G.number_of_edges()})"
        logger.warning(msg)
        return False, msg
    
    # Check average degree preservation
    avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
    expected_avg_degree = 2 * DEFAULT_K_NEIGHBORS  # For regular ring lattice
    if abs(avg_degree - expected_avg_degree) > 1e-6:
        msg = f"Average degree mismatch: expected {expected_avg_degree}, got {avg_degree}"
        logger.warning(msg)
        # We allow this warning but don't fail validation as rewiring preserves degree
    
    return True, "Graph is valid."

def save_graph_and_metadata(G: nx.Graph, p: float, seed: int, output_dir: Path = OUTPUT_DIR) -> str:
    """
    Save a graph to disk and update metadata.

    Args:
        G: The graph to save.
        p: Rewiring probability.
        seed: Random seed used.
        output_dir: Directory to save files.

    Returns:
        Path to the saved graph file.
    """
    logger = get_logger()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"graph_p{p:.2f}_seed_{seed}.gpickle"
    filepath = output_dir / filename
    
    # Save graph
    nx.write_gpickle(G, str(filepath))
    logger.info(f"Saved graph to {filepath}")
    
    # Compute checksum
    checksum = compute_file_checksum(filepath)
    
    # Update metadata
    metadata_entry = {
        "filename": filename,
        "p": p,
        "seed": seed,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes(),
        "clustering_coefficient": nx.average_clustering(G),
        "checksum": checksum
    }
    
    # Load existing metadata or initialize
    metadata_path = output_dir / "graph_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata_list = json.load(f)
    else:
        metadata_list = []
    
    metadata_list.append(metadata_entry)
    
    # Save updated metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    # Update checksums file
    update_checksums_file(filepath, checksum)
    
    return str(filepath)

def update_checksums_file(filepath: Path, checksum: str):
    """Update the global checksums file with a new entry."""
    checksums_path = CHECKSUMS_FILE
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing checksums
    existing = {}
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    existing[parts[1]] = parts[0]
    
    # Add new entry
    existing[filepath.name] = checksum
    
    # Write back
    with open(checksums_path, 'w') as f:
        for fname, cksum in existing.items():
            f.write(f"{cksum} {fname}\n")

def log_disconnected_graph(p: float, seed: int, disconnected_log_path: Path = DISCONNECTED_LOG_FILE):
    """Log a disconnected graph attempt to the disconnected log file."""
    logger = get_logger()
    disconnected_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing log
    if disconnected_log_path.exists():
        with open(disconnected_log_path, 'r') as f:
            log_data = json.load(f)
    else:
        log_data = {"count": 0, "entries": []}
    
    # Add entry
    entry = {"p": p, "seed": seed, "reason": "Disconnected graph"}
    log_data["entries"].append(entry)
    log_data["count"] += 1
    
    # Save
    with open(disconnected_log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.warning(f"Logged disconnected graph: p={p}, seed={seed}")

def log_methodology_correction():
    """Log the methodology correction (synthetic base vs ca-AstroPh)."""
    logger = get_logger()
    log_path = METHODOLOGY_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    correction_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "original_spec": "FR-001 (ca-AstroPh)",
        "actual_approach": "Synthetic regular ring lattice (N=500)",
        "justification": "Methodological incoherence of reconstructing irregular citation network into regular lattice",
        "reference": "T000, T000a, T012b"
    }
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(correction_entry) + "\n")
    
    logger.info("Logged methodology correction.")

def load_config() -> Dict[str, Any]:
    """Load configuration from data/processed/config.json."""
    config_path = Path("data/processed/config.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def run_generation_batch(config: Optional[Dict[str, Any]] = None):
    """
    Run the batch generation loop for network topologies.

    Generates N topologies with rewiring probabilities ranging from 0.0 to 1.0
    in 50 steps, as defined in the configuration.

    Args:
        config: Configuration dictionary. If None, loads from data/processed/config.json.
    """
    logger = init_logging_module()
    logger.info("Starting batch generation of network topologies.")
    
    # Load config if not provided
    if config is None:
        config = load_config()
    
    n_topologies = config.get("n_topologies", 50)
    logger.info(f"Generating {n_topologies} topologies.")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize disconnected log
    if not DISCONNECTED_LOG_FILE.exists():
        with open(DISCONNECTED_LOG_FILE, 'w') as f:
            json.dump({"count": 0, "entries": []}, f)
    
    # Initialize metadata file
    if not METADATA_FILE.exists():
        with open(METADATA_FILE, 'w') as f:
            json.dump([], f)
    
    # Log methodology correction
    log_methodology_correction()
    
    # Generate p values: 50 steps from 0.0 to 1.0
    # We need to generate n_topologies graphs, distributed across 50 p steps
    # If n_topologies is 50, we generate one graph per p step
    # If n_topologies is different, we distribute as evenly as possible
    
    p_values = np.linspace(0.0, 1.0, 50)
    
    # Distribute n_topologies across p_values
    # We'll generate floor(n_topologies / 50) graphs for each p, 
    # and distribute the remainder
    base_count = n_topologies // 50
    remainder = n_topologies % 50
    
    generated_count = 0
    skipped_count = 0
    
    for i, p in enumerate(p_values):
        # Determine how many graphs to generate for this p
        count = base_count + (1 if i < remainder else 0)
        
        for j in range(count):
            seed = DEFAULT_SEED + generated_count
            
            # Generate graph
            G = generate_watts_strogatz_graph(n=DEFAULT_N_NODES, k=DEFAULT_K_NEIGHBORS, p=p, seed=seed)
            
            # Validate graph
            is_valid, msg = validate_graph(G)
            
            if not is_valid:
                log_disconnected_graph(p, seed)
                skipped_count += 1
                logger.warning(f"Skipped disconnected graph: p={p}, seed={seed}")
                continue
            
            # Save graph and metadata
            save_graph_and_metadata(G, p, seed)
            generated_count += 1
            logger.info(f"Generated graph {generated_count}/{n_topologies}: p={p}, seed={seed}")
    
    logger.info(f"Batch generation complete. Generated: {generated_count}, Skipped: {skipped_count}")
    
    # Verify total
    total_expected = generated_count + skipped_count
    if total_expected != n_topologies:
        logger.error(f"Total mismatch: expected {n_topologies}, got {total_expected}")
        raise RuntimeError(f"Generation mismatch: expected {n_topologies}, got {total_expected}")
    
    return {
        "generated": generated_count,
        "skipped": skipped_count,
        "total": total_expected
    }

def main():
    """Main entry point for the topology generation script."""
    logger = init_logging_module()
    logger.info("=== Topology Generation Script Started ===")
    
    try:
        result = run_generation_batch()
        logger.info(f"Generation result: {result}")
        logger.info("=== Topology Generation Script Completed Successfully ===")
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise

if __name__ == "__main__":
    main()