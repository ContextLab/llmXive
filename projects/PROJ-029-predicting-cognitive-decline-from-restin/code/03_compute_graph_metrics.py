from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import psutil
import networkx as nx
import pandas as pd
from scipy import sparse

# Project-relative imports based on provided API surface
from utils.logger import get_logger, log_operation
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from utils.io import ensure_dir, load_csv

# Constants
EXIT_CODE_RAM_EXCEEDED = 5
RAM_LIMIT_GB = 7.0
INPUT_CSV = "data/processed/eligible_subjects.csv"
CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
OUTPUT_CSV = "data/processed/graph_metrics.csv"
EXCLUDED_LOG = "data/processed/excluded_subjects.log"
STATUS_FILE = "data/artifacts/graph_metrics_status.json"

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> float:
    """Check current RAM usage in GB. Raises if limit exceeded."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > RAM_LIMIT_GB:
        logger.log(
            operation="memory_limit_exceeded",
            message=f"RAM usage {mem_gb:.2f}GB exceeds limit {RAM_LIMIT_GB}GB",
        )
        raise MemoryError(f"RAM limit exceeded: {mem_gb:.2f}GB > {RAM_LIMIT_GB}GB")
    return mem_gb


def read_eligible_subjects(csv_path: str) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    # Assume column 'subject_id' exists as per T017a output schema
    if 'subject_id' not in df.columns:
        raise ValueError(f"Input CSV missing 'subject_id' column. Found: {df.columns.tolist()}")
    return df['subject_id'].astype(str).tolist()


def load_connectivity(subject_id: str, base_dir: str) -> np.ndarray:
    """
    Load connectivity matrix for a subject.
    Expected file: <base_dir>/<subject_id>_connectivity.npy
    """
    file_path = Path(base_dir) / f"{subject_id}_connectivity.npy"
    if not file_path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found for {subject_id} at {file_path}")
    try:
        mat = np.load(file_path)
        if mat.shape[0] != mat.shape[1]:
            raise ValueError(f"Non-square matrix for {subject_id}: {mat.shape}")
        return mat
    except Exception as e:
        raise RuntimeError(f"Failed to load connectivity for {subject_id}: {e}")


def compute_subject_metrics(adj_matrix: np.ndarray) -> Dict[str, float]:
    """
    Compute graph metrics for a single adjacency matrix.
    Returns dict: {node_degree, global_efficiency, clustering_coeff, path_length}
    """
    # Threshold to create a graph (example: keep edges > 0)
    # Using a simple threshold to avoid dense graph issues if needed,
    # but strictly following the task: calculate from the matrix.
    # We convert to a graph object.
    # Note: The matrix is likely correlation-based. We treat positive values as edges.
    # To ensure graph is valid for path length, we might need to handle disconnected components.
    
    # Create NetworkX graph from adjacency matrix
    G = nx.from_numpy_array(adj_matrix)
    
    # 1. Node Degree (Average)
    # Task asks for "node_degree" - usually means average degree in global metrics context
    degrees = dict(G.degree())
    avg_degree = np.mean(list(degrees.values())) if degrees else 0.0

    # 2. Global Efficiency
    try:
        global_eff = nx.global_efficiency(G)
    except nx.NetworkXError:
        global_eff = 0.0

    # 3. Clustering Coefficient (Average)
    try:
        clustering = nx.average_clustering(G)
    except nx.NetworkXError:
        clustering = 0.0

    # 4. Path Length (Average Shortest Path Length)
    # Only for connected components or average over all reachable pairs
    try:
        if nx.is_connected(G):
            path_len = nx.average_shortest_path_length(G)
        else:
            # For disconnected graphs, average over largest component or handle infinity
            # Standard practice: average over all pairs with finite distance
            lengths = nx.shortest_path_length(G)
            finite_lengths = [l for path in lengths.values() for l in path.values() if l != float('inf')]
            path_len = np.mean(finite_lengths) if finite_lengths else 0.0
    except nx.NetworkXError:
        path_len = 0.0

    return {
        "node_degree": float(avg_degree),
        "global_efficiency": float(global_eff),
        "clustering_coeff": float(clustering),
        "path_length": float(path_len)
    }


def process_subject_wrapper(subject_id: str, connectivity_dir: str) -> Optional[Dict[str, Any]]:
    """
    Process a single subject: load, check memory, compute metrics.
    Returns metrics dict or None if failed.
    """
    try:
        # Check memory before heavy load
        check_memory_usage()
        
        adj = load_connectivity(subject_id, connectivity_dir)
        
        # Check memory after load
        check_memory_usage()
        
        metrics = compute_subject_metrics(adj)
        metrics['subject_id'] = subject_id
        return metrics
    except MemoryError:
        raise
    except Exception as e:
        logger.log(
            operation="subject_processing_failed",
            subject_id=subject_id,
            error=str(e)
        )
        return None


def write_metrics_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write results to CSV with exact schema."""
    ensure_dir(output_path)
    fieldnames = ["subject_id", "node_degree", "global_efficiency", "clustering_coeff", "path_length"]
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Ensure only these keys are written
            writer.writerow({k: row.get(k, 0.0) for k in fieldnames})


