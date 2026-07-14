"""
T035: Compute Graph Metrics with Parallel Optimization

Refactored to use joblib.Parallel(n_jobs=2) for subject-by-subject processing
to reduce runtime while staying within 7GB RAM limits.

Outputs:
    data/processed/graph_metrics.csv: Subject IDs and calculated graph metrics
"""
import os
import sys
import time
import logging
import json
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from joblib import Parallel, delayed
import pandas as pd
import numpy as np
import networkx as nx
import nibabel as nib

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.graph import (
    load_aal_atlas_mask,
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_local_efficiency,
    calculate_shortest_path_length
)
from utils.io import load_csv, save_dataframe, ensure_dir
from config import get_config

# Constants
MEMORY_LIMIT_GB = 7.0
TARGET_RUNTIME_MINUTES = 30.0
N_JOBS = 2

def get_logger_wrapper(name: str) -> logging.Logger:
    """Get a logger instance for this module."""
    return get_logger(name)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """Check if current memory usage is within limit."""
    current = get_memory_usage_gb()
    return current < limit_gb

def load_subject_list(subject_file: Path) -> List[Dict[str, Any]]:
    """Load list of subjects from eligible_subjects.csv."""
    if not subject_file.exists():
        raise FileNotFoundError(f"Subject list file not found: {subject_file}")
    
    df = load_csv(subject_file)
    if df is None or df.empty:
        raise ValueError(f"Subject list file is empty: {subject_file}")
    
    subjects = []
    for _, row in df.iterrows():
        subjects.append({
            'subject_id': row['subject_id'],
            'session_1': row['session_1'],
            'session_2': row['session_2'],
            'nifti_path': row['nifti_path']
        })
    
    return subjects

def load_connectivity_matrix(nifti_path: Path, atlas_mask: np.ndarray, logger: logging.Logger) -> Optional[np.ndarray]:
    """Load and process connectivity matrix from NIfTI file."""
    try:
        # Load the NIfTI file
        img = nib.load(str(nifti_path))
        data = img.get_fdata()
        
        # Extract time series for each region
        n_regions = atlas_mask.max() + 1
        time_series = []
        
        for region in range(n_regions):
            mask = atlas_mask == region
            if np.sum(mask) > 0:
                region_data = data[mask]
                # Average time series for this region
                ts = np.mean(region_data, axis=0) if region_data.ndim > 1 else region_data
                time_series.append(ts)
        
        if len(time_series) < n_regions:
            logger.warning(f"Missing regions for {nifti_path}")
            return None
        
        # Convert to numpy array
        ts_array = np.array(time_series)
        
        # Compute correlation matrix
        corr_matrix = np.corrcoef(ts_array)
        
        # Handle NaN values
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        
        return corr_matrix
        
        return metrics

    except Exception as e:
        logger.error(f"Error loading connectivity matrix for {nifti_path}: {e}")
        return None

def process_single_subject_matrix(subject_info: Dict[str, Any], atlas_mask: np.ndarray, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Process a single subject's connectivity matrix and compute graph metrics."""
    subject_id = subject_info['subject_id']
    nifti_path = Path(subject_info['nifti_path'])
    
    if not nifti_path.exists():
        logger.warning(f"NIfTI file not found for {subject_id}: {nifti_path}")
        return None
    
    # Load connectivity matrix
    corr_matrix = load_connectivity_matrix(nifti_path, atlas_mask, logger)
    if corr_matrix is None:
        return None
    
    # Create graph from adjacency matrix
    graph = create_graph_from_adjacency(corr_matrix)
    if graph is None:
        logger.warning(f"Failed to create graph for {subject_id}")
        return None
    
    # Compute graph metrics
    try:
        metrics = {
            'subject_id': subject_id,
            'global_efficiency': calculate_global_efficiency(graph),
            'clustering_coefficient': calculate_clustering_coefficient(graph),
            'degree_centrality': calculate_degree_centrality(graph),
            'local_efficiency': calculate_local_efficiency(graph),
            'average_path_length': calculate_shortest_path_length(graph)
        }
        
        # Check memory usage
        if not check_memory_limit():
            logger.warning(f"Memory limit exceeded for {subject_id}")
            return None
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error computing graph metrics for {subject_id}: {e}")
        return None

def compute_metrics_parallel(subjects: List[Dict[str, Any]], atlas_mask: np.ndarray, logger: logging.Logger) -> List[Dict[str, Any]]:
    """Compute graph metrics for all subjects in parallel."""
    logger.info(f"Starting parallel computation for {len(subjects)} subjects with n_jobs={N_JOBS}")
    
    # Use joblib for parallel processing
    results = Parallel(n_jobs=N_JOBS, verbose=10)(
        delayed(process_single_subject_matrix)(subject, atlas_mask, logger)
        for subject in subjects
    )
    
    # Filter out None results
    valid_results = [r for r in results if r is not None]
    
    logger.info(f"Successfully processed {len(valid_results)}/{len(subjects)} subjects")
    return valid_results

def write_outputs(metrics: List[Dict[str, Any]], output_path: Path, logger: logging.Logger):
    """Write graph metrics to CSV file."""
    if not metrics:
        logger.error("No metrics to write")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(metrics)
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    
    # Save to CSV
    save_dataframe(df, output_path)
    logger.info(f"Graph metrics written to {output_path}")

def main():
    """Main entry point for graph metrics computation."""
    logger = get_logger_wrapper('graph_metrics')
    logger.info("Starting T035: Compute Graph Metrics (Parallel Optimized)")
    
    start_time = time.time()
    
    # Load configuration
    config = get_config()
    data_dir = Path(config['data']['processed'])
    atlas_path = Path(config['data']['atlas'])
    
    # Load subject list
    subject_file = data_dir / 'eligible_subjects.csv'
    try:
        subjects = load_subject_list(subject_file)
        logger.info(f"Loaded {len(subjects)} eligible subjects")
    except Exception as e:
        logger.error(f"Failed to load subject list: {e}")
        sys.exit(1)
    
    # Load AAL atlas mask
    try:
        atlas_mask = load_aal_atlas_mask(atlas_path)
        logger.info(f"Loaded AAL atlas mask with shape {atlas_mask.shape}")
    except Exception as e:
        logger.error(f"Failed to load atlas mask: {e}")
        sys.exit(1)
    
    # Compute graph metrics in parallel
    metrics = compute_metrics_parallel(subjects, atlas_mask, logger)
    
    # Write outputs
    output_path = data_dir / 'graph_metrics.csv'
    write_outputs(metrics, output_path, logger)
    
    # Calculate runtime
    elapsed_time = time.time() - start_time
    elapsed_minutes = elapsed_time / 60.0
    
    logger.info(f"Total runtime: {elapsed_minutes:.2f} minutes")
    
    # Verify runtime target
    if elapsed_minutes > TARGET_RUNTIME_MINUTES:
        logger.warning(f"Runtime exceeded target of {TARGET_RUNTIME_MINUTES} minutes")
    else:
        logger.info(f"Runtime target met: {elapsed_minutes:.2f} < {TARGET_RUNTIME_MINUTES} minutes")
    
    # Log final memory usage
    final_memory = get_memory_usage_gb()
    logger.info(f"Final memory usage: {final_memory:.2f} GB")
    
    if final_memory > MEMORY_LIMIT_GB:
        logger.warning(f"Memory limit exceeded: {final_memory:.2f} > {MEMORY_LIMIT_GB} GB")
    
    logger.info("T035 completed successfully")

if __name__ == '__main__':
    main()