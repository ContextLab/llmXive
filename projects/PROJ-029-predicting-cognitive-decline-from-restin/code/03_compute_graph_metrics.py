"""Compute graph metrics for each subject in parallel.

This module loads a list of eligible subjects, reads their precomputed
connectivity matrices, constructs graphs, computes a set of graph‑theoretic
metrics and writes the results to ``data/processed/graph_metrics.csv``.
The implementation uses ``joblib.Parallel`` with ``n_jobs=2`` to satisfy
the performance target of < 30 min for 100 subjects.

Public API (as declared in the project spec):
  - load_config()
  - get_data_directories()
  - load_subject_list()
  - load_connectivity_matrix(subject_id)
  - compute_subject_metrics(subject_id)
  - write_outputs(metrics_list)
  - main()
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
from joblib import Parallel, delayed

# Project utilities
from utils.io import ensure_dir, load_csv, save_csv
from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)
from utils.logger import get_logger

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------
def load_config() -> Dict:
    """Load the JSON configuration file.

    The configuration file location is resolved relative to this script.
    If the file cannot be read, the function logs the error and exits
    with a non‑zero status code.
    """
    logger = get_logger("load_config")
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    if not config_path.is_file():
        logger.error("Configuration file not found at %s", config_path)
        sys.exit(1)
    try:
        with config_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        logger.info("Loaded config from %s", config_path)
        return cfg
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to parse config %s: %s", config_path, exc)
        sys.exit(1)

# ----------------------------------------------------------------------
# Directory helpers
# ----------------------------------------------------------------------
def get_data_directories(cfg: Dict) -> Dict[str, Path]:
    """Return a mapping with ``raw`` and ``processed`` data directories."""
    raw_dir = Path(cfg.get("raw_data_dir", "data/raw"))
    processed_dir = Path(cfg.get("processed_data_dir", "data/processed"))
    ensure_dir(raw_dir)
    ensure_dir(processed_dir)
    return {"raw": raw_dir, "processed": processed_dir}

# ----------------------------------------------------------------------
# Subject list handling
# ----------------------------------------------------------------------
def load_subject_list(processed_dir: Path) -> List[str]:
    """Load the list of eligible subject IDs.

    Expects ``eligible_subjects.csv`` with a ``subject_id`` column in the
    processed data directory.
    """
    logger = get_logger("load_subject_list")
    csv_path = processed_dir / "eligible_subjects.csv"
    if not csv_path.is_file():
        logger.error("Eligible subjects file not found at %s", csv_path)
        sys.exit(1)
    df = load_csv(csv_path)
    if "subject_id" not in df.columns:
        logger.error("Column 'subject_id' missing in %s", csv_path)
        sys.exit(1)
    subjects = df["subject_id"].astype(str).tolist()
    logger.info("Loaded %d eligible subjects", len(subjects))
    return subjects

# ----------------------------------------------------------------------
# Connectivity matrix loader
# ----------------------------------------------------------------------
def load_connectivity_matrix(subject_id: str, raw_dir: Path) -> np.ndarray:
    """Load a subject's 90×90 connectivity matrix.

    The matrix is stored as a NumPy ``.npy`` file named
    ``{subject_id}_connectivity.npy`` inside the raw data directory.
    """
    logger = get_logger("load_connectivity_matrix")
    matrix_path = raw_dir / f"{subject_id}_connectivity.npy"
    if not matrix_path.is_file():
        logger.error("Connectivity matrix not found for %s at %s", subject_id, matrix_path)
        sys.exit(1)
    try:
        mat = np.load(matrix_path)
        if mat.shape != (90, 90):
            logger.warning("Unexpected matrix shape %s for %s", mat.shape, subject_id)
        return mat
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to load matrix for %s: %s", subject_id, exc)
        sys.exit(1)

# ----------------------------------------------------------------------
# Metric computation per subject
# ----------------------------------------------------------------------
def compute_subject_metrics(subject_id: str, raw_dir: Path) -> Dict:
    """Compute graph metrics for a single subject.

    Returns a dictionary that can be directly written to CSV.
    """
    logger = get_logger("compute_subject_metrics")
    try:
        adj = load_connectivity_matrix(subject_id, raw_dir)
        G = create_graph_from_adjacency(adj)

        # Degree centrality – we take the mean across nodes
        degree_dict = calculate_degree_centrality(G)
        mean_degree = float(np.mean(list(degree_dict.values())))

        global_eff = float(calculate_global_efficiency(G))
        clustering = float(calculate_clustering_coefficient(G))
        avg_path_len = float(calculate_shortest_path_length(G))

        result = {
            "subject_id": subject_id,
            "degree": mean_degree,
            "global_efficiency": global_eff,
            "clustering_coefficient": clustering,
            "average_path_length": avg_path_len,
        }
        logger.debug("Metrics for %s: %s", subject_id, result)
        return result
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to compute metrics for %s: %s", subject_id, exc)
        # Return a dict with NaNs so the CSV stays aligned
        return {
            "subject_id": subject_id,
            "degree": float("nan"),
            "global_efficiency": float("nan"),
            "clustering_coefficient": float("nan"),
            "average_path_length": float("nan"),
        }

# ----------------------------------------------------------------------
# Output writer
# ----------------------------------------------------------------------
def write_outputs(metrics: List[Dict], processed_dir: Path) -> None:
    """Write the list of metric dictionaries to CSV."""
    logger = get_logger("write_outputs")
    output_path = processed_dir / "graph_metrics.csv"
    try:
        save_csv(metrics, output_path)
        logger.info("Wrote graph metrics for %d subjects to %s", len(metrics), output_path)
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to write graph metrics CSV: %s", exc)
        sys.exit(1)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Orchestrate the whole pipeline.

    Returns an exit code (0 for success, non‑zero otherwise).
    """
    logger = get_logger("03_compute_graph_metrics")
    start_time = time.time()

    # Load configuration and directories
    cfg = load_config()
    dirs = get_data_directories(cfg)
    raw_dir = dirs["raw"]
    processed_dir = dirs["processed"]

    # Load subject list
    subjects = load_subject_list(processed_dir)

    if not subjects:
        logger.error("No eligible subjects found – aborting.")
        return 1

    # Parallel computation – joblib with 2 workers
    logger.info("Starting parallel metric computation with 2 workers")
    try:
        metrics = Parallel(n_jobs=2, backend="loky")(
            delayed(compute_subject_metrics)(subj, raw_dir) for subj in subjects
        )
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Parallel execution failed: %s", exc)
        return 1

    # Write results
    write_outputs(metrics, processed_dir)

    # Runtime report (optional but useful for verification)
    elapsed = time.time() - start_time
    runtime_path = processed_dir / "graph_metrics_runtime.txt"
    try:
        with runtime_path.open("w", encoding="utf-8") as f:
            f.write(f"Graph metrics computation time (seconds): {elapsed:.2f}\\n")
        logger.info("Runtime report written to %s", runtime_path)
    except Exception as exc:  # pragma: no cover – defensive
        logger.warning("Failed to write runtime report: %s", exc)

    logger.info("Graph metric computation completed in %.2f seconds", elapsed)
    return 0

if __name__ == "__main__":
    sys.exit(main())