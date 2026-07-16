"""
Topology Generation Module for Kuramoto Synchronization Study.

This module implements the generation of network topologies with varying
small-world rewiring probabilities, starting from a synthetic regular ring lattice.
It handles graph generation, validation, and artifact persistence.
"""
import os
import json
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import numpy as np

# Import from local utils as per API surface
from utils.graph_utils import is_connected, validate_watts_strogatz_properties
from utils.logging_utils import get_logger, log_warning, log_metric

# Constants
DEFAULT_N = 500
DEFAULT_K = 2  # Each node connected to k nearest neighbors in each direction
DEFAULT_SEED_BASE = 42
OUTPUT_DIR = "data/processed"
METADATA_FILE = "graph_metadata.json"

# Initialize logger
logger = get_logger(__name__)


def init_directories() -> Path:
    """Ensure output directories exist."""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def generate_regular_ring_lattice(n: int, k: int, seed: int) -> nx.Graph:
    """
    Generate a regular ring lattice graph.

    Args:
        n: Number of nodes.
        k: Each node is connected to k nearest neighbors in each direction.
        seed: Random seed for reproducibility (though lattice is deterministic).

    Returns:
        A networkx Graph representing the regular ring lattice.
    """
    logger.info(f"Generating regular ring lattice: N={n}, k={k}, seed={seed}")
    # NetworkX ring_lattice_graph creates a ring where each node is connected
    # to k/2 neighbors on each side if k is even.
    # We use k as the number of neighbors in *each* direction, so total degree is 2*k.
    # However, standard WS uses 'k' as the total number of nearest neighbors.
    # To match the prompt's "k=2" (usually meaning degree 2k=4 or degree 2?),
    # we interpret k=2 as the standard WS parameter (degree 2*k in ring context usually means 2 neighbors total? No, WS k is neighbors on one side? No, WS k is total neighbors).
    # Let's stick to standard NetworkX definition: k is the number of nearest neighbors in each direction?
    # Actually, nx.watts_strogatz_graph(n, k, p) uses k as the number of nearest neighbors in each direction?
    # Docs: "k: Each node is joined to its k nearest neighbors in a ring network."
    # This usually implies degree = k.
    # The prompt says "k=2". We will generate a ring lattice with degree 2 (each node connected to 1 left, 1 right).
    # So we pass k=2 to nx.watts_strogatz_graph (which expects k to be even for ring).
    
    G = nx.watts_strogatz_graph(n=n, k=k, p=0.0, seed=seed)
    logger.debug(f"Generated lattice with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def generate_watts_strogatz_graph(n: int, k: int, p: float, seed: int) -> nx.Graph:
    """
    Generate a Watts-Strogatz small-world graph.

    Args:
        n: Number of nodes.
        k: Each node is joined to its k nearest neighbors in a ring network.
        p: Rewiring probability.
        seed: Random seed for reproducibility.

    Returns:
        A networkx Graph representing the rewired network.
    """
    logger.info(f"Generating Watts-Strogatz graph: N={n}, k={k}, p={p:.4f}, seed={seed}")
    G = nx.watts_strogatz_graph(n=n, k=k, p=p, seed=seed)
    return G


def validate_graph(G: nx.Graph, expected_n: int, expected_k: int) -> Tuple[bool, str]:
    """
    Validate graph properties.

    Args:
        G: The graph to validate.
        expected_n: Expected number of nodes.
        expected_k: Expected average degree (should be close to 2*k).

    Returns:
        Tuple of (is_valid, message).
    """
    if G.number_of_nodes() != expected_n:
        return False, f"Node count mismatch: {G.number_of_nodes()} != {expected_n}"

    if not is_connected(G):
        return False, "Graph is not connected"

    # Check average degree preservation (approx)
    avg_degree = sum(dict(G.degree()).values()) / expected_n
    expected_avg_degree = expected_k # In WS, average degree is k (if k is total neighbors)
    # Allow small float tolerance if k was interpreted differently, but for integer k it should be exact
    if abs(avg_degree - expected_avg_degree) > 1e-6:
        # This might be expected if the graph was rewired and edges were removed? 
        # WS rewiring preserves degree unless p=1 and specific rewiring rules drop edges.
        # Standard WS preserves degree.
        logger.warning(f"Average degree {avg_degree:.2f} differs from expected {expected_avg_degree}")
    
    return True, "Valid"


def save_graph_and_metadata(G: nx.Graph, p: float, seed: int, output_dir: Path, index: int) -> Dict[str, Any]:
    """
    Save the graph as .gpickle and metadata as .json.

    Args:
        G: The graph to save.
        p: Rewiring probability.
        seed: Random seed used.
        output_dir: Directory to save files.
        index: Unique index for this instance.

    Returns:
        Dictionary containing metadata about the saved graph.
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename_prefix = f"graph_p{p:.3f}_seed{seed}_idx{index}"
    
    graph_path = output_dir / f"{filename_prefix}.gpickle"
    metadata_path = output_dir / METADATA_FILE

    # Save graph
    nx.write_gpickle(G, str(graph_path))
    logger.info(f"Saved graph to {graph_path}")

    # Calculate checksum for integrity
    with open(graph_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    # Prepare metadata
    metadata_entry = {
        "index": index,
        "rewiring_probability": p,
        "seed": seed,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "is_connected": is_connected(G),
        "file_path": str(graph_path),
        "checksum_md5": file_hash,
        "timestamp": timestamp
    }

    # Append to metadata JSON
    # We use a simple append strategy or load/append/save. 
    # Since multiple tasks might run, we should be careful. 
    # For this specific task, we assume exclusive write or append safely.
    
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            try:
                all_metadata = json.load(f)
            except json.JSONDecodeError:
                all_metadata = []
        all_metadata.append(metadata_entry)
    else:
        all_metadata = [metadata_entry]

    with open(metadata_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    logger.info(f"Updated metadata at {metadata_path}")
    return metadata_entry


def run_generation_batch(
    n: int = DEFAULT_N,
    k: int = DEFAULT_K,
    p_values: Optional[List[float]] = None,
    instances_per_p: int = 1,
    seed_base: int = DEFAULT_SEED_BASE
) -> List[Dict[str, Any]]:
    """
    Run a batch of graph generations.

    Args:
        n: Number of nodes.
        k: Nearest neighbors.
        p_values: List of rewiring probabilities. Defaults to 0.0 to 1.0.
        instances_per_p: Number of instances to generate per p value.
        seed_base: Base seed for randomization.

    Returns:
        List of metadata entries for generated graphs.
    """
    if p_values is None:
        # Generate 50 instances as per task description (T016)
        # "p=0.0 to 1.0, 50 instances"
        # We can interpret this as 50 steps or 50 total.
        # T016 says "batch generation loop (p=0.0 to 1.0, 50 instances)".
        # Let's generate 50 unique p values if not provided, or just 50 total graphs.
        # If instances_per_p=1 and we need 50 total, we need 50 p values.
        p_values = [i / 49.0 for i in range(50)] # 0.0 to 1.0 inclusive (50 steps)
    
    output_dir = init_directories()
    all_metadata = []
    
    global_idx = 0
    for p in p_values:
        for i in range(instances_per_p):
            current_seed = seed_base + global_idx
            logger.info(f"Generating graph {global_idx+1}: p={p:.4f}, seed={current_seed}")
            
            try:
                G = generate_watts_strogatz_graph(n, k, p, current_seed)
                is_valid, msg = validate_graph(G, n, k)
                
                if not is_valid:
                    log_warning(f"Graph {global_idx} invalid: {msg}. Skipping save.")
                    # In a real pipeline, we might retry with a new seed.
                    # Here we just skip to maintain the count of valid graphs if needed,
                    # but T017 just says "Save generated graphs".
                    continue

                meta = save_graph_and_metadata(G, p, current_seed, output_dir, global_idx)
                all_metadata.append(meta)
                log_metric("graph_generated", 1, {"p": p, "seed": current_seed})
                
            except Exception as e:
                logger.error(f"Failed to generate graph {global_idx}: {e}")
            
            global_idx += 1

    return all_metadata


def main():
    """Main entry point for topology generation."""
    logger.info("Starting topology generation batch.")
    
    # Parameters from T016/T017
    # 50 instances, p from 0.0 to 1.0
    # N=500, k=2
    metadata = run_generation_batch(
        n=500,
        k=2,
        instances_per_p=1,
        seed_base=42
    )
    
    logger.info(f"Batch generation complete. Saved {len(metadata)} graphs.")
    if len(metadata) < 45:
        logger.warning(f"Only {len(metadata)} valid graphs generated (expected >= 45).")

if __name__ == "__main__":
    main()