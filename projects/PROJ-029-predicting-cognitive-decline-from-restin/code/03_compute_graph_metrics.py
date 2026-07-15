"""Compute graph metrics from connectivity matrices.

This script calculates node degree, global efficiency, clustering coefficient,
and path length for every subject in the eligible list. It processes subjects
one-by-one to stay within memory limits and uses joblib for parallelization
where appropriate.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
from joblib import Parallel, delayed

# Project-relative imports
from utils.io import ensure_dir, load_csv, save_csv, load_json
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
    load_aal_atlas_mask,
)
from utils.logger import get_logger, log_operation

# Constants
RAM_LIMIT_GB = 7.0
JOBLIB_N_JOBS = 2
CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
METRICS_OUTPUT = Path("data/processed/graph_metrics.csv")
EXCLUDED_LOG = Path("data/processed/excluded_subjects.log")
STATUS_PATH = Path("data/artifacts/graph_metrics_status.json")

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> bool:
    """Check if current memory usage is below the limit.

    Returns:
        True if usage is below limit, False otherwise.
    """
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024**3)
    if mem_gb > RAM_LIMIT_GB:
        logger.log(
            "memory_exceeded",
            current_gb=mem_gb,
            limit_gb=RAM_LIMIT_GB,
        )
        return False
    return True


def read_eligible_subjects(csv_path: Path) -> List[Dict[str, Any]]:
    """Read eligible subjects from CSV file.

    Args:
        csv_path: Path to eligible subjects CSV.

    Returns:
        List of subject dictionaries.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {csv_path}")

    subjects = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append(row)
    return subjects


def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """Load connectivity matrix for a subject.

    Args:
        subject_id: Subject identifier.

    Returns:
        Connectivity matrix as numpy array, or None if not found.
    """
    matrix_path = CONNECTIVITY_DIR / f"{subject_id}_connectivity.npy"
    if not matrix_path.exists():
        logger.log(
            "connectivity_missing",
            subject_id=subject_id,
            path=str(matrix_path),
        )
        return None

    try:
        matrix = np.load(matrix_path)
        return matrix
    except Exception as e:
        logger.log(
            "connectivity_load_error",
            subject_id=subject_id,
            error=str(e),
        )
        return None


def compute_subject_metrics(
    subject_id: str, connectivity: np.ndarray
) -> Dict[str, Any]:
    """Compute graph metrics for a single subject.

    Args:
        subject_id: Subject identifier.
        connectivity: Connectivity matrix.

    Returns:
        Dictionary of metrics.
    """
    # Ensure symmetry and zero diagonal
    connectivity = (connectivity + connectivity.T) / 2.0
    np.fill_diagonal(connectivity, 0.0)

    # Calculate metrics
    degree = calculate_degree_centrality(connectivity)
    efficiency = calculate_global_efficiency(connectivity)
    clustering = calculate_clustering_coefficient(connectivity)
    path_length = calculate_shortest_path_length(connectivity)

    return {
        "subject_id": subject_id,
        "degree": float(np.mean(degree)),
        "global_efficiency": float(efficiency),
        "clustering_coefficient": float(clustering),
        "mean_path_length": float(path_length),
    }


