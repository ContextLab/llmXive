from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import psutil
import pandas as pd

# Import from project utilities
from utils.logger import get_logger, log_operation
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
    calculate_local_efficiency
)

logger = get_logger("compute_graph_metrics")

# Constants
DATA_DIR = Path("data/processed")
CONNECTIVITY_DIR = DATA_DIR / "connectivity_matrices"
OUTPUT_CSV = DATA_DIR / "graph_metrics.csv"
EXCLUDED_LOG = DATA_DIR / "excluded_subjects.log"
STATUS_FILE = DATA_DIR / "graph_metrics_status.json"

RAM_LIMIT_GB = 7.0

def check_memory_usage() -> float:
    """Check current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def read_eligible_subjects() -> List[str]:
    """Read eligible subjects from the filtered CSV."""
    eligible_file = DATA_DIR / "eligible_subjects.csv"
    if not eligible_file.exists():
        logger.log("missing_eligible_file", operation="read_eligible_subjects", error="File not found")
        return []
    
    subjects = []
    with open(eligible_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'subject_id' in row:
                subjects.append(row['subject_id'])
    logger.log("subjects_loaded", count=len(subjects), operation="read_eligible_subjects")
    return subjects

def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """Load connectivity matrix for a subject."""
    # Expecting files like: connectivity_matrices/sub-001/sub-001_matrix.npy or similar
    # Based on T018 output structure
    subj_dir = CONNECTIVITY_DIR / subject_id
    
    if not subj_dir.exists():
        # Try looking for .npy directly in the subject dir or common naming
        potential_files = list(subj_dir.glob("*.npy"))
        if not potential_files:
            return None
        matrix_path = potential_files[0]
    else:
        potential_files = list(subj_dir.glob("*.npy"))
        if not potential_files:
            # Fallback: check for specific naming convention if directory structure varies
            # e.g., if T018 saved directly to CONNECTIVITY_DIR/subject_id_matrix.npy
            alt_path = CONNECTIVITY_DIR / f"{subject_id}_matrix.npy"
            if alt_path.exists():
                matrix_path = alt_path
            else:
                return None
        else:
            matrix_path = potential_files[0]

    try:
        matrix = np.load(matrix_path)
        return matrix
    except Exception as e:
        logger.log("load_failure", subject=subject_id, error=str(e), operation="load_connectivity")
        return None

def compute_subject_metrics(subject_id: str, matrix: np.ndarray) -> Dict[str, Any]:
    """Compute graph metrics for a single subject's connectivity matrix."""
    try:
        # Ensure matrix is symmetric and float
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(f"Matrix for {subject_id} is not square: {matrix.shape}")
        
        # Calculate metrics using utils.graph
        degree = calculate_degree_centrality(matrix)
        efficiency = calculate_global_efficiency(matrix)
        clustering = calculate_clustering_coefficient(matrix)
        # Shortest path length might return infinity for disconnected graphs, handle safely
        path_len = calculate_shortest_path_length(matrix)
        local_eff = calculate_local_efficiency(matrix)

        return {
            "subject_id": subject_id,
            "node_degree": float(degree),
            "global_efficiency": float(efficiency),
            "clustering_coeff": float(clustering),
            "path_length": float(path_len) if not np.isinf(path_len) else -1.0,
            "local_efficiency": float(local_eff)
        }
    except Exception as e:
        logger.log("computation_error", subject=subject_id, error=str(e), operation="compute_subject_metrics")
        return None

def process_subject_wrapper(subject_id: str) -> Optional[Dict[str, Any]]:
    """Wrapper to process a single subject, checking memory."""
    start_ram = check_memory_usage()
    logger.log("processing_subject_start", subject=subject_id, ram_gb=start_ram, operation="process_subject_wrapper")
    
    matrix = load_connectivity(subject_id)
    if matrix is None:
        logger.log("skipped_no_matrix", subject=subject_id, operation="process_subject_wrapper")
        return None

    result = compute_subject_metrics(subject_id, matrix)
    
    end_ram = check_memory_usage()
    if end_ram > RAM_LIMIT_GB:
        logger.log("ram_warning", subject=subject_id, ram_gb=end_ram, limit_gb=RAM_LIMIT_GB, operation="process_subject_wrapper")
    
    return result

def write_metrics_csv(results: List[Dict[str, Any]]) -> None:
    """Write results to CSV."""
    if not results:
        logger.log("no_results_to_write", operation="write_metrics_csv")
        return

    fieldnames = [
        "subject_id", "node_degree", "global_efficiency", 
        "clustering_coeff", "path_length", "local_efficiency"
    ]
    
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            if row:  # Skip None entries
                writer.writerow(row)
    
    logger.log("metrics_written", count=len(results), path=str(OUTPUT_CSV), operation="write_metrics_csv")

def write_excluded_log(excluded_subjects: List[str]) -> None:
    """Write log of excluded subjects."""
    with open(EXCLUDED_LOG, 'w') as f:
        for subj in excluded_subjects:
            f.write(f"{subj}\n")
    logger.log("excluded_log_written", count=len(excluded_subjects), operation="write_excluded_log")

def write_status(status: str, details: Dict[str, Any]) -> None:
    """Write status JSON."""
    status_data = {
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)
    logger.log("status_written", path=str(STATUS_FILE), operation="write_status")

@log_operation("compute_graph_metrics_main")
def main():
    logger.log("start", operation="main")
    
    # Read eligible subjects
    subjects = read_eligible_subjects()
    if not subjects:
        logger.log("no_eligible_subjects", operation="main")
        write_status("error", {"reason": "No eligible subjects found in data/processed/eligible_subjects.csv"})
        sys.exit(1)
    
    results = []
    excluded = []
    
    for subj_id in subjects:
        res = process_subject_wrapper(subj_id)
        if res:
            results.append(res)
        else:
            excluded.append(subj_id)
    
    # Write outputs
    write_metrics_csv(results)
    write_excluded_log(excluded)
    
    success = len(results) > 0
    status_msg = "success" if success else "partial_failure"
    if not success:
        status_msg = "failure"
    
    write_status(
        status_msg, 
        {
            "total_subjects": len(subjects),
            "processed": len(results),
            "excluded": len(excluded),
            "output_file": str(OUTPUT_CSV)
        }
    )
    
    if not success:
        sys.exit(1)
    
    logger.log("end", operation="main")

if __name__ == "__main__":
    main()