"""
T019: Compute graph-theoretical metrics from connectivity matrices.

Calculates node degree, global efficiency, clustering coefficient, and
shortest path length for every subject. Processes subjects one-by-one
to stay within 7GB RAM limit.

Output: data/processed/graph_metrics.csv
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import networkx as nx
import psutil

# Import from local utils
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir
from utils.graph import calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality

# Configuration
ELIGIBLE_SUBJECTS_FILE = Path("data/processed/eligible_subjects.csv")
CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
OUTPUT_FILE = Path("data/processed/graph_metrics.csv")
EXCLUDED_LOG = Path("data/processed/excluded_graph_metrics.log")
STATUS_FILE = Path("data/artifacts/graph_metrics_status.json")
MAX_MEMORY_GB = 7.0
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def read_eligible_subjects() -> List[str]:
    """Read eligible subjects from CSV."""
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
    
    df = pd.read_csv(ELIGIBLE_SUBJECTS_FILE)
    # Handle both 'subject_id' and 'subject' columns for robustness
    col = 'subject_id' if 'subject_id' in df.columns else 'subject'
    return df[col].astype(str).tolist()


def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """
    Load connectivity matrix for a single subject.
    Returns None if file not found or invalid.
    """
    # Expected filename pattern based on T018 output
    matrix_file = CONNECTIVITY_DIR / f"{subject_id}_connectivity.npy"
    
    if not matrix_file.exists():
        logger.log("missing_matrix", subject=subject_id, file=str(matrix_file))
        return None
    
    try:
        matrix = np.load(matrix_file)
        if matrix.shape[0] != matrix.shape[1]:
            logger.log("invalid_shape", subject=subject_id, shape=str(matrix.shape))
            return None
        return matrix
    except Exception as e:
        logger.log("load_error", subject=subject_id, error=str(e))
        return None


def compute_subject_metrics(subject_id: str, matrix: np.ndarray) -> Dict[str, Any]:
    """
    Compute graph metrics for a single subject's connectivity matrix.
    
    Metrics:
    - node_degree: Average degree centrality
    - global_efficiency: Global efficiency of the graph
    - clustering_coefficient: Average clustering coefficient
    - path_length: Average shortest path length (normalized)
    """
    try:
        # Create a weighted graph from the connectivity matrix
        # Threshold small weights to avoid noise, but keep structure
        threshold = 0.1
        matrix_clean = np.where(matrix > threshold, matrix, 0.0)
        
        # Create graph
        G = nx.from_numpy_array(matrix_clean)
        
        # Remove isolated nodes for path length calculation
        G = G.subgraph([n for n, d in G.degree() if d > 0]).copy()
        
        if len(G.nodes()) < 2:
            logger.log("insufficient_nodes", subject=subject_id, nodes=len(G.nodes()))
            return {
                "subject_id": subject_id,
                "node_degree": np.nan,
                "global_efficiency": np.nan,
                "clustering_coefficient": np.nan,
                "path_length": np.nan
            }

        # Calculate metrics
        # 1. Node Degree (Average)
        degrees = [d for _, d in G.degree()]
        avg_degree = np.mean(degrees) if degrees else 0.0

        # 2. Global Efficiency
        global_eff = calculate_global_efficiency(matrix_clean)

        # 3. Clustering Coefficient
        clust_coef = calculate_clustering_coefficient(matrix_clean)

        # 4. Average Shortest Path Length
        # Use only the largest connected component for meaningful path length
        if nx.is_connected(G):
            path_len = nx.average_shortest_path_length(G)
        else:
            # Use largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            subG = G.subgraph(largest_cc)
            if len(subG.nodes()) > 1:
                path_len = nx.average_shortest_path_length(subG)
            else:
                path_len = np.nan

        return {
            "subject_id": subject_id,
            "node_degree": float(avg_degree),
            "global_efficiency": float(global_eff),
            "clustering_coefficient": float(clust_coef),
            "path_length": float(path_len) if not np.isnan(path_len) else np.nan
        }

    except Exception as e:
        logger.log("computation_error", subject=subject_id, error=str(e), traceback=traceback.format_exc())
        return {
            "subject_id": subject_id,
            "node_degree": np.nan,
            "global_efficiency": np.nan,
            "clustering_coefficient": np.nan,
            "path_length": np.nan
        }


def process_subject_wrapper(subject_id: str) -> Dict[str, Any]:
    """Wrapper to process a single subject and handle errors."""
    start_time = time.time()
    mem_start = check_memory_usage()
    
    result = {
        "subject_id": subject_id,
        "status": "unknown",
        "error": None,
        "duration": 0.0,
        "peak_memory_gb": mem_start
    }
    
    try:
        matrix = load_connectivity(subject_id)
        if matrix is None:
            result["status"] = "skipped_missing_matrix"
            return result
        
        metrics = compute_subject_metrics(subject_id, matrix)
        result.update(metrics)
        result["status"] = "success"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    result["duration"] = time.time() - start_time
    result["peak_memory_gb"] = check_memory_usage()
    
    return result


def write_metrics_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write metrics to CSV file."""
    if not results:
        logger.log("no_results_to_write")
        return
    
    ensure_dir(output_path.parent)
    
    fieldnames = ["subject_id", "node_degree", "global_efficiency", "clustering_coefficient", "path_length"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            row = {k: r.get(k, np.nan) for k in fieldnames}
            # Convert nan to empty string or specific placeholder if needed, 
            # but CSV writer handles floats well.
            writer.writerow(row)
    
    logger.log("metrics_written", path=str(output_path), count=len(results))


def write_excluded_log(excluded: List[Tuple[str, str]], log_path: Path) -> None:
    """Write log of excluded subjects."""
    ensure_dir(log_path.parent)
    with open(log_path, 'w') as f:
        f.write("SubjectID,Reason\n")
        for subj, reason in excluded:
            f.write(f"{subj},{reason}\n")
    logger.log("excluded_log_written", path=str(log_path), count=len(excluded))


def write_status(status: Dict[str, Any], status_path: Path) -> None:
    """Write execution status to JSON."""
    ensure_dir(status_path.parent)
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2, default=str)
    logger.log("status_written", path=str(status_path))


