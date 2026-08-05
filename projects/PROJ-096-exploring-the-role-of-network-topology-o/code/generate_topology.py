"""
Topology Generation Module for Kuramoto Synchronization Study.

Implements synthetic ring lattice generation, Watts-Strogatz rewiring,
connectivity validation, and batch generation with metadata logging.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import numpy as np

from utils.logging_utils import get_logger, log_operation

# Constants
DEFAULT_N_NODES = 500
DEFAULT_K_NEIGHBORS = 2
DEFAULT_SEED = 42
MAX_RETRIES = 10
LOG_FILE = "data/processed/simulation_{}.log"

# Initialize logger
logger = get_logger(__name__)


def load_config(config_path: str = "data/processed/config.json") -> Dict[str, Any]:
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        return json.load(f)


def generate_regular_ring_lattice(n: int = DEFAULT_N_NODES, k: int = DEFAULT_K_NEIGHBORS) -> nx.Graph:
    """
    Generate a synthetic regular ring lattice.
    
    Args:
        n: Number of nodes
        k: Each node is joined with its k nearest neighbors
        
    Returns:
        NetworkX Graph representing the ring lattice
    """
    logger.log("generate_regular_ring_lattice", n=n, k=k)
    G = nx.watts_strogatz_graph(n, k, 0.0, seed=DEFAULT_SEED)
    return G


def generate_watts_strogatz_graph(
    n: int = DEFAULT_N_NODES,
    k: int = DEFAULT_K_NEIGHBORS,
    p: float = 0.1,
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a Watts-Strogatz small-world graph.
    
    Args:
        n: Number of nodes
        k: Each node is joined with its k nearest neighbors
        p: Probability of rewiring each edge
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX Graph representing the Watts-Strogatz graph
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
        
    logger.log("generate_watts_strogatz_graph", n=n, k=k, p=p, seed=seed)
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    return G


def validate_graph(G: nx.Graph, n_expected: int = DEFAULT_N_NODES) -> Tuple[bool, str]:
    """
    Validate graph properties for connectivity and node count.
    
    Args:
        G: NetworkX Graph to validate
        n_expected: Expected number of nodes
        
    Returns:
        Tuple of (is_valid, message)
    """
    logger.log("validate_graph", n_nodes=G.number_of_nodes(), n_expected=n_expected)
    
    if G.number_of_nodes() != n_expected:
        return False, f"Node count mismatch: {G.number_of_nodes()} != {n_expected}"
    
    if not nx.is_connected(G):
        return False, "Graph is disconnected"
    
    return True, "Graph is valid"


def compute_graph_checksum(G: nx.Graph) -> str:
    """
    Compute a checksum of the graph structure for reproducibility.
    
    Args:
        G: NetworkX Graph
        
    Returns:
        SHA256 checksum string
    """
    # Serialize graph to a canonical string representation
    nodes = sorted(G.nodes())
    edges = sorted([tuple(sorted(e)) for e in G.edges()])
    data = f"{nodes}_{edges}"
    return hashlib.sha256(data.encode()).hexdigest()


def save_graph_and_metadata(
    G: nx.Graph,
    topology_id: int,
    p: float,
    seed: int,
    output_dir: str = "data/processed"
) -> str:
    """
    Save graph to disk and update metadata JSON.
    
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
    
    # File naming convention
    graph_filename = f"topology_{topology_id}_p{p:.2f}_seed_{seed}.gpickle"
    graph_path = os.path.join(output_dir, graph_filename)
    
    # Save graph
    nx.write_gpickle(G, graph_path)
    
    # Compute checksum
    checksum = compute_graph_checksum(G)
    
    # Load or initialize metadata
    metadata_path = os.path.join(output_dir, "graph_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
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
        "checksum": checksum,
        "timestamp": datetime.utcnow().isoformat(),
        "filename": graph_filename
    }
    metadata_list.append(new_entry)
    
    # Save updated metadata
    with open(metadata_path, "w") as f:
        json.dump(metadata_list, f, indent=2)
    
    logger.log("save_graph_and_metadata", path=graph_path, checksum=checksum)
    return graph_path


