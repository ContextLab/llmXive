"""Compute graph metrics for each eligible subject.

This script reads the list of eligible subjects produced by
``code/01_download_and_filter.py`` (``data/processed/eligible_subjects.csv``),
loads each subject's functional connectivity matrix, builds a graph, and
computes the following metrics:

* mean node degree
* global efficiency
* mean clustering coefficient
* mean shortest path length

The results are written to ``data/processed/graph_metrics.csv``.  The script
processes subjects one‑by‑one to keep peak RAM usage below the 7 GB limit
(checked via :func:`check_memory_limit`).

The implementation relies on the utility modules under ``code/utils``:
* ``utils.io`` – CSV I/O helpers
* ``utils.graph`` – graph construction and metric functions
* ``utils.logger`` – tolerant reproducibility logger
"""
from __future__ import annotations

import sys
import psutil
from pathlib import Path
from typing import List, Dict

import numpy as np

# Project utilities
from utils.io import ensure_dir, load_csv, save_csv
from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)
from utils.logger import get_logger, log_operation

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
MEMORY_LIMIT_GB = 7.0
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
OUTPUT_PATH = Path("data/processed/graph_metrics.csv")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> None:
    """Abort the script if the current process exceeds *limit_gb*.

    The check is performed once at start‑up; the heavy lifting later in the
    loop processes one subject at a time, keeping memory bounded.
    """
    mem = psutil.Process().memory_info().rss / (1024 ** 3)  # GB
    if mem > limit_gb:
        logger = get_logger("graph_metrics")
        logger.error(
            f"Memory usage {mem:.2f} GB exceeds limit of {limit_gb} GB. "
            "Aborting."
        )
        sys.exit(1)

def load_eligible_subjects(csv_path: Path = ELIGIBLE_SUBJECTS_PATH) -> List[str]:
    """Return a list of subject IDs from the eligibility CSV."""
    logger = get_logger("graph_metrics")
    if not csv_path.is_file():
        logger.error(f"Eligible subjects file not found: {csv_path}")
        sys.exit(1)

    rows = load_csv(csv_path)
    # Expect a column named ``subject_id``; fall back to first column.
    if rows and "subject_id" in rows[0]:
        subject_ids = [row["subject_id"] for row in rows]
    else:
        subject_ids = [list(row.values())[0] for row in rows]

    logger.info(f"Loaded {len(subject_ids)} eligible subjects.")
    return subject_ids

def load_connectivity_matrix(subject_id: str) -> np.ndarray:
    """Load a subject's 90 × 90 connectivity matrix (NumPy ``.npy``)."""
    logger = get_logger("graph_metrics")
    mat_path = CONNECTIVITY_DIR / f"{subject_id}.npy"
    if not mat_path.is_file():
        logger.error(f"Connectivity matrix not found for subject {subject_id}: {mat_path}")
        sys.exit(1)

    try:
        matrix = np.load(mat_path)
    except Exception as exc:
        logger.error(f"Failed to load matrix for {subject_id}: {exc}")
        sys.exit(1)

    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        logger.error(f"Invalid matrix shape for {subject_id}: {matrix.shape}")
        sys.exit(1)

    return matrix

def compute_subject_metrics(subject_id: str) -> Dict[str, float]:
    """Compute the required graph metrics for a single subject."""
    logger = get_logger("graph_metrics")
    matrix = load_connectivity_matrix(subject_id)

    # Build an undirected graph; weight = absolute correlation strength
    G = create_graph_from_adjacency(matrix)

    # Degree centrality returns a dict {node: degree}
    degree_dict = calculate_degree_centrality(G)
    mean_degree = float(np.mean(list(degree_dict.values())))

    # Global efficiency – single scalar
    global_eff = calculate_global_efficiency(G)

    # Clustering coefficient – dict per node
    clustering_dict = calculate_clustering_coefficient(G)
    mean_clustering = float(np.mean(list(clustering_dict.values())))

    # Shortest path length – dict of dicts; we take the mean of finite lengths
    path_length_dict = calculate_shortest_path_length(G)
    # Flatten to list of lengths (ignore infinities)
    lengths = [
        d
        for target_dict in path_length_dict.values()
        for d in target_dict.values()
        if np.isfinite(d)
    ]
    mean_path_len = float(np.mean(lengths)) if lengths else float("nan")

    logger.debug(
        f"Metrics for {subject_id}: degree={mean_degree:.3f}, "
        f"efficiency={global_eff:.3f}, clustering={mean_clustering:.3f}, "
        f"path_len={mean_path_len:.3f}"
    )

    return {
        "subject_id": subject_id,
        "mean_degree": mean_degree,
        "global_efficiency": global_eff,
        "mean_clustering": mean_clustering,
        "mean_path_length": mean_path_len,
    }

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
@log_operation("compute_graph_metrics")
def main() -> None:
    """Run the full graph‑metric computation pipeline."""
    logger = get_logger("graph_metrics")
    logger.info("Starting graph‑metric computation.")

    # Ensure we do not exceed the RAM budget.
    check_memory_limit()

    # Load subjects
    subjects = load_eligible_subjects()

    # Compute metrics subject‑by‑subject
    results: List[Dict[str, float]] = []
    for sid in subjects:
        try:
            metrics = compute_subject_metrics(sid)
            results.append(metrics)
        except SystemExit:
            # Already logged; continue with next subject.
            continue
        except Exception as exc:
            logger.error(f"Unexpected error for {sid}: {exc}")
            continue

    # Write results
    ensure_dir(OUTPUT_PATH.parent)
    save_csv(OUTPUT_PATH, results)
    logger.info(f"Wrote graph metrics for {len(results)} subjects to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
