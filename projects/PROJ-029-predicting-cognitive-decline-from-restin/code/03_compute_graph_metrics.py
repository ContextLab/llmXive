"""
T035: Compute Graph Metrics with Parallel Optimization
Refactored to use joblib.Parallel(n_jobs=2) for runtime reduction.
Targets < 30 min for 100 subjects on a 2-core runner.
"""
import os
import sys
import time
import logging
import json
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import networkx as nx
import nibabel as nib
from joblib import Parallel, delayed

# Project-relative imports
from utils.logger import get_logger
from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
    load_aal_atlas_mask
)
from utils.io import load_csv, save_csv, ensure_dir
from config import get_config

# Setup logger
logger = get_logger("graph_metrics")

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if current memory usage is within limit."""
    current = get_memory_usage_gb()
    if current > limit_gb:
        logger.error(f"Memory limit exceeded: {current:.2f}GB > {limit_gb}GB")
        return False
    return True

def load_subject_list(subject_list_path: Path) -> List[str]:
    """Load list of eligible subjects from CSV."""
    if not subject_list_path.exists():
        logger.error(f"Subject list not found: {subject_list_path}")
        sys.exit(1)
    
    df = load_csv(subject_list_path)
    # Expect column 'subject_id' based on T017 output
    if 'subject_id' not in df.columns:
        logger.error(f"Expected 'subject_id' column in {subject_list_path}")
        sys.exit(1)
    
    return df['subject_id'].tolist()

def load_connectivity_matrix(subject_id: str, data_dir: Path) -> Optional[np.ndarray]:
    """
    Load pre-computed connectivity matrix for a subject.
    Assumes matrices are stored as .npy files in data/processed/connectivity/
    """
    matrix_path = data_dir / "connectivity" / f"{subject_id}_connectivity.npy"
    if not matrix_path.exists():
        logger.warning(f"Connectivity matrix not found for {subject_id}: {matrix_path}")
        return None
    
    try:
        matrix = np.load(matrix_path)
        return matrix
    except Exception as e:
        logger.error(f"Failed to load matrix for {subject_id}: {e}")
        return None

def process_single_subject_matrix(subject_id: str, data_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single subject's connectivity matrix and compute graph metrics.
    Returns a dictionary of metrics or None if processing fails.
    """
    try:
        # Load matrix
        adj_matrix = load_connectivity_matrix(subject_id, data_dir)
        if adj_matrix is None:
            return None

        # Create graph
        G = create_graph_from_adjacency(adj_matrix)
        
        if G.number_of_nodes() == 0:
            logger.warning(f"Empty graph for {subject_id}")
            return None

        # Calculate metrics
        metrics = {
            "subject_id": subject_id,
            "degree_centrality": float(np.mean([d for n, d in G.degree()])),
            "global_efficiency": float(calculate_global_efficiency(G)),
            "clustering_coefficient": float(calculate_clustering_coefficient(G)),
            "average_path_length": float(calculate_shortest_path_length(G))
        }
        
        return metrics

    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        return None

def compute_metrics_parallel(subject_ids: List[str], data_dir: Path, n_jobs: int = 2) -> List[Dict[str, Any]]:
    """
    Compute graph metrics for all subjects in parallel using joblib.
    """
    logger.info(f"Starting parallel computation for {len(subject_ids)} subjects with n_jobs={n_jobs}")
    
    # Use joblib.Parallel with delayed execution
    results = Parallel(n_jobs=n_jobs, backend='loky')(
        delayed(process_single_subject_matrix)(sid, data_dir) 
        for sid in subject_ids
    )
    
    # Filter out None results (failed subjects)
    valid_results = [r for r in results if r is not None]
    
    logger.info(f"Successfully processed {len(valid_results)}/{len(subject_ids)} subjects")
    return valid_results

def write_outputs(metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """Write computed metrics to CSV."""
    ensure_dir(output_path.parent)
    save_csv(metrics, output_path)
    logger.info(f"Wrote {len(metrics)} records to {output_path}")

def main():
    """Main entry point for T035."""
    logger.info("Starting T035: Compute Graph Metrics (Parallel Optimized)")
    
    # Load configuration
    config = get_config()
    data_dir = Path(config["data"]["processed"])
    subject_list_path = data_dir / "eligible_subjects.csv"
    output_path = data_dir / "graph_metrics.csv"
    
    # Check memory before starting
    if not check_memory_limit():
        logger.error("Memory check failed before starting computation")
        sys.exit(1)
    
    # Load subject list
    subject_ids = load_subject_list(subject_list_path)
    logger.info(f"Loaded {len(subject_ids)} eligible subjects")
    
    if len(subject_ids) == 0:
        logger.error("No eligible subjects found")
        sys.exit(1)
    
    # Record start time
    start_time = time.time()
    
    # Compute metrics in parallel
    metrics = compute_metrics_parallel(subject_ids, data_dir, n_jobs=2)
    
    # Record end time
    elapsed_time = time.time() - start_time
    logger.info(f"Total computation time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    # Write outputs
    write_outputs(metrics, output_path)
    
    # Verify output
    if not output_path.exists():
        logger.error("Output file was not created")
        sys.exit(1)
    
    logger.info("T035 completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
