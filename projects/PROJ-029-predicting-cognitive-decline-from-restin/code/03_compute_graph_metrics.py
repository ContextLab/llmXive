"""
T019: Compute graph metrics (degree, efficiency, clustering, path length)
from connectivity matrices. Processes subject-by-subject to stay within 7GB RAM.
Implements streaming/chunked processing and MemoryError handling.
"""
from __future__ import annotations

import csv
import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import networkx as nx

# Import from project utilities
from utils.logger import get_logger, log_operation
from utils.graph import (
    create_graph_from_adjacency,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)

# Constants
EXIT_CODE_NO_INPUT = 2
EXIT_CODE_SUCCESS = 0
RAM_LIMIT_GB = 7.0
SUBJECTS_CSV = "data/processed/eligible_subjects.csv"
CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
OUTPUT_CSV = "data/processed/graph_metrics.csv"
EXCLUDED_LOG = "data/processed/excluded_subjects.log"
STATUS_FILE = "data/artifacts/graph_metrics_status.json"

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> float:
    """Return current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)


@log_operation("read_eligible_subjects")
def read_eligible_subjects(path: str) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    subjects = []
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle potential variations in column names
                sub_id = row.get('subject_id') or row.get('subject') or row.get('sub_id')
                if sub_id:
                    subjects.append(str(sub_id))
    except FileNotFoundError:
        logger.log("error", message=f"File not found: {path}")
        sys.exit(EXIT_CODE_NO_INPUT)
    except Exception as e:
        logger.log("error", message=f"Error reading eligible subjects: {e}")
        sys.exit(EXIT_CODE_NO_INPUT)
    return subjects


@log_operation("load_connectivity")
def load_connectivity(subject_id: str, base_dir: str) -> Optional[np.ndarray]:
    """
    Load a connectivity matrix for a given subject.
    Expects files like: <base_dir>/<subject_id>_connectivity.npy or .nii.gz
    """
    base_path = Path(base_dir)
    possible_extensions = ['.npy', '.nii.gz', '.nii']
    conn_file = None

    for ext in possible_extensions:
        candidate = base_path / f"{subject_id}_connectivity{ext}"
        if candidate.exists():
            conn_file = candidate
            break

    if not conn_file:
        logger.log("warning", message=f"No connectivity file found for {subject_id}")
        return None

    try:
        if str(conn_file).endswith('.npy'):
            matrix = np.load(conn_file)
        elif str(conn_file).endswith(('.nii.gz', '.nii')):
            # If it's a NIfTI, we assume it's a 3D volume where the first two dims are the matrix
            # This is a simplification; usually we'd need to reshape or extract the ROI time series first.
            # Given the pipeline context, we assume the file is already processed to a 2D adjacency.
            import nibabel as nib
            img = nib.load(str(conn_file))
            data = img.get_fdata()
            # If it's 3D, take the first slice or average if it's a volume representation
            if len(data.shape) == 3:
                # Assume it's a stack of slices, take the middle or average
                # For adjacency, we expect 2D. If 3D, it might be (N, N, 1) or similar.
                # Let's try to squeeze or take the first 2D slice
                if data.shape[2] == 1:
                    matrix = data[:, :, 0]
                else:
                    # Fallback: average over the third dimension
                    matrix = np.mean(data, axis=2)
            else:
                matrix = data
        else:
            logger.log("error", message=f"Unsupported file format: {conn_file}")
            return None

        # Ensure it's 2D
        if matrix.ndim != 2:
            logger.log("error", message=f"Matrix for {subject_id} is not 2D: {matrix.shape}")
            return None

        return matrix
    except Exception as e:
        logger.log("error", message=f"Failed to load connectivity for {subject_id}: {e}")
        return None


@log_operation("compute_subject_metrics")
def compute_subject_metrics(
    adjacency: np.ndarray,
    subject_id: str
) -> Dict[str, Any]:
    """
    Compute graph metrics for a single subject's adjacency matrix.
    Returns a dict with subject_id and metrics.
    """
    try:
        # Create NetworkX graph
        G = create_graph_from_adjacency(adjacency)

        # Calculate metrics
        degree = calculate_degree_centrality(G)
        efficiency = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        path_len = calculate_shortest_path_length(G)

        return {
            "subject_id": subject_id,
            "node_degree": float(degree) if degree is not None else 0.0,
            "global_efficiency": float(efficiency) if efficiency is not None else 0.0,
            "clustering_coeff": float(clustering) if clustering is not None else 0.0,
            "path_length": float(path_len) if path_len is not None else 0.0,
        }
    except Exception as e:
        logger.log("error", message=f"Failed to compute metrics for {subject_id}: {e}")
        raise


@log_operation("process_subject_wrapper")
def process_subject_wrapper(
    subject_id: str,
    connectivity_dir: str,
    results: List[Dict[str, Any]],
    excluded_log: List[Tuple[str, str]]
) -> None:
    """
    Process a single subject: load connectivity, compute metrics, handle MemoryError.
    """
    try:
        # Check memory before processing
        current_ram = check_memory_usage()
        if current_ram > RAM_LIMIT_GB * 0.9:
            logger.log("warning", message=f"High memory usage ({current_ram:.2f}GB). Clearing cache.")
            gc.collect()

        adjacency = load_connectivity(subject_id, connectivity_dir)
        if adjacency is None:
            excluded_log.append((subject_id, "Connectivity file missing or invalid"))
            return

        metrics = compute_subject_metrics(adjacency, subject_id)
        results.append(metrics)

        # Clear memory after processing
        del adjacency
        gc.collect()

    except MemoryError:
        logger.log("error", message=f"MemoryError processing {subject_id}. Skipping.")
        excluded_log.append((subject_id, "MemoryError"))
        gc.collect()
        # Do NOT exit; continue with next subject
    except Exception as e:
        logger.log("error", message=f"Unexpected error processing {subject_id}: {e}")
        excluded_log.append((subject_id, f"Error: {str(e)}"))


@log_operation("write_metrics_csv")
def write_metrics_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write the computed metrics to a CSV file."""
    if not results:
        logger.log("warning", message="No results to write.")
        # Still write an empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["subject_id", "node_degree", "global_efficiency", "clustering_coeff", "path_length"])
        return

    fieldnames = ["subject_id", "node_degree", "global_efficiency", "clustering_coeff", "path_length"]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    logger.log("success", message=f"Wrote {len(results)} rows to {output_path}")


