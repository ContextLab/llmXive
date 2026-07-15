"""
Compute graph-theoretical metrics from connectivity matrices.

Reads eligible subjects from data/processed/eligible_subjects.csv,
loads their connectivity matrices from data/processed/connectivity_matrices/,
computes degree, global efficiency, clustering coefficient, and path length,
and writes results to data/processed/graph_metrics.csv.

Processes subject-by-subject to stay within 7GB RAM.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import networkx as nx
import pandas as pd

# Import from local utils
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_json, save_json
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from utils.memory_profiler import get_peak_memory_gb

# Constants
SUBJECTS_FILE = "data/processed/eligible_subjects.csv"
CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
OUTPUT_FILE = "data/processed/graph_metrics.csv"
EXCLUDED_LOG = "data/processed/excluded_graph_metrics.log"
STATUS_FILE = "data/artifacts/graph_metrics_status.json"
MEMORY_LIMIT_GB = 7.0

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> bool:
    """Check if current memory usage is within limits."""
    peak_gb = get_peak_memory_gb()
    if peak_gb > MEMORY_LIMIT_GB:
        logger.log(
            "memory_exceeded",
            message=f"Peak memory {peak_gb:.2f}GB exceeds limit {MEMORY_LIMIT_GB}GB",
        )
        return False
    return True


def read_eligible_subjects() -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not os.path.exists(SUBJECTS_FILE):
        raise FileNotFoundError(
            f"Eligible subjects file not found: {SUBJECTS_FILE}. "
            "Run code/01_download_and_filter.py first."
        )
    df = pd.read_csv(SUBJECTS_FILE)
    # Expect column 'subject_id' or 'sub_id'
    if "subject_id" in df.columns:
        return df["subject_id"].astype(str).tolist()
    elif "sub_id" in df.columns:
        return df["sub_id"].astype(str).tolist()
    else:
        raise ValueError(
            f"Eligible subjects file must contain 'subject_id' or 'sub_id' column. "
            f"Found columns: {list(df.columns)}"
        )


def load_connectivity(subject_id: str) -> np.ndarray:
    """
    Load connectivity matrix for a subject.

    Expected file: data/processed/connectivity_matrices/{subject_id}_connectivity.npy
    """
    conn_file = Path(CONNECTIVITY_DIR) / f"{subject_id}_connectivity.npy"
    if not conn_file.exists():
        raise FileNotFoundError(
            f"Connectivity matrix not found for subject {subject_id}: {conn_file}"
        )
    matrix = np.load(conn_file)
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(
            f"Connectivity matrix for {subject_id} is not square: {matrix.shape}"
        )
    return matrix


def compute_subject_metrics(
    subject_id: str, matrix: np.ndarray
) -> Dict[str, Any]:
    """
    Compute graph metrics for a single subject's connectivity matrix.

    Metrics:
      - degree: mean node degree
      - global_efficiency: global efficiency of the network
      - clustering_coefficient: mean clustering coefficient
      - characteristic_path_length: mean shortest path length
    """
    # Create graph from adjacency matrix
    # Threshold small values to avoid numerical issues
    matrix = np.abs(matrix)
    np.fill_diagonal(matrix, 0)  # No self-loops

    # Create weighted graph
    G = nx.from_numpy_array(matrix, create_using=nx.Graph)

    # Compute metrics
    try:
        degree = calculate_degree_centrality(G)
        global_eff = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)

        # Handle disconnected graphs for path length
        try:
            path_length = calculate_shortest_path_length(G)
        except nx.NetworkXError:
            # Graph is disconnected or has no edges
            path_length = float("nan")

        return {
            "subject_id": subject_id,
            "degree": float(np.mean(degree)) if len(degree) > 0 else 0.0,
            "global_efficiency": float(global_eff),
            "clustering_coefficient": float(clustering),
            "characteristic_path_length": float(path_length),
        }
    except Exception as e:
        logger.log(
            "metric_computation_error",
            subject_id=subject_id,
            error=str(e),
        )
        raise


def process_subject_wrapper(
    subject_id: str, matrix: np.ndarray
) -> Optional[Dict[str, Any]]:
    """Wrapper with error handling for single subject processing."""
    try:
        return compute_subject_metrics(subject_id, matrix)
    except Exception as e:
        logger.log(
            "subject_processing_failed",
            subject_id=subject_id,
            error=str(e),
        )
        return None


def write_metrics_csv(
    results: List[Dict[str, Any]], output_path: str
) -> None:
    """Write computed metrics to CSV file."""
    if not results:
        raise ValueError("No results to write to CSV")

    # Ensure output directory exists
    ensure_dir(output_path)

    # Write CSV
    fieldnames = [
        "subject_id",
        "degree",
        "global_efficiency",
        "clustering_coefficient",
        "characteristic_path_length",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    logger.log(
        "metrics_written",
        output_path=output_path,
        num_subjects=len(results),
    )


def write_excluded_log(excluded: List[Tuple[str, str]], log_path: str) -> None:
    """Write log of excluded subjects and reasons."""
    ensure_dir(log_path)
    with open(log_path, "w") as f:
        f.write("Subject ID,Reason\n")
        for subj_id, reason in excluded:
            f.write(f"{subj_id},{reason}\n")
    logger.log(
        "excluded_log_written",
        log_path=log_path,
        num_excluded=len(excluded),
    )


def write_status(
    total: int, processed: int, failed: int, status_path: str
) -> None:
    """Write processing status to JSON file."""
    ensure_dir(status_path)
    status = {
        "total_subjects": total,
        "processed_successfully": processed,
        "failed": failed,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "memory_limit_gb": MEMORY_LIMIT_GB,
    }
    save_json(status, status_path)
    logger.log("status_written", status_path=status_path)


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point for graph metrics computation."""
    start_time = time.time()
    logger.log("start", message="Starting graph metrics computation")

    # Check memory before starting
    if not check_memory_usage():
        logger.log("abort", reason="memory_limit_exceeded")
        return 1

    # Read eligible subjects
    try:
        subject_ids = read_eligible_subjects()
    except FileNotFoundError as e:
        logger.log("abort", reason=str(e))
        return 1
    except ValueError as e:
        logger.log("abort", reason=str(e))
        return 1

    if not subject_ids:
        logger.log("abort", reason="no_eligible_subjects")
        return 1

    logger.log("subjects_loaded", count=len(subject_ids))

    # Process each subject
    results: List[Dict[str, Any]] = []
    excluded: List[Tuple[str, str]] = []

    for idx, subj_id in enumerate(subject_ids):
        # Check memory periodically
        if idx % 10 == 0:
            if not check_memory_usage():
                logger.log(
                    "abort",
                    reason="memory_limit_exceeded_during_processing",
                    processed_so_far=len(results),
                )
                break

        logger.log("processing_subject", index=idx + 1, total=len(subject_ids), subject_id=subj_id)

        try:
            matrix = load_connectivity(subj_id)
            metrics = process_subject_wrapper(subj_id, matrix)
            if metrics is not None:
                results.append(metrics)
            else:
                excluded.append((subj_id, "computation_failed"))
        except FileNotFoundError as e:
            excluded.append((subj_id, f"file_not_found: {str(e)}"))
        except Exception as e:
            excluded.append((subj_id, f"error: {str(e)}"))

    # Write outputs
    if results:
        try:
            write_metrics_csv(results, OUTPUT_FILE)
            logger.log("output_written", file=OUTPUT_FILE, rows=len(results))
        except Exception as e:
            logger.log("output_write_failed", error=str(e))
            return 1
    else:
        logger.log("no_results", message="No subjects processed successfully")
        # Still write empty file with headers for downstream compatibility
        try:
            write_metrics_csv(
                [
                    {
                        "subject_id": "none",
                        "degree": 0.0,
                        "global_efficiency": 0.0,
                        "clustering_coefficient": 0.0,
                        "characteristic_path_length": 0.0,
                    }
                ],
                OUTPUT_FILE,
            )
        except Exception as e:
            logger.log("output_write_failed", error=str(e))
            return 1

    # Write excluded log
    if excluded:
        write_excluded_log(excluded, EXCLUDED_LOG)
    else:
        # Write empty log
        with open(EXCLUDED_LOG, "w") as f:
            f.write("Subject ID,Reason\n")

    # Write status
    write_status(len(subject_ids), len(results), len(excluded), STATUS_FILE)

    elapsed = time.time() - start_time
    logger.log(
        "complete",
        total=len(subject_ids),
        successful=len(results),
        failed=len(excluded),
        elapsed_seconds=elapsed,
    )

    print(f"Graph metrics computation complete: {len(results)}/{len(subject_ids)} subjects processed in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())