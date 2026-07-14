from __future__ import annotations

import csv
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import networkx as nx
import psutil
import pandas as pd

# Import from project utils
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_csv, load_csv
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)

# Constants
RAM_LIMIT_GB = 7.0
CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")
EXCLUDED_LOG_PATH = Path("data/processed/excluded_subjects.log")
STATUS_PATH = Path("data/artifacts/graph_metrics_status.json")

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)


def read_eligible_subjects() -> List[str]:
    """Read eligible subject IDs from the filtered CSV."""
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        logger.log("error", message=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
    
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    # Ensure we get a list of strings from the subject_id column
    if "subject_id" not in df.columns:
        # Fallback if column name differs, though spec implies subject_id
        col = df.columns[0]
        logger.log("warning", message=f"Column 'subject_id' not found. Using '{col}' instead.")
        return [str(x) for x in df[col].tolist()]
    
    return [str(x) for x in df["subject_id"].tolist()]


def load_connectivity(subject_id: str) -> Optional[np.ndarray]:
    """Load the connectivity matrix for a specific subject."""
    # Expecting file naming convention: sub-<id>_desc-connectivity.npy or similar
    # Based on T018 output description: data/processed/connectivity_matrices/
    # We try common patterns.
    patterns = [
        f"sub-{subject_id}_desc-connectivity.npy",
        f"sub-{subject_id}_connectivity.npy",
        f"{subject_id}_connectivity.npy",
        f"sub-{subject_id}_func_desc-connectivity.npy",
    ]
    
    for pattern in patterns:
        file_path = CONNECTIVITY_DIR / pattern
        if file_path.exists():
            try:
                matrix = np.load(file_path)
                return matrix
            except Exception as e:
                logger.log("warning", message=f"Failed to load {file_path}: {e}")
                continue
    
    # Check if directory exists and list files for debugging if not found
    if not CONNECTIVITY_DIR.exists():
        logger.log("error", message=f"Connectivity directory not found: {CONNECTIVITY_DIR}")
        return None
        
    logger.log("warning", message=f"No connectivity file found for subject {subject_id}")
    return None


def compute_subject_metrics(subject_id: str, connectivity_matrix: np.ndarray) -> Dict[str, Any]:
    """Compute graph metrics for a single subject's connectivity matrix."""
    metrics = {
        "subject_id": subject_id,
    }
    
    # Create graph from adjacency matrix
    # Ensure matrix is symmetric for undirected graph (common in rs-fMRI)
    adj_matrix = (connectivity_matrix + connectivity_matrix.T) / 2.0
    
    # Threshold to remove weak connections (optional, but good for stability)
    # Using a small threshold to avoid fully disconnected graphs if data is noisy
    threshold = 0.0 
    adj_matrix[adj_matrix < threshold] = 0.0
    
    np.fill_diagonal(adj_matrix, 0.0) # Remove self-loops
    
    G = nx.from_numpy_array(adj_matrix)
    
    # Check if graph is valid (has nodes)
    if G.number_of_nodes() == 0:
        raise ValueError("Graph has no nodes.")
    
    # Calculate metrics
    try:
        # Degree Centrality (mean)
        degree_centrality = calculate_degree_centrality(G)
        metrics["mean_degree_centrality"] = float(np.mean(degree_centrality)) if degree_centrality.size > 0 else 0.0
        metrics["max_degree_centrality"] = float(np.max(degree_centrality)) if degree_centrality.size > 0 else 0.0
        
        # Global Efficiency
        global_eff = calculate_global_efficiency(G)
        metrics["global_efficiency"] = float(global_eff) if global_eff is not None else 0.0
        
        # Clustering Coefficient (mean)
        clustering = calculate_clustering_coefficient(G)
        metrics["mean_clustering_coefficient"] = float(np.mean(clustering)) if clustering.size > 0 else 0.0
        
        # Average Path Length
        # Use average shortest path length. If graph is disconnected, use largest connected component
        if not nx.is_connected(G):
            largest_cc = max(nx.connected_components(G), key=len)
            G_sub = G.subgraph(largest_cc)
            avg_path = nx.average_shortest_path_length(G_sub)
        else:
            avg_path = nx.average_shortest_path_length(G)
        metrics["average_path_length"] = float(avg_path)
        
    except Exception as e:
        logger.log("error", message=f"Failed to compute metrics for {subject_id}: {e}")
        # Return zeros or NaNs for failed metrics
        metrics["mean_degree_centrality"] = np.nan
        metrics["global_efficiency"] = np.nan
        metrics["mean_clustering_coefficient"] = np.nan
        metrics["average_path_length"] = np.nan
    
    return metrics


def process_subject_wrapper(subject_id: str) -> Optional[Dict[str, Any]]:
    """Wrapper to process a single subject, handling memory and errors."""
    mem_before = check_memory_usage()
    if mem_before > RAM_LIMIT_GB * 0.9:
        logger.log("warning", message=f"Memory usage high ({mem_before:.2f}GB) before processing {subject_id}")
    
    try:
        matrix = load_connectivity(subject_id)
        if matrix is None:
            logger.log("warning", message=f"Skipping {subject_id}: No connectivity matrix found.")
            return None
        
        result = compute_subject_metrics(subject_id, matrix)
        return result
    except Exception as e:
        logger.log("error", message=f"Error processing subject {subject_id}: {e}")
        return None
    finally:
        mem_after = check_memory_usage()
        # Force garbage collection to help with memory limits
        import gc
        gc.collect()


def write_metrics_csv(results: List[Dict[str, Any]], output_path: Path):
    """Write computed metrics to CSV."""
    if not results:
        logger.log("warning", message="No results to write.")
        # Create empty file with headers if possible, or just touch it
        ensure_dir(output_path)
        with open(output_path, 'w', newline='') as f:
            f.write("subject_id,mean_degree_centrality,global_efficiency,mean_clustering_coefficient,average_path_length\n")
        return

    fieldnames = list(results[0].keys())
    ensure_dir(output_path)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.log("success", message=f"Wrote metrics for {len(results)} subjects to {output_path}")


def write_excluded_log(excluded_ids: List[str], log_path: Path):
    """Write log of excluded subjects."""
    ensure_dir(log_path)
    with open(log_path, 'w') as f:
        for sid in excluded_ids:
            f.write(f"{sid}\n")
    logger.log("info", message=f"Wrote excluded subjects log to {log_path}")


def write_status(status: Dict[str, Any], path: Path):
    """Write status JSON."""
    ensure_dir(path)
    with open(path, 'w') as f:
        json.dump(status, f, indent=2)
    logger.log("info", message=f"Wrote status to {path}")


def main():
    """Main entry point for graph metrics computation."""
    logger.log("start", message="Starting graph metrics computation")
    start_time = time.time()
    logger.log("start", message="Beginning graph metrics computation")
    
    try:
        # 1. Read eligible subjects
        subject_ids = read_eligible_subjects()
        logger.log("info", message=f"Found {len(subject_ids)} eligible subjects")
        
        if not subject_ids:
            logger.log("error", message="No eligible subjects found.")
            write_status({"status": "error", "message": "No eligible subjects"}, STATUS_PATH)
            sys.exit(1)
        
        results = []
        excluded_ids = []
        
        # 2. Process subject-by-subject to stay within RAM limits
        for i, sid in enumerate(subject_ids):
            logger.log("progress", message=f"Processing subject {i+1}/{len(subject_ids)}: {sid}")
            
            # Check memory periodically
            if i > 0 and i % 10 == 0:
                current_mem = check_memory_usage()
                logger.log("info", message=f"Current memory usage: {current_mem:.2f} GB")
                if current_mem > RAM_LIMIT_GB:
                    logger.log("error", message=f"Memory limit exceeded ({current_mem:.2f}GB > {RAM_LIMIT_GB}GB). Stopping.")
                    break
            
            result = process_subject_wrapper(sid)
            if result:
                results.append(result)
            else:
                excluded_ids.append(sid)
        
        # 3. Write outputs
        write_metrics_csv(results, GRAPH_METRICS_PATH)
        
        if excluded_ids:
            write_excluded_log(excluded_ids, EXCLUDED_LOG_PATH)
        
        elapsed = time.time() - start_time
        status = {
            "status": "success",
            "subjects_processed": len(results),
            "subjects_excluded": len(excluded_ids),
            "elapsed_seconds": elapsed,
            "peak_memory_gb": check_memory_usage()
        }
        write_status(status, STATUS_PATH)
        
        logger.log("finish", message=f"Completed in {elapsed:.2f}s. Processed {len(results)} subjects.")
        
    except Exception as e:
        logger.log("fatal", message=f"Critical error: {e}")
        write_status({"status": "error", "message": str(e)}, STATUS_PATH)
        sys.exit(1)


if __name__ == "__main__":
    main()