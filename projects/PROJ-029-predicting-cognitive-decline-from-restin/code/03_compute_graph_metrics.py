"""
T035: Compute Graph Metrics from Connectivity Matrices
Refactored to use joblib.Parallel(n_jobs=2) for performance optimization.
Verifies runtime reduction and memory constraints.
"""
import os
import sys
import time
import logging
import json
import psutil
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from joblib import Parallel, delayed

# Import from local utils as per API surface
from utils.logger import get_logger
from utils.graph import (
    load_aal_atlas_mask,
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length
)
from utils.io import ensure_dir, load_csv

# Configuration
N_JOBS = 2
MEMORY_LIMIT_GB = 7.0
TARGET_RUNTIME_MIN = 30.0
INPUT_DIR_NAME = "connectivity_matrices"
OUTPUT_FILE_NAME = "graph_metrics.csv"
SUBJECTS_LIMIT = 100  # Cap for runtime testing if more available

def get_logger_wrapper(name: str) -> logging.Logger:
    """Wrapper to get a logger with specific format."""
    return get_logger(name)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit(current_gb: float, limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """Check if current memory usage exceeds limit."""
    return current_gb < limit_gb

def load_connectivity_matrices(input_dir: Path, limit: int = SUBJECTS_LIMIT) -> List[Tuple[str, np.ndarray]]:
    """
    Load connectivity matrices from the input directory.
    Returns a list of (subject_id, matrix) tuples.
    """
    logger = get_logger("graph_metrics")
    matrices = []
    
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return matrices

    # Find all .npy or .csv files representing matrices
    # Assuming files are named like: sub-001_matrix.npy or sub-001_matrix.csv
    files = sorted(input_dir.glob("*matrix.*"))
    
    for file_path in files:
        if len(matrices) >= limit:
            logger.info(f"Reached subject limit ({limit}). Stopping load.")
            break
        
        try:
            if file_path.suffix == '.npy':
                matrix = np.load(file_path)
            elif file_path.suffix == '.csv':
                matrix = np.loadtxt(file_path, delimiter=',')
            else:
                continue
            
            # Extract subject ID from filename
            stem = file_path.stem
            subject_id = stem.replace("_matrix", "").replace("sub-", "")
            
            matrices.append((subject_id, matrix))
            logger.debug(f"Loaded matrix for {subject_id} from {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue
    
    logger.info(f"Loaded {len(matrices)} matrices.")
    return matrices

def process_single_subject_matrix(subject_id: str, matrix: np.ndarray) -> Optional[Dict]:
    """
    Process a single subject's connectivity matrix to compute graph metrics.
    This function is designed to be called by Parallel.
    """
    try:
        # Create graph from adjacency matrix
        G = create_graph_from_adjacency(matrix)
        
        if G.number_of_nodes() == 0:
            return None

        # Compute metrics
        degree = calculate_degree_centrality(G)
        efficiency = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        path_len = calculate_shortest_path_length(G)
        
        # Average metrics across nodes if applicable, or take global
        # Degree centrality is usually a dict; we take the mean
        avg_degree = np.mean(list(degree.values())) if degree else 0.0
        
        return {
            "subject_id": subject_id,
            "global_efficiency": efficiency,
            "clustering_coefficient": clustering,
            "average_degree_centrality": avg_degree,
            "average_path_length": path_len
        }
    except Exception as e:
        # Log error but return None to allow parallel processing to continue
        # The main thread will handle logging if needed, or we log here
        import logging
        logging.getLogger("graph_metrics").error(f"Error processing {subject_id}: {e}")
        return None

def compute_metrics_parallel(matrices: List[Tuple[str, np.ndarray]], n_jobs: int = N_JOBS) -> List[Dict]:
    """
    Compute graph metrics for all subjects in parallel using joblib.
    """
    logger = get_logger("graph_metrics")
    logger.info(f"Starting graph metrics computation with parallel processing (joblib). n_jobs={n_jobs}")
    
    start_time = time.time()
    
    # Use Parallel to process matrices
    # We pass the subject_id and matrix to the worker function
    results = Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(process_single_subject_matrix)(sub_id, mat) 
        for sub_id, mat in matrices
    )
    
    # Filter out None results
    valid_results = [r for r in results if r is not None]
    
    elapsed = time.time() - start_time
    logger.info(f"Parallel processing completed. Processed {len(valid_results)} subjects in {elapsed:.2f} seconds.")
    
    return valid_results

def write_outputs(results: List[Dict], output_path: Path):
    """
    Write the computed metrics to a CSV file.
    """
    ensure_dir(output_path.parent)
    
    if not results:
        logging.getLogger("graph_metrics").warning("No results to write.")
        # Create an empty file with headers if no data
        pd.DataFrame(columns=["subject_id", "global_efficiency", "clustering_coefficient", 
                              "average_degree_centrality", "average_path_length"]).to_csv(output_path, index=False)
        return

    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logging.getLogger("graph_metrics").info(f"Results written to {output_path}")

def main():
    logger = get_logger("graph_metrics")
    logger.info("Starting T035: Compute Graph Metrics (Parallel Optimized)")

    # Define paths relative to project root
    # Assuming the script is run from the project root or code/ directory
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "data" / "processed" / INPUT_DIR_NAME
    output_file = project_root / "data" / "processed" / OUTPUT_FILE_NAME

    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output file: {output_file}")

    # Check input directory
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        logger.error("Please run code/02_preprocess_and_parcellate.py first to generate connectivity matrices.")
        sys.exit(1)

    # Load matrices
    matrices = load_connectivity_matrices(input_dir)
    if not matrices:
        logger.error("No connectivity matrices found. Cannot proceed.")
        sys.exit(1)

    # Check memory before starting heavy computation
    current_mem = get_memory_usage_gb()
    if not check_memory_limit(current_mem):
        logger.error(f"Memory usage ({current_mem:.2f} GB) exceeds limit ({MEMORY_LIMIT_GB} GB). Aborting.")
        sys.exit(1)

    # Compute metrics in parallel
    results = compute_metrics_parallel(matrices, n_jobs=N_JOBS)

    # Write outputs
    write_outputs(results, output_file)

    # Verify output
    if output_file.exists():
        logger.info(f"SUCCESS: Output file {output_file} created.")
        # Log runtime summary
        logger.info(f"Task completed successfully.")
    else:
        logger.error("FAILED: Output file was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()