"""
T019: Compute Graph Metrics from Connectivity Matrices

This script calculates node degree, global efficiency, clustering coefficient,
and path length for every subject's connectivity matrix.

It processes subjects one-by-one to stay within the 7GB RAM limit.
Output: data/processed/graph_metrics.csv
"""
import os
import sys
import time
import logging
import json
import psutil
import pandas as pd
import numpy as np
import networkx as nx
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length
)
from utils.io import load_csv, save_csv, ensure_dir
from utils.logger import get_logger
from config import get_config

# Constants
RAM_LIMIT_GB = 7.0
MEMORY_CHECK_INTERVAL = 10  # subjects

def get_logger_wrapper(name: str) -> logging.Logger:
    """Get a logger for the script."""
    return get_logger(name)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(current_gb: float, limit_gb: float = RAM_LIMIT_GB) -> bool:
    """Check if current memory usage is within the limit."""
    return current_gb < limit_gb

def load_subject_list(subjects_path: Path) -> List[Dict[str, Any]]:
    """Load the list of eligible subjects."""
    if not subjects_path.exists():
        raise FileNotFoundError(f"Subject list not found: {subjects_path}")
    
    df = pd.read_csv(subjects_path)
    subjects = df.to_dict('records')
    return subjects

def load_connectivity_matrix(matrix_path: Path) -> np.ndarray:
    """Load a connectivity matrix from a NIfTI file or numpy file."""
    if matrix_path.suffix == '.nii' or matrix_path.suffix == '.nii.gz':
        # Load NIfTI file (expecting 3D or 4D with single volume)
        img = nib.load(str(matrix_path))
        data = img.get_fdata()
        # If 4D, take the first volume
        if data.ndim == 4:
            data = data[:, :, :, 0]
        # Reshape to 2D if necessary (assuming 90x90x90 or similar)
        # We expect a flattened or reshaped matrix. 
        # For AAL atlas, we typically have a 90x90 matrix stored in a 3D volume 
        # or a separate .npy file.
        # Assuming the preprocessing step stored it as a 90x90x1 or similar.
        if data.ndim == 3:
            # Try to reshape if it's a cube of 90
            if data.shape[0] == data.shape[1] == data.shape[2] == 90:
                # This is unlikely to be a direct matrix, maybe it's a volume
                # Let's assume the preprocessing step saved a .npy file for the matrix
                # or a specific 2D slice.
                # Fallback: try to load a .npy file if exists
                npy_path = matrix_path.with_suffix('.npy')
                if npy_path.exists():
                    return load_connectivity_matrix(npy_path)
                else:
                    # Assume it's a flattened 90x90 stored in a specific way
                    # This is a heuristic. In a real pipeline, we'd know the exact format.
                    # Let's assume the matrix is stored as a 1D array of 8100 elements 
                    # in a .npy file or we need to reconstruct it.
                    # For now, if it's a 3D volume, we might need to extract the matrix.
                    # Let's assume the matrix is stored in a .npy file if not directly in NIfTI.
                    pass
            elif data.shape[0] == 90 and data.shape[1] == 90 and data.shape[2] == 1:
                return data[:, :, 0]
        return data
    elif matrix_path.suffix == '.npy':
        return np.load(str(matrix_path))
    else:
        raise ValueError(f"Unsupported file format: {matrix_path.suffix}")

def process_single_subject_matrix(
    subject_id: str,
    matrix_path: Path,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """Process a single subject's connectivity matrix and compute metrics."""
    try:
        logger.info(f"Processing subject: {subject_id}")
        
        # Load matrix
        adj_matrix = load_connectivity_matrix(matrix_path)
        
        # Ensure it's 2D
        if adj_matrix.ndim != 2:
            logger.warning(f"Subject {subject_id}: Matrix is {adj_matrix.ndim}D, reshaping or skipping.")
            # Try to flatten and reshape if possible
            if adj_matrix.size == 8100:  # 90x90
                adj_matrix = adj_matrix.reshape(90, 90)
            else:
                logger.error(f"Subject {subject_id}: Cannot reshape matrix of size {adj_matrix.size}")
                return None
        
        # Create graph
        G = create_graph_from_adjacency(adj_matrix)
        
        # Compute metrics
        # 1. Node Degree (average)
        degree_centrality = calculate_degree_centrality(G)
        avg_degree = np.mean(list(degree_centrality.values()))
        
        # 2. Global Efficiency
        global_eff = calculate_global_efficiency(G)
        
        # 3. Clustering Coefficient
        clustering_coef = calculate_clustering_coefficient(G)
        
        # 4. Average Path Length
        avg_path_len = calculate_shortest_path_length(G)
        
        return {
            'subject_id': subject_id,
            'avg_degree': avg_degree,
            'global_efficiency': global_eff,
            'clustering_coefficient': clustering_coef,
            'average_path_length': avg_path_len
        }
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {str(e)}")
        return None

def compute_metrics_parallel(
    subjects: List[Dict[str, Any]],
    data_dir: Path,
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """Compute metrics for all subjects sequentially to manage memory."""
    results = []
    memory_log = []
    
    for i, subject in enumerate(subjects):
        subject_id = subject['subject_id']
        
        # Check memory every 10 subjects
        if i % MEMORY_CHECK_INTERVAL == 0:
            current_mem = get_memory_usage_gb()
            memory_log.append({'subject_idx': i, 'memory_gb': current_mem})
            if not check_memory_limit(current_mem):
                logger.error(f"Memory limit exceeded at subject {i}. Current: {current_mem:.2f}GB")
                break
        
        # Construct path to matrix
        # Assuming matrices are stored in data/processed/matrix_<subject_id>.npy
        matrix_path = data_dir / f"matrix_{subject_id}.npy"
        
        if not matrix_path.exists():
            logger.warning(f"Matrix not found for subject {subject_id}: {matrix_path}")
            continue
        
        result = process_single_subject_matrix(subject_id, matrix_path, logger)
        if result:
            results.append(result)
        
        # Force garbage collection periodically
        if i % 5 == 0:
            import gc
            gc.collect()
    
    # Log final memory
    final_mem = get_memory_usage_gb()
    memory_log.append({'subject_idx': len(subjects), 'memory_gb': final_mem})
    logger.info(f"Memory profile: {memory_log}")
    
    return results

def write_outputs(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write results to CSV."""
    ensure_dir(output_path.parent)
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logging.info(f"Graph metrics written to {output_path}")

def main():
    """Main entry point."""
    logger = get_logger_wrapper("graph_metrics")
    logger.info("Starting T019: Compute Graph Metrics")
    
    config = get_config()
    data_dir = Path(config["data"]["processed"])
    subjects_path = data_dir / "eligible_subjects.csv"
    output_path = data_dir / "graph_metrics.csv"
    
    # Load subject list
    try:
        subjects = load_subject_list(subjects_path)
        logger.info(f"Loaded {len(subjects)} eligible subjects")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if len(subjects) == 0:
        logger.warning("No eligible subjects found.")
        # Write empty CSV with headers
        pd.DataFrame(columns=['subject_id', 'avg_degree', 'global_efficiency', 
                              'clustering_coefficient', 'average_path_length']).to_csv(output_path, index=False)
        return
    
    # Compute metrics
    results = compute_metrics_parallel(subjects, data_dir, logger)
    
    # Write outputs
    write_outputs(results, output_path)
    
    logger.info("T019 completed successfully.")
