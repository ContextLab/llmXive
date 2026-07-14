"""Compute graph metrics for eligible subjects using parallel processing.

This script reads the list of eligible subjects from
`data/processed/eligible_subjects.csv`, loads each subject's connectivity
matrix (expected as a NumPy ``.npy`` file under
``data/processed/connectivity_matrices/<subject_id>.npy``), computes a set of
graph‑theoretic metrics, and writes the results to
``data/processed/graph_metrics.csv``.

The implementation uses ``joblib.Parallel`` with ``n_jobs=2`` to stay within
the project's runtime constraints and to satisfy task T035.
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

# Project utilities
from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)
from utils.logger import get_logger, log_operation

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
OUTPUT_PATH = Path("data/processed/graph_metrics.csv")
MAX_RAM_GB = 7.0  # Memory limit for the whole pipeline

logger = get_logger("graph_metrics")

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def check_memory_limit() -> None:
    """Abort if the current process exceeds the RAM limit."""
    try:
        import psutil
    except ImportError:
        logger.warning("psutil not installed; skipping memory limit check")
        return
    mem_gb = psutil.virtual_memory().used / 1e9
    if mem_gb > MAX_RAM_GB:
        logger.error(f"Memory usage {mem_gb:.2f} GB exceeds limit of {MAX_RAM_GB} GB")
        sys.exit(1)

def load_eligible_subjects() -> list[str]:
    """Return a list of subject IDs from the eligible CSV."""
    if not ELIGIBLE_SUBJECTS_PATH.is_file():
        logger.error(f"Eligible subjects file missing: {ELIGIBLE_SUBJECTS_PATH}")
        sys.exit(1)
    subjects = []
    with ELIGIBLE_SUBJECTS_PATH.open(newline="") as f:
        reader = csv.DictReader(f)
        if "subject_id" not in reader.fieldnames:
            logger.error("eligible_subjects.csv missing 'subject_id' column")
            sys.exit(1)
        for row in reader:
            subjects.append(row["subject_id"])
    return subjects

def load_connectivity_matrix(subject_id: str) -> np.ndarray | None:
    """Load a subject's connectivity matrix; return ``None`` on failure."""
    matrix_path = CONNECTIVITY_DIR / f"{subject_id}.npy"
    if not matrix_path.is_file():
        logger.warning(f"Connectivity matrix not found for {subject_id}")
        return None
    try:
        mat = np.load(matrix_path)
        if mat.shape != (90, 90):
            logger.error(f"Invalid matrix shape for {subject_id}: {mat.shape}")
            return None
        return mat
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to load matrix for {subject_id}: {exc}")
        return None

def compute_subject_metrics(subject_id: str) -> dict | None:
    """Compute graph metrics for a single subject."""
    mat = load_connectivity_matrix(subject_id)
    if mat is None:
        return None

    # Build an undirected graph from the adjacency matrix
    G = create_graph_from_adjacency(mat)

    # Degree centrality (average across nodes)
    degree_centrality = np.mean(list(calculate_degree_centrality(G).values()))

    # Global efficiency
    global_eff = calculate_global_efficiency(G)

    # Clustering coefficient (average)
    clustering = np.mean(list(calculate_clustering_coefficient(G).values()))

    # Average shortest path length
    # If the graph is disconnected, the function returns np.inf; handle gracefully
    avg_path_len = calculate_shortest_path_length(G)
    if np.isinf(avg_path_len):
        avg_path_len = float("nan")

    return {
        "subject_id": subject_id,
        "degree_centrality": degree_centrality,
        "global_efficiency": global_eff,
        "clustering_coefficient": clustering,
        "average_shortest_path_length": avg_path_len,
    }

def write_graph_metrics_csv(rows: list[dict]) -> None:
    """Write the list of metric dictionaries to CSV."""
    if not rows:
        logger.warning("No metric rows to write; producing empty CSV")
    fieldnames = [
        "subject_id",
        "degree_centrality",
        "global_efficiency",
        "clustering_coefficient",
        "average_shortest_path_length",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    logger.info(f"Graph metrics written to {OUTPUT_PATH}")

# --------------------------------------------------------------------------- #
# Main pipeline
# --------------------------------------------------------------------------- #

@log_operation
def main() -> None:
    start = time.time()
    logger.info("Starting graph‑metric computation")

    # Memory sanity check before heavy work
    check_memory_limit()

    subjects = load_eligible_subjects()
    if not subjects:
        logger.error("No eligible subjects found; exiting.")
        sys.exit(1)

    # Parallel processing (subject‑wise)
    results = Parallel(n_jobs=2, backend="loky")(
        delayed(compute_subject_metrics)(sid) for sid in subjects
    )

    # Filter out any ``None`` results (subjects without a matrix)
    metric_rows = [r for r in results if r is not None]

    write_graph_metrics_csv(metric_rows)

    elapsed = time.time() - start
    logger.info(f"Graph‑metric pipeline completed in {elapsed:.2f} s")


if __name__ == "__main__":
    main()
