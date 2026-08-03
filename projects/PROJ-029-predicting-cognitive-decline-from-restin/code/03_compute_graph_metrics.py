"""
Compute graph-theoretical metrics from connectivity matrices.

Task: T019 [US1]
Input: data/processed/connectivity_matrices/ (from T018)
Output: data/processed/graph_metrics.csv

This script processes subjects one-by-one to stay within 7GB RAM.
It calculates node degree, global efficiency, clustering coefficient,
path length, and local efficiency.
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
import psutil

# Local imports matching the provided API surface
from utils.logger import get_logger, log_operation
from utils.graph import (
    create_graph_from_adjacency,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_local_efficiency,
    calculate_shortest_path_length,
)
from utils.io import load_csv

# --- Configuration ---
MAX_RAM_GB = 7.0
INPUT_DIR = Path("data/processed/connectivity_matrices")
ELIGIBLE_SUBJECTS_FILE = Path("data/processed/eligible_subjects.csv")
OUTPUT_FILE = Path("data/processed/graph_metrics.csv")
EXCLUDED_LOG = Path("data/processed/excluded_subjects.log")
STATUS_FILE = Path("data/artifacts/graph_metrics_status.json")

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> float:
    """Check current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    return mem_gb


def read_eligible_subjects(filepath: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not filepath.exists():
        logger.log("error", message=f"File not found: {filepath}")
        return []
    
    subjects = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming the column is 'subject_id' based on T017 output
            subjects.append(row.get('subject_id', '').strip())
    return subjects


def load_connectivity(filepath: Path) -> np.ndarray:
    """Load a connectivity matrix from a .npy file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Connectivity matrix not found: {filepath}")
    return np.load(filepath)


def compute_subject_metrics(
    subject_id: str, 
    connectivity_matrix: np.ndarray
) -> Dict[str, Any]:
    """
    Compute graph metrics for a single subject.
    
    Returns a dictionary with:
    - subject_id
    - node_degree (mean)
    - global_efficiency
    - clustering_coeff
    - path_length (mean)
    - local_efficiency
    """
    # Create graph from adjacency matrix
    # The graph utility expects a symmetric adjacency matrix
    # We assume the input is already normalized/weighted appropriately
    G = create_graph_from_adjacency(connectivity_matrix)
    
    if G is None or G.number_of_nodes() == 0:
        return {
            "subject_id": subject_id,
            "node_degree": np.nan,
            "global_efficiency": np.nan,
            "clustering_coeff": np.nan,
            "path_length": np.nan,
            "local_efficiency": np.nan
        }

    # Calculate metrics
    degree_centrality = calculate_degree_centrality(G)
    node_degree = float(np.mean(list(degree_centrality.values()))) if degree_centrality else np.nan
    
    global_eff = calculate_global_efficiency(G)
    global_efficiency = float(global_eff) if global_eff is not None else np.nan
    
    clustering = calculate_clustering_coefficient(G)
    clustering_coeff = float(clustering) if clustering is not None else np.nan
    
    # Average shortest path length
    path_lengths = calculate_shortest_path_length(G)
    # Filter out inf/nan values if the graph is disconnected
    valid_paths = [p for p in path_lengths.values() if p is not None and np.isfinite(p)]
    mean_path_length = float(np.mean(valid_paths)) if valid_paths else np.nan
    
    local_eff = calculate_local_efficiency(G)
    local_efficiency = float(local_eff) if local_eff is not None else np.nan

    return {
        "subject_id": subject_id,
        "node_degree": node_degree,
        "global_efficiency": global_efficiency,
        "clustering_coeff": clustering_coeff,
        "path_length": mean_path_length,
        "local_efficiency": local_efficiency
    }


def process_subject_wrapper(
    subject_id: str, 
    input_dir: Path, 
    results: List[Dict[str, Any]], 
    excluded: List[Tuple[str, str]]
) -> None:
    """Process a single subject, handling errors and memory checks."""
    # Memory check before processing
    current_ram = check_memory_usage()
    if current_ram > MAX_RAM_GB:
        logger.log("warning", message=f"RAM usage high: {current_ram:.2f} GB. Continuing but monitoring.")
    
    matrix_file = input_dir / f"{subject_id}_connectivity.npy"
    
    if not matrix_file.exists():
        excluded.append((subject_id, "Connectivity matrix file not found"))
        return

    try:
        conn_matrix = load_connectivity(matrix_file)
        metrics = compute_subject_metrics(subject_id, conn_matrix)
        results.append(metrics)
        
        # Memory check after processing
        current_ram = check_memory_usage()
        if current_ram > MAX_RAM_GB:
            logger.log("warning", message=f"RAM usage spike after {subject_id}: {current_ram:.2f} GB")
            
    except Exception as e:
        excluded.append((subject_id, str(e)))
        logger.log("error", message=f"Failed to process {subject_id}: {e}")


def write_metrics_csv(results: List[Dict[str, Any]], filepath: Path) -> None:
    """Write the computed metrics to a CSV file."""
    if not results:
        logger.log("error", message="No results to write.")
        return

    fieldnames = [
        "subject_id", 
        "node_degree", 
        "global_efficiency", 
        "clustering_coeff", 
        "path_length", 
        "local_efficiency"
    ]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.log("success", message=f"Wrote metrics for {len(results)} subjects to {filepath}")


def write_excluded_log(excluded: List[Tuple[str, str]], filepath: Path) -> None:
    """Write excluded subjects to a log file."""
    with open(filepath, 'w') as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 40 + "\n")
        for subj, reason in excluded:
            f.write(f"Subject: {subj} | Reason: {reason}\n")
    logger.log("info", message=f"Wrote excluded log to {filepath}")


def write_status(success: bool, count: int, total: int, filepath: Path) -> None:
    """Write a status JSON file."""
    status = {
        "operation": "compute_graph_metrics",
        "success": success,
        "subjects_processed": count,
        "subjects_total": total,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    with open(filepath, 'w') as f:
        json.dump(status, f, indent=2)


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point."""
    start_time = time.time()
    logger.log("start", message="Starting graph metrics computation")

    # Check inputs
    if not INPUT_DIR.exists():
        logger.log("error", message=f"Input directory not found: {INPUT_DIR}")
        write_status(False, 0, 0, STATUS_FILE)
        return 1

    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.log("error", message=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
        write_status(False, 0, 0, STATUS_FILE)
        return 1

    subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    if not subjects:
        logger.log("error", message="No eligible subjects found.")
        write_status(False, 0, 0, STATUS_FILE)
        return 1

    logger.log("info", message=f"Processing {len(subjects)} subjects...")

    results: List[Dict[str, Any]] = []
    excluded: List[Tuple[str, str]] = []

    # Process subject-by-subject
    for subj in subjects:
        process_subject_wrapper(subj, INPUT_DIR, results, excluded)

    # Write outputs
    write_metrics_csv(results, OUTPUT_FILE)
    write_excluded_log(excluded, EXCLUDED_LOG)
    
    elapsed = time.time() - start_time
    success = len(results) > 0
    write_status(success, len(results), len(subjects), STATUS_FILE)

    logger.log(
        "complete", 
        message=f"Finished in {elapsed:.2f}s. Processed {len(results)}/{len(subjects)} subjects."
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())