@log_operation("compute_graph_metrics")
def main() -> int:
    """Main entry point."""
    start_time = time.time()
    logger.log("start", message="Beginning graph metrics computation")
    
    # Check memory at start
    initial_mem = check_memory_usage()
    logger.log("initial_memory_gb", value=initial_mem)
    
    if initial_mem > MAX_MEMORY_GB * 0.8:
        logger.log("warning", message=f"High initial memory usage: {initial_mem:.2f}GB")
    
    # 1. Read eligible subjects
    try:
        # Read eligible subjects
        subjects = read_eligible_subjects()
        logger.log("subjects_loaded", count=len(subjects))
    except FileNotFoundError as e:
        logger.log("fatal_error", message=str(e))
        return 1
    
    if not subjects:
        logger.log("fatal_error", message="No eligible subjects found")
        return 1
    
    results = []
    excluded = []
    successful = 0
    failed = 0
    
    # 2. Process subject-by-subject
    for i, subject_id in enumerate(subjects):
        logger.log("processing", index=i+1, total=len(subjects), subject=subject_id)
        
        result = process_subject_wrapper(subject_id)
        
        if result["status"] == "success":
            results.append(result)
            successful += 1
        else:
            excluded.append((subject_id, result.get("status", "unknown")))
            failed += 1
        
        # Memory check every 10 subjects
        if (i + 1) % 10 == 0:
            current_mem = check_memory_usage()
            if current_mem > MAX_MEMORY_GB:
                logger.log("memory_limit_exceeded", current=current_mem, limit=MAX_MEMORY_GB)
                # Continue but log warning
    
    # 3. Write outputs
    if results:
        write_metrics_csv(results, OUTPUT_FILE)
    
    if excluded:
        write_excluded_log(excluded, EXCLUDED_LOG)
    
    # 4. Write status
    total_time = time.time() - start_time
    final_mem = check_memory_usage()
    
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_subjects": len(subjects),
        "successful": successful,
        "failed": failed,
        "excluded": len(excluded),
        "initial_memory_gb": initial_mem,
        "final_memory_gb": final_mem,
        "total_runtime_seconds": total_time,
        "output_file": str(OUTPUT_FILE),
        "excluded_log": str(EXCLUDED_LOG) if excluded else None
    }
    
    write_status(status, STATUS_FILE)
    
    logger.log("complete", 
               total=len(subjects), 
               success=successful, 
               failed=failed, 
               runtime=total_time)
    
    return 0 if successful > 0 else 1


if __name__ == "__main__":
    sys.exit(main())