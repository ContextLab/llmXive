"""Compute graph theoretical metrics from connectivity matrices.

This script reads the list of eligible subjects, loads their preprocessed
connectivity matrices, and calculates node degree, global efficiency,
clustering coefficient, and average path length for each subject.

It processes subjects one-by-one to stay within the 7GB RAM limit.
It uses joblib for parallel processing to reduce runtime.
"""
from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import networkx as nx
from joblib import Parallel, delayed
import psutil

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.io import ensure_dir, load_csv
from utils.logger import get_logger, log_operation

# Configuration
CONNECTIVITY_DIR = PROJECT_ROOT / "data" / "processed" / "connectivity_matrices"
ELIGIBLE_SUBJECTS_FILE = PROJECT_ROOT / "data" / "processed" / "eligible_subjects.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "graph_metrics.csv"
RAM_LIMIT_GB = 7.0
N_JOBS = 2

logger = get_logger("graph_metrics")


def read_eligible_subjects(filepath: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not filepath.exists():
        logger.log("error", message=f"Eligible subjects file not found: {filepath}")
        return []
    subjects = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential variations in column name
            subj_id = row.get('subject_id') or row.get('subject') or row.get('bids_id')
            if subj_id:
                subjects.append(str(subj_id))
    logger.log("info", operation="read_eligible_subjects", count=len(subjects))
    return subjects


def load_connectivity(subject_id: str) -> np.ndarray:
    """Load connectivity matrix for a subject.

    Expects a .npy or .csv file in CONNECTIVITY_DIR named <subject_id>.npy or .csv.
    """
    possible_paths = [
        CONNECTIVITY_DIR / f"{subject_id}.npy",
        CONNECTIVITY_DIR / f"{subject_id}.csv",
        CONNECTIVITY_DIR / subject_id / "connectivity.npy",
        CONNECTIVITY_DIR / subject_id / "connectivity.csv",
    ]

    for p in possible_paths:
        if p.exists():
            if p.suffix == '.npy':
                return np.load(p)
            elif p.suffix == '.csv':
                return np.loadtxt(p, delimiter=',')
    
    # Fallback: try to find any file matching subject_id in subdirectories
    if CONNECTIVITY_DIR.exists():
        for item in CONNECTIVITY_DIR.rglob("*"):
            if subject_id in item.name and (item.suffix in ['.npy', '.csv']):
                if item.suffix == '.npy':
                    return np.load(item)
                else:
                    return np.loadtxt(item, delimiter=',')

    logger.log("warning", operation="load_connectivity", subject_id=subject_id, message="File not found")
    return None


def compute_subject_metrics(subject_id: str) -> Dict[str, Any]:
    """Compute graph metrics for a single subject."""
    matrix = load_connectivity(subject_id)
    
    if matrix is None:
        return {
            "subject_id": subject_id,
            "degree_mean": np.nan,
            "global_efficiency": np.nan,
            "clustering_coeff": np.nan,
            "avg_path_length": np.nan,
            "status": "missing_matrix"
        }

    try:
        # Ensure symmetric and zero diagonal for undirected graph
        matrix = np.array(matrix)
        matrix = (matrix + matrix.T) / 2.0
        np.fill_diagonal(matrix, 0)

        # Create graph
        G = nx.from_numpy_array(matrix)

        # Calculate metrics
        # 1. Node Degree (Mean)
        degrees = dict(G.degree())
        degree_mean = np.mean(list(degrees.values()))

        # 2. Global Efficiency
        # NetworkX raises NetworkXError if graph is disconnected for average shortest path
        # Global efficiency is defined for disconnected graphs (sum of 1/d)
        try:
            global_eff = nx.global_efficiency(G)
        except Exception:
            global_eff = np.nan

        # 3. Clustering Coefficient (Mean)
        try:
            clustering = nx.average_clustering(G)
        except Exception:
            clustering = np.nan

        # 4. Average Path Length
        # For disconnected graphs, nx.average_shortest_path_length raises
        # We use a weighted average or just the largest connected component
        try:
            # Only compute on largest connected component to avoid infinity
            if nx.is_connected(G):
                avg_path = nx.average_shortest_path_length(G)
            else:
                largest_cc = max(nx.connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc)
                avg_path = nx.average_shortest_path_length(subgraph)
        except Exception:
            avg_path = np.nan

        return {
            "subject_id": subject_id,
            "degree_mean": float(degree_mean),
            "global_efficiency": float(global_eff),
            "clustering_coeff": float(clustering),
            "avg_path_length": float(avg_path),
            "status": "success"
        }

    except Exception as e:
        logger.log("error", operation="compute_subject_metrics", subject_id=subject_id, error=str(e))
        return {
            "subject_id": subject_id,
            "degree_mean": np.nan,
            "global_efficiency": np.nan,
            "clustering_coeff": np.nan,
            "avg_path_length": np.nan,
            "status": f"error: {str(e)}"
        }


def process_subject_wrapper(args: tuple) -> Dict[str, Any]:
    """Wrapper for parallel processing to handle arguments correctly."""
    subject_id, _ = args
    return compute_subject_metrics(subject_id)


def write_metrics_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write results to CSV."""
    ensure_dir(output_path.parent)
    fieldnames = ["subject_id", "degree_mean", "global_efficiency", "clustering_coeff", "avg_path_length", "status"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Ensure all keys exist, fill missing with NaN
            safe_row = {k: row.get(k, np.nan) for k in fieldnames}
            writer.writerow(safe_row)
    
    logger.log("info", operation="write_metrics_csv", output=str(output_path), count=len(results))


def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)


@log_operation("compute_graph_metrics")
def main() -> int:
    """Main entry point."""
    start_time = time.time()
    logger.log("start", operation="main", ram_limit_gb=RAM_LIMIT_GB)

    # 1. Read eligible subjects
    subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    if not subjects:
        logger.log("warning", message="No eligible subjects found.")
        # Write empty file with headers
        write_metrics_csv([], OUTPUT_FILE)
        return 0

    logger.log("info", message=f"Processing {len(subjects)} subjects with {N_JOBS} jobs.")

    # 2. Process subjects
    # Use joblib for parallelization as requested in T035
    # We pass a list of tuples to match the wrapper signature
    subject_args = [(s, None) for s in subjects]
    
    # Check memory before starting
    mem_before = check_memory_usage()
    logger.log("info", operation="memory_check", memory_gb=mem_before)

    results = Parallel(n_jobs=N_JOBS, verbose=10)(
        delayed(process_subject_wrapper)(args) for args in subject_args
    )

    # 3. Check memory after
    mem_after = check_memory_usage()
    logger.log("info", operation="memory_check_post", memory_gb=mem_after, delta=mem_after - mem_before)

    # 4. Write results
    write_metrics_csv(results, OUTPUT_FILE)

    elapsed = time.time() - start_time
    logger.log("complete", operation="main", elapsed_seconds=elapsed, output=str(OUTPUT_FILE))
    
    print(f"Graph metrics computed in {elapsed:.2f} seconds. Output: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())