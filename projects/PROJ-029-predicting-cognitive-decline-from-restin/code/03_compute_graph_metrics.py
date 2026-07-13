import os
import sys
import time
import psutil
import numpy as np
import pandas as pd
from pathlib import Path
from joblib import Parallel, delayed
from typing import Dict, Any, List, Optional
import logging

# Import from project utils
from utils.logger import get_logger
from utils.io import load_csv, save_dataframe, ensure_dir
from utils.graph import create_graph_from_adjacency, calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality

# Configuration
MEMORY_LIMIT_GB = 7.0
N_JOBS = 2
INPUT_DIR = Path("data/processed/adjacency_matrices")
OUTPUT_FILE = Path("data/processed/graph_metrics.csv")
LOG_FILE = Path("data/artifacts/graph_metrics_runtime.log")

logger = get_logger("graph_metrics")

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """Check if current memory usage is within the limit."""
    current = get_memory_usage_gb()
    if current > limit_gb:
        logger.error(f"Memory limit exceeded: {current:.2f}GB > {limit_gb}GB")
        return False
    return True

def load_adjacency_matrix(subject_id: str, input_dir: Path) -> Optional[np.ndarray]:
    """Load adjacency matrix for a subject."""
    matrix_path = input_dir / f"{subject_id}_adjacency.npy"
    if not matrix_path.exists():
        logger.warning(f"Adjacency matrix not found for {subject_id}: {matrix_path}")
        return None
    try:
        return np.load(matrix_path)
    except Exception as e:
        logger.error(f"Failed to load {matrix_path}: {e}")
        return None

def calculate_graph_metrics(adjacency_matrix: np.ndarray) -> Dict[str, float]:
    """Calculate graph metrics for a single adjacency matrix."""
    try:
        G = create_graph_from_adjacency(adjacency_matrix)
        if G is None or len(G.nodes()) == 0:
            return {}

        metrics = {
            'global_efficiency': float(calculate_global_efficiency(G)),
            'clustering_coefficient': float(calculate_clustering_coefficient(G)),
            'degree_centrality_mean': float(np.mean(list(calculate_degree_centrality(G).values()))),
        }
        return metrics
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return {}

def process_subject_matrix(subject_id: str, input_dir: Path) -> Optional[Dict[str, Any]]:
    """Process a single subject's matrix and return metrics."""
    if not check_memory_limit():
        return None

    adj_matrix = load_adjacency_matrix(subject_id, input_dir)
    if adj_matrix is None:
        return None

    metrics = calculate_graph_metrics(adj_matrix)
    if not metrics:
        return None

    metrics['subject_id'] = subject_id
    return metrics

def process_all_subjects_parallel(subject_ids: List[str], input_dir: Path, n_jobs: int = N_JOBS) -> List[Dict[str, Any]]:
    """Process all subjects in parallel using joblib."""
    logger.info(f"Starting parallel processing of {len(subject_ids)} subjects with {n_jobs} jobs...")
    start_time = time.time()

    results = Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(process_subject_matrix)(sub_id, input_dir)
        for sub_id in subject_ids
    )

    # Filter out None results (failed subjects)
    valid_results = [r for r in results if r is not None]
    
    elapsed = time.time() - start_time
    logger.info(f"Parallel processing completed in {elapsed:.2f}s. Processed {len(valid_results)}/{len(subject_ids)} subjects.")
    return valid_results

def main():
    """Main entry point for graph metrics computation."""
    logger.info("Starting T035: Graph Metrics Calculation with Parallelization")
    
    ensure_dir(OUTPUT_FILE.parent)
    ensure_dir(LOG_FILE.parent)

    if not INPUT_DIR.exists():
        logger.error(f"Input directory {INPUT_DIR} does not exist.")
        logger.error("Please run code/02_preprocess_and_parcellate.py first.")
        sys.exit(1)

    # Load eligible subjects list
    eligible_file = Path("data/processed/eligible_subjects.csv")
    if not eligible_file.exists():
        logger.error(f"Eligible subjects file not found: {eligible_file}")
        logger.error("Please run code/01_download_and_filter.py first.")
        sys.exit(1)

    eligible_df = load_csv(eligible_file)
    subject_ids = eligible_df['subject_id'].tolist()
    logger.info(f"Found {len(subject_ids)} eligible subjects.")

    # Process subjects in parallel
    results = process_all_subjects_parallel(subject_ids, INPUT_DIR, n_jobs=N_JOBS)

    if not results:
        logger.error("No valid graph metrics computed.")
        sys.exit(1)

    # Convert to DataFrame and save
    output_df = pd.DataFrame(results)
    
    # Ensure column order
    cols = ['subject_id', 'global_efficiency', 'clustering_coefficient', 'degree_centrality_mean']
    available_cols = [c for c in cols if c in output_df.columns]
    output_df = output_df[available_cols]

    save_dataframe(output_df, OUTPUT_FILE)
    logger.info(f"Graph metrics saved to {OUTPUT_FILE}")
    
    # Log runtime for verification
    with open(LOG_FILE, 'a') as f:
        f.write(f"T035 completed. Subjects: {len(subject_ids)}, Output: {OUTPUT_FILE}\n")

    logger.info("T035: Graph metrics calculation finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
