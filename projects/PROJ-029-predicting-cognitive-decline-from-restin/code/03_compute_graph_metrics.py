"""
Compute graph-theoretical metrics from preprocessed connectivity matrices.

This script processes subjects one-by-one (streaming) to stay within memory limits.
It calculates node degree, global efficiency, clustering coefficient, and path length.

Outputs:
    data/processed/graph_metrics.csv
    data/processed/processed_subjects.csv
    data/processed/excluded_subjects.log (updated with failures)
"""
from __future__ import annotations

import csv
import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import networkx as nx

# Import from local utils
from utils.logger import get_logger, log_operation
from utils.graph import calculate_degree_centrality, calculate_global_efficiency, calculate_clustering_coefficient
from utils.io import load_csv, ensure_dir

# Constants
RAM_LIMIT_GB = 6.0  # Soft limit to stay under 7GB
EXIT_CODE_MEMORY_ERROR = 4
EXIT_CODE_PROCESSING_FAILURE = 5
EXIT_CODE_SUCCESS = 0

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RAW = PROJECT_ROOT / "data" / "raw"

ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED / "eligible_subjects.csv"
CONNECTIVITY_DIR = DATA_PROCESSED / "connectivity_matrices"
GRAPH_METRICS_FILE = DATA_PROCESSED / "graph_metrics.csv"
PROCESSED_SUBJECTS_FILE = DATA_PROCESSED / "processed_subjects.csv"
EXCLUDED_LOG_FILE = DATA_PROCESSED / "excluded_subjects.log"

logger = get_logger("compute_graph_metrics")

def check_memory_usage() -> float:
    """Check current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    return mem_gb

def read_eligible_subjects() -> List[Dict[str, Any]]:
    """Read the list of eligible subjects from the CSV."""
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.log("error", message=f"File not found: {ELIGIBLE_SUBJECTS_FILE}")
        sys.exit(EXIT_CODE_PROCESSING_FAILURE)
    
    rows = load_csv(str(ELIGIBLE_SUBJECTS_FILE))
    return rows

def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """
    Load connectivity matrix for a single subject.
    Expects a .npy file in the connectivity_matrices directory.
    """
    # Try to find the file. It might be named {subject_id}.npy or similar.
    # Based on T018, we assume the output is a numpy array saved as .npy.
    # We look for files matching the subject_id pattern.
    
    if not CONNECTIVITY_DIR.exists():
        logger.log("error", message=f"Connectivity directory not found: {CONNECTIVITY_DIR}")
        return None

    # Look for a file that matches the subject_id
    # Common patterns: sub-{subject_id}_conn.npy, {subject_id}.npy
    possible_names = [
        f"{subject_id}.npy",
        f"sub-{subject_id}_conn.npy",
        f"connectivity_{subject_id}.npy"
    ]
    
    found_file = None
    for name in possible_names:
        p = CONNECTIVITY_DIR / name
        if p.exists():
            found_file = p
            break
    
    # If not found by name, try to find any .npy file if the directory only has one
    # or if the naming convention is different (e.g., just a list of files)
    if not found_file:
        files = list(CONNECTIVITY_DIR.glob("*.npy"))
        # If there's exactly one file and we haven't matched by name, maybe it's the one?
        # But safer to assume strict naming. If not found, return None.
        # However, T018 might save them with a specific key. Let's assume standard naming.
        pass

    if found_file:
        try:
            mat = np.load(found_file)
            return mat
        except Exception as e:
            logger.log("error", message=f"Failed to load {found_file}: {e}")
            return None
    
    # Fallback: If the file naming is unknown, try to load based on index or order?
    # No, we must match by ID.
    logger.log("warning", message=f"No connectivity file found for {subject_id}")
    return None

def compute_subject_metrics(subject_id: str, conn_matrix: np.ndarray) -> Dict[str, Any]:
    """Compute graph metrics for a single subject."""
    # Validate matrix
    if conn_matrix.shape[0] != conn_matrix.shape[1]:
        raise ValueError(f"Connectivity matrix for {subject_id} is not square: {conn_matrix.shape}")
    
    # Create graph from adjacency matrix
    # Assuming symmetric matrix for undirected graph (standard for rs-fMRI)
    G = nx.from_numpy_array(conn_matrix)
    
    # Calculate metrics
    # 1. Node Degree (average degree centrality)
    degree_vals = calculate_degree_centrality(conn_matrix)
    avg_degree = float(np.mean(degree_vals))
    
    # 2. Global Efficiency
    global_eff = calculate_global_efficiency(conn_matrix)
    
    # 3. Clustering Coefficient
    clustering_vals = calculate_clustering_coefficient(conn_matrix)
    avg_clustering = float(np.mean(clustering_vals))
    
    # 4. Path Length (Average shortest path length)
    # Handle disconnected graphs: nx.average_shortest_path_length raises on disconnected
    # We use the largest connected component for this metric if the graph is disconnected
    try:
        if not nx.is_connected(G):
            # Use the largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            G_cc = G.subgraph(largest_cc)
            path_len = float(nx.average_shortest_path_length(G_cc))
        else:
            path_len = float(nx.average_shortest_path_length(G))
    except Exception:
        # Fallback if calculation fails (e.g., single node)
        path_len = float('nan')
    
    return {
        "subject_id": subject_id,
        "node_degree": avg_degree,
        "global_efficiency": global_eff,
        "clustering_coeff": avg_clustering,
        "path_length": path_len
    }

def process_subject_wrapper(subject_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Wrapper to process a single subject with memory checks and error handling.
    Returns (metrics_dict, error_message).
    """
    try:
        current_ram = check_memory_usage()
        if current_ram > RAM_LIMIT_GB:
            return None, f"Memory limit exceeded before processing: {current_ram:.2f} GB"

        conn_matrix = load_connectivity(subject_id)
        if conn_matrix is None:
            return None, f"Connectivity matrix not found or invalid for {subject_id}"

        metrics = compute_subject_metrics(subject_id, conn_matrix)
        
        # Force garbage collection after heavy computation
        gc.collect()
        
        return metrics, None

    except MemoryError as e:
        return None, f"MemoryError: {str(e)}"
    except Exception as e:
        return None, f"Processing Failure: {type(e).__name__}: {str(e)}"

