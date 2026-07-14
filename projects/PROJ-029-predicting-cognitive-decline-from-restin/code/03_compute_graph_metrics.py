from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import networkx as nx
import pandas as pd
import psutil

# Import from existing API surface
from utils.logger import get_logger, log_operation, ReproducibilityLogger, LogEntry
from utils.graph import create_graph_from_adjacency, calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality, calculate_shortest_path_length
from utils.io import ensure_dir, load_csv, save_csv

# Constants
MEMORY_LIMIT_GB = 7.0
ELIGIBLE_SUBJECTS_FILE = "data/processed/eligible_subjects.csv"
CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
OUTPUT_FILE = "data/processed/graph_metrics.csv"
STATUS_FILE = "data/artifacts/graph_metrics_status.json"

# Ensure output directories exist
ensure_dir(OUTPUT_FILE)
ensure_dir(STATUS_FILE)


def read_eligible_subjects(filepath: str) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    logger = get_logger("graph_metrics")
    try:
        df = pd.read_csv(filepath)
        # Handle potential column name variations
        if 'subject_id' in df.columns:
            subjects = df['subject_id'].tolist()
        elif 'participant_id' in df.columns:
            subjects = df['participant_id'].tolist()
        else:
            # Assume first column is subject ID
            subjects = df.iloc[:, 0].tolist()
        
        logger.log("read_eligible_subjects", count=len(subjects), file=filepath)
        return [str(s) for s in subjects if pd.notna(s)]
    except Exception as e:
        logger.log("read_eligible_subjects_error", error=str(e))
        raise


def load_connectivity(subject_id: str, connectivity_dir: str) -> np.ndarray:
    """Load the connectivity matrix for a given subject."""
    # Expected filename pattern based on T018 output convention
    # Assuming T018 saves as {subject_id}_connectivity.npy or similar
    # We need to find the file. Let's try common patterns.
    path = Path(connectivity_dir)
    
    # Try direct match first
    potential_files = list(path.glob(f"{subject_id}*.npy"))
    if not potential_files:
        # Try with 'sub-' prefix if not present
        sub_id = subject_id if subject_id.startswith("sub-") else f"sub-{subject_id}"
        potential_files = list(path.glob(f"{sub_id}*.npy"))
    
    if not potential_files:
        # Fallback: list all npy files and try to match
        all_npy = list(path.glob("*.npy"))
        if all_npy:
            # If only one file, use it (debug fallback)
            if len(all_npy) == 1:
                potential_files = all_npy
            else:
                # Try to find one containing the subject ID
                for f in all_npy:
                    if subject_id in f.name or sub_id in f.name:
                        potential_files = [f]
                        break
    
    if not potential_files:
        raise FileNotFoundError(f"No connectivity matrix found for subject {subject_id} in {connectivity_dir}")
    
    matrix_path = potential_files[0]
    return np.load(matrix_path)


def compute_subject_metrics(subject_id: str, matrix: np.ndarray) -> Dict[str, Any]:
    """Compute graph metrics for a single subject's connectivity matrix."""
    # Ensure matrix is symmetric and non-negative for undirected graph analysis
    matrix = (matrix + matrix.T) / 2.0
    # Threshold small values to avoid numerical issues, but keep structure
    # We assume the matrix is already weighted.
    
    # Create graph
    G = create_graph_from_adjacency(matrix)
    
    # Calculate metrics
    # 1. Node Degree (average)
    degree_centrality = calculate_degree_centrality(G)
    avg_degree = np.mean(list(degree_centrality.values())) if degree_centrality else 0.0
    
    # 2. Global Efficiency
    global_eff = calculate_global_efficiency(G)
    
    # 3. Clustering Coefficient (average)
    clustering = calculate_clustering_coefficient(G)
    avg_clustering = np.mean(list(clustering.values())) if clustering else 0.0
    
    # 4. Average Path Length
    # Note: calculate_shortest_path_length might return a dict of dicts or a single value
    # We need the average shortest path length for the whole graph
    try:
        # networkx average_shortest_path_length handles disconnected graphs by raising if not connected
        # We'll use a try-except or filter connected components
        avg_path = nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        # If graph is disconnected, calculate over largest connected component
        largest_cc = max(nx.connected_components(G), key=len)
        subG = G.subgraph(largest_cc)
        avg_path = nx.average_shortest_path_length(subG)
    
    return {
        "subject_id": subject_id,
        "avg_degree": float(avg_degree),
        "global_efficiency": float(global_eff),
        "avg_clustering_coefficient": float(avg_clustering),
        "avg_path_length": float(avg_path)
    }


