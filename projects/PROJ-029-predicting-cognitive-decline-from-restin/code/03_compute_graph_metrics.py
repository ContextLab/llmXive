from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import psutil
import networkx as nx
from scipy.stats import pearsonr

# Import from existing API surface
from utils.logger import get_logger, log_operation
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_local_efficiency,
    calculate_shortest_path_length,
)
from utils.io import ensure_dir, load_csv, save_csv, load_json, save_json
from utils.stats import calculate_correlation_matrix

logger = get_logger("compute_graph_metrics")

# Constants
MAX_RAM_GB = 7.0
INPUT_CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
OUTPUT_GRAPH_METRICS = Path("data/processed/graph_metrics.csv")
OUTPUT_EXCLUDED_LOG = Path("data/processed/excluded_subjects.log")
OUTPUT_STATUS = Path("data/artifacts/data_gate_status.json")
ELIGIBLE_SUBJECTS_FILE = Path("data/processed/eligible_subjects.csv")

EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_INPUT = 2
EXIT_CODE_NO_ELIGIBLE = 3

def check_memory_usage() -> float:
    """Check current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def read_eligible_subjects() -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.log("error", message=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
        return []
    
    try:
        df = pd.read_csv(ELIGIBLE_SUBJECTS_FILE)
        # Assume column is 'subject_id' or similar; check schema from T017
        col_name = None
        for c in df.columns:
            if 'subject' in c.lower() or 'id' in c.lower():
                col_name = c
                break
        if not col_name:
            logger.log("error", message="Could not identify subject ID column in eligible subjects file")
            return []
        
        subjects = df[col_name].astype(str).tolist()
        logger.log("info", message=f"Loaded {len(subjects)} eligible subjects")
        return subjects
    except Exception as e:
        logger.log("error", message=f"Failed to read eligible subjects: {e}")
        return []

def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """Load connectivity matrix for a subject from disk."""
    # Expected file pattern: data/processed/connectivity_matrices/{subject_id}_connectivity.npy
    # Or potentially .csv; we try .npy first as it's standard for matrices
    npy_path = INPUT_CONNECTIVITY_DIR / f"{subject_id}_connectivity.npy"
    csv_path = INPUT_CONNECTIVITY_DIR / f"{subject_id}_connectivity.csv"
    
    if npy_path.exists():
        try:
            matrix = np.load(npy_path)
            return matrix
        except Exception as e:
            logger.log("warning", message=f"Failed to load numpy matrix for {subject_id}: {e}")
    
    if csv_path.exists():
        try:
            matrix = np.loadtxt(csv_path, delimiter=',')
            return matrix
        except Exception as e:
            logger.log("warning", message=f"Failed to load CSV matrix for {subject_id}: {e}")
    
    logger.log("warning", message=f"No connectivity matrix found for {subject_id} at {npy_path} or {csv_path}")
    return None

def compute_subject_metrics(matrix: np.ndarray, subject_id: str) -> Dict[str, Any]:
    """Compute graph metrics for a single subject's connectivity matrix."""
    if matrix is None or matrix.size == 0:
        return {}

    # Ensure matrix is symmetric and zero-diagonal for graph construction
    # Connectivity matrices from fMRI are often symmetric correlation matrices
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 0.0)
    
    # Thresholding: Keep top 10% of edges to ensure graph is not too sparse/dense
    # This is a common practice in network neuroscience to compare graphs of same density
    threshold = np.percentile(matrix[np.nonzero(matrix)], 90)
    binary_adj = (matrix >= threshold).astype(float)
    
    # Create NetworkX graph
    G = nx.from_numpy_array(binary_adj)
    
    # Check if graph is connected; if not, use largest connected component
    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()
    
    # Calculate metrics
    try:
        degree = calculate_degree_centrality(G)
        global_eff = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        local_eff = calculate_local_efficiency(G)
        
        # Average path length calculation (handle disconnected components if any remain)
        try:
            avg_path = calculate_shortest_path_length(G)
        except nx.NetworkXError:
            avg_path = 0.0
        
        return {
            "subject_id": subject_id,
            "node_degree": float(np.mean(degree)) if degree.size > 0 else 0.0,
            "global_efficiency": float(global_eff) if global_eff is not None else 0.0,
            "clustering_coeff": float(clustering) if clustering is not None else 0.0,
            "path_length": float(avg_path) if avg_path is not None else 0.0,
            "local_efficiency": float(local_eff) if local_eff is not None else 0.0,
        }
    except Exception as e:
        logger.log("error", message=f"Failed to compute metrics for {subject_id}: {e}")
        return {
            "subject_id": subject_id,
            "node_degree": 0.0,
            "global_efficiency": 0.0,
            "clustering_coeff": 0.0,
            "path_length": 0.0,
            "local_efficiency": 0.0,
        }

