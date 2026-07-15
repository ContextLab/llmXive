from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import networkx as nx
import psutil

from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_csv, save_csv, load_json, save_json
from utils.graph import create_graph_from_adjacency, calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality

logger = get_logger("compute_graph_metrics")


def check_memory_usage(max_gb: float = 7.0) -> bool:
    """Check if current memory usage is within the limit."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > max_gb:
        logger.log("memory_exceeded", current_gb=mem_gb, limit_gb=max_gb)
        return False
    return True


def read_eligible_subjects(path: str) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    ensure_dir(path)
    subjects = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'subject_id' in row:
                subjects.append(row['subject_id'])
            elif 'participant_id' in row:
                subjects.append(row['participant_id'])
    logger.log("read_eligible_subjects", count=len(subjects), path=path)
    return subjects


def load_connectivity(subject_id: str, base_dir: str) -> Optional[np.ndarray]:
    """
    Load the connectivity matrix for a subject from the preprocessed directory.
    Expects a .npy file named {subject_id}.npy in data/processed/connectivity_matrices/
    """
    conn_path = Path(base_dir) / "connectivity_matrices" / f"{subject_id}.npy"
    if not conn_path.exists():
        logger.log("connectivity_missing", subject_id=subject_id, path=str(conn_path))
        return None
    try:
        matrix = np.load(conn_path)
        return matrix
    except Exception as e:
        logger.log("connectivity_load_error", subject_id=subject_id, error=str(e))
        return None


def compute_subject_metrics(subject_id: str, adjacency_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Compute graph metrics for a single subject's adjacency matrix.
    Metrics: degree, global_efficiency, clustering_coefficient, shortest_path_length.
    """
    # Ensure symmetry and zero diagonal for undirected graph
    adj = adjacency_matrix.copy()
    np.fill_diagonal(adj, 0)
    adj = (adj + adj.T) / 2

    # Create NetworkX graph
    G = create_graph_from_adjacency(adj)

    if G.number_of_nodes() == 0:
        return {"subject_id": subject_id, "error": "empty_graph"}

    # Calculate metrics
    # Degree centrality (average degree)
    degree_dict = calculate_degree_centrality(G)
    avg_degree = np.mean(list(degree_dict.values())) if degree_dict else 0.0

    # Global efficiency
    global_eff = calculate_global_efficiency(G)

    # Clustering coefficient (average local clustering)
    clustering_dict = calculate_clustering_coefficient(G)
    avg_clustering = np.mean(list(clustering_dict.values())) if clustering_dict else 0.0

    # Average shortest path length (only for connected components or finite paths)
    try:
        # nx.average_shortest_path_length handles disconnected graphs by raising if not all pairs connected
        # We compute it on the largest connected component to be robust
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        avg_path_len = nx.average_shortest_path_length(subgraph)
    except (nx.NetworkXError, ZeroDivisionError):
        avg_path_len = float('nan')

    return {
        "subject_id": subject_id,
        "avg_degree": float(avg_degree),
        "global_efficiency": float(global_eff) if not np.isnan(global_eff) else float('nan'),
        "clustering_coefficient": float(avg_clustering),
        "avg_path_length": float(avg_path_len) if not np.isnan(avg_path_len) else float('nan')
    }


def process_subject_wrapper(subject_id: str, base_dir: str) -> Optional[Dict[str, Any]]:
    """Wrapper to process a single subject, handling errors and memory checks."""
    if not check_memory_usage():
        logger.log("skipped_memory_limit", subject_id=subject_id)
        return None

    matrix = load_connectivity(subject_id, base_dir)
    if matrix is None:
        return None

    try:
        metrics = compute_subject_metrics(subject_id, matrix)
        return metrics
    except Exception as e:
        logger.log("metric_calculation_error", subject_id=subject_id, error=str(e))
        return None


def write_metrics_csv(metrics_list: List[Dict[str, Any]], output_path: str) -> None:
    """Write the computed metrics to a CSV file."""
    if not metrics_list:
        logger.log("no_metrics_to_write")
        # Write empty file with headers if no data
        headers = ["subject_id", "avg_degree", "global_efficiency", "clustering_coefficient", "avg_path_length"]
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return

    headers = list(metrics_list[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(metrics_list)
    logger.log("metrics_written", count=len(metrics_list), path=output_path)


def write_excluded_log(excluded_subjects: List[str], output_path: str) -> None:
    """Write a log of excluded subjects."""
    with open(output_path, 'w') as f:
        for subj in excluded_subjects:
            f.write(f"{subj}\n")
    logger.log("excluded_log_written", count=len(excluded_subjects), path=output_path)


def write_status(status: Dict[str, Any], output_path: str) -> None:
    """Write the status JSON file."""
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    logger.log("status_written", path=output_path)


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point for computing graph metrics."""
    start_time = time.time()
    base_dir = Path("data/processed")
    eligible_path = base_dir / "eligible_subjects.csv"
    output_path = base_dir / "graph_metrics.csv"
    excluded_log_path = base_dir / "excluded_graph_metrics.log"
    status_path = Path("data/artifacts") / "graph_metrics_status.json"

    # Check input file
    if not eligible_path.exists():
        logger.log("error", message="eligible_subjects.csv not found")
        return 1

    subjects = read_eligible_subjects(str(eligible_path))
    if not subjects:
        logger.log("error", message="No eligible subjects found")
        return 1

    logger.log("start_processing", count=len(subjects))

    metrics_list = []
    excluded_subjects = []

    for subj in subjects:
        result = process_subject_wrapper(subj, str(base_dir))
        if result:
            metrics_list.append(result)
        else:
            excluded_subjects.append(subj)

    write_metrics_csv(metrics_list, str(output_path))
    write_excluded_log(excluded_subjects, str(excluded_log_path))

    end_time = time.time()
    elapsed = end_time - start_time

    status = {
        "operation": "compute_graph_metrics",
        "subjects_processed": len(subjects),
        "subjects_successful": len(metrics_list),
        "subjects_excluded": len(excluded_subjects),
        "elapsed_seconds": elapsed,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "output_file": str(output_path)
    }
    write_status(status, str(status_path))

    logger.log("complete", elapsed=elapsed, success_count=len(metrics_list))
    return 0


if __name__ == "__main__":
    sys.exit(main())