def write_excluded_log(excluded_subjects: List[str], log_path: str) -> None:
    """Write excluded subjects log."""
    ensure_dir(log_path)
    with open(log_path, 'w') as f:
        f.write("subject_id,reason\n")
        for sub in excluded_subjects:
            f.write(f"{sub},processing_error\n")


def write_status(status: str, message: str, output_path: str) -> None:
    """Write status JSON."""
    ensure_dir(output_path)
    data = {
        "status": status,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point."""
    logger.log(operation="start", message="Starting graph metrics computation")
    
    start_time = time.time()
    excluded_subjects = []
    results = []
    
    try:
        # 1. Read eligible subjects
        subjects = read_eligible_subjects(INPUT_CSV)
        if not subjects:
            logger.log(operation="no_subjects", message="No eligible subjects found")
            write_status("completed", "No eligible subjects to process", STATUS_FILE)
            return 0
        
        logger.log(operation="subjects_loaded", count=len(subjects))
        
        # 2. Process each subject
        for i, sub_id in enumerate(subjects):
            logger.log(operation="processing_subject", index=i+1, total=len(subjects), subject_id=sub_id)
            
            try:
                res = process_subject_wrapper(sub_id, CONNECTIVITY_DIR)
                if res:
                    results.append(res)
                else:
                    excluded_subjects.append(sub_id)
            except MemoryError:
                logger.log(operation="ram_exceeded", message=f"RAM exceeded for {sub_id}")
                write_status("failed", "RAM limit exceeded", STATUS_FILE)
                return EXIT_CODE_RAM_EXCEEDED
            except Exception as e:
                logger.log(operation="subject_error", subject_id=sub_id, error=str(e))
                excluded_subjects.append(sub_id)
        
        # 3. Write outputs
        write_metrics_csv(results, OUTPUT_CSV)
        write_excluded_log(excluded_subjects, EXCLUDED_LOG)
        
        elapsed = time.time() - start_time
        write_status(
            "completed",
            f"Processed {len(results)} subjects, excluded {len(excluded_subjects)}. Runtime: {elapsed:.2f}s",
            STATUS_FILE
        )
        
        logger.log(operation="finished", success=True, count=len(results))
        return 0
        
    except FileNotFoundError as e:
        logger.log(operation="file_not_found", error=str(e))
        write_status("failed", f"Input file missing: {e}", STATUS_FILE)
        return 1
    except Exception as e:
        logger.log(operation="fatal_error", error=str(e))
        write_status("failed", f"Unexpected error: {e}", STATUS_FILE)
        return 1


if __name__ == "__main__":
    sys.exit(main())