@log_operation("write_excluded_log")
def write_excluded_log(excluded: List[Tuple[str, str]], log_path: str) -> None:
    """Write the exclusion log."""
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("subject_id,reason\n")
        for sub_id, reason in excluded:
            f.write(f"{sub_id},{reason}\n")
    logger.log("info", message=f"Wrote exclusion log to {log_path}")


@log_operation("write_status")
def write_status(
    total_subjects: int,
    processed: int,
    skipped: int,
    status_path: str
) -> None:
    """Write the status JSON file."""
    status = {
        "total_subjects": total_subjects,
        "processed": processed,
        "skipped": skipped,
        "status": "completed" if skipped < total_subjects else "failed",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)
    logger.log("info", message=f"Status written to {status_path}")


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point for computing graph metrics."""
    start_time = time.time()
    logger.log("start", message="Starting graph metrics computation")

    # Ensure directories exist
    Path(CONNECTIVITY_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    Path(STATUS_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Read eligible subjects
    subjects = read_eligible_subjects(SUBJECTS_CSV)
    if not subjects:
        logger.log("error", message="No eligible subjects found.")
        write_status(0, 0, 0, STATUS_FILE)
        return EXIT_CODE_NO_INPUT

    logger.log("info", message=f"Found {len(subjects)} eligible subjects")

    results: List[Dict[str, Any]] = []
    excluded_log: List[Tuple[str, str]] = []

    # Process subject-by-subject
    for i, sub_id in enumerate(subjects):
        logger.log("progress", message=f"Processing subject {i+1}/{len(subjects)}: {sub_id}")
        process_subject_wrapper(sub_id, CONNECTIVITY_DIR, results, excluded_log)

    # Write outputs
    write_metrics_csv(results, OUTPUT_CSV)
    write_excluded_log(excluded_log, EXCLUDED_LOG)
    write_status(len(subjects), len(results), len(excluded_log), STATUS_FILE)

    elapsed = time.time() - start_time
    logger.log("complete", message=f"Finished in {elapsed:.2f} seconds. Processed {len(results)}/{len(subjects)} subjects.")

    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main())