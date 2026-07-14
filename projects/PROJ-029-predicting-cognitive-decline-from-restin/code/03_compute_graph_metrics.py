import os
import sys
import time
import logging
import json
import psutil
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from joblib import Parallel, delayed
from utils.logger import get_logger, setup_logger
from utils.graph import calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality, calculate_shortest_path_length
from utils.io import load_csv, save_dataframe, ensure_dir
from config import get_config

def get_logger_wrapper(name: str) -> logging.Logger:
    """Wrapper to get a logger with the specified name."""
    return setup_logger(name)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if current memory usage is within the limit."""
    current = get_memory_usage_gb()
    if current > limit_gb:
        return False
    return True

def load_subject_list(subjects_file: str) -> List[str]:
    """Load list of subject IDs from a CSV file."""
    if not os.path.exists(subjects_file):
        raise FileNotFoundError(f"Subject list file not found: {subjects_file}")
    df = pd.read_csv(subjects_file)
    return df['subject_id'].tolist()

def load_connectivity_matrices(input_dir: str, subject_id: str) -> Optional[np.ndarray]:
    """Load a single subject's connectivity matrix."""
    matrix_path = Path(input_dir) / f"{subject_id}_connectivity.npy"
    if not matrix_path.exists():
        logging.warning(f"Matrix not found for {subject_id}: {matrix_path}")
        return None
    try:
        matrix = np.load(matrix_path)
        return matrix
    except Exception as e:
        logging.error(f"Failed to load matrix for {subject_id}: {e}")
        return None

def process_single_subject_matrix(subject_id: str, input_dir: str) -> Optional[Dict[str, Any]]:
    """Process a single subject's connectivity matrix and compute graph metrics."""
    matrix = load_connectivity_matrices(input_dir, subject_id)
    if matrix is None:
        return None

    # Create graph from adjacency matrix
    G = nx.from_numpy_array(matrix)

    # Compute metrics
    try:
        degree = calculate_degree_centrality(G)
        efficiency = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        path_length = calculate_shortest_path_length(G)
    except Exception as e:
        logging.error(f"Error computing metrics for {subject_id}: {e}")
        return None

    return {
        'subject_id': subject_id,
        'degree_centrality': float(np.mean(degree)),
        'global_efficiency': float(efficiency),
        'clustering_coefficient': float(clustering),
        'average_path_length': float(path_length)
    }

def compute_metrics_parallel(subject_ids: List[str], input_dir: str, n_jobs: int = 2) -> List[Dict[str, Any]]:
    """Compute graph metrics for all subjects in parallel."""
    results = Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(process_single_subject_matrix)(sid, input_dir) for sid in subject_ids
    )
    # Filter out None results
    return [r for r in results if r is not None]

def write_outputs(results: List[Dict[str, Any]], output_file: str):
    """Write results to a CSV file."""
    ensure_dir(output_file)
    df = pd.DataFrame(results)
    save_dataframe(df, output_file)
    logging.info(f"Results written to {output_file}")

def main():
    """Main entry point for T035: Compute Graph Metrics (Parallel Optimized)."""
    logger = get_logger("graph_metrics")
    logger.info("Starting T035: Compute Graph Metrics (Parallel Optimized)")

    config = get_config()
    input_dir = config.get('connectivity_matrix_dir', 'data/processed/connectivity_matrices')
    subject_list_file = config.get('eligible_subjects_file', 'data/processed/eligible_subjects.csv')
    output_file = config.get('graph_metrics_output', 'data/processed/graph_metrics.csv')
    n_jobs = config.get('graph_metrics_n_jobs', 2)
    memory_limit = config.get('memory_limit_gb', 7.0)

    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Parallel jobs: {n_jobs}")

    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        logger.error("Please run code/02_preprocess_and_parcellate.py first to generate connectivity matrices.")
        sys.exit(1)

    if not os.path.exists(subject_list_file):
        logger.error(f"Subject list file not found: {subject_list_file}")
        logger.error("Please run code/01_download_and_filter.py first to generate eligible subjects.")
        sys.exit(1)

    subject_ids = load_subject_list(subject_list_file)
    logger.info(f"Loaded {len(subject_ids)} subjects")

    # Check memory before starting
    if not check_memory_limit(memory_limit):
        logger.error(f"Memory usage exceeds limit of {memory_limit} GB. Aborting.")
        sys.exit(1)

    start_time = time.time()
    results = compute_metrics_parallel(subject_ids, input_dir, n_jobs)
    elapsed_time = time.time() - start_time

    logger.info(f"Processed {len(results)} subjects in {elapsed_time:.2f} seconds")
    logger.info(f"Average time per subject: {elapsed_time / len(results):.2f} seconds")

    # Estimate runtime for 100 subjects
    if len(results) > 0:
        estimated_100_time = (elapsed_time / len(results)) * 100
        logger.info(f"Estimated time for 100 subjects: {estimated_100_time:.2f} seconds ({estimated_100_time / 60:.2f} minutes)")
        if estimated_100_time > 1800:
            logger.warning(f"Estimated time for 100 subjects ({estimated_100_time/60:.2f} min) exceeds 30 minute target.")
        else:
            logger.info(f"Estimated time for 100 subjects ({estimated_100_time/60:.2f} min) meets 30 minute target.")

    write_outputs(results, output_file)

    # Log memory usage after processing
    final_memory = get_memory_usage_gb()
    logger.info(f"Final memory usage: {final_memory:.2f} GB")

    logger.info("T035 completed successfully")

if __name__ == "__main__":
    main()