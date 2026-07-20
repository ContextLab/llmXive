"""
Topology Generation Module for Network Synchronization Research.

This module handles the generation of network topologies for the Kuramoto
oscillator simulation. It implements:
1. Synthetic regular ring lattice generation (base graph).
2. Watts-Strogatz small-world network generation via rewiring.
3. Graph validation (connectivity, degree preservation).
4. Batch generation and metadata logging.

NOTE: The base graph is a synthetic regular ring lattice (N=500, k=2).
The ca-AstroPh dataset (downloaded in T013a) is used solely for Constitution
compliance (reproducibility requirement) and its structure is explicitly ignored
for the generation of the Watts-Strogatz graphs.
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

from utils.graph_utils import is_connected, calculate_graph_metrics
from utils.logging_utils import init_logging, get_logger
from utils.checksum_utils import compute_file_checksum

# Constants
DEFAULT_N = 500
DEFAULT_K = 2  # Each node connected to k nearest neighbors
DEFAULT_SEED_BASE = 42
REWIRING_PROBABILITIES = [0.0, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
OUTPUT_DIR = Path("data/processed")
METADATA_FILE = Path("data/processed/graph_metadata.json")
CHECKSUM_FILE = Path("data/checksums.txt")
METHODOLOGY_LOG = Path("data/processed/methodology_log.md")

logger = get_logger(__name__)


def init_directories():
    """Ensure output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initialized directories: {OUTPUT_DIR}, {CHECKSUM_FILE.parent}")


def generate_regular_ring_lattice(n: int = DEFAULT_N, k: int = DEFAULT_K) -> nx.Graph:
    """
    Generate a synthetic regular ring lattice.

    Args:
        n: Number of nodes.
        k: Each node is connected to k nearest neighbors in each direction.

    Returns:
        NetworkX Graph object representing the ring lattice.
    """
    logger.info(f"Generating synthetic regular ring lattice with N={n}, k={k}")
    # Explicitly synthetic; ca-AstroPh structure is ignored per methodology correction.
    G = nx.watts_strogatz_graph(n=n, k=k, p=0.0, seed=0)
    # Verify it is indeed a ring lattice (p=0.0)
    assert nx.is_regular(G), "Generated graph is not regular"
    logger.info("Synthetic ring lattice generated successfully.")
    return G


