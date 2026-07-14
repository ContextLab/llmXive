"""
Compute graph-theoretical metrics from connectivity matrices.

This script calculates node degree, global efficiency, clustering coefficient,
and path length for every subject in the eligible subjects list.

It processes subjects one-by-one to stay within memory limits and uses
joblib for parallel processing of the computation.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import networkx as nx
import psutil
from joblib import Parallel, delayed

# Import from local utils
from utils.logger import get_logger, log_operation
from utils.graph import (
    load_aal_atlas_mask,
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)
from utils.io import ensure_dir, load_csv, save_csv, load_json, save_json

# Configuration
DATA_PROCESSED_DIR = Path("data/processed")
DATA_RAW_DIR = Path("data/raw")
CONNECTIVITY_DIR = DATA_PROCESSED_DIR / "connectivity_matrices"
GRAPH_METRICS_FILE = DATA_PROCESSED_DIR / "graph_metrics.csv"
EXCLUDED_LOG_FILE = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_FILE = DATA_PROCESSED_DIR / "graph_metrics_status.json"
ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED_DIR / "eligible_subjects.csv"

# Memory limit (7GB)
MEMORY_LIMIT_GB = 7.0

def get_logger_wrapper(name: str = "graph_metrics") -> Any:
    """Wrapper to get a logger instance."""
    return get_logger(name)

def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    return mem_gb

def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """
    Load a connectivity matrix for a given subject.
    
    Args:
        subject_id: The subject identifier.
        
    Returns:
        The connectivity matrix as a numpy array, or None if not found.
    """
    # Expected path pattern: data/processed/connectivity_matrices/<subject_id>_conn.npy
    conn_file = CONNECTIVITY_DIR / f"{subject_id}_conn.npy"
    
    if not conn_file.exists():
        # Try alternative pattern: subject_id might be in a subdirectory
        conn_file = CONNECTIVITY_DIR / subject_id / "connectivity.npy"
        if not conn_file.exists():
            # Try .mat extension
            conn_file = CONNECTIVITY_DIR / f"{subject_id}_conn.mat"
            if not conn_file.exists():
                return None
    
    try:
        if conn_file.suffix == '.npy':
            return np.load(conn_file)
        elif conn_file.suffix == '.mat':
            import scipy.io
            mat_data = scipy.io.loadmat(conn_file)
            # Try common keys
            for key in ['conn', 'connectivity', 'adjacency', 'data']:
                if key in mat_data:
                    return mat_data[key]
            # If no known key, return the first array found
            for key in mat_data:
                if key != '__header__' and key != '__version__' and key != '__globals__':
                    return mat_data[key]
            return None
        else:
            return None
    except Exception as e:
        logger = get_logger_wrapper("load_connectivity")
        logger.log("load_connectivity_error", subject_id=subject_id, error=str(e))
        return None

def compute_subject_metrics(subject_id: str) -> Dict[str, Any]:
    """
    Compute graph metrics for a single subject.
    
    Args:
        subject_id: The subject identifier.
        
    Returns:
        A dictionary containing the subject ID and computed metrics.
    """
    logger = get_logger_wrapper("compute_subject_metrics")
    logger.log("start_compute", subject_id=subject_id)
    
    # Check memory before processing
    current_mem = check_memory_usage()
    if current_mem > MEMORY_LIMIT_GB * 0.9:
        logger.log("memory_warning", subject_id=subject_id, current_memory_gb=current_mem)
    
    conn_matrix = load_connectivity(subject_id)
    
    if conn_matrix is None:
        logger.log("no_connectivity", subject_id=subject_id)
        return {"subject_id": subject_id, "status": "failed", "reason": "no_connectivity"}
    
    # Validate matrix
    if conn_matrix.shape[0] != conn_matrix.shape[1]:
        logger.log("invalid_matrix", subject_id=subject_id, shape=str(conn_matrix.shape))
        return {"subject_id": subject_id, "status": "failed", "reason": "invalid_matrix"}
    
    # Create graph from adjacency matrix
    try:
        G = create_graph_from_adjacency(conn_matrix)
    except Exception as e:
        logger.log("graph_creation_error", subject_id=subject_id, error=str(e))
        return {"subject_id": subject_id, "status": "failed", "reason": "graph_creation_error"}
    
    # Calculate metrics
    try:
        degree = calculate_degree_centrality(G)
        global_eff = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        avg_path = calculate_shortest_path_length(G)
        
        result = {
            "subject_id": subject_id,
            "status": "success",
            "degree_centrality": float(np.mean(degree)) if len(degree) > 0 else 0.0,
            "global_efficiency": float(global_eff) if global_eff is not None else 0.0,
            "clustering_coefficient": float(clustering) if clustering is not None else 0.0,
            "average_path_length": float(avg_path) if avg_path is not None else 0.0,
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
        }
        
        logger.log("success", subject_id=subject_id, metrics=result)
        return result
        
    except Exception as e:
        logger.log("metric_calculation_error", subject_id=subject_id, error=str(e))
        return {"subject_id": subject_id, "status": "failed", "reason": "metric_calculation_error"}

def process_subject_wrapper(subject_id: str) -> Dict[str, Any]:
    """
    Wrapper for parallel processing of a subject.
    
    Args:
        subject_id: The subject identifier.
        
    Returns:
        A dictionary containing the subject ID and computed metrics.
    """
    return compute_subject_metrics(subject_id)

def read_eligible_subjects() -> List[str]:
    """
    Read the list of eligible subjects from the CSV file.
    
    Returns:
        A list of subject IDs.
    """
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger = get_logger_wrapper("read_eligible_subjects")
        logger.log("file_not_found", path=str(ELIGIBLE_SUBJECTS_FILE))
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
    
    subjects = []
    with open(ELIGIBLE_SUBJECTS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'subject_id' in row:
                subjects.append(row['subject_id'])
            elif 'subject' in row:
                subjects.append(row['subject'])
            else:
                # Assume first column is subject ID
                subjects.append(list(row.values())[0])
    
    return subjects

def write_metrics_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the computed metrics to a CSV file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
    """
    ensure_dir(output_path.parent)
    
    # Filter successful results
    successful = [r for r in results if r.get("status") == "success"]
    
    if not successful:
        logger = get_logger_wrapper("write_metrics_csv")
        logger.log("no_successful_results", output_path=str(output_path))
        return
    
    fieldnames = [
        "subject_id",
        "degree_centrality",
        "global_efficiency",
        "clustering_coefficient",
        "average_path_length",
        "num_nodes",
        "num_edges"
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in successful:
            row = {k: result[k] for k in fieldnames if k in result}
            writer.writerow(row)

def write_excluded_log(results: List[Dict[str, Any]], log_path: Path) -> None:
    """
    Write a log of excluded subjects.
    
    Args:
        results: List of result dictionaries.
        log_path: Path to the log file.
    """
    ensure_dir(log_path.parent)
    
    failed = [r for r in results if r.get("status") == "failed"]
    
    with open(log_path, 'w') as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total failed: {len(failed)}\n\n")
        
        for result in failed:
            f.write(f"Subject: {result.get('subject_id', 'unknown')}\n")
            f.write(f"  Reason: {result.get('reason', 'unknown')}\n")
            f.write("\n")

def write_status(results: List[Dict[str, Any]], status_path: Path) -> None:
    """
    Write a status report.
    
    Args:
        results: List of result dictionaries.
        status_path: Path to the status file.
    """
    ensure_dir(status_path.parent)
    
    total = len(results)
    successful = len([r for r in results if r.get("status") == "success"])
    failed = total - successful
    
    status = {
        "total_subjects": total,
        "successful": successful,
        "failed": failed,
        "success_rate": successful / total if total > 0 else 0.0,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "output_file": str(GRAPH_METRICS_FILE),
        "excluded_log": str(EXCLUDED_LOG_FILE)
    }
    
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2)

