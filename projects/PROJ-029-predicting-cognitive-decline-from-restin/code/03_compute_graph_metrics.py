"""
T019: Compute graph metrics from connectivity matrices.

This script calculates node degree, global efficiency, clustering coefficient,
and path length for every subject's connectivity matrix. It processes subjects
one-by-one to stay within the 7GB RAM limit.
"""
import os
import sys
import time
import logging
import json
import psutil
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logger import get_logger
from utils.io import ensure_dir, save_csv, load_dataframe
from utils.graph import (
    create_graph_from_adjacency,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length
)
from config import get_config

# Constants
MEMORY_LIMIT_GB = 7.0
INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "connectivity_matrices"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "graph_metrics.csv"
LOG_FILE = PROJECT_ROOT / "data" / "artifacts" / "graph_metrics.log"

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(current_usage_gb: float, limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """Check if current memory usage is within the limit."""
    return current_usage_gb < limit_gb

def load_connectivity_matrices() -> Dict[str, np.ndarray]:
    """
    Load all connectivity matrices from the input directory.
    Returns a dictionary mapping subject IDs to their adjacency matrices.
    """
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")

    matrices = {}
    for file_path in INPUT_DIR.glob("*.npy"):
        subject_id = file_path.stem
        try:
            matrices[subject_id] = np.load(file_path)
        except Exception as e:
            logger = get_logger("graph_metrics")
            logger.error(f"Failed to load matrix for {subject_id}: {e}")

    return matrices

def process_single_subject_matrix(
    subject_id: str,
    adjacency_matrix: np.ndarray,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Process a single subject's adjacency matrix and compute graph metrics.
    Returns a dictionary with the metrics or None if processing fails.
    """
    try:
        # Check memory before processing
        current_mem = get_memory_usage_gb()
        if not check_memory_limit(current_mem):
            logger.error(f"Memory limit exceeded for subject {subject_id}: {current_mem:.2f}GB")
            return None

        # Create graph from adjacency matrix
        # Ensure matrix is symmetric and binary/weighted appropriately
        adj = adjacency_matrix.copy()
        np.fill_diagonal(adj, 0)  # Remove self-loops

        # Create NetworkX graph
        G = create_graph_from_adjacency(adj)

        if G.number_of_nodes() == 0:
            logger.warning(f"Subject {subject_id} has no nodes in graph")
            return None

        # Calculate metrics
        # 1. Node Degree (average)
        degree_centrality = calculate_degree_centrality(G)
        avg_degree = np.mean(list(degree_centrality.values())) if degree_centrality else 0.0

        # 2. Global Efficiency
        global_eff = calculate_global_efficiency(G)

        # 3. Clustering Coefficient (average)
        clustering_coef = calculate_clustering_coefficient(G)

        # 4. Average Path Length
        try:
            avg_path_len = calculate_shortest_path_length(G)
        except nx.NetworkXError:
            # Graph might be disconnected
            avg_path_len = np.nan

        # Check memory after processing
        current_mem = get_memory_usage_gb()
        if not check_memory_limit(current_mem):
            logger.warning(f"Memory usage high after processing {subject_id}: {current_mem:.2f}GB")

        return {
            "subject_id": subject_id,
            "avg_degree": avg_degree,
            "global_efficiency": global_eff,
            "clustering_coefficient": clustering_coef,
            "avg_path_length": avg_path_len,
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges()
        }

    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}", exc_info=True)
        return None

def main():
    """Main entry point for graph metrics computation."""
    logger = get_logger("graph_metrics", log_file=str(LOG_FILE))
    logger.info("Starting graph metrics computation with parallel processing (joblib).")

    # Ensure output directory exists
    ensure_dir(OUTPUT_FILE.parent)

    # Load connectivity matrices
    try:
        matrices = load_connectivity_matrices()
        logger.info(f"Loaded {len(matrices)} connectivity matrices from {INPUT_DIR}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if not matrices:
        logger.error("No connectivity matrices found to process.")
        sys.exit(1)

    results = []
    start_time = time.time()

    # Process subjects one-by-one to manage memory
    for i, (subject_id, adjacency_matrix) in enumerate(matrices.items()):
        logger.info(f"Processing subject {i+1}/{len(matrices)}: {subject_id}")

        result = process_single_subject_matrix(subject_id, adjacency_matrix, logger)

        if result:
            results.append(result)
            logger.info(f"  -> Computed metrics: degree={result['avg_degree']:.4f}, "
                        f"eff={result['global_efficiency']:.4f}, "
                        f"clust={result['clustering_coefficient']:.4f}")
        else:
            logger.warning(f"Skipping subject {subject_id} due to processing error or memory limit")

        # Optional: Force garbage collection every 10 subjects
        if (i + 1) % 10 == 0:
            import gc
            gc.collect()

    elapsed_time = time.time() - start_time
    logger.info(f"Completed processing {len(results)}/{len(matrices)} subjects in {elapsed_time:.2f}s")

    if not results:
        logger.error("No results to write. Exiting.")
        sys.exit(1)

    # Write results to CSV
    try:
        save_csv(results, str(OUTPUT_FILE))
        logger.info(f"Successfully wrote graph metrics to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to write output CSV: {e}", exc_info=True)
        sys.exit(1)

    # Log memory usage summary
    final_mem = get_memory_usage_gb()
    logger.info(f"Final memory usage: {final_mem:.2f}GB")

    logger.info("Graph metrics computation finished successfully.")

if __name__ == "__main__":
    main()