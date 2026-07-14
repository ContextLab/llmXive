from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import networkx as nx
import numpy as np
import pandas as pd
import psutil

# Import from project utilities
from utils.io import ensure_dir, load_json, save_json
from utils.graph import (
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_local_efficiency,
    calculate_shortest_path_length,
    create_graph_from_adjacency,
)
from utils.logger import get_logger, log_operation

# Constants
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")
EXCLUDED_LOG_PATH = Path("data/processed/excluded_subjects.log")
STATUS_PATH = Path("data/artifacts/data_gate_status.json")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
MAX_MEMORY_GB = 7.0
N_JOBS = 2
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> bool:
    """Check if current memory usage is within the limit."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024**3)
    if mem_gb > MAX_MEMORY_GB:
        logger.log("memory_exceeded", current_gb=mem_gb, limit_gb=MAX_MEMORY_GB)
        return False
    return True


def read_eligible_subjects() -> List[str]:
    """Read eligible subject IDs from the filtered list."""
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    return df["subject_id"].tolist()


def load_connectivity(subject_id: str) -> np.ndarray:
    """Load the connectivity matrix for a given subject."""
    matrix_path = CONNECTIVITY_DIR / f"{subject_id}_connectivity.npy"
    if not matrix_path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found for {subject_id}: {matrix_path}")
    return np.load(matrix_path)


def compute_subject_metrics(subject_id: str) -> Optional[Dict[str, Any]]:
    """Compute graph metrics for a single subject."""
    try:
        if not check_memory_usage():
            logger.log("skip_subject", reason="memory_limit", subject_id=subject_id)
            return None

        start_time = time.time()
        adjacency = load_connectivity(subject_id)

        # Ensure symmetric and zero diagonal
        adjacency = (adjacency + adjacency.T) / 2
        np.fill_diagonal(adjacency, 0)

        G = create_graph_from_adjacency(adjacency)

        metrics = {
            "subject_id": subject_id,
            "degree_centrality": float(np.mean(calculate_degree_centrality(G))),
            "global_efficiency": float(calculate_global_efficiency(G)),
            "clustering_coefficient": float(np.mean(nx.clustering(G).values())),
            "average_path_length": float(calculate_shortest_path_length(G)),
            "local_efficiency": float(calculate_local_efficiency(G)),
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
            "computation_time_sec": time.time() - start_time,
        }

        logger.log(
            "subject_processed",
            subject_id=subject_id,
            n_nodes=metrics["n_nodes"],
            n_edges=metrics["n_edges"],
            time_sec=metrics["computation_time_sec"],
        )
        return metrics

    except Exception as e:
        logger.log("subject_failed", subject_id=subject_id, error=str(e))
        return None


def process_subject_wrapper(subject_id: str) -> Dict[str, Any]:
    """Wrapper for joblib parallel processing."""
    result = compute_subject_metrics(subject_id)
    return result if result else {"subject_id": subject_id, "status": "failed"}


def write_metrics_csv(metrics_list: List[Dict[str, Any]]) -> None:
    """Write computed metrics to CSV."""
    ensure_dir(GRAPH_METRICS_PATH)
    if not metrics_list:
        logger.log("no_metrics_written", reason="empty_list")
        return

    # Ensure all keys are present
    all_keys = list(metrics_list[0].keys())
    # Sort keys to ensure consistent column order (subject_id first)
    all_keys.sort(key=lambda k: 0 if k == "subject_id" else 1)

    with open(GRAPH_METRICS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        for row in metrics_list:
            writer.writerow(row)

    logger.log("metrics_written", path=str(GRAPH_METRICS_PATH), n_rows=len(metrics_list))


def write_excluded_log(excluded_subjects: List[str], reason: str) -> None:
    """Write log of excluded subjects."""
    ensure_dir(EXCLUDED_LOG_PATH)
    with open(EXCLUDED_LOG_PATH, "w") as f:
        for subj in excluded_subjects:
            f.write(f"{subj}\t{reason}\n")
    logger.log("excluded_log_written", path=str(EXCLUDED_LOG_PATH), n_excluded=len(excluded_subjects))


def write_status(status: Dict[str, Any]) -> None:
    """Write execution status to JSON."""
    ensure_dir(STATUS_PATH)
    save_json(status, str(STATUS_PATH))
    logger.log("status_written", path=str(STATUS_PATH))


def main() -> int:
    """Main entry point for graph metrics computation."""
    logger.log("start_operation", operation="compute_graph_metrics")
    start_total = time.time()

    try:
        # Read eligible subjects
        subject_ids = read_eligible_subjects()
        logger.log("subjects_loaded", count=len(subject_ids))

        if not subject_ids:
            logger.log("no_eligible_subjects")
            write_status({"status": "no_subjects", "timestamp": datetime.utcnow().isoformat()})
            return 0

        # Process subjects in parallel
        logger.log("parallel_execution_start", n_jobs=N_JOBS)
        results = joblib.Parallel(n_jobs=N_JOBS, backend="loky")(
            joblib.delayed(process_subject_wrapper)(sid) for sid in subject_ids
        )

        # Filter successful results
        valid_metrics = [r for r in results if r.get("status") != "failed"]
        failed_subjects = [r["subject_id"] for r in results if r.get("status") == "failed"]

        if failed_subjects:
            write_excluded_log(failed_subjects, "computation_failed")

        # Write outputs
        write_metrics_csv(valid_metrics)

        elapsed = time.time() - start_total
        status = {
            "status": "completed",
            "n_subjects_processed": len(valid_metrics),
            "n_subjects_failed": len(failed_subjects),
            "total_time_sec": elapsed,
            "timestamp": datetime.utcnow().isoformat(),
            "peak_memory_gb": psutil.Process(os.getpid()).memory_info().rss / (1024**3),
        }
        write_status(status)

        logger.log("operation_complete", elapsed_sec=elapsed)
        return 0

    except Exception as e:
        logger.log("operation_failed", error=str(e))
        status = {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
        write_status(status)
        return 1


if __name__ == "__main__":
    sys.exit(main())