def generate_watts_strogatz_graph(
    n: int = DEFAULT_N,
    k: int = DEFAULT_K,
    p: float = 0.0,
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a Watts-Strogatz small-world network.

    Args:
        n: Number of nodes.
        k: Each node is connected to k nearest neighbors in each direction.
        p: Probability of rewiring each edge.
        seed: Random seed for reproducibility.

    Returns:
        NetworkX Graph object.
    """
    if seed is None:
        seed = int(time.time() * 1000) % 1000000

    logger.info(f"Generating Watts-Strogatz graph: N={n}, k={k}, p={p}, seed={seed}")
    G = nx.watts_strogatz_graph(n=n, k=k, p=p, seed=seed)
    return G


def validate_graph(G: nx.Graph, expected_n: int = DEFAULT_N) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate graph properties.

    Args:
        G: NetworkX graph to validate.
        expected_n: Expected number of nodes.

    Returns:
        Tuple of (is_valid, metrics_dict).
    """
    metrics = calculate_graph_metrics(G)
    is_valid = True
    warnings = []

    if G.number_of_nodes() != expected_n:
        is_valid = False
        warnings.append(f"Node count mismatch: expected {expected_n}, got {G.number_of_nodes()}")

    if not is_connected(G):
        is_valid = False
        warnings.append("Graph is not connected")

    # Check degree preservation (approximate)
    avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
    expected_avg_degree = DEFAULT_K  # For regular ring, avg degree is k
    # For WS, avg degree is preserved exactly in the rewiring process
    if abs(avg_degree - expected_avg_degree) > 1e-6:
        warnings.append(f"Avg degree deviation: expected {expected_avg_degree}, got {avg_degree:.4f}")

    result = {
        "is_valid": is_valid,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "avg_degree": avg_degree,
        "clustering_coefficient": metrics.get("clustering_coefficient", 0.0),
        "avg_path_length": metrics.get("avg_path_length", float('inf')),
        "warnings": warnings
    }

    return is_valid, result


def save_graph_and_metadata(
    G: nx.Graph,
    p: float,
    seed: int,
    validation_result: Dict[str, Any],
    output_dir: Path = OUTPUT_DIR
) -> str:
    """
    Save graph to disk and update metadata.

    Args:
        G: The graph to save.
        p: Rewiring probability.
        seed: Random seed used.
        validation_result: Results from validate_graph.
        output_dir: Directory to save files.

    Returns:
        Path to the saved graph file.
    """
    # Create safe filename
    p_str = f"{p:.2f}".replace(".", "_")
    filename = f"graph_p{p_str}_seed{seed}.gpickle"
    graph_path = output_dir / filename
    metadata_path = output_dir / f"metadata_p{p_str}_seed{seed}.json"

    # Save graph
    nx.write_gpickle(G, str(graph_path))
    logger.info(f"Saved graph to {graph_path}")

    # Compute checksum
    checksum = compute_file_checksum(str(graph_path))

    # Prepare metadata
    metadata = {
        "filename": filename,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "rewiring_probability": p,
        "seed": seed,
        "avg_degree": validation_result["avg_degree"],
        "clustering_coefficient": validation_result["clustering_coefficient"],
        "avg_path_length": validation_result["avg_path_length"],
        "is_connected": validation_result["is_valid"],
        "checksum": checksum,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Save metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

    # Update global checksums file
    update_checksums_file(str(graph_path), checksum)

    return str(graph_path)


def update_checksums_file(filepath: str, checksum: str):
    """Append a checksum entry to the checksums file."""
    filename = os.path.basename(filepath)
    entry = f"{checksum}  {filename}\n"
    
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, 'r') as f:
            lines = f.readlines()
        # Avoid duplicates
        if not any(entry.strip() == l.strip() for l in lines):
            with open(CHECKSUM_FILE, 'a') as f:
                f.write(entry)
    else:
        with open(CHECKSUM_FILE, 'w') as f:
            f.write(entry)


def run_generation_batch(
    n: int = DEFAULT_N,
    k: int = DEFAULT_K,
    p_values: List[float] = REWIRING_PROBABILITIES,
    instances_per_p: int = 1,
    seed_base: int = DEFAULT_SEED_BASE
) -> List[Dict[str, Any]]:
    """
    Generate a batch of graphs with varying rewiring probabilities.

    Args:
        n: Number of nodes.
        k: Nearest neighbors.
        p_values: List of rewiring probabilities to try.
        instances_per_p: Number of graph instances per probability.
        seed_base: Base seed for generation.

    Returns:
        List of metadata dictionaries for generated graphs.
    """
    init_directories()
    results = []

    logger.info(f"Starting batch generation: N={n}, k={k}, p_values={p_values}")

    for p in p_values:
        for i in range(instances_per_p):
            seed = seed_base + int(p * 10000) + i
            logger.info(f"Generating graph for p={p}, instance={i}, seed={seed}")

            # Generate graph
            G = generate_watts_strogatz_graph(n=n, k=k, p=p, seed=seed)

            # Validate
            is_valid, validation_result = validate_graph(G, expected_n=n)

            if not is_valid:
                logger.warning(f"Graph p={p}, seed={seed} failed validation: {validation_result['warnings']}")
                # In a full pipeline, we might retry or log and skip
                # For now, we proceed but log the issue
            
            # Save
            graph_path = save_graph_and_metadata(G, p, seed, validation_result)

            result_entry = {
                "graph_path": graph_path,
                "p": p,
                "seed": seed,
                "is_valid": is_valid,
                "validation_details": validation_result
            }
            results.append(result_entry)
            logger.info(f"Completed generation for p={p}, seed={seed}")

    # Log methodology correction if not already present
    log_methodology_correction()

    return results


def log_methodology_correction():
    """Log the decision to use synthetic lattice instead of ca-AstroPh structure."""
    if METHODOLOGY_LOG.exists():
        with open(METHODOLOGY_LOG, 'r') as f:
            content = f.read()
        if "Synthetic Ring Lattice" in content:
            return # Already logged

    with open(METHODOLOGY_LOG, 'a') as f:
        f.write("\n### Methodology Correction Log\n")
        f.write(f"**Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write("**Decision**: Use synthetic regular ring lattice for Watts-Strogatz base.\n")
        f.write("**Reason**: Reconstructing an irregular citation network (ca-AstroPh) into a regular ring lattice is methodologically incoherent.\n")
        f.write("**Action**: ca-AstroPh dataset is downloaded (T013a) solely for Constitution reproducibility compliance, but its structure is explicitly ignored for graph generation.\n")
        f.write("**Reference**: plan.md, T012, T013c.\n")
        f.write("-" * 50 + "\n")
    logger.info("Methodology correction logged.")


def main():
    """Entry point for running the topology generation."""
    init_logging()
    
    # Example batch run
    # In a full pipeline, arguments would be parsed from CLI or config
    p_values = [0.0, 0.1, 0.5, 1.0]
    results = run_generation_batch(p_values=p_values, instances_per_p=5)
    
    logger.info(f"Batch generation complete. Generated {len(results)} graphs.")
    
    # Print summary
    for r in results:
        status = "OK" if r["is_valid"] else "WARN"
        logger.info(f"[{status}] p={r['p']}, seed={r['seed']}, path={r['graph_path']}")

    return results


if __name__ == "__main__":
    main()