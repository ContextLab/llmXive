from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import networkx as nx
from joblib import Parallel, delayed
import psutil

# Import from project utilities
from utils.io import load_csv, save_csv, save_json
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from utils.logger import get_logger, log_operation

# Constants
RAM_LIMIT_GB = 7.0
OUTPUT_METRICS_CSV = "data/processed/graph_metrics.csv"
OUTPUT_EXCLUDED_LOG = "data/processed/excluded_subjects.log"
OUTPUT_STATUS_JSON = "data/artifacts/data_gate_status.json"

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> bool:
    """Check if current memory usage is within the 7GB limit."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024**3)
    if mem_gb > RAM_LIMIT_GB:
        logger.log("memory_exceeded", usage_gb=mem_gb, limit_gb=RAM_LIMIT_GB)
        return False
    return True


def read_eligible_subjects(file_path: str) -> List[str]:
    """Read eligible subject IDs from a CSV file."""
    df = pd.read_csv(file_path)
    if "subject_id" in df.columns:
        return df["subject_id"].astype(str).tolist()
    elif "subject" in df.columns:
        return df["subject"].astype(str).tolist()
    else:
        raise ValueError(f"Expected 'subject_id' or 'subject' column in {file_path}")


def load_connectivity(subject_id: str, base_dir: str = "data/processed/connectivity_matrices") -> Optional[np.ndarray]:
    """Load a connectivity matrix for a given subject."""
    # Expected filename pattern: sub-<id>_conn.npy or similar
    # Try common patterns
    possible_paths = [
        Path(base_dir) / f"sub-{subject_id}_conn.npy",
        Path(base_dir) / f"{subject_id}_conn.npy",
        Path(base_dir) / f"sub-{subject_id}.npy",
        Path(base_dir) / f"{subject_id}.npy",
    ]

    for p in possible_paths:
        if p.exists():
            try:
                mat = np.load(p)
                return mat
            except Exception as e:
                logger.log("load_error", path=str(p), error=str(e))
                continue
    return None


def compute_subject_metrics(subject_id: str, matrix: np.ndarray) -> Dict[str, Any]:
    """Compute graph metrics for a single subject's connectivity matrix."""
    try:
        # Create graph from adjacency matrix
        # Ensure symmetry and zero diagonal for undirected graph
        adj = matrix.copy()
        adj = (adj + adj.T) / 2.0
        np.fill_diagonal(adj, 0)

        G = nx.from_numpy_array(adj)

        # Calculate metrics
        degree = calculate_degree_centrality(G)
        efficiency = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        path_len = calculate_shortest_path_length(G)

        # Store as scalar (mean) if the function returns an array/dict
        # For degree centrality, we often want the mean node degree centrality
        if isinstance(degree, (list, np.ndarray)):
            degree = float(np.mean(degree))
        elif isinstance(degree, dict):
            degree = float(np.mean(list(degree.values())))
        else:
            degree = float(degree)

        if isinstance(efficiency, (list, np.ndarray)):
            efficiency = float(np.mean(efficiency))
        elif isinstance(efficiency, dict):
            efficiency = float(np.mean(list(efficiency.values())))
        else:
            efficiency = float(efficiency)

        if isinstance(clustering, (list, np.ndarray)):
            clustering = float(np.mean(clustering))
        elif isinstance(clustering, dict):
            clustering = float(np.mean(list(clustering.values())))
        else:
            clustering = float(clustering)

        if isinstance(path_len, (list, np.ndarray)):
            path_len = float(np.mean(path_len))
        elif isinstance(path_len, dict):
            path_len = float(np.mean(list(path_len.values())))
        else:
            path_len = float(path_len)

        return {
            "subject_id": subject_id,
            "degree_centrality": degree,
            "global_efficiency": efficiency,
            "clustering_coefficient": clustering,
            "average_path_length": path_len,
        }
    except Exception as e:
        logger.log("metric_calculation_error", subject_id=subject_id, error=str(e))
        return None


def process_subject_wrapper(subject_id: str, base_dir: str) -> Optional[Dict[str, Any]]:
    """Wrapper for parallel processing."""
    if not check_memory_usage():
        logger.log("skipped_memory", subject_id=subject_id)
        return None

    matrix = load_connectivity(subject_id, base_dir)
    if matrix is None:
        logger.log("no_matrix", subject_id=subject_id)
        return None

    return compute_subject_metrics(subject_id, matrix)


@log_operation
def write_metrics_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write computed metrics to a CSV file."""
    if not results:
        logger.log("no_results_to_write")
        # Still write header to avoid empty file confusion
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "degree_centrality", "global_efficiency", "clustering_coefficient", "average_path_length"])
            writer.writeheader()
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        fieldnames = ["subject_id", "degree_centrality", "global_efficiency", "clustering_coefficient", "average_path_length"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            if row:
                writer.writerow(row)


def write_excluded_log(excluded_ids: List[str], output_path: str) -> None:
    """Write excluded subjects to a log file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for sid in excluded_ids:
            f.write(f"{sid}\n")


def write_status(status: str, message: str) -> None:
    """Write status JSON."""
    status_data = {
        "status": status,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    Path(OUTPUT_STATUS_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_STATUS_JSON, 'w') as f:
        json.dump(status_data, f, indent=2)


@log_operation
def main() -> int:
    """Main entry point for graph metric computation."""
    start_time = time.time()
    logger.log("start")

    eligible_file = "data/processed/eligible_subjects.csv"
    if not os.path.exists(eligible_file):
        logger.log("missing_eligible_file", path=eligible_file)
        write_status("error", f"Eligible subjects file not found: {eligible_file}")
        return 1

    subjects = read_eligible_subjects(eligible_file)
    logger.log("found_subjects", count=len(subjects))

    if not subjects:
        logger.log("no_eligible_subjects")
        write_metrics_csv([], OUTPUT_METRICS_CSV)
        write_status("warning", "No eligible subjects found.")
        return 0

    # Process subjects in parallel using joblib
    # n_jobs=2 as per task requirement
    logger.log("starting_parallel_processing", n_jobs=2)

    results = Parallel(n_jobs=2, verbose=10)(
        delayed(process_subject_wrapper)(sid, "data/processed/connectivity_matrices")
        for sid in subjects
    )

    # Filter out None results
    valid_results = [r for r in results if r is not None]
    excluded_subjects = [
        subjects[i] for i, r in enumerate(results) if r is None
    ]

    logger.log("processing_complete", valid_count=len(valid_results), excluded_count=len(excluded_subjects))

    write_metrics_csv(valid_results, OUTPUT_METRICS_CSV)
    write_excluded_log(excluded_subjects, OUTPUT_EXCLUDED_LOG)

    elapsed = time.time() - start_time
    logger.log("end", elapsed_seconds=elapsed)
    write_status("success", f"Completed in {elapsed:.2f}s. Processed {len(valid_results)} subjects.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
