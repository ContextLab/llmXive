"""
Compute graph metrics (degree, efficiency, clustering, path length) from connectivity matrices.
Refactored for T035: Uses joblib.Parallel(n_jobs=2) for runtime optimization.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import networkx as nx
import psutil
from joblib import Parallel, delayed

# Import from local utils (API Surface)
from utils.graph import (
    load_aal_atlas_mask,
    validate_atlas_shape,
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
)
from utils.io import ensure_dir, load_csv
from utils.logger import get_logger

# Constants
DATA_PROCESSED_DIR = Path("data/processed")
CONNECTIVITY_DIR = DATA_PROCESSED_DIR / "connectivity_matrices"
GRAPH_METRICS_PATH = DATA_PROCESSED_DIR / "graph_metrics.csv"
EXCLUDED_LOG_PATH = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_PATH = Path("data/artifacts/data_gate_status.json")
ELIGIBLE_SUBJECTS_PATH = DATA_PROCESSED_DIR / "eligible_subjects.csv"
MAX_MEMORY_GB = 7.0
N_JOBS = 2  # T035: Parallel execution
RANDOM_SEED = 42

logger = get_logger("compute_graph_metrics")

def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """
    Load connectivity matrix for a subject.
    Expects file: data/processed/connectivity_matrices/{subject_id}_conn.npy
    """
    conn_path = CONNECTIVITY_DIR / f"{subject_id}_conn.npy"
    if not conn_path.exists():
        logger.warning(f"Connectivity matrix not found for {subject_id}: {conn_path}")
        return None
    try:
        return np.load(conn_path)
    except Exception as e:
        logger.error(f"Failed to load {conn_path}: {e}")
        return None

def compute_subject_metrics(subject_id: str, connectivity: np.ndarray) -> Optional[Dict[str, Any]]:
    """
    Compute graph metrics for a single subject.
    Returns dict with subject_id and metrics, or None if computation fails.
    """
    try:
        # Validate shape
        if not validate_atlas_shape(connectivity):
            logger.warning(f"Invalid connectivity shape for {subject_id}: {connectivity.shape}")
            return None

        # Create graph
        G = create_graph_from_adjacency(connectivity)

        if G.number_of_nodes() == 0:
            logger.warning(f"Empty graph for {subject_id}")
            return None

        # Calculate metrics
        degree = calculate_degree_centrality(G)
        global_eff = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        path_len = calculate_shortest_path_length(G)

        return {
            "subject_id": subject_id,
            "degree_centrality": float(np.mean(degree)),
            "global_efficiency": float(global_eff),
            "clustering_coefficient": float(clustering),
            "average_path_length": float(path_len),
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
        }
    except Exception as e:
        logger.error(f"Error computing metrics for {subject_id}: {e}")
        return None

def process_subject_wrapper(subject_id: str) -> Optional[Dict[str, Any]]:
    """Wrapper for parallel execution."""
    mem_usage = check_memory_usage()
    if mem_usage > MAX_MEMORY_GB:
        logger.warning(f"Memory usage {mem_usage:.2f}GB exceeds limit. Skipping {subject_id}.")
        return None

    connectivity = load_connectivity(subject_id)
    if connectivity is None:
        return None

    return compute_subject_metrics(subject_id, connectivity)

def read_eligible_subjects() -> List[str]:
    """Read eligible subjects from CSV."""
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")

    subjects = []
    with open(ELIGIBLE_SUBJECTS_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "subject_id" in row:
                subjects.append(row["subject_id"])
            elif "participant_id" in row:
                subjects.append(row["participant_id"])
    return subjects

def write_metrics_csv(results: List[Dict[str, Any]]) -> None:
    """Write results to CSV."""
    if not results:
        logger.warning("No results to write.")
        return

    ensure_dir(GRAPH_METRICS_PATH.parent)
    fieldnames = list(results[0].keys())

    with open(GRAPH_METRICS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Wrote {len(results)} metrics to {GRAPH_METRICS_PATH}")

def write_excluded_log(subject_ids: List[str]) -> None:
    """Log excluded subjects."""
    ensure_dir(EXCLUDED_LOG_PATH.parent)
    with open(EXCLUDED_LOG_PATH, "w") as f:
        for sid in subject_ids:
            f.write(f"{sid}\n")
    logger.info(f"Wrote {len(subject_ids)} excluded subjects to {EXCLUDED_LOG_PATH}")

def write_status(status: Dict[str, Any]) -> None:
    """Write status JSON."""
    ensure_dir(STATUS_PATH.parent)
    with open(STATUS_PATH, "w") as f:
        json.dump(status, f, indent=2)

def main() -> int:
    """Main entry point."""
    start_time = time.time()
    logger.info("Starting graph metrics computation.")

    try:
        # Read eligible subjects
        subjects = read_eligible_subjects()
        logger.info(f"Loaded {len(subjects)} eligible subjects.")

        if not subjects:
            logger.error("No eligible subjects found.")
            return 1

        # Process subjects in parallel (T035 Optimization)
        logger.info(f"Processing {len(subjects)} subjects with {N_JOBS} workers...")
        results = Parallel(n_jobs=N_JOBS, backend="loky")(
            delayed(process_subject_wrapper)(sid) for sid in subjects
        )

        # Filter None results
        valid_results = [r for r in results if r is not None]
        excluded_count = len(subjects) - len(valid_results)

        if excluded_count > 0:
            excluded_subjects = [
                subjects[i] for i, r in enumerate(results) if r is None
            ]
            write_excluded_log(excluded_subjects)

        # Write output
        write_metrics_csv(valid_results)

        # Write status
        end_time = time.time()
        elapsed = end_time - start_time
        status = {
            "status": "success",
            "subjects_processed": len(valid_results),
            "subjects_excluded": excluded_count,
            "elapsed_seconds": elapsed,
            "parallel_workers": N_JOBS,
        }
        write_status(status)

        logger.info(f"Completed in {elapsed:.2f}s. Processed {len(valid_results)} subjects.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
