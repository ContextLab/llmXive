"""
Compute graph-theoretical metrics from connectivity matrices.
Refactored for performance using joblib.Parallel (n_jobs=2).
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import networkx as nx
import psutil
from joblib import Parallel, delayed

# Local imports matching the API surface
from utils.logger import get_logger, log_operation
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from utils.io import ensure_dir, load_numpy, save_csv

logger = get_logger("compute_graph_metrics")

# Configuration
N_JOBS = 2
MEMORY_LIMIT_GB = 7.0
OUTPUT_DIR = Path("data/processed")
METRICS_FILE = OUTPUT_DIR / "graph_metrics.csv"
STATUS_FILE = OUTPUT_DIR / "graph_metrics_status.json"
EXCLUDED_LOG = OUTPUT_DIR / "excluded_graph_metrics.log"

def check_memory_usage() -> bool:
    """Check if current memory usage is within limits."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > MEMORY_LIMIT_GB:
        logger.warning(f"Memory usage {mem_gb:.2f}GB exceeds limit {MEMORY_LIMIT_GB}GB")
        return False
    return True

def read_eligible_subjects(filepath: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {filepath}")
    subjects = []
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential variations in column names
            sub_id = row.get("subject_id") or row.get("sub_id") or row.get("participant_id")
            if sub_id:
                subjects.append(sub_id.strip())
    return subjects

def load_connectivity(subject_id: str, base_dir: Path) -> Optional[np.ndarray]:
    """
    Load a connectivity matrix for a given subject.
    Expected path: data/processed/connectivity_matrices/{subject_id}_conn.npy
    """
    conn_path = base_dir / "connectivity_matrices" / f"{subject_id}_conn.npy"
    if not conn_path.exists():
        logger.debug(f"Connectivity matrix not found for {subject_id}: {conn_path}")
        return None
    try:
        matrix = load_numpy(conn_path)
        if matrix is None or matrix.size == 0:
            return None
        return matrix
    except Exception as e:
        logger.error(f"Error loading connectivity for {subject_id}: {e}")
        return None

def compute_subject_metrics(subject_id: str, base_dir: Path) -> Dict[str, Any]:
    """
    Compute graph metrics for a single subject.
    Returns a dictionary with subject_id and metrics, or None if failed.
    """
    try:
        matrix = load_connectivity(subject_id, base_dir)
        if matrix is None:
            return None

        # Ensure matrix is symmetric and zero-diagonal for graph construction
        matrix = np.array(matrix, dtype=float)
        if matrix.shape[0] != matrix.shape[1]:
            logger.warning(f"Non-square matrix for {subject_id}: {matrix.shape}")
            return None

        # Symmetrize (take upper triangle and mirror)
        matrix = (matrix + matrix.T) / 2.0
        np.fill_diagonal(matrix, 0.0)

        # Threshold: keep positive weights, set negative to 0
        matrix = np.maximum(matrix, 0.0)

        # Build graph
        G = nx.from_numpy_array(matrix)

        # Compute metrics
        try:
            degree = calculate_degree_centrality(G)
            global_eff = calculate_global_efficiency(G)
            clustering = calculate_clustering_coefficient(G)
            # Average shortest path length (only for connected components or using all pairs)
            try:
                path_len = calculate_shortest_path_length(G)
            except nx.NetworkXError:
                # Graph might be disconnected or have isolated nodes
                path_len = float("nan")

        except Exception as e:
            logger.error(f"Graph metric calculation failed for {subject_id}: {e}")
            return None

        return {
            "subject_id": subject_id,
            "degree_centrality": float(np.mean(degree)) if len(degree) > 0 else 0.0,
            "global_efficiency": float(global_eff) if not np.isnan(global_eff) else 0.0,
            "clustering_coefficient": float(clustering) if not np.isnan(clustering) else 0.0,
            "average_path_length": float(path_len) if not np.isnan(path_len) else 0.0,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Unexpected error processing {subject_id}: {e}\n{traceback.format_exc()}")
        return {
            "subject_id": subject_id,
            "degree_centrality": 0.0,
            "global_efficiency": 0.0,
            "clustering_coefficient": 0.0,
            "average_path_length": 0.0,
            "status": f"failed: {str(e)}"
        }

def process_subject_wrapper(args: tuple) -> Dict[str, Any]:
    """Wrapper for parallel execution."""
    subject_id, base_dir = args
    return compute_subject_metrics(subject_id, base_dir)

def write_metrics_csv(results: List[Dict[str, Any]], filepath: Path) -> None:
    """Write results to CSV."""
    ensure_dir(filepath)
    fieldnames = ["subject_id", "degree_centrality", "global_efficiency", 
                  "clustering_coefficient", "average_path_length", "status"]
    
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            if res is not None:
                writer.writerow(res)

def write_excluded_log(excluded: List[str], filepath: Path) -> None:
    """Write log of excluded subjects."""
    ensure_dir(filepath)
    with open(filepath, "w") as f:
        for sub in excluded:
            f.write(f"{sub}\n")

def write_status(status: Dict[str, Any], filepath: Path) -> None:
    """Write status JSON."""
    ensure_dir(filepath)
    with open(filepath, "w") as f:
        json.dump(status, f, indent=2, default=str)

@log_operation("compute_graph_metrics_main")
def main() -> None:
    """Main entry point for graph metrics computation."""
    start_time = time.time()
    logger.info("Starting graph metrics computation")

    # Paths
    eligible_file = OUTPUT_DIR / "eligible_subjects.csv"
    base_dir = Path("data/processed")

    # Check prerequisites
    if not eligible_file.exists():
        logger.error(f"Eligible subjects file not found: {eligible_file}")
        write_status({"error": "Eligible subjects file missing", "status": "failed"}, STATUS_FILE)
        sys.exit(1)

    # Read subjects
    try:
        subjects = read_eligible_subjects(eligible_file)
    except Exception as e:
        logger.error(f"Failed to read eligible subjects: {e}")
        write_status({"error": str(e), "status": "failed"}, STATUS_FILE)
        sys.exit(1)

    if not subjects:
        logger.warning("No eligible subjects found")
        write_status({"status": "no_subjects", "count": 0}, STATUS_FILE)
        return

    logger.info(f"Processing {len(subjects)} subjects with {N_JOBS} parallel jobs")

    # Prepare arguments for parallel processing
    args_list = [(sub, base_dir) for sub in subjects]

    # Process subjects in parallel using joblib
    # This is the key optimization for T035
    results = Parallel(n_jobs=N_JOBS, backend="loky", max_nbytes="100M")(
        delayed(process_subject_wrapper)(args) for args in args_list
    )

    # Separate successful and failed
    successful = [r for r in results if r is not None and r.get("status") == "success"]
    failed = [r for r in results if r is not None and r.get("status") != "success"]
    excluded = [sub for sub, _ in args_list if all(r is None or r.get("subject_id") != sub for r in results)]

    # Write outputs
    write_metrics_csv(results, METRICS_FILE)
    write_excluded_log(excluded, EXCLUDED_LOG)

    # Calculate runtime
    end_time = time.time()
    duration = end_time - start_time
    duration_min = duration / 60.0

    # Check target: < 30 min for 100 subjects
    target_met = duration_min < 30.0
    if len(subjects) >= 100:
        logger.info(f"Target runtime check: {duration_min:.2f} min (target < 30 min) -> {'PASS' if target_met else 'FAIL'}")
    else:
        logger.info(f"Runtime: {duration_min:.2f} min for {len(subjects)} subjects")

    status = {
        "status": "completed",
        "subjects_processed": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "excluded": len(excluded),
        "runtime_seconds": duration,
        "runtime_minutes": duration_min,
        "target_met_for_100": target_met if len(subjects) >= 100 else "N/A",
        "n_jobs": N_JOBS
    }

    write_status(status, STATUS_FILE)
    logger.info(f"Graph metrics computation complete. Output: {METRICS_FILE}")
    logger.info(f"Status: {status}")

if __name__ == "__main__":
    main()