def log_disconnected_graph(
    p: float,
    seed: int,
    log_file: str = "data/processed/disconnected_log.json"
) -> None:
    """
    Log a disconnected graph attempt.
    
    Args:
        p: Rewiring probability that failed
        seed: Seed that failed
        log_file: Path to the disconnected log file
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            disconnected_log = json.load(f)
    else:
        disconnected_log = []
    
    disconnected_log.append({
        "p": p,
        "seed": seed,
        "timestamp": datetime.utcnow().isoformat(),
        "reason": "Disconnected graph"
    })
    
    with open(log_file, "w") as f:
        json.dump(disconnected_log, f, indent=2)
    
    logger.log("log_disconnected_graph", p=p, seed=seed)


def log_methodology_correction(
    base_graph: str = "synthetic_regular_ring_lattice",
    n_nodes: int = DEFAULT_N_NODES,
    k_neighbors: int = DEFAULT_K_NEIGHBORS
) -> None:
    """
    Log the methodology correction regarding the base graph.
    
    Args:
        base_graph: Type of base graph used
        n_nodes: Number of nodes
        k_neighbors: Number of neighbors
    """
    logger.log(
        "log_methodology_correction",
        base_graph=base_graph,
        n_nodes=n_nodes,
        k_neighbors=k_neighbors,
        note="Using synthetic regular ring lattice instead of ca-AstroPh per T000a"
    )


def run_generation_batch(
    n_topologies: int,
    config_path: str = "data/processed/config.json"
) -> List[str]:
    """
    Generate a batch of connected Watts-Strogatz graphs.
    
    Args:
        n_topologies: Target number of valid graphs to generate
        config_path: Path to configuration file
        
    Returns:
        List of paths to generated graph files
    """
    logger.log("run_generation_batch", n_topologies=n_topologies)
    
    # Load config
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        logger.log("run_generation_batch", error="Config not found", severity="ERROR")
        # Create fallback config if missing
        config = {
            "n_topologies": n_topologies,
            "n_nodes": DEFAULT_N_NODES,
            "k_neighbors": DEFAULT_K_NEIGHBORS,
            "sampling_p_values": [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0][:n_topologies]
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    
    n_nodes = config.get("n_nodes", DEFAULT_N_NODES)
    k_neighbors = config.get("k_neighbors", DEFAULT_K_NEIGHBORS)
    
    # Determine p values
    if "sampling_p_values" in config:
        p_values = config["sampling_p_values"]
    else:
        if n_topologies >= 10:
            p_values = np.linspace(0.0, 1.0, n_topologies).tolist()
        else:
            p_values = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0][:n_topologies]
    
    # Record sampling strategy in config
    config["sampling_p_values"] = p_values
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    generated_graphs = []
    topology_id = 0
    
    for p in p_values:
        if len(generated_graphs) >= n_topologies:
            break
        
        retries = 0
        success = False
        
        while retries < MAX_RETRIES and not success:
            seed = random.randint(0, 2**32 - 1)
            try:
                G = generate_watts_strogatz_graph(n_nodes, k_neighbors, p, seed)
                is_valid, msg = validate_graph(G, n_nodes)
                
                if is_valid:
                    graph_path = save_graph_and_metadata(
                        G, topology_id, p, seed
                    )
                    generated_graphs.append(graph_path)
                    topology_id += 1
                    success = True
                else:
                    log_disconnected_graph(p, seed)
                    retries += 1
                    logger.log(
                        "run_generation_batch",
                        p=p,
                        seed=seed,
                        retry=retries,
                        reason=msg
                    )
            except Exception as e:
                logger.log("run_generation_batch", error=str(e), severity="ERROR")
                retries += 1
        
        if not success:
            logger.log(
                "run_generation_batch",
                warning=f"Failed to generate connected graph for p={p:.2f} after {MAX_RETRIES} retries"
            )
    
    logger.log("run_generation_batch", total_generated=len(generated_graphs))
    return generated_graphs


def main() -> None:
    """Main entry point for topology generation."""
    logger.log("main", status="starting")
    
    # Ensure output directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    # Run batch generation
    config_path = "data/processed/config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        n_topologies = config.get("n_topologies", 10)
    else:
        n_topologies = 10
    
    generated_paths = run_generation_batch(n_topologies, config_path)
    
    logger.log("main", status="completed", files_generated=len(generated_paths))
    print(f"Generated {len(generated_paths)} topologies")


if __name__ == "__main__":
    main()