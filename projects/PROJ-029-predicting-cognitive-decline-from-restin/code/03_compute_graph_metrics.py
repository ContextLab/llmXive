"""Compute graph‑theoretic metrics for each eligible subject using parallel processing.

This script reads the list of eligible subjects (produced by ``01_download_and_filter.py``),
loads each subject's functional connectivity matrix, computes a set of graph metrics,
and writes the results to ``data/processed/graph_metrics.csv``.  Runtime information is
written to ``data/artifacts/graph_metrics_runtime.txt`` for verification that the
processing stays below the 30‑minute target for 100 subjects.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List, Dict, Any

from joblib import Parallel, delayed
from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)
from utils.io import load_csv, save_csv
from utils.logger import get_logger, log_operation


def read_eligible_subjects(csv_path: Path) -> List[Dict[str, str]]:
    """Load ``eligible_subjects.csv``; exit with an error if missing."""
    if not csv_path.is_file():
        get_logger().error(f"Eligible subjects file not found: {csv_path}")
        sys.exit(1)
    return load_csv(csv_path)


def load_connectivity(subject_id: str, conn_dir: Path) -> Any:
    """Load a NumPy ``.npy`` connectivity matrix for *subject_id*."""
    conn_path = conn_dir / f"{subject_id}_connectivity.npy"
    if not conn_path.is_file():
        get_logger().warning(f"Connectivity file missing for {subject_id}")
        return None
    import numpy as np

    return np.load(conn_path)


def compute_subject_metrics(subject_id: str, conn_matrix: Any) -> Dict[str, Any]:
    """Given a connectivity matrix, compute a suite of graph metrics."""
    if conn_matrix is None:
        return {"subject_id": subject_id}

    # Build a NetworkX graph from the adjacency matrix
    G = create_graph_from_adjacency(conn_matrix)

    # Degree centrality (average over nodes)
    degree = calculate_degree_centrality(G)
    degree_mean = sum(degree.values()) / len(degree) if degree else None

    # Global efficiency
    global_eff = calculate_global_efficiency(G)

    # Clustering coefficient (average)
    clustering = calculate_clustering_coefficient(G)

    # Average shortest path length
    path_len = calculate_shortest_path_length(G)

    return {
        "subject_id": subject_id,
        "degree_mean": degree_mean,
        "global_efficiency": global_eff,
        "clustering_coefficient": clustering,
        "average_shortest_path": path_len,
    }


def process_subject(subject_record: Dict[str, str], conn_dir: Path) -> Dict[str, Any]:
    """Wrapper used by the parallel executor."""
    subject_id = subject_record["subject_id"]
    conn = load_connectivity(subject_id, conn_dir)
    return compute_subject_metrics(subject_id, conn)


def main() -> None:
    start = time.time()
    logger = get_logger("graph_metrics")

    # Load eligible subjects
    eligible_path = Path("data/processed/eligible_subjects.csv")
    subjects = read_eligible_subjects(eligible_path)

    # Directory where per‑subject connectivity matrices are stored
    conn_dir = Path("data/processed/connectivity")

    # Parallel processing (2 jobs as required)
    results = Parallel(n_jobs=2)(
        delayed(process_subject)(subj, conn_dir) for subj in subjects
    )

    # Keep only entries that contain computed metrics
    metrics = [r for r in results if "degree_mean" in r]

    # Write the aggregated metrics CSV
    output_path = Path("data/processed/graph_metrics.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if metrics:
        fieldnames = list(metrics[0].keys())
        save_csv(metrics, output_path, fieldnames=fieldnames)
        logger.info(f"Graph metrics written to {output_path}")
    else:
        logger.warning("No graph metrics were computed.")

    # Record runtime for verification
    runtime_path = Path("data/artifacts/graph_metrics_runtime.txt")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    elapsed = time.time() - start
    runtime_path.write_text(f"Runtime seconds: {elapsed:.2f}\n")
    logger.info(f"Graph metrics computation completed in {elapsed:.2f}s")


if __name__ == "__main__":
    sys.exit(main())