def process_subject_wrapper(subject_id: str, results: List[Dict[str, Any]]) -> None:
    """Process a single subject and append metrics to results list."""
    # Memory check before processing
    current_ram = check_memory_usage()
    if current_ram > MAX_RAM_GB:
        logger.log("warning", message=f"RAM usage high ({current_ram:.2f} GB) before processing {subject_id}")
    
    matrix = load_connectivity(subject_id)
    metrics = compute_subject_metrics(matrix, subject_id)
    if metrics:
        results.append(metrics)
    
    # Memory check after processing
    current_ram = check_memory_usage()
    if current_ram > MAX_RAM_GB:
        logger.log("warning", message=f"RAM usage high ({current_ram:.2f} GB) after processing {subject_id}")

def write_metrics_csv(results: List[Dict[str, Any]]) -> None:
    """Write graph metrics to CSV file."""
    ensure_dir(OUTPUT_GRAPH_METRICS.parent)
    
    if not results:
        logger.log("warning", message="No results to write to graph metrics CSV")
        # Write empty file with headers
        with open(OUTPUT_GRAPH_METRICS, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "subject_id", "node_degree", "global_efficiency", 
                "clustering_coeff", "path_length", "local_efficiency"
            ])
            writer.writeheader()
        return

    fieldnames = ["subject_id", "node_degree", "global_efficiency", 
                  "clustering_coeff", "path_length", "local_efficiency"]
    
    with open(OUTPUT_GRAPH_METRICS, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, 0.0) for k in fieldnames})
    
    logger.log("info", message=f"Wrote {len(results)} subjects to {OUTPUT_GRAPH_METRICS}")

def write_excluded_log(excluded_subjects: List[str]) -> None:
    """Write excluded subjects to log file."""
    ensure_dir(OUTPUT_EXCLUDED_LOG.parent)
    with open(OUTPUT_EXCLUDED_LOG, 'w') as f:
        for subj in excluded_subjects:
            f.write(f"{subj}\n")
    logger.log("info", message=f"Wrote {len(excluded_subjects)} excluded subjects to log")

def write_status(success: bool, message: str, count: int) -> None:
    """Write status JSON file."""
    ensure_dir(OUTPUT_STATUS.parent)
    status = {
        "task": "compute_graph_metrics",
        "success": success,
        "message": message,
        "subjects_processed": count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(OUTPUT_STATUS, 'w') as f:
        json.dump(status, f, indent=2)
    logger.log("info", message=f"Status written: {message}")

def main() -> int:
    """Main entry point for computing graph metrics."""
    logger.log("start", operation="compute_graph_metrics_main")
    
    # Read eligible subjects
    subjects = read_eligible_subjects()
    if not subjects:
        logger.log("error", message="No eligible subjects found or file missing")
        write_status(False, "No eligible subjects found", 0)
        return EXIT_CODE_NO_ELIGIBLE

    if not INPUT_CONNECTIVITY_DIR.exists():
        logger.log("error", message=f"Connectivity directory not found: {INPUT_CONNECTIVITY_DIR}")
        write_status(False, "Connectivity matrices directory missing", 0)
        return EXIT_CODE_NO_INPUT

    results: List[Dict[str, Any]] = []
    excluded: List[str] = []

    # Process subject-by-subject to stay within RAM limits
    start_time = time.time()
    for i, subj in enumerate(subjects):
        logger.log("progress", message=f"Processing subject {i+1}/{len(subjects)}: {subj}")
        try:
            process_subject_wrapper(subj, results)
        except Exception as e:
            logger.log("error", message=f"Failed to process {subj}: {e}")
            excluded.append(subj)
    
    elapsed = time.time() - start_time
    logger.log("end", operation="compute_graph_metrics_main", duration=elapsed)

    # Write outputs
    write_metrics_csv(results)
    write_excluded_log(excluded)
    
    success = len(results) > 0
    status_msg = f"Processed {len(results)} subjects successfully" if success else "No subjects processed"
    write_status(success, status_msg, len(results))

    if not success:
        return EXIT_CODE_NO_INPUT
    
    return EXIT_CODE_SUCCESS

if __name__ == "__main__":
    sys.exit(main())