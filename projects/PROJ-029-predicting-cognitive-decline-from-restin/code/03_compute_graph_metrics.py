"""
Compute graph-theoretical metrics from connectivity matrices.

This script processes subjects one-by-one to stay within RAM limits.
It uses joblib for parallel processing of subjects where possible.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import psutil
import joblib
from joblib import Parallel, delayed

# Import from project utilities
from utils.io import ensure_dir, load_csv, save_csv, load_json, save_json
from utils.graph import (
    create_graph_from_adjacency,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_local_efficiency,
    calculate_shortest_path_length,
)
from utils.logger import get_logger, log_operation

# Configuration
MEMORY_LIMIT_GB = 7.0
N_JOBS = 2
SUBJECT_LIMIT = 100
INPUT_CSV = "data/processed/eligible_subjects.csv"
CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
OUTPUT_CSV = "data/processed/graph_metrics.csv"
EXCLUDED_LOG = "data/processed/excluded_graph_metrics.log"
STATUS_FILE = "data/artifacts/graph_metrics_status.json"


def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024**3)


def read_eligible_subjects(csv_path: str) -> List[Dict[str, Any]]:
    """Read eligible subjects from CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Eligible subjects file not found: {csv_path}")
    return load_csv(csv_path)


def load_connectivity(subject_id: str, connectivity_dir: str) -> Optional[np.ndarray]:
    """Load connectivity matrix for a subject."""
    matrix_path = os.path.join(connectivity_dir, f"{subject_id}_connectivity.npy")
    if not os.path.exists(matrix_path):
        return None
    return np.load(matrix_path)


def compute_subject_metrics(subject_id: str, connectivity_matrix: np.ndarray) -> Dict[str, Any]:
    """Compute graph metrics for a single subject."""
    try:
        graph = create_graph_from_adjacency(connectivity_matrix)

        metrics = {
            "subject_id": subject_id,
            "degree_centrality": float(np.mean(calculate_degree_centrality(graph))),
            "global_efficiency": float(calculate_global_efficiency(graph)),
            "clustering_coefficient": float(calculate_clustering_coefficient(graph)),
            "local_efficiency": float(calculate_local_efficiency(graph)),
            "average_path_length": float(calculate_shortest_path_length(graph)),
        }
        return metrics
    except Exception as e:
        return {"subject_id": subject_id, "error": str(e)}


def process_subject_wrapper(subject_info: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper for parallel processing of a subject."""
    subject_id = subject_info.get("subject_id")
    if not subject_id:
        return {"subject_id": "unknown", "error": "Missing subject_id"}

    connectivity_matrix = load_connectivity(subject_id, CONNECTIVITY_DIR)
    if connectivity_matrix is None:
        return {"subject_id": subject_id, "error": "Connectivity matrix not found"}

    return compute_subject_metrics(subject_id, connectivity_matrix)


def write_metrics_csv(metrics: List[Dict[str, Any]], output_path: str) -> None:
    """Write metrics to CSV."""
    if not metrics:
        raise ValueError("No metrics to write")

    fieldnames = [
        "subject_id",
        "degree_centrality",
        "global_efficiency",
        "clustering_coefficient",
        "local_efficiency",
        "average_path_length",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for m in metrics:
            writer.writerow(m)


def write_excluded_log(excluded: List[Dict[str, Any]], log_path: str) -> None:
    """Write excluded subjects to log."""
    ensure_dir(log_path)
    with open(log_path, "w") as f:
        for entry in excluded:
            f.write(json.dumps(entry) + "\n")


def write_status(status: Dict[str, Any], status_path: str) -> None:
    """Write processing status."""
    ensure_dir(status_path)
    with open(status_path, "w") as f:
        json.dump(status, f, indent=2)


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point for graph metrics computation."""
    logger = get_logger("compute_graph_metrics")

    start_time = time.time()
    logger.log("start", operation="compute_graph_metrics_main")

    # Check memory before starting
    initial_memory = check_memory_usage()
    logger.log("memory_check", initial_memory_gb=round(initial_memory, 2))

    if initial_memory > MEMORY_LIMIT_GB * 0.8:
        logger.log("warning", message="Memory usage already high, proceeding with caution")

    # Ensure input exists
    if not os.path.exists(INPUT_CSV):
        logger.log("error", message=f"Input file not found: {INPUT_CSV}")
        print(f"Error: {INPUT_CSV} not found. Run T017 first.")
        return 1

    # Read eligible subjects
    subjects = read_eligible_subjects(INPUT_CSV)
    if not subjects:
        logger.log("error", message="No eligible subjects found")
        print("Error: No eligible subjects found.")
        return 1

    # Limit subjects if necessary
    if len(subjects) > SUBJECT_LIMIT:
        subjects = subjects[:SUBJECT_LIMIT]
        logger.log("limit", subjects_processed=len(subjects), total_available=len(read_eligible_subjects(INPUT_CSV)))

    logger.log("subjects_loaded", count=len(subjects))

    # Check connectivity directory
    if not os.path.exists(CONNECTIVITY_DIR):
        logger.log("error", message=f"Connectivity directory not found: {CONNECTIVITY_DIR}")
        print(f"Error: {CONNECTIVITY_DIR} not found. Run T018 first.")
        return 1

    # Process subjects in parallel using joblib
    logger.log("parallel_processing_start", n_jobs=N_JOBS)

    results = Parallel(n_jobs=N_JOBS, backend="loky")(
        delayed(process_subject_wrapper)(subject) for subject in subjects
    )

    # Separate successful and failed results
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    logger.log(
        "parallel_processing_complete",
        successful=len(successful),
        failed=len(failed),
    )

    # Write outputs
    if successful:
        write_metrics_csv(successful, OUTPUT_CSV)
        logger.log("output_written", path=OUTPUT_CSV, rows=len(successful))
    else:
        logger.log("error", message="No successful results to write")
        print("Error: No successful results.")
        return 1

    if failed:
        write_excluded_log(failed, EXCLUDED_LOG)
        logger.log("excluded_written", path=EXCLUDED_LOG, count=len(failed))

    # Write status
    end_time = time.time()
    elapsed = end_time - start_time
    status = {
        "status": "completed" if not failed else "completed_with_errors",
        "total_subjects": len(subjects),
        "successful": len(successful),
        "failed": len(failed),
        "elapsed_seconds": round(elapsed, 2),
        "final_memory_gb": round(check_memory_usage(), 2),
    }
    write_status(status, STATUS_FILE)
    logger.log("finish", **status)

    print(f"Graph metrics computed: {len(successful)} subjects processed in {elapsed:.2f}s")
    if failed:
        print(f"Warning: {len(failed)} subjects failed. See {EXCLUDED_LOG}")

    return 0


if __name__ == "__main__":
    sys.exit(main())