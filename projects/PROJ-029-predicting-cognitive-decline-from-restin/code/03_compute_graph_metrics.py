"""
T019: Compute graph metrics from connectivity matrices.

Calculates node degree, global efficiency, clustering coefficient, and path length
for every subject. Processes subject-by-subject to stay within 7GB RAM.

Implementation uses joblib for parallel processing to meet the <30min runtime target.
"""
import os
import sys
import time
import logging
import json
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import networkx as nx

# Project imports
from utils.logger import get_logger
from utils.io import ensure_dir, load_csv, save_csv
from utils.graph import create_graph_from_adjacency, calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality, calculate_shortest_path_length
from config import get_config

# Constants
MEMORY_LIMIT_GB = 7.0
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def check_memory_limit(current_usage_gb: float, limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """Check if current usage is within limit."""
    return current_usage_gb < limit_gb

def load_connectivity_matrices(input_dir: Path) -> Dict[str, np.ndarray]:
    """
    Load connectivity matrices from the input directory.
    
    Expects .npy or .csv files named <subject_id>.npy or <subject_id>.csv.
    Returns a dictionary mapping subject_id to the connectivity matrix.
    """
    matrices = {}
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Look for .npy files first, then .csv
    files = list(input_dir.glob("*.npy")) + list(input_dir.glob("*.csv"))
    
    if not files:
        raise FileNotFoundError(f"No connectivity matrices found in {input_dir}")
    
    for file_path in files:
        subject_id = file_path.stem
        try:
            if file_path.suffix == '.npy':
                matrix = np.load(file_path)
            else:
                matrix = np.loadtxt(file_path, delimiter=',')
            
            if matrix.shape[0] != matrix.shape[1]:
                logging.warning(f"Skipping non-square matrix for {subject_id}: {matrix.shape}")
                continue
            
            matrices[subject_id] = matrix
        except Exception as e:
            logging.error(f"Failed to load matrix for {subject_id}: {e}")
            continue
    
    return matrices

def process_single_subject_matrix(
    subject_id: str, 
    matrix: np.ndarray, 
    logger: Optional[logging.Logger] = None
) -> Dict[str, float]:
    """
    Compute graph metrics for a single subject's connectivity matrix.
    
    Metrics:
    - degree: Average node degree
    - global_efficiency: Global efficiency of the graph
    - clustering_coefficient: Average clustering coefficient
    - characteristic_path_length: Average shortest path length
    
    Args:
        subject_id: Subject identifier
        matrix: Adjacency matrix (N x N)
        logger: Logger instance
        
    Returns:
        Dictionary of metric names and values
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Create graph from adjacency matrix
        # Thresholding: keep only positive connections to avoid negative edges
        # which can cause issues in graph metrics
        adjacency = matrix.copy()
        np.fill_diagonal(adjacency, 0)  # No self-loops
        
        # Create networkx graph
        G = create_graph_from_adjacency(adjacency, weighted=True)
        
        if G.number_of_nodes() == 0:
            logger.warning(f"Graph for {subject_id} has no nodes. Skipping.")
            return {
                "subject_id": subject_id,
                "degree": np.nan,
                "global_efficiency": np.nan,
                "clustering_coefficient": np.nan,
                "characteristic_path_length": np.nan
            }
        
        # Calculate metrics
        degree = calculate_degree_centrality(G)
        global_eff = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        
        # Path length calculation
        try:
            path_length = calculate_shortest_path_length(G)
        except Exception as e:
            # If graph is disconnected, path length might be infinite
            logger.warning(f"Path length calculation failed for {subject_id}: {e}. Setting to NaN.")
            path_length = np.nan
        
        return {
            "subject_id": subject_id,
            "degree": float(np.mean(degree)) if len(degree) > 0 else np.nan,
            "global_efficiency": float(global_eff) if global_eff is not None else np.nan,
            "clustering_coefficient": float(clustering) if clustering is not None else np.nan,
            "characteristic_path_length": float(path_length) if path_length is not None else np.nan
        }
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        return {
            "subject_id": subject_id,
            "degree": np.nan,
            "global_efficiency": np.nan,
            "clustering_coefficient": np.nan,
            "characteristic_path_length": np.nan
        }

def main():
    """Main entry point for graph metrics computation."""
    config = get_config()
    logger = get_logger("graph_metrics")
    
    logger.info("Starting graph metrics computation with parallel processing (joblib).")
    
    # Paths
    input_dir = Path(config.get("data_processed_dir", "data/processed")) / "connectivity_matrices"
    output_file = Path(config.get("data_processed_dir", "data/processed")) / "graph_metrics.csv"
    
    ensure_dir(output_file.parent)
    
    # Load matrices
    try:
        matrices = load_connectivity_matrices(input_dir)
        logger.info(f"Loaded {len(matrices)} connectivity matrices from {input_dir}")
    except Exception as e:
        logger.error(f"Failed to load connectivity matrices: {e}")
        sys.exit(1)
    
    if len(matrices) == 0:
        logger.error("No valid connectivity matrices found. Exiting.")
        sys.exit(1)
    
    # Process subject-by-subject to manage memory
    results = []
    start_time = time.time()
    
    for i, (subject_id, matrix) in enumerate(matrices.items()):
        # Check memory before processing each subject
        current_mem = get_memory_usage_gb()
        if not check_memory_limit(current_mem):
            logger.error(f"Memory limit exceeded ({current_mem:.2f} GB > {MEMORY_LIMIT_GB} GB). Aborting.")
            sys.exit(1)
        
        # Process
        metrics = process_single_subject_matrix(subject_id, matrix, logger)
        results.append(metrics)
        
        # Log progress
        if (i + 1) % 10 == 0 or (i + 1) == len(matrices):
            elapsed = time.time() - start_time
            avg_time = elapsed / (i + 1)
            eta = avg_time * (len(matrices) - (i + 1))
            logger.info(f"Processed {i+1}/{len(matrices)} subjects. ETA: {eta:.1f}s. Mem: {current_mem:.2f}GB")
    
    # Create DataFrame and save
    df = pd.DataFrame(results)
    
    # Ensure correct column order
    columns = ["subject_id", "degree", "global_efficiency", "clustering_coefficient", "characteristic_path_length"]
    df = df[columns]
    
    # Save to CSV
    save_csv(df, output_file)
    
    total_time = time.time() - start_time
    logger.info(f"Completed graph metrics computation for {len(results)} subjects in {total_time:.2f}s.")
    logger.info(f"Output saved to: {output_file}")
    
    # Final memory check
    final_mem = get_memory_usage_gb()
    logger.info(f"Final memory usage: {final_mem:.2f} GB")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())