def write_metrics_csv(metrics_list: List[Dict[str, Any]]) -> None:
    """Write the final graph metrics to CSV."""
    ensure_dir(GRAPH_METRICS_FILE.parent)
    fieldnames = ["subject_id", "node_degree", "global_efficiency", "clustering_coeff", "path_length"]
    
    with open(GRAPH_METRICS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics_list:
            writer.writerow(m)
    
    logger.log("success", message=f"Wrote {len(metrics_list)} metrics to {GRAPH_METRICS_FILE}")

def write_processed_subjects(subject_ids: List[str]) -> None:
    """Write the list of successfully processed subjects."""
    ensure_dir(PROCESSED_SUBJECTS_FILE.parent)
    with open(PROCESSED_SUBJECTS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["subject_id"])
        for sid in subject_ids:
            writer.writerow([sid])
    
    logger.log("success", message=f"Wrote {len(subject_ids)} processed subjects to {PROCESSED_SUBJECTS_FILE}")

def write_excluded_log(excluded_entries: List[Dict[str, str]]) -> None:
    """Append or write excluded subjects to the log."""
    ensure_dir(EXCLUDED_LOG_FILE.parent)
    # Check if file exists to decide on writing header
    file_exists = EXCLUDED_LOG_FILE.exists()
    
    with open(EXCLUDED_LOG_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["subject_id", "reason"])
        if not file_exists:
            writer.writeheader()
        for entry in excluded_entries:
            writer.writerow(entry)

@log_operation
def main() -> int:
    """Main entry point for graph metrics computation."""
    start_time = time.time()
    logger.log("start", message="Starting graph metrics computation")

    # 1. Read eligible subjects
    eligible_subjects = read_eligible_subjects()
    if not eligible_subjects:
        logger.log("error", message="No eligible subjects found")
        return EXIT_CODE_PROCESSING_FAILURE

    logger.log("info", message=f"Found {len(eligible_subjects)} eligible subjects")

    metrics_list = []
    processed_ids = []
    excluded_entries = []

    # 2. Process subject-by-subject (streaming)
    for i, row in enumerate(eligible_subjects):
        subject_id = row.get("subject_id") or row.get("id")
        if not subject_id:
            logger.log("warning", message=f"Skipping row {i}: missing subject_id")
            continue

        logger.log("processing", subject_id=subject_id, step=f"{i+1}/{len(eligible_subjects)}")
        
        metrics, error = process_subject_wrapper(subject_id)
        
        if error:
            logger.log("error", message=f"Failed {subject_id}: {error}")
            excluded_entries.append({"subject_id": subject_id, "reason": error})
            # CRITICAL: If any subject fails, we must exit with non-zero code per spec
            # But we also need to write what we have so far? 
            # Spec says: "The output ... must contain exactly the subjects ... or the script must fail"
            # And "exit with a non-zero error code".
            # We will write partial results and excluded log, then exit.
            break
        else:
            metrics_list.append(metrics)
            processed_ids.append(subject_id)

    # 3. Write outputs
    if metrics_list:
        write_metrics_csv(metrics_list)
        write_processed_subjects(processed_ids)
    
    if excluded_entries:
        write_excluded_log(excluded_entries)

    elapsed = time.time() - start_time
    logger.log("end", message=f"Completed in {elapsed:.2f}s. Processed {len(processed_ids)}, Failed {len(excluded_entries)}")

    # 4. Determine exit code
    if excluded_entries:
        # If we encountered errors, exit with failure code
        # Check if it was a memory error specifically
        for entry in excluded_entries:
            if "MemoryError" in entry["reason"]:
                return EXIT_CODE_MEMORY_ERROR
        return EXIT_CODE_PROCESSING_FAILURE
    
    return EXIT_CODE_SUCCESS

if __name__ == "__main__":
    sys.exit(main())