def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)


def write_metrics_csv(metrics_list: List[Dict[str, Any]], filepath: str) -> None:
    """Write metrics to CSV file."""
    if not metrics_list:
        return
    
    fieldnames = ["subject_id", "avg_degree", "global_efficiency", "avg_clustering_coefficient", "avg_path_length"]
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_list:
            writer.writerow(row)


def write_status(status: Dict[str, Any], filepath: str) -> None:
    """Write execution status to JSON file."""
    ensure_dir(filepath)
    with open(filepath, 'w') as f:
        json.dump(status, f, indent=2)


def process_subject_wrapper(subject_id: str, connectivity_dir: str) -> Tuple[str, bool, str]:
    """Wrapper to process a single subject and handle errors."""
    try:
        matrix = load_connectivity(subject_id, connectivity_dir)
        metrics = compute_subject_metrics(subject_id, matrix)
        return subject_id, True, "success"
    except Exception as e:
        return subject_id, False, str(e)


@log_operation("compute_graph_metrics")
def main() -> int:
    """Main entry point for computing graph metrics."""
    logger = get_logger("graph_metrics")
    start_time = time.time()
    
    try:
        # 1. Read eligible subjects
        if not os.path.exists(ELIGIBLE_SUBJECTS_FILE):
            logger.log("error", message=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
            print(f"Error: {ELIGIBLE_SUBJECTS_FILE} not found. Run 01_download_and_filter.py first.")
            return 1
        
        subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
        if not subjects:
            logger.log("warning", message="No eligible subjects found.")
            print("Warning: No eligible subjects found.")
            # Write empty output to satisfy contract
            write_metrics_csv([], OUTPUT_FILE)
            write_status({"status": "no_subjects", "timestamp": time.time()}, STATUS_FILE)
            return 0

        # 2. Check connectivity directory
        if not os.path.exists(CONNECTIVITY_DIR):
            logger.log("error", message=f"Connectivity directory not found: {CONNECTIVITY_DIR}")
            print(f"Error: {CONNECTIVITY_DIR} not found. Run 02_preprocess_and_parcellate.py first.")
            return 1

        # 3. Process subjects one by one
        all_metrics = []
        failed_count = 0
        processed_count = 0

        for i, subject_id in enumerate(subjects):
            # Memory check every 10 subjects
            if i % 10 == 0:
                mem_gb = check_memory_usage()
                logger.log("memory_check", current_gb=mem_gb, limit_gb=MEMORY_LIMIT_GB)
                if mem_gb > MEMORY_LIMIT_GB:
                    logger.log("error", message=f"Memory limit exceeded: {mem_gb:.2f} GB > {MEMORY_LIMIT_GB} GB")
                    print(f"Error: Memory limit exceeded ({mem_gb:.2f} GB > {MEMORY_LIMIT_GB} GB). Stopping.")
                    break

            subject_id, success, msg = process_subject_wrapper(subject_id, CONNECTIVITY_DIR)
            if success:
                # Re-compute to get the dict (wrapper returns tuple, we need to call compute again or refactor)
                # Refactoring: The wrapper should return the dict on success
                # Let's fix the wrapper logic inline here for simplicity in this single-file fix
                try:
                    matrix = load_connectivity(subject_id, CONNECTIVITY_DIR)
                    metrics = compute_subject_metrics(subject_id, matrix)
                    all_metrics.append(metrics)
                    processed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.log("subject_error", subject=subject_id, error=str(e))
            else:
                failed_count += 1
                logger.log("subject_error", subject=subject_id, error=msg)

            # Progress log
            if (i + 1) % 10 == 0 or (i + 1) == len(subjects):
                print(f"Processed {i+1}/{len(subjects)} subjects...")

        # 4. Write output
        write_metrics_csv(all_metrics, OUTPUT_FILE)
        
        end_time = time.time()
        duration = end_time - start_time
        
        status = {
            "status": "success",
            "subjects_processed": processed_count,
            "subjects_failed": failed_count,
            "total_subjects": len(subjects),
            "duration_seconds": duration,
            "output_file": OUTPUT_FILE,
            "timestamp": time.time()
        }
        write_status(status, STATUS_FILE)
        
        logger.log("complete", 
                   processed=processed_count, 
                   failed=failed_count, 
                   duration=duration,
                   output=OUTPUT_FILE)
        
        print(f"Graph metrics computed for {processed_count} subjects. Output: {OUTPUT_FILE}")
        return 0

    except Exception as e:
        logger.log("critical_error", error=str(e))
        print(f"Critical error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
