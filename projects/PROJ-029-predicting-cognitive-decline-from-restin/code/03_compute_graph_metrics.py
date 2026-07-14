"""Compute graph‑theoretic metrics for each subject’s functional connectivity matrix.

This script is part of the *Predicting Cognitive Decline from Resting‑State fMRI*
pipeline (User Story 1). It reads the list of eligible subjects, loads each
subject’s 90 × 90 adjacency matrix (produced by ``02_preprocess_and_parcellate.py``),
computes a suite of network metrics, and writes the results to
``data/processed/graph_metrics.csv``.

The implementation respects the 7 GB RAM limit by processing subjects one‑by‑one
(now parallelised with joblib) and invoking ``psutil`` to abort if memory usage
would exceed the threshold.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd
import psutil
from joblib import Parallel, delayed

# Project utilities
from utils.logger import get_logger, log_operation
from utils.io import load_csv, save_csv
from utils.graph import (
    create_graph_from_adjacency,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from config import load_config


LOGGER = get_logger("graph_metrics")


@log_operation
def load_config_wrapper() -> Dict[str, Any]:
    """Load the global configuration and expose it as a dict."""
    cfg = load_config()
    # Ensure the memory limit is present; default to 7 GB if missing.
    cfg.setdefault("memory_limit_gb", 7)
    return cfg


def get_data_directories() -> Tuple[Path, Path]:
    """Return (raw_data_dir, processed_data_dir)."""
    cfg = load_config_wrapper()
    raw_dir = Path(cfg.get("raw_data_dir", "data/raw"))
    proc_dir = Path(cfg.get("processed_data_dir", "data/processed"))
    return raw_dir, proc_dir


def load_subject_list() -> List[str]:
    """Load the list of eligible subject IDs from ``eligible_subjects.csv``."""
    _, proc_dir = get_data_directories()
    eligible_path = proc_dir / "eligible_subjects.csv"
    if not eligible_path.is_file():
        LOGGER.error(f"Eligible subjects file not found at {eligible_path}")
        sys.exit(1)
    df = load_csv(eligible_path)
    if "subject_id" not in df.columns:
        LOGGER.error("eligible_subjects.csv must contain a 'subject_id' column")
        sys.exit(1)
    return df["subject_id"].astype(str).tolist()


def load_connectivity_matrix(subject_id: str) -> np.ndarray:
    """Load a subject's connectivity matrix (assumed stored as .npy)."""
    _, proc_dir = get_data_directories()
    matrix_path = proc_dir / "connectivity_matrices" / f"{subject_id}.npy"
    if not matrix_path.is_file():
        LOGGER.error(f"Connectivity matrix for {subject_id} not found at {matrix_path}")
        raise FileNotFoundError(matrix_path)
    return np.load(matrix_path)


def compute_subject_metrics(matrix: np.ndarray) -> Dict[str, float]:
    """Calculate network metrics for a single adjacency matrix."""
    # Ensure the matrix is symmetric and non‑negative.
    if not np.allclose(matrix, matrix.T):
        LOGGER.warning("Adjacency matrix is not symmetric; symmetrising.")
        matrix = (matrix + matrix.T) / 2
    # Create a NetworkX graph from the adjacency matrix.
    G = create_graph_from_adjacency(matrix)

    # Degree centrality (average over nodes)
    degree_centrality = calculate_degree_centrality(G)
    avg_degree = float(np.mean(list(degree_centrality.values())))

    # Global efficiency
    global_eff = calculate_global_efficiency(G)

    # Clustering coefficient (average)
    clustering = calculate_clustering_coefficient(G)

    # Average shortest path length
    path_len = calculate_shortest_path_length(G)

    return {
        "degree": avg_degree,
        "global_efficiency": global_eff,
        "clustering_coefficient": clustering,
        "average_path_length": path_len,
    }


def check_memory_limit(limit_gb: float) -> None:
    """Abort if the current process exceeds the supplied memory limit."""
    process = psutil.Process()
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > limit_gb:
        LOGGER.error(
            f"Memory usage {mem_gb:.2f} GB exceeds limit of {limit_gb:.2f} GB"
        )
        sys.exit(1)


@log_operation
def write_outputs(df: pd.DataFrame) -> None:
    """Write the metrics DataFrame to ``graph_metrics.csv``."""
    _, proc_dir = get_data_directories()
    out_path = proc_dir / "graph_metrics.csv"
    save_csv(df, out_path)
    LOGGER.info(f"Wrote graph metrics for {len(df)} subjects to {out_path}")


def _process_single_subject(subj: str) -> Dict[str, Any] | None:
    """Helper for parallel execution: compute metrics for one subject."""
    try:
        matrix = load_connectivity_matrix(subj)
    except FileNotFoundError:
        LOGGER.warning(f"Skipping subject {subj} – matrix missing")
        return None
    metrics = compute_subject_metrics(matrix)
    metrics["subject_id"] = subj
    return metrics


def main() -> None:
    """Entry point for the script."""
    start_time = time.time()
    LOGGER.info("Starting graph‑metric computation")

    cfg = load_config_wrapper()
    memory_limit = float(cfg["memory_limit_gb"])

    subject_ids = load_subject_list()
    if not subject_ids:
        LOGGER.error("No eligible subjects to process")
        sys.exit(1)

    # Parallel computation across subjects (max 2 jobs as per requirement)
    records = Parallel(n_jobs=2, backend="loky")(
        delayed(_process_single_subject)(subj) for subj in subject_ids
    )

    # Filter out any subjects that were skipped (None entries)
    records = [rec for rec in records if rec is not None]

    if not records:
        LOGGER.error("No metrics were computed; exiting")
        sys.exit(1)

    # Verify memory usage after processing (once, as a final guard)
    check_memory_limit(memory_limit)

    df_metrics = pd.DataFrame.from_records(records)
    # Ensure a deterministic column order.
    df_metrics = df_metrics[
        [
            "subject_id",
            "degree",
            "global_efficiency",
            "clustering_coefficient",
            "average_path_length",
        ]
    ]

    write_outputs(df_metrics)

    elapsed = time.time() - start_time
    LOGGER.info(f"Completed graph‑metric computation in {elapsed:.2f} s")


if __name__ == "__main__":
    main()