def main() -> int:
    """
    Main entry point for the graph metrics computation.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger = get_logger_wrapper("main")
    logger.log("start")
    
    start_time = time.time()
    
    # Ensure output directories exist
    ensure_dir(DATA_PROCESSED_DIR)
    ensure_dir(CONNECTIVITY_DIR)
    
    # Read eligible subjects
    try:
        subjects = read_eligible_subjects()
    except FileNotFoundError as e:
        logger.log("error", message=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    if not subjects:
        logger.log("no_subjects")
        print("No eligible subjects found.", file=sys.stderr)
        return 1
    
    logger.log("subjects_loaded", count=len(subjects))
    
    # Process subjects in parallel
    # Use n_jobs=2 as specified in the task
    logger.log("parallel_processing_start", n_jobs=2)
    
    results = Parallel(n_jobs=2, backend='loky')(
        delayed(process_subject_wrapper)(subject_id)
        for subject_id in subjects
    )
    
    # Write outputs
    write_metrics_csv(results, GRAPH_METRICS_FILE)
    write_excluded_log(results, EXCLUDED_LOG_FILE)
    write_status(results, STATUS_FILE)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.log("complete", duration_seconds=duration)
    
    # Report results
    successful = len([r for r in results if r.get("status") == "success"])
    print(f"Processed {len(subjects)} subjects: {successful} successful, {len(results) - successful} failed")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Output: {GRAPH_METRICS_FILE}")
    
    # Check if we met the runtime target (30 minutes = 1800 seconds)
    if duration > 1800:
        print(f"Warning: Runtime exceeded 30-minute target ({duration:.2f}s)", file=sys.stderr)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
