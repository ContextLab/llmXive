"""
code/03_compute_graph_metrics.py
Compute graph-theoretical metrics from connectivity matrices.
Refactored for joblib parallelization (n_jobs=2) and memory safety.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import networkx as nx
from joblib import Parallel, delayed

# Project-relative imports
from utils.io import load_json, ensure_dir
from utils.logger import get_logger, log_operation
from utils.graph import (
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)

# Constants
MAX_MEMORY_GB = 7.0
OUTPUT_CSV = "data/processed/graph_metrics.csv"
EXCLUDED_LOG = "data/processed/excluded_graph_metrics.log"
STATUS_FILE = "data/artifacts/graph_metrics_status.json"
CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
ELIGIBLE_SUBJECTS_FILE = "data/processed/eligible_subjects.csv"

logger = get_logger("compute_graph_metrics")

def check_memory_usage() -> bool:
    """Check if current memory usage is within limits."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > MAX_MEMORY_GB:
        logger.log("memory_exceeded", current_gb=mem_gb, limit_gb=MAX_MEMORY_GB)
        return False
    return True

def read_eligible_subjects(filepath: str) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    subjects = []
    try:
        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle potential variations in column name
                sub_id = row.get("subject_id") or row.get("sub_id") or row.get("participant_id")
                if sub_id:
                    subjects.append(str(sub_id))
    except FileNotFoundError:
        logger.log("file_not_found", path=filepath)
        raise
    return subjects

def load_connectivity(subject_id: str, conn_dir: str) -> Optional[np.ndarray]:
    """Load connectivity matrix for a subject."""
    # Expected filename pattern: sub-<id>_connectivity.npy or .json
    # Try .npy first
    npy_path = Path(conn_dir) / f"{subject_id}_connectivity.npy"
    if npy_path.exists():
        return np.load(npy_path)

    # Try .json
    json_path = Path(conn_dir) / f"{subject_id}_connectivity.json"
    if json_path.exists():
        data = load_json(str(json_path))
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            return np.array(data)
        elif isinstance(data, dict) and "matrix" in data:
            return np.array(data["matrix"])

    # Try generic pattern
    generic_npy = Path(conn_dir) / f"{subject_id}.npy"
    if generic_npy.exists():
        return np.load(generic_npy)

    logger.log("connectivity_not_found", subject=subject_id, path=str(conn_dir))
    return None

def compute_subject_metrics(subject_id: str, conn_matrix: np.ndarray) -> Dict[str, Any]:
    """Compute graph metrics for a single subject."""
    metrics: Dict[str, Any] = {"subject_id": subject_id}

    try:
        # Ensure symmetric and zero diagonal
        conn_matrix = np.asarray(conn_matrix, dtype=float)
        if conn_matrix.ndim != 2 or conn_matrix.shape[0] != conn_matrix.shape[1]:
            raise ValueError("Connectivity matrix must be square.")

        np.fill_diagonal(conn_matrix, 0.0)
        conn_matrix = (conn_matrix + conn_matrix.T) / 2.0

        # Create graph (undirected, weighted)
        G = nx.from_numpy_array(conn_matrix, create_using=nx.Graph)

        # Calculate metrics
        # Degree centrality (average)
        metrics["degree_centrality"] = float(np.mean(list(calculate_degree_centrality(G).values())))

        # Global efficiency
        try:
            metrics["global_efficiency"] = float(calculate_global_efficiency(G))
        except Exception as e:
            metrics["global_efficiency"] = 0.0
            logger.log("efficiency_calc_failed", subject=subject_id, error=str(e))

        # Clustering coefficient (average)
        try:
            metrics["clustering_coefficient"] = float(np.mean(list(calculate_clustering_coefficient(G).values())))
        except Exception as e:
            metrics["clustering_coefficient"] = 0.0
            logger.log("clustering_calc_failed", subject=subject_id, error=str(e))

        # Average shortest path length
        try:
            if nx.is_connected(G):
                metrics["avg_path_length"] = float(nx.average_shortest_path_length(G))
            else:
                # For disconnected graphs, use harmonic mean or infinity
                # Using infinity to indicate disconnection, but could be handled differently
                metrics["avg_path_length"] = float('inf')
        except Exception as e:
            metrics["avg_path_length"] = float('inf')
            logger.log("path_length_calc_failed", subject=subject_id, error=str(e))

        # Node count
        metrics["num_nodes"] = G.number_of_nodes()
        metrics["num_edges"] = G.number_of_edges()

        # Check memory after processing
        if not check_memory_usage():
            logger.log("memory_warning_during_compute", subject=subject_id)

    except Exception as e:
        logger.log("compute_error", subject=subject_id, error=str(e), traceback=traceback.format_exc())
        # Fill with NaNs or 0s to keep CSV structure
        metrics["degree_centrality"] = np.nan
        metrics["global_efficiency"] = np.nan
        metrics["clustering_coefficient"] = np.nan
        metrics["avg_path_length"] = np.nan
        metrics["num_nodes"] = 0
        metrics["num_edges"] = 0

    return metrics

