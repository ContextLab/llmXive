"""
T019: Compute graph metrics (degree, efficiency, clustering, path length) from connectivity matrices.
Processes subjects one-by-one to stay within 7GB RAM.
Output: data/processed/graph_metrics.csv
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import networkx as nx
import psutil

# Import from local utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_csv
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
    create_graph_from_adjacency
)

# Configuration
RAM_LIMIT_GB = 7.0
ELIGIBLE_SUBJECTS_FILE = "data/processed/eligible_subjects.csv"
CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
OUTPUT_FILE = "data/processed/graph_metrics.csv"
EXCLUDED_LOG = "data/processed/excluded_subjects.log"
STATUS_FILE = "data/artifacts/data_gate_status.json"

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> bool:
    """Check if current memory usage is below the limit."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > RAM_LIMIT_GB:
        logger.warning(f"Memory usage {mem_gb:.2f}GB exceeds limit {RAM_LIMIT_GB}GB")
        return False
    return True


def read_eligible_subjects(file_path: str) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Eligible subjects file not found: {file_path}")
    
    df = load_csv(file_path)
    # Handle both DataFrame and list returns from load_csv
    if isinstance(df, list):
        return df
    
    # Check for common column names
    col = None
    for c in ["subject_id", "subject", "participant_id", "id"]:
        if c in df.columns:
            col = c
            break
    
    if col is None:
        raise ValueError(f"Could not find subject ID column in {file_path}. Columns: {list(df.columns)}")
    
    return df[col].astype(str).tolist()


def load_connectivity(subject_id: str, connectivity_dir: str) -> Optional[np.ndarray]:
    """Load connectivity matrix for a subject."""
    # Try common filename patterns
    possible_names = [
        f"{subject_id}.npy",
        f"{subject_id}_connectivity.npy",
        f"{subject_id}_corr.npy",
        f"{subject_id}_matrix.npy"
    ]
    
    for name in possible_names:
        path = os.path.join(connectivity_dir, name)
        if os.path.exists(path):
            try:
                matrix = np.load(path)
                return matrix
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")
    
    # Also try .mat files or other extensions if needed
    # Try finding any file starting with subject_id
    if os.path.exists(connectivity_dir):
        for fname in os.listdir(connectivity_dir):
            if fname.startswith(subject_id) and fname.endswith(('.npy', '.mat', '.csv')):
                path = os.path.join(connectivity_dir, fname)
                try:
                    if fname.endswith('.npy'):
                        return np.load(path)
                    elif fname.endswith('.csv'):
                        return np.loadtxt(path, delimiter=',')
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")
    
    return None


def compute_subject_metrics(matrix: np.ndarray, subject_id: str) -> Dict[str, Any]:
    """Compute graph metrics for a single subject's connectivity matrix."""
    # Ensure matrix is symmetric and has zeros on diagonal
    matrix = np.array(matrix, dtype=float)
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 0.0)
    
    # Create graph from adjacency matrix
    G = create_graph_from_adjacency(matrix)
    
    # Calculate metrics
    degree = calculate_degree_centrality(G)
    efficiency = calculate_global_efficiency(G)
    clustering = calculate_clustering_coefficient(G)
    path_length = calculate_shortest_path_length(G)
    
    return {
        "subject_id": subject_id,
        "degree": float(degree) if degree is not None else np.nan,
        "global_efficiency": float(efficiency) if efficiency is not None else np.nan,
        "clustering_coefficient": float(clustering) if clustering is not None else np.nan,
        "mean_path_length": float(path_length) if path_length is not None else np.nan
    }


def process_subject_wrapper(subject_id: str, connectivity_dir: str, excluded_log: str) -> Optional[Dict[str, Any]]:
    """Wrapper to process a single subject with error handling."""
    try:
        matrix = load_connectivity(subject_id, connectivity_dir)
        if matrix is None:
            logger.error(f"No connectivity matrix found for {subject_id}")
            with open(excluded_log, 'a') as f:
                f.write(f"{subject_id}: No connectivity matrix found\n")
            return None
        
        metrics = compute_subject_metrics(matrix, subject_id)
        return metrics
    except Exception as e:
        logger.error(f"Error processing {subject_id}: {e}")
        with open(excluded_log, 'a') as f:
            f.write(f"{subject_id}: {str(e)}\n")
        return None


def write_metrics_csv(metrics_list: List[Dict[str, Any]], output_path: str) -> None:
    """Write metrics to CSV file."""
    if not metrics_list:
        logger.warning("No metrics to write")
        # Write header only to indicate file was created
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "degree", "global_efficiency", "clustering_coefficient", "mean_path_length"])
            writer.writeheader()
        return

    fieldnames = ["subject_id", "degree", "global_efficiency", "clustering_coefficient", "mean_path_length"]
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for metrics in metrics_list:
            writer.writerow(metrics)


def write_excluded_log(excluded_log: str, subject_id: str, reason: str) -> None:
    """Log excluded subjects."""
    ensure_dir(excluded_log)
    with open(excluded_log, 'a') as f:
        f.write(f"{subject_id}: {reason}\n")


def write_status(total: int, success: int, status: str, message: str = "") -> None:
    """Write status JSON file."""
    status_data = {
        "task": "compute_graph_metrics",
        "total_subjects": total,
        "successful": success,
        "failed": total - success,
        "status": status,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    ensure_dir(STATUS_FILE)
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point for graph metrics computation."""
    start_time = time.time()
    logger.info("Starting graph metrics computation")
    
    # Ensure directories exist
    ensure_dir(OUTPUT_FILE)
    ensure_dir(EXCLUDED_LOG)
    ensure_dir(CONNECTIVITY_DIR)
    
    # Clear previous excluded log
    if os.path.exists(EXCLUDED_LOG):
        os.remove(EXCLUDED_LOG)
    
    # Read eligible subjects
    try:
        subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    except Exception as e:
        logger.error(f"Failed to read eligible subjects: {e}")
        write_status(0, 0, "error", str(e))
        return 1
    
    if not subjects:
        logger.warning("No eligible subjects found")
        write_status(0, 0, "warning", "No eligible subjects")
        # Still create output file with headers
        write_metrics_csv([], OUTPUT_FILE)
        write_status(0, 0, "success", "Completed with no subjects")
        return 0
    
    logger.info(f"Processing {len(subjects)} subjects")
    
    metrics_list = []
    success_count = 0
    
    for i, subject_id in enumerate(subjects):
        # Check memory periodically
        if i % 10 == 0:
            if not check_memory_usage():
                logger.error("Memory limit exceeded, stopping")
                write_status(i, success_count, "error", "Memory limit exceeded")
                return 1
        
        metrics = process_subject_wrapper(subject_id, CONNECTIVITY_DIR, EXCLUDED_LOG)
        if metrics:
            metrics_list.append(metrics)
            success_count += 1
            logger.debug(f"Processed {i+1}/{len(subjects)}: {subject_id}")
    
    # Write results
    write_metrics_csv(metrics_list, OUTPUT_FILE)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed processing {success_count}/{len(subjects)} subjects in {elapsed:.2f}s")
    
    if success_count == 0:
        write_status(len(subjects), 0, "error", "No subjects successfully processed")
        return 1
    
    write_status(len(subjects), success_count, "success", f"Processed {success_count} subjects in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())