def process_subject_wrapper(
    subject_row: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Wrapper to process a single subject with error handling.

    Args:
        subject_row: Subject dictionary from eligible list.

    Returns:
        Metrics dictionary or None if processing failed.
    """
    subject_id = subject_row.get("subject_id", "")
    if not subject_id:
        logger.log("missing_subject_id", row=subject_row)
        return None

    connectivity = load_connectivity(subject_id)
    if connectivity is None:
        return None

    try:
        metrics = compute_subject_metrics(subject_id, connectivity)
        return metrics
    except Exception as e:
        logger.log(
            "metrics_computation_error",
            subject_id=subject_id,
            error=str(e),
        )
        return None


def write_metrics_csv(
    metrics_list: List[Dict[str, Any]], output_path: Path
) -> None:
    """Write computed metrics to CSV file.

    Args:
        metrics_list: List of metrics dictionaries.
        output_path: Output CSV path.
    """
    ensure_dir(output_path)

    fieldnames = [
        "subject_id",
        "degree",
        "global_efficiency",
        "clustering_coefficient",
        "mean_path_length",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for metrics in metrics_list:
            writer.writerow(metrics)

    logger.log(
        "metrics_written",
        path=str(output_path),
        count=len(metrics_list),
    )


def write_excluded_log(excluded_subjects: List[Tuple[str, str]], log_path: Path) -> None:
    """Write log of excluded subjects.

    Args:
        excluded_subjects: List of (subject_id, reason) tuples.
        log_path: Output log path.
    """
    ensure_dir(log_path)

    with open(log_path, "w", encoding="utf-8") as f:
        for subject_id, reason in excluded_subjects:
            f.write(f"{subject_id}: {reason}\n")

    logger.log(
        "excluded_log_written",
        path=str(log_path),
        count=len(excluded_subjects),
    )


def write_status(
    total: int,
    processed: int,
    excluded: int,
    start_time: float,
    end_time: float,
    status_path: Path,
) -> None:
    """Write status JSON file.

    Args:
        total: Total subjects attempted.
        processed: Successfully processed subjects.
        excluded: Excluded subjects count.
        start_time: Start timestamp.
        end_time: End timestamp.
        status_path: Output status path.
    """
    ensure_dir(status_path)

    status = {
        "total_subjects": total,
        "processed_subjects": processed,
        "excluded_subjects": excluded,
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
        "end_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time)),
        "duration_seconds": end_time - start_time,
        "status": "completed" if excluded == 0 else "partial",
    }

    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    logger.log("status_written", path=str(status_path))


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    start_time = time.time()
    excluded_subjects: List[Tuple[str, str]] = []
    metrics_list: List[Dict[str, Any]] = []

    # Read eligible subjects
    eligible_csv = Path("data/processed/eligible_subjects.csv")
    if not eligible_csv.exists():
        logger.log("eligible_csv_missing", path=str(eligible_csv))
        print(f"Error: Eligible subjects file not found: {eligible_csv}", file=sys.stderr)
        return 1

    subjects = read_eligible_subjects(eligible_csv)
    total_subjects = len(subjects)
    logger.log("subjects_loaded", count=total_subjects)

    if total_subjects == 0:
        logger.log("no_eligible_subjects")
        print("Warning: No eligible subjects found.", file=sys.stderr)
        write_status(0, 0, 0, start_time, time.time(), STATUS_PATH)
        return 0

    # Check memory before processing
    if not check_memory_usage():
        logger.log("memory_limit_exceeded_before_start")
        print(f"Error: Memory usage exceeds limit ({RAM_LIMIT_GB} GB).", file=sys.stderr)
        return 1

    # Process subjects in parallel using joblib
    # Note: We use a wrapper to handle errors gracefully
    logger.log("starting_parallel_processing", n_jobs=JOBLIB_N_JOBS)

    results = Parallel(n_jobs=JOBLIB_N_JOBS)(
        delayed(process_subject_wrapper)(subject) for subject in subjects
    )

    # Collect successful results and track failures
    for i, result in enumerate(results):
        subject_id = subjects[i].get("subject_id", f"subject_{i}")
        if result is not None:
            metrics_list.append(result)
        else:
            excluded_subjects.append((subject_id, "processing_failed"))

    # Write outputs
    write_metrics_csv(metrics_list, METRICS_OUTPUT)
    write_excluded_log(excluded_subjects, EXCLUDED_LOG)

    end_time = time.time()
    write_status(
        total_subjects,
        len(metrics_list),
        len(excluded_subjects),
        start_time,
        end_time,
        STATUS_PATH,
    )

    logger.log(
        "processing_complete",
        total=total_subjects,
        processed=len(metrics_list),
        excluded=len(excluded_subjects),
        duration=end_time - start_time,
    )

    print(f"Graph metrics computed for {len(metrics_list)}/{total_subjects} subjects.")
    print(f"Output written to {METRICS_OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
