"""
Compute graph-theoretical metrics from precomputed connectivity matrices.

This script processes connectivity matrices stored in data/processed/
to calculate graph metrics (degree, efficiency, clustering, path length)
for each subject. It uses joblib for parallel processing to stay within
memory limits and reduce runtime.

Output: data/processed/graph_metrics.csv
"""

import os
import sys
import time
import logging
import psutil
import numpy as np
import pandas as pd
import networkx as nx
import psutil
from joblib import Parallel, delayed
from typing import Dict, List, Tuple, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length
)
from utils.logger import get_logger
from utils.io import save_csv, load_csv
from config import get_config

# Configuration
CONFIG = get_config()
MEMORY_LIMIT_GB = 7.0  # Hard limit as per requirements
N_JOBS = 2  # Parallel processing cores
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

def get_memory_usage_gb() -> float:
    """Return current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """Check if current memory usage is within limit."""
    current = get_memory_usage_gb()
    return current < limit_gb

def process_single_subject_matrix(
    subject_id: str,
    matrix_path: Path,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Process a single subject's connectivity matrix and compute graph metrics.
    
    Args:
        subject_id: Subject identifier
        matrix_path: Path to the connectivity matrix (.npy file)
        logger: Logger instance
        
    Returns:
        Dictionary with subject_id and computed metrics, or None if failed
    """
    try:
        # Load connectivity matrix
        matrix = np.load(matrix_path)
        
        if matrix.shape[0] != matrix.shape[1]:
            logger.warning(f"Non-square matrix for {subject_id}: {matrix.shape}")
            return None
        
        if matrix.shape[0] != 90:
            logger.warning(f"Unexpected matrix size for {subject_id}: {matrix.shape[0]} (expected 90)")
            # Still process but log warning
        
        # Create graph from adjacency matrix
        graph = create_graph_from_adjacency(matrix)
        
        if graph is None or graph.number_of_nodes() == 0:
            logger.warning(f"Failed to create graph for {subject_id}")
            return None
        
        # Compute metrics
        degree = calculate_degree_centrality(graph)
        global_eff = calculate_global_efficiency(graph)
        clustering = calculate_clustering_coefficient(graph)
        avg_path = calculate_shortest_path_length(graph)
        
        # Calculate mean values for the subject
        metrics = {
            'subject_id': subject_id,
            'mean_degree': float(np.mean(degree)) if len(degree) > 0 else 0.0,
            'max_degree': float(np.max(degree)) if len(degree) > 0 else 0.0,
            'global_efficiency': float(global_eff) if global_eff is not None else 0.0,
            'clustering_coefficient': float(clustering) if clustering is not None else 0.0,
            'average_path_length': float(avg_path) if avg_path is not None else 0.0
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error processing {subject_id}: {str(e)}")
        return None

def process_subject_wrapper(
    subject_id: str,
    matrix_path: Path,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """Wrapper for parallel processing with error handling."""
    return process_single_subject_matrix(subject_id, matrix_path, logger)

def load_connectivity_matrices(
    input_dir: Path,
    logger: logging.Logger
) -> List[Tuple[str, Path]]:
    """
    Load list of connectivity matrices from input directory.
    
    Args:
        input_dir: Directory containing .npy matrix files
        logger: Logger instance
        
    Returns:
        List of (subject_id, matrix_path) tuples
    """
    matrix_files = []
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return matrix_files
        
    for file_path in input_dir.glob("*.npy"):
        # Extract subject ID from filename (e.g., sub-001_matrix.npy -> sub-001)
        subject_id = file_path.stem.replace("_matrix", "").replace("matrix_", "")
        matrix_files.append((subject_id, file_path))
    
    logger.info(f"Found {len(matrix_files)} connectivity matrices in {input_dir}")
    return matrix_files

def main():
    """Main entry point for graph metrics computation."""
    # Setup logger
    logger = get_logger("graph_metrics", log_file="data/artifacts/graph_metrics.log")
    logger.info("Starting graph metrics computation")
    
    start_time = time.time()
    
    # Define paths
    config = get_config()
    matrices_dir = Path(config['paths']['processed_data']) / "connectivity_matrices"
    output_file = Path(config['paths']['processed_data']) / "graph_metrics.csv"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load matrices
    matrix_list = load_connectivity_matrices(matrices_dir, logger)
    
    if not matrix_list:
        logger.error("No connectivity matrices found. Cannot proceed.")
        sys.exit(1)
    
    logger.info(f"Processing {len(matrix_list)} subjects with {N_JOBS} parallel jobs")
    
    # Check memory before starting
    if not check_memory_limit():
        logger.error(f"Memory usage exceeds limit ({MEMORY_LIMIT_GB} GB). Aborting.")
        sys.exit(1)
    
    # Process matrices in parallel using joblib
    logger.info("Starting parallel processing...")
    parallel_start = time.time()
    
    results = Parallel(n_jobs=N_JOBS, backend='loky')(
        delayed(process_subject_wrapper)(sid, path, logger)
        for sid, path in matrix_list
    )
    
    parallel_time = time.time() - parallel_start
    logger.info(f"Parallel processing completed in {parallel_time:.2f} seconds")
    
    # Filter out None results
    valid_results = [r for r in results if r is not None]
    
    if not valid_results:
        logger.error("No valid results generated. Check logs for errors.")
        sys.exit(1)
    
    # Create DataFrame and save
    df = pd.DataFrame(valid_results)
    
    # Ensure consistent column order
    columns = ['subject_id', 'mean_degree', 'max_degree', 'global_efficiency', 
               'clustering_coefficient', 'average_path_length']
    df = df[columns]
    
    # Save to CSV
    save_csv(df, output_file)
    logger.info(f"Saved {len(df)} subjects to {output_file}")
    
    # Final memory check
    final_memory = get_memory_usage_gb()
    logger.info(f"Final memory usage: {final_memory:.2f} GB")
    
    # Runtime summary
    total_time = time.time() - start_time
    logger.info(f"Total runtime: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    
    # Verify target runtime for 100 subjects
    if len(df) >= 100:
        if total_time < 1800:  # 30 minutes
            logger.info(f"✓ Runtime target met: {total_time:.2f}s < 1800s (30 min)")
        else:
            logger.warning(f"✗ Runtime target NOT met: {total_time:.2f}s >= 1800s (30 min)")
    
    logger.info("Graph metrics computation completed successfully")
    return 0

if __name__ == "__main__":
    main()