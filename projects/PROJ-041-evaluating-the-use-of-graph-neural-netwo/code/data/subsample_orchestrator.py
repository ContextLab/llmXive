import os
import sys
import logging
import json
import networkx as nx
from typing import Optional, Tuple

# Project local imports
from utils.seed import set_seed, get_seed_value
from utils.memory_monitor import (
    get_peak_memory_mb,
    start_monitoring,
    stop_monitoring,
    check_memory_limit,
    MemoryLimitExceededError,
)
from data.preprocess import extract_lcc, subsample_graph, calculate_sha256

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

NODE_LIMIT = 5000
MEMORY_LIMIT_GB = 7

def load_graph_safe(path: str) -> nx.Graph:
    """Load a graph from a file, raising a clear error if it fails."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input graph file not found: {path}")
    logger.info(f"Loading graph from {path}")
    try:
        G = nx.read_graphml(path)
        return G
    except Exception as e:
        logger.error(f"Failed to load graph {path}: {e}")
        raise

def write_graph_with_hash(G: nx.Graph, output_path: str) -> str:
    """Write graph to file and generate a sidecar hash file."""
    logger.info(f"Writing graph to {output_path}")
    nx.write_graphml(G, output_path)
    hash_val = calculate_sha256(output_path)
    hash_path = output_path + ".hash"
    with open(hash_path, "w") as f:
        f.write(hash_val)
    logger.info(f"Graph written with hash {hash_val} -> {hash_path}")
    return hash_path

def run_subsampling_orchestration(
    raw_graph_path: str,
    seed: int,
    output_dir: str = "data/processed",
    memory_limit_gb: float = MEMORY_LIMIT_GB,
    node_limit: int = NODE_LIMIT,
) -> Tuple[str, str]:
    """
    Orchestrates the subsampling logic:
    1. Check node count and memory.
    2. If > limits, extract LCC.
    3. If LCC > limits, apply degree-based subsampling.
    4. Write final graph with hash.

    Returns: (final_graph_path, hash_path)
    """
    set_seed(seed)
    logger.info(f"Starting subsampling orchestration with seed {seed}")
    logger.info(f"Limits: Nodes={node_limit}, Memory={memory_limit_gb}GB")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load Raw Graph
    G_raw = load_graph_safe(raw_graph_path)
    initial_nodes = G_raw.number_of_nodes()
    logger.info(f"Initial graph nodes: {initial_nodes}")

    # 2. Check Conditions
    needs_subsample = initial_nodes > node_limit

    # Memory check: We estimate peak memory roughly by graph size if not already monitored
    # In a real pipeline, we might wrap the load in memory_monitor, but for this logic
    # we rely on the node count as the primary driver for this task's logic tree.
    # If the raw load itself exceeds memory, the process would have OOMed or we catch it here.
    # We'll assume the check_memory_limit is for the subsequent operations.
    
    final_graph = None
    step_taken = "none"

    if needs_subsample:
        logger.warning(f"Node count {initial_nodes} exceeds limit {node_limit}. Initiating subsampling.")
        
        # Start monitoring for the subsampling operations
        start_monitoring()
        
        try:
            # Step A: Extract LCC
            logger.info("Step 1: Extracting Largest Connected Component (LCC)...")
            G_lcc = extract_lcc(G_raw)
            lcc_nodes = G_lcc.number_of_nodes()
            logger.info(f"LCC nodes: {lcc_nodes}")
            
            # Save intermediate LCC if requested or for debugging (optional, but good practice)
            # The task description implies LCC is an intermediate step, but T008a handles writing it.
            # We just use it here.
            
            if lcc_nodes > node_limit:
                logger.warning(f"LCC node count {lcc_nodes} still exceeds limit {node_limit}.")
                logger.info("Step 2: Applying Degree-Based Subsampling...")
                
                # Step B: Degree-based subsampling
                final_graph = subsample_graph(G_lcc, n_nodes=node_limit, seed=seed)
                final_nodes = final_graph.number_of_nodes()
                step_taken = "lcc_then_degree"
                logger.info(f"Final subsampled nodes: {final_nodes}")
            else:
                final_graph = G_lcc
                step_taken = "lcc_only"
                logger.info("LCC was within limits. Using LCC as final graph.")
                
        finally:
            peak_mem = stop_monitoring()
            logger.info(f"Peak memory during subsampling: {peak_mem:.2f} MB")
            
            if peak_mem > (memory_limit_gb * 1024):
                raise MemoryLimitExceededError(f"Peak memory {peak_mem:.2f} MB exceeded limit {memory_limit_gb * 1024} MB")
    else:
        logger.info("Node count within limits. No subsampling required.")
        final_graph = G_raw
        step_taken = "none"

    # 3. Write Final Output
    # Determine scenario name from input path
    base_name = os.path.basename(raw_graph_path)
    scenario_name = base_name.replace("_raw.graphml", "").replace(".graphml", "")
    output_filename = f"graph_{scenario_name}_subsampled.graphml"
    output_path = os.path.join(output_dir, output_filename)

    write_graph_with_hash(final_graph, output_path)

    logger.info(f"Subsampling orchestration complete. Step: {step_taken}")
    return output_path, output_path + ".hash"

def main():
    """
    Entry point for the subsampling orchestrator.
    Expects arguments or environment variables, or defaults to a specific scenario.
    For the pipeline, this is called with specific paths.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Subsampling Orchestrator")
    parser.add_argument("--input", type=str, required=True, help="Path to raw graphml file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--node-limit", type=int, default=5000, help="Max nodes allowed")
    parser.add_argument("--memory-limit-gb", type=float, default=7.0, help="Max memory in GB")

    args = parser.parse_args()

    try:
        out_path, hash_path = run_subsampling_orchestration(
            raw_graph_path=args.input,
            seed=args.seed,
            output_dir=args.output_dir,
            memory_limit_gb=args.memory_limit_gb,
            node_limit=args.node_limit,
        )
        logger.info(f"Success. Output: {out_path}, Hash: {hash_path}")
        # Exit with 0 on success
        sys.exit(0)
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
