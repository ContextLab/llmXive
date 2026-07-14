"""Compute graph‑theoretic metrics for each eligible subject.

This script reads the list of subjects that passed the eligibility filter
(``data/processed/eligible_subjects.csv``), loads each subject's functional
connectivity matrix, builds a NetworkX graph, computes a handful of
standard graph metrics, and writes the results to
``data/processed/graph_metrics.csv``.  The implementation processes subjects
one‑by‑one to stay well under the 7 GB RAM limit.
"""

from __future__ import annotations

import csv
import sys
import traceback
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

# Local utilities
from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)
from utils.logger import get_logger, log_operation

# ----------------------------------------------------------------------
# Configuration helpers
# ----------------------------------------------------------------------

def load_config_wrapper() -> dict:
    """Return a minimal configuration dictionary.

@log_operation
def load_config_wrapper() -> dict:
    """
    Load a minimal configuration.  In a full project this would read a
    JSON/YAML file; here we hard‑code the relevant paths to keep the
    implementation self‑contained.
    """
    base_dir = Path(__file__).resolve().parents[1]  # project root
    config = {
        "eligible_csv": base_dir / "data" / "processed" / "eligible_subjects.csv",
        "connectivity_dir": base_dir
        / "data"
        / "processed"
        / "connectivity_matrices",
        "output_csv": base_dir / "data" / "processed" / "graph_metrics.csv",
    }
    return config


# ----------------------------------------------------------------------
# I/O helpers
# ----------------------------------------------------------------------


@log_operation
def get_data_directories(config: dict) -> dict:
    """Ensure that required directories exist; create them if missing."""
    for key in ("connectivity_dir",):
        Path(config[key]).mkdir(parents=True, exist_ok=True)
    return config


@log_operation
def load_subject_list(eligible_csv: Path) -> List[str]:
    """Read the CSV produced by ``01_download_and_filter``."""
    if not eligible_csv.is_file():
        raise FileNotFoundError(f"Eligible subjects file not found: {eligible_csv}")
    df = pd.read_csv(eligible_csv)
    if "subject_id" not in df.columns:
        raise KeyError("eligible_subjects.csv must contain a 'subject_id' column")
    return df["subject_id"].astype(str).tolist()


@log_operation
def load_connectivity_matrix(connectivity_dir: Path, subject_id: str) -> np.ndarray:
    """
    Load a subject's functional connectivity matrix.

    The expected filename is ``{subject_id}_conn.npy``.  If the file does not
    exist we raise an informative error – the caller can decide whether to
    skip the subject or abort the whole pipeline.
    """
    matrix_path = connectivity_dir / f"{subject_id}_conn.npy"
    if not matrix_path.is_file():
        raise FileNotFoundError(f"Connectivity matrix not found for {subject_id}: {matrix_path}")
    return np.load(matrix_path)


# ----------------------------------------------------------------------
# Metric computation
# ----------------------------------------------------------------------


@log_operation
def compute_subject_metrics(matrix: np.ndarray) -> dict:
    """
    Given a (square) adjacency matrix, compute a suite of graph metrics.

    Returns a dictionary with the metric names as keys.
    """
    # Build an undirected weighted graph from the adjacency matrix.
    G = create_graph_from_adjacency(matrix)

    # Degree centrality – we take the mean across nodes.
    degree_dict = calculate_degree_centrality(G)
    degree_mean = float(np.mean(list(degree_dict.values())))

    # Global efficiency (weighted)
    global_eff = calculate_global_efficiency(G)

    # Clustering coefficient (average)
    clustering = calculate_clustering_coefficient(G)

    # Average shortest path length (weighted)
    path_length = calculate_shortest_path_length(G)

    return {
        "degree_mean": degree_mean,
        "global_efficiency": global_eff,
        "clustering_coefficient": clustering,
        "average_path_length": path_length,
    }


# ----------------------------------------------------------------------
# Memory guard (very lightweight – just a sanity check)
# ----------------------------------------------------------------------


@log_operation
def check_memory_limit(max_gb: float = 7.0) -> None:
    """
    Simple guard that aborts if the current process exceeds ``max_gb``.
    Uses ``psutil`` if available; otherwise it is a no‑op.
    """
    try:
        import psutil
    except Exception:  # pragma: no cover
        return

    process = psutil.Process()
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > max_gb:
        raise MemoryError(f"Memory usage {mem_gb:.2f} GB exceeds limit of {max_gb} GB")


# ----------------------------------------------------------------------
# Output writer
# ----------------------------------------------------------------------


@log_operation
def write_outputs(output_path: Path, rows: List[dict]) -> None:
    """Write the collected metric rows to a CSV file."""
    if not rows:
        raise ValueError("No metric rows to write")
    df = pd.DataFrame(rows)
    # Ensure deterministic column ordering
    columns = ["subject_id", "degree_mean", "global_efficiency", "clustering_coefficient", "average_path_length"]
    df = df[columns]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------


@log_operation("compute_graph_metrics")
def main() -> None:
    """Entry point used by the quick‑start run‑book."""
    logger = get_logger("graph_metrics")
    start = time.time()

    try:
        cfg = load_config_wrapper()
        cfg = get_data_directories(cfg)

        subject_ids = load_subject_list(Path(cfg["eligible_csv"]))
        logger.info(f"Found {len(subject_ids)} eligible subjects")

        rows: List[dict] = []
        for sid in subject_ids:
            try:
                matrix = load_connectivity_matrix(Path(cfg["connectivity_dir"]), sid)
                metrics = compute_subject_metrics(matrix)
                metrics["subject_id"] = sid
                rows.append(metrics)
            except FileNotFoundError as exc:
                logger.warning(str(exc))
                continue
            except Exception as exc:  # pragma: no cover
                logger.error(f"Failed to process {sid}: {exc}")
                continue

            # Light memory guard after each subject.
            check_memory_limit()

        write_outputs(Path(cfg["output_csv"]), rows)
        elapsed = time.time() - start
        logger.info(f"Graph metrics written to {cfg['output_csv']} (took {elapsed:.1f}s)")

    except Exception as exc:  # pragma: no cover
        logger.error(f"Fatal error in compute_graph_metrics: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()