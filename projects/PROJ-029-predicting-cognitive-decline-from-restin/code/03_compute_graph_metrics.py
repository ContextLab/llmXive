"""
Compute graph-theoretical metrics from adjacency matrices.

This script calculates node degree, global efficiency, clustering coefficient,
and path length for each subject's connectivity matrix. It uses joblib for
parallel processing to stay within memory and time constraints.

Inputs:
    data/processed/adjacency_matrices/*.npy (or .csv)

Outputs:
    data/processed/graph_metrics.csv
    data/artifacts/memory_profile.log (appended)
"""

import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
import networkx as nx
import psutil
from joblib import Parallel, delayed

# Project-relative imports
from utils.logger import get_logger
from utils.io import ensure_dir, load_csv, save_dataframe
from config import get_config

# Constants
N_JOBS = 2
MEMORY_LIMIT_GB = 7.0
OUTPUT_DIR = Path("data/processed")
INPUT_DIR = Path("data/processed/adjacency_matrices")
OUTPUT_FILE = OUTPUT_DIR / "graph_metrics.csv"
MEMORY_LOG = Path("data/artifacts/memory_profile.log")
CONFIG = get_config()
RANDOM_SEED = CONFIG.get("random_seed", 42)
np.random.seed(RANDOM_SEED)

logger = get_logger("compute_graph_metrics")

def get_memory_usage_gb() -> float:
    """Return current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(current_usage_gb: float) -> bool:
    """Check if current usage exceeds the limit. Returns True if safe."""
    if current_usage_gb > MEMORY_LIMIT_GB:
        logger.warning(f"Memory usage {current_usage_gb:.2f} GB exceeds limit {MEMORY_LIMIT_GB} GB")
        return False
    return True

def calculate_graph_metrics(adjacency_matrix: np.ndarray, subject_id: str) -> Optional[Dict[str, Any]]:
    """
    Calculate graph metrics for a single adjacency matrix.

    Args:
        adjacency_matrix: N x N symmetric matrix
        subject_id: Subject identifier

    Returns:
        Dictionary of metrics or None if calculation fails.
    """
    try:
        # Ensure matrix is symmetric and has zeros on diagonal
        adj = adjacency_matrix.copy()
        adj = (adj + adj.T) / 2.0
        np.fill_diagonal(adj, 0.0)

        # Create graph
        G = nx.from_numpy_array(adj)

        # Remove self-loops just in case
        G.remove_edges_from(nx.selfloop_edges(G))

        # Calculate metrics
        # 1. Node Degree (average)
        degrees = [d for n, d in G.degree()]
        avg_degree = np.mean(degrees) if degrees else 0.0

        # 2. Global Efficiency
        if nx.is_connected(G):
            global_eff = nx.global_efficiency(G)
        else:
            # For disconnected graphs, use sum of efficiencies of components
            components = nx.connected_components(G)
            eff_sum = 0.0
            count = 0
            for comp in components:
                subgraph = G.subgraph(comp)
                if len(subgraph.nodes) > 1:
                    eff_sum += nx.global_efficiency(subgraph)
                    count += 1
            global_eff = eff_sum / count if count > 0 else 0.0

        # 3. Clustering Coefficient (average)
        clustering = nx.average_clustering(G)

        # 4. Average Path Length (only for connected graphs)
        if nx.is_connected(G):
            avg_path_len = nx.average_shortest_path_length(G)
        else:
            # Approximation for disconnected: average over reachable pairs or infinity
            # Here we use 0.0 for disconnected to indicate undefined, or could use max path
            avg_path_len = 0.0

        return {
            "subject_id": subject_id,
            "avg_degree": avg_degree,
            "global_efficiency": global_eff,
            "clustering_coefficient": clustering,
            "avg_path_length": avg_path_len,
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges()
        }
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        logger.error(traceback.format_exc())
        return None

def process_subject_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a single adjacency matrix file and compute metrics.

    Args:
        file_path: Path to .npy or .csv file

    Returns:
        Metrics dictionary or None.
    """
    try:
        if file_path.suffix == ".npy":
            adj_matrix = np.load(file_path)
        elif file_path.suffix == ".csv":
            adj_matrix = pd.read_csv(file_path, header=None).values
        else:
            logger.warning(f"Skipping unsupported file type: {file_path}")
            return None

        # Extract subject ID from filename (e.g., sub-001.npy -> 001)
        subject_id = file_path.stem.replace("sub-", "")

        # Check memory before processing
        mem_usage = get_memory_usage_gb()
        if not check_memory_limit(mem_usage):
            raise MemoryError(f"Memory limit exceeded before processing {subject_id}")

        return calculate_graph_metrics(adj_matrix, subject_id)

    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")
        logger.error(traceback.format_exc())
        return None

def process_all_subjects_parallel(input_dir: Path, n_jobs: int = 2) -> List[Dict[str, Any]]:
    """
    Process all adjacency matrices in parallel.

    Args:
        input_dir: Directory containing .npy or .csv files
        n_jobs: Number of parallel jobs

    Returns:
        List of metric dictionaries.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory {input_dir} does not exist")

    files = list(input_dir.glob("*.npy")) + list(input_dir.glob("*.csv"))
    if not files:
        raise ValueError(f"No adjacency matrix files found in {input_dir}")

    logger.info(f"Found {len(files)} subject files. Processing with {n_jobs} jobs...")
    start_time = time.time()

    # Use joblib for parallel processing
    results = Parallel(n_jobs=n_jobs, backend="loky")(
        delayed(process_subject_file)(f) for f in files
    )

    elapsed = time.time() - start_time
    logger.info(f"Parallel processing completed in {elapsed:.2f} seconds.")

    # Filter out None results
    valid_results = [r for r in results if r is not None]
    return valid_results

def main():
    """Main entry point."""
    ensure_dir(OUTPUT_DIR)
    ensure_dir(MEMORY_LOG.parent)

    logger.info("Starting graph metrics computation...")

    try:
        # Check input
        if not INPUT_DIR.exists():
            logger.error(f"Input directory {INPUT_DIR} not found. "
                         f"Run 02_preprocess_and_parcellate.py first.")
            sys.exit(1)

        # Process
        metrics_list = process_all_subjects_parallel(INPUT_DIR, n_jobs=N_JOBS)

        if not metrics_list:
            logger.error("No valid metrics computed. Exiting.")
            sys.exit(1)

        # Convert to DataFrame
        df = pd.DataFrame(metrics_list)
        df = df.sort_values("subject_id")

        # Save
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Saved graph metrics to {OUTPUT_FILE}")
        logger.info(f"Total subjects processed: {len(df)}")

        # Log memory usage
        final_mem = get_memory_usage_gb()
        with open(MEMORY_LOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | compute_graph_metrics | "
                    f"peak_mem_gb={final_mem:.2f} | subjects={len(df)}\n")

        logger.info("Graph metrics computation finished successfully.")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()