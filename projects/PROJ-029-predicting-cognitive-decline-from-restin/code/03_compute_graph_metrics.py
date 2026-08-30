"""Compute graph metrics from connectivity matrices.

This script calculates node degree, global efficiency, clustering coefficient,
and path length for every subject listed in the eligible subjects CSV.
It processes subjects one-by-one to stay within memory limits.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import psutil

# Import from existing API surface
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_csv, save_csv, load_json, save_json
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)

# Constants
RAM_THRESHOLD_GB = 1.0
TOTAL_RAM_LIMIT_GB = 7.0
EXIT_CODE_NO_ELIGIBLE = 3
EXIT_CODE_MEMORY_ERROR = 1

logger = get_logger("compute_graph_metrics")


def check_memory_usage(subject_id: str, estimated_file_size_gb: float) -> None:
    """Check available RAM before processing a subject.

    Args:
        subject_id: The subject identifier.
        estimated_file_size_gb: Estimated size of the file to load in GB.

    Raises:
        RuntimeError: If available RAM is insufficient.
    """
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    total_used_gb = (mem.total - mem.available) / (1024 ** 3)

    logger.log(
        "check_memory_usage",
        subject_id=subject_id,
        available_ram_gb=round(available_gb, 2),
        estimated_file_size_gb=estimated_file_size_gb,
        total_used_ram_gb=round(total_used_gb, 2),
    )

    if available_gb < RAM_THRESHOLD_GB:
        error_msg = (
            f"Insufficient available RAM for subject {subject_id}: "
            f"{available_gb:.2f} GB available, minimum {RAM_THRESHOLD_GB} GB required."
        )
        logger.log("memory_warning", error=error_msg)
        raise RuntimeError(error_msg)

    if (total_used_gb + estimated_file_size_gb) > TOTAL_RAM_LIMIT_GB:
        error_msg = (
            f"Estimated total RAM would exceed limit for subject {subject_id}: "
            f"current usage {total_used_gb:.2f} GB + file {estimated_file_size_gb:.2f} GB "
            f"> {TOTAL_RAM_LIMIT_GB} GB limit."
        )
        logger.log("memory_warning", error=error_msg)
        raise RuntimeError(error_msg)


def read_eligible_subjects(eligible_csv_path: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV.

    Args:
        eligible_csv_path: Path to the eligible subjects CSV file.

    Returns:
        List of subject IDs.

    Raises:
        FileNotFoundError: If the eligible subjects CSV does not exist.
        ValueError: If no eligible subjects are found.
    """
    if not eligible_csv_path.exists():
        raise FileNotFoundError(f"Eligible subjects CSV not found: {eligible_csv_path}")

    subjects = []
    with open(eligible_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assume the CSV has a 'subject_id' column
            if "subject_id" in row:
                subjects.append(row["subject_id"])
            elif "id" in row:
                subjects.append(row["id"])
            else:
                # Fallback: use the first column
                subjects.append(list(row.values())[0])

    if not subjects:
        raise ValueError("No eligible subjects found in the CSV file.")

    return subjects


def load_connectivity(connectivity_dir: Path, subject_id: str) -> np.ndarray:
    """Load a connectivity matrix for a subject.

    Args:
        connectivity_dir: Directory containing connectivity matrices.
        subject_id: The subject identifier.

    Returns:
        Connectivity matrix as a numpy array.
    """
    # Try common extensions
    for ext in [".npy", ".csv", ".txt"]:
        file_path = connectivity_dir / f"{subject_id}{ext}"
        if file_path.exists():
            if ext == ".npy":
                return np.load(file_path)
            else:
                data = np.loadtxt(file_path, delimiter=",")
                return data

    raise FileNotFoundError(
        f"Connectivity matrix not found for subject {subject_id} in {connectivity_dir}"
    )


def compute_subject_metrics(connectivity_matrix: np.ndarray) -> Dict[str, float]:
    """Compute graph metrics for a single subject.

    Args:
        connectivity_matrix: Adjacency matrix (numpy array).

    Returns:
        Dictionary of graph metrics.
    """
    # Ensure matrix is symmetric (undirected graph)
    if not np.allclose(connectivity_matrix, connectivity_matrix.T):
        connectivity_matrix = (connectivity_matrix + connectivity_matrix.T) / 2

    # Compute metrics
    degree = calculate_degree_centrality(connectivity_matrix)
    global_eff = calculate_global_efficiency(connectivity_matrix)
    clustering = calculate_clustering_coefficient(connectivity_matrix)
    path_len = calculate_shortest_path_length(connectivity_matrix)

    # Aggregate to single values (mean across nodes)
    return {
        "node_degree": float(np.mean(degree)),
        "global_efficiency": float(global_eff),
        "clustering_coeff": float(np.mean(clustering)),
        "path_length": float(path_len),
    }


def process_subject_wrapper(
    subject_id: str,
    connectivity_dir: Path,
    metrics_output: List[Dict[str, Any]],
) -> None:
    """Process a single subject: check memory, load data, compute metrics.

    Args:
        subject_id: The subject identifier.
        connectivity_dir: Directory containing connectivity matrices.
        metrics_output: List to append results to.
    """
    # Estimate file size (assume ~1MB for typical connectivity matrix)
    estimated_file_size_gb = 0.001  # 1 MB

    try:
        check_memory_usage(subject_id, estimated_file_size_gb)
        connectivity = load_connectivity(connectivity_dir, subject_id)
        metrics = compute_subject_metrics(connectivity)
        metrics["subject_id"] = subject_id
        metrics_output.append(metrics)
        logger.log("subject_processed", subject_id=subject_id, success=True)
    except (MemoryError, RuntimeError) as e:
        logger.log("subject_failed", subject_id=subject_id, error=str(e))
        raise


def write_metrics_csv(metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """Write computed metrics to a CSV file.

    Args:
        metrics: List of metric dictionaries.
        output_path: Path to the output CSV file.
    """
    ensure_dir(output_path.parent)
    fieldnames = ["subject_id", "node_degree", "global_efficiency", "clustering_coeff", "path_length"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            # Ensure all fields are present
            safe_row = {k: row.get(k, np.nan) for k in fieldnames}
            writer.writerow(safe_row)

    logger.log("metrics_written", output_path=str(output_path), count=len(metrics))


def write_excluded_log(excluded_subjects: List[str], log_path: Path) -> None:
    """Write a log of excluded subjects.

    Args:
        excluded_subjects: List of excluded subject IDs.
        log_path: Path to the log file.
    """
    ensure_dir(log_path.parent)
    with open(log_path, "w", encoding="utf-8") as f:
        if excluded_subjects:
            for sub in excluded_subjects:
                f.write(f"{sub}\n")
        else:
            f.write("# No subjects excluded\n")

    logger.log("excluded_log_written", path=str(log_path), count=len(excluded_subjects))


def write_status(status_path: Path, success: bool, message: str, metrics_count: int = 0) -> None:
    """Write a status file.

    Args:
        status_path: Path to the status file.
        success: Whether the operation was successful.
        message: Status message.
        metrics_count: Number of metrics computed.
    """
    ensure_dir(status_path.parent)
    status = {
        "success": success,
        "message": message,
        "metrics_computed": metrics_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    logger.log("status_written", path=str(status_path), success=success)


@log_operation
def main() -> None:
    """Main entry point for computing graph metrics."""
    start_time = time.time()

    # Define paths
    project_root = Path(__file__).parent.parent
    eligible_csv_path = project_root / "data" / "processed" / "eligible_subjects.csv"
    connectivity_dir = project_root / "data" / "processed" / "connectivity_matrices"
    output_csv_path = project_root / "data" / "processed" / "graph_metrics.csv"
    excluded_log_path = project_root / "data" / "processed" / "excluded_graph_subjects.log"
    status_path = project_root / "data" / "artifacts" / "graph_metrics_status.json"

    logger.log("main_start", eligible_csv=str(eligible_csv_path))

    try:
        # Read eligible subjects
        subjects = read_eligible_subjects(eligible_csv_path)
        logger.log("subjects_read", count=len(subjects))

        if not subjects:
            msg = "No eligible subjects found."
            write_status(status_path, False, msg, 0)
            logger.log("main_end", success=False, reason=msg)
            sys.exit(EXIT_CODE_NO_ELIGIBLE)

        # Ensure connectivity directory exists
        if not connectivity_dir.exists():
            msg = f"Connectivity directory not found: {connectivity_dir}"
            write_status(status_path, False, msg, 0)
            logger.log("main_end", success=False, reason=msg)
            sys.exit(1)

        # Process subjects
        metrics_output: List[Dict[str, Any]] = []
        excluded_subjects: List[str] = []

        for subject_id in subjects:
            try:
                process_subject_wrapper(subject_id, connectivity_dir, metrics_output)
            except (MemoryError, RuntimeError) as e:
                excluded_subjects.append(subject_id)
                logger.log("subject_excluded", subject_id=subject_id, reason=str(e))
                # Re-raise to fail the entire run as per constraints
                raise

        # Write outputs
        write_metrics_csv(metrics_output, output_csv_path)
        write_excluded_log(excluded_subjects, excluded_log_path)

        elapsed = time.time() - start_time
        write_status(status_path, True, "Success", len(metrics_output))

        logger.log(
            "main_end",
            success=True,
            subjects_processed=len(metrics_output),
            subjects_excluded=len(excluded_subjects),
            elapsed_seconds=round(elapsed, 2),
        )
        print(f"Graph metrics computed for {len(metrics_output)} subjects in {elapsed:.2f}s")

    except (MemoryError, RuntimeError) as e:
        elapsed = time.time() - start_time
        write_status(status_path, False, f"Memory error: {str(e)}", 0)
        logger.log("main_end", success=False, reason=str(e), elapsed_seconds=round(elapsed, 2))
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(EXIT_CODE_MEMORY_ERROR)
    except FileNotFoundError as e:
        elapsed = time.time() - start_time
        write_status(status_path, False, f"File not found: {str(e)}", 0)
        logger.log("main_end", success=False, reason=str(e), elapsed_seconds=round(elapsed, 2))
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        elapsed = time.time() - start_time
        write_status(status_path, False, f"Unexpected error: {str(e)}", 0)
        logger.log("main_end", success=False, reason=str(e), elapsed_seconds=round(elapsed, 2))
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()