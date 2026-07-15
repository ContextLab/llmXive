"""
T019: Compute graph metrics for each subject's connectivity matrix.

Calculates node degree, global efficiency, clustering coefficient, and
average shortest path length. Processes subject-by-subject to respect
the 7GB RAM limit.
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
import networkx as nx
import psutil

# Import from local utils
from utils.logger import get_logger, log_operation
from utils.graph import calculate_degree_centrality, calculate_global_efficiency
from utils.graph import calculate_clustering_coefficient, calculate_shortest_path_length
from utils.io import load_csv, save_csv, ensure_dir

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
CONNECTIVITY_DIR = DATA_PROCESSED / "connectivity_matrices"
OUTPUT_CSV = DATA_PROCESSED / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED / "excluded_subjects.log"
STATUS_FILE = DATA_PROCESSED / "graph_metrics_status.json"

logger = get_logger("compute_graph_metrics")

def check_memory_usage(max_gb: float = 7.0) -> bool:
    """Check if current process memory usage is below the limit."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > max_gb:
        logger.log(
            "memory_warning",
            operation="check_memory_usage",
            current_gb=mem_gb,
            limit_gb=max_gb,
            status="exceeded"
        )
        return False
    return True

def read_eligible_subjects(file_path: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not file_path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {file_path}")
    
    rows = load_csv(file_path)
    # Expecting a 'subject_id' column based on T017 contract
    subject_ids = [row.get("subject_id", row.get("id", "")) for row in rows]
    return [s for s in subject_ids if s]

def load_connectivity(subject_id: str, connectivity_dir: Path) -> Optional[np.ndarray]:
    """Load a subject's connectivity matrix from disk."""
    # Expected filename pattern: sub-<id>_connectivity.npy
    matrix_file = connectivity_dir / f"sub-{subject_id}_connectivity.npy"
    
    if not matrix_file.exists():
        # Fallback check for other potential naming conventions
        matrix_file = connectivity_dir / f"{subject_id}_connectivity.npy"
        if not matrix_file.exists():
            logger.log(
                "file_not_found",
                operation="load_connectivity",
                subject_id=subject_id,
                path=str(matrix_file)
            )
            return None
    
    try:
        data = np.load(matrix_file)
        return data
    except Exception as e:
        logger.log(
            "load_error",
            operation="load_connectivity",
            subject_id=subject_id,
            error=str(e)
        )
        return None

def compute_subject_metrics(
    connectivity_matrix: np.ndarray,
    subject_id: str
) -> Dict[str, Any]:
    """
    Compute graph metrics for a single connectivity matrix.
    
    Metrics:
    - degree: Mean node degree
    - global_efficiency: Global efficiency of the graph
    - clustering_coefficient: Mean local clustering coefficient
    - avg_path_length: Average shortest path length (over connected components)
    """
    # Ensure matrix is symmetric and float
    matrix = np.array(connectivity_matrix, dtype=float)
    if not np.allclose(matrix, matrix.T):
        matrix = (matrix + matrix.T) / 2.0
    
    # Create NetworkX graph
    # Thresholding: Keep edges with weight > 0 (or a small epsilon)
    # For this implementation, we use the raw weights but handle zeros
    np.fill_diagonal(matrix, 0) # Remove self-loops
    
    # Create graph from adjacency matrix
    G = nx.from_numpy_array(matrix)
    
    # Remove isolated nodes if any (though they contribute 0 to degree)
    # We keep them for degree calculation but they might affect path length
    # Calculate metrics
    metrics = {
        "subject_id": subject_id,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges()
    }
    
    try:
        # 1. Mean Degree
        degrees = [d for _, d in G.degree()]
        metrics["degree"] = float(np.mean(degrees)) if degrees else 0.0
        
        # 2. Global Efficiency
        # NetworkX global_efficiency handles disconnected graphs correctly
        metrics["global_efficiency"] = float(nx.global_efficiency(G))
        
        # 3. Clustering Coefficient (Mean)
        metrics["clustering_coefficient"] = float(nx.average_clustering(G))
        
        # 4. Average Shortest Path Length
        # Only calculate over the largest connected component or all if connected
        # If graph is disconnected, nx.average_shortest_path_length raises NetworkXError
        # We calculate for the largest connected component to be robust
        if nx.is_connected(G):
            metrics["avg_path_length"] = float(nx.average_shortest_path_length(G))
        else:
            # Fallback: largest connected component
            try:
                largest_cc = max(nx.connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc)
                metrics["avg_path_length"] = float(nx.average_shortest_path_length(subgraph))
            except Exception:
                metrics["avg_path_length"] = np.nan
                
    except Exception as e:
        logger.log(
            "metric_calculation_error",
            operation="compute_subject_metrics",
            subject_id=subject_id,
            error=str(e)
        )
        # Return NaNs for failed metrics
        metrics["degree"] = np.nan
        metrics["global_efficiency"] = np.nan
        metrics["clustering_coefficient"] = np.nan
        metrics["avg_path_length"] = np.nan

    return metrics

def process_subject_wrapper(
    subject_id: str,
    connectivity_dir: Path,
    results: List[Dict[str, Any]],
    excluded_log: List[str]
) -> None:
    """Wrapper to process a single subject and handle errors."""
    try:
        # Check memory before processing
        if not check_memory_usage():
            excluded_log.append(f"{subject_id}: Memory limit exceeded")
            return

        matrix = load_connectivity(subject_id, connectivity_dir)
        if matrix is None:
            excluded_log.append(f"{subject_id}: Connectivity matrix not found")
            return

        metrics = compute_subject_metrics(matrix, subject_id)
        results.append(metrics)
        
        logger.log(
            "subject_processed",
            operation="process_subject_wrapper",
            subject_id=subject_id,
            status="success"
        )

    except Exception as e:
        logger.log(
            "subject_error",
            operation="process_subject_wrapper",
            subject_id=subject_id,
            error=str(e)
        )
        excluded_log.append(f"{subject_id}: {str(e)}")

def write_metrics_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write results to CSV."""
    if not results:
        logger.log(
            "no_results",
            operation="write_metrics_csv",
            status="empty"
        )
        # Create empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "subject_id", "num_nodes", "num_edges", 
                "degree", "global_efficiency", 
                "clustering_coefficient", "avg_path_length"
            ])
            writer.writeheader()
        return

    # Determine fieldnames from first result
    fieldnames = list(results[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.log(
        "csv_written",
        operation="write_metrics_csv",
        path=str(output_path),
        count=len(results)
    )

def write_excluded_log(excluded: List[str], log_path: Path) -> None:
    """Write excluded subjects to log file."""
    with open(log_path, 'w') as f:
        for entry in excluded:
            f.write(f"{entry}\n")
    
    logger.log(
        "log_written",
        operation="write_excluded_log",
        path=str(log_path),
        count=len(excluded)
    )

def write_status(status: Dict[str, Any], status_path: Path) -> None:
    """Write execution status to JSON."""
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2, default=str)
    
    logger.log(
        "status_written",
        operation="write_status",
        path=str(status_path)
    )

@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point."""
    start_time = time.time()
    logger.log("start", operation="main", start_time=start_time)

    try:
        # 1. Read eligible subjects
        subject_ids = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
        if not subject_ids:
            logger.log("no_eligible_subjects", operation="main")
            # Write empty status
            write_status({"status": "no_eligible_subjects"}, STATUS_FILE)
            return 0

        logger.log("subjects_loaded", operation="main", count=len(subject_ids))

        # 2. Prepare storage
        results: List[Dict[str, Any]] = []
        excluded_log: List[str] = []

        # 3. Process subject-by-subject
        for i, sid in enumerate(subject_ids):
            logger.log(
                "processing_subject",
                operation="main",
                index=i,
                total=len(subject_ids),
                subject_id=sid
            )
            process_subject_wrapper(sid, CONNECTIVITY_DIR, results, excluded_log)

            # Periodic memory check (every 10 subjects)
            if (i + 1) % 10 == 0:
                if not check_memory_usage():
                    logger.log("memory_critical", operation="main")
                    # Continue but log warning
                    pass

        # 4. Write outputs
        write_metrics_csv(results, OUTPUT_CSV)
        write_excluded_log(excluded_log, EXCLUDED_LOG)

        # 5. Write status
        end_time = time.time()
        status = {
            "status": "success",
            "total_subjects": len(subject_ids),
            "processed": len(results),
            "excluded": len(excluded_log),
            "runtime_seconds": end_time - start_time,
            "output_file": str(OUTPUT_CSV)
        }
        write_status(status, STATUS_FILE)

        logger.log("end", operation="main", status="success", runtime=end_time - start_time)
        return 0

    except Exception as e:
        logger.log(
            "fatal_error",
            operation="main",
            error=str(e)
        )
        write_status({"status": "failed", "error": str(e)}, STATUS_FILE)
        return 1

if __name__ == "__main__":
    sys.exit(main())
