"""
T035: Compute Graph Metrics with Parallel Optimization

Calculates node degree, global efficiency, clustering coefficient, and path length
for every subject using joblib.Parallel(n_jobs=2).

Output: data/processed/graph_metrics.csv
"""
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
from joblib import Parallel, delayed
from typing import Dict, List, Tuple, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "code"))

from utils.logger import get_logger
from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_local_efficiency,
    calculate_shortest_path_length
)
from utils.io import load_csv, save_dataframe, ensure_dir
from config import get_config

# Configuration
CONFIG = get_config()
MEMORY_LIMIT_GB = 7.0
N_JOBS = 2  # Hardcoded for T035 optimization requirement
RANDOM_SEED = CONFIG.get("random_seed", 42)

def get_logger_wrapper(name: str) -> logging.Logger:
    """Setup logger for this module."""
    return get_logger(name)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """Check if current memory usage is within limit."""
    current = get_memory_usage_gb()
    if current > limit_gb:
        return False
    return True

def load_connectivity_matrices(input_dir: str) -> List[Tuple[str, np.ndarray]]:
    """
    Load all connectivity matrices from the input directory.
    Returns a list of tuples: (subject_id, adjacency_matrix)
    """
    logger = get_logger("graph_metrics")
    input_path = Path(input_dir)
    
    if not input_path.exists():
        logger.error(f"Input directory not found: {input_dir}")
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Find all .npy files (assuming matrices are saved as numpy arrays)
    matrix_files = sorted(input_path.glob("*.npy"))
    logger.info(f"Found {len(matrix_files)} connectivity matrices in {input_dir}")
    
    if len(matrix_files) == 0:
        logger.error("No connectivity matrices found. Please run 02_preprocess_and_parcellate.py first.")
        raise ValueError("No connectivity matrices found")
    
    results = []
    for file_path in matrix_files:
        # Extract subject ID from filename (e.g., "sub-001_matrix.npy" -> "sub-001")
        subject_id = file_path.stem.replace("_matrix", "").replace("sub-", "")
        try:
            matrix = np.load(file_path)
            results.append((subject_id, matrix))
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            continue
    
    return results

def process_single_subject_matrix(subject_id: str, adjacency_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Process a single subject's adjacency matrix and compute graph metrics.
    This function is designed to be called in parallel.
    """
    # Ensure symmetry for undirected graph
    adj = np.array(adjacency_matrix, dtype=float)
    adj = (adj + adj.T) / 2.0
    
    # Create graph
    G = create_graph_from_adjacency(adj)
    
    if G.number_of_nodes() == 0:
        return {
            "subject_id": subject_id,
            "degree_centrality_mean": np.nan,
            "global_efficiency": np.nan,
            "clustering_coefficient_mean": np.nan,
            "average_path_length": np.nan,
            "local_efficiency_mean": np.nan
        }
    
    # Calculate metrics
    degree_cent = calculate_degree_centrality(G)
    global_eff = calculate_global_efficiency(G)
    clustering = calculate_clustering_coefficient(G)
    path_len = calculate_shortest_path_length(G)
    local_eff = calculate_local_efficiency(G)
    
    return {
        "subject_id": subject_id,
        "degree_centrality_mean": float(np.mean(list(degree_cent.values()))),
        "global_efficiency": float(global_eff),
        "clustering_coefficient_mean": float(np.mean(list(clustering.values()))),
        "average_path_length": float(path_len) if np.isfinite(path_len) else np.nan,
        "local_efficiency_mean": float(np.mean(list(local_eff.values())))
    }

def compute_metrics_parallel(subjects_data: List[Tuple[str, np.ndarray]], n_jobs: int = N_JOBS) -> List[Dict[str, Any]]:
    """
    Compute graph metrics for all subjects in parallel using joblib.
    """
    logger = get_logger("graph_metrics")
    logger.info(f"Starting parallel computation with {n_jobs} jobs for {len(subjects_data)} subjects")
    
    start_time = time.time()
    
    # Use joblib.Parallel for parallel execution
    results = Parallel(n_jobs=n_jobs, backend="loky")(
        delayed(process_single_subject_matrix)(sub_id, matrix) 
        for sub_id, matrix in subjects_data
    )
    
    elapsed = time.time() - start_time
    logger.info(f"Parallel computation completed in {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
    
    return results

def write_outputs(results: List[Dict[str, Any]], output_path: str):
    """Write results to CSV file."""
    logger = get_logger("graph_metrics")
    ensure_dir(output_path)
    
    df = pd.DataFrame(results)
    
    # Sort by subject_id
    df = df.sort_values("subject_id").reset_index(drop=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Results written to {output_path}")
    logger.info(f"Total subjects processed: {len(df)}")

def main():
    """Main entry point for T035."""
    logger = get_logger("graph_metrics")
    logger.info("Starting T035: Compute Graph Metrics (Parallel Optimized)")
    
    # Get paths from config or command line
    config = get_config()
    input_dir = config.get("connectivity_matrices_dir", "data/processed/connectivity_matrices")
    output_file = config.get("graph_metrics_output", "data/processed/graph_metrics.csv")
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output file: {output_file}")
    
    try:
        # Load matrices
        subjects_data = load_connectivity_matrices(input_dir)
        
        if len(subjects_data) == 0:
            logger.error("No valid connectivity matrices found.")
            sys.exit(1)
        
        # Check memory before processing
        if not check_memory_limit(MEMORY_LIMIT_GB):
            logger.error(f"Memory usage exceeds limit of {MEMORY_LIMIT_GB} GB")
            sys.exit(1)
        
        # Compute metrics in parallel
        results = compute_metrics_parallel(subjects_data, n_jobs=N_JOBS)
        
        # Write outputs
        write_outputs(results, output_file)
        
        # Log success
        logger.info("T035 completed successfully")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Please run code/02_preprocess_and_parcellate.py first to generate connectivity matrices.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()