def process_subject_wrapper(subject_id: str, conn_dir: str) -> Dict[str, Any]:
    """Wrapper for joblib parallelization."""
    conn_matrix = load_connectivity(subject_id, conn_dir)
    if conn_matrix is None:
        return {"subject_id": subject_id, "error": "no_connectivity"}
    return compute_subject_metrics(subject_id, conn_matrix)

def write_metrics_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write results to CSV."""
    if not results:
        logger.log("no_results_to_write")
        return

    # Determine all possible keys
    fieldnames = ["subject_id"]
    for r in results:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    ensure_dir(output_path)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Convert inf/nan to strings for CSV
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float):
                    if np.isnan(v):
                        clean_row[k] = "NaN"
                    elif np.isinf(v):
                        clean_row[k] = "Inf"
                    else:
                        clean_row[k] = v
                else:
                    clean_row[k] = v
            writer.writerow(clean_row)

    logger.log("metrics_written", path=output_path, count=len(results))

def write_excluded_log(excluded_subjects: List[str], log_path: str) -> None:
    """Write log of excluded subjects."""
    ensure_dir(log_path)
    with open(log_path, "w") as f:
        f.write("Excluded Subjects for Graph Metrics Calculation\n")
        f.write("=" * 50 + "\n")
        for sub in excluded_subjects:
            f.write(f"{sub}\n")
    logger.log("excluded_log_written", path=log_path, count=len(excluded_subjects))

def write_status(status: Dict[str, Any], path: str) -> None:
    """Write status JSON."""
    ensure_dir(path)
    with open(path, "w") as f:
        json.dump(status, f, indent=2)
    logger.log("status_written", path=path)

@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point."""
    start_time = time.time()
    logger.log("start", message="Starting graph metrics computation")

    # Read eligible subjects
    try:
        subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    except Exception as e:
        logger.log("error", message=f"Failed to read eligible subjects: {e}")
        return 1

    if not subjects:
        logger.log("warning", message="No eligible subjects found.")
        write_status({"status": "no_subjects", "duration_seconds": 0}, STATUS_FILE)
        return 0

    logger.log("subjects_found", count=len(subjects))

    # Ensure connectivity directory exists
    conn_dir = CONNECTIVITY_DIR
    if not os.path.exists(conn_dir):
        logger.log("error", message=f"Connectivity directory not found: {conn_dir}")
        write_status({"status": "error", "message": "Connectivity directory missing", "duration_seconds": 0}, STATUS_FILE)
        return 1

    # Process subjects in parallel
    # Use n_jobs=2 as per task requirement
    logger.log("parallel_execution", n_jobs=2, total_subjects=len(subjects))

    try:
        results = Parallel(n_jobs=2, backend="loky")(
            delayed(process_subject_wrapper)(sub, conn_dir) for sub in subjects
        )
    except Exception as e:
        logger.log("parallel_error", error=str(e), traceback=traceback.format_exc())
        # Fallback to sequential if parallel fails
        logger.log("fallback_sequential")
        results = [process_subject_wrapper(sub, conn_dir) for sub in subjects]

    # Filter out errors for CSV (but keep in log)
    excluded = [r["subject_id"] for r in results if "error" in r]
    valid_results = [r for r in results if "error" not in r]

    # Write outputs
    write_metrics_csv(valid_results, OUTPUT_CSV)
    if excluded:
        write_excluded_log(excluded, EXCLUDED_LOG)

    duration = time.time() - start_time
    status = {
        "status": "completed",
        "subjects_processed": len(valid_results),
        "subjects_excluded": len(excluded),
        "duration_seconds": duration,
        "output_file": OUTPUT_CSV,
        "parallel": True,
        "n_jobs": 2
    }
    write_status(status, STATUS_FILE)

    logger.log("finish", duration=duration, output=OUTPUT_CSV)
    return 0

if __name__ == "__main__":
    sys.exit(main())