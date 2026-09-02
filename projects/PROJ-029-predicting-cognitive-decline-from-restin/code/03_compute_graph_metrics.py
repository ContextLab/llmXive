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

# Import from existing project utilities
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_json, save_json
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
    load_aal_atlas_mask
)

logger = get_logger("compute_graph_metrics")

# Constants
RAM_THRESHOLD_GB = 1.0
MAX_TOTAL_RAM_GB = 7.0
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
CONNECTIVITY_DIR = Path("data/processed/connectivity_matrices")
OUTPUT_PATH = Path("data/processed/graph_metrics.csv")
EXCLUDED_LOG_PATH = Path("data/processed/excluded_graph_metrics.log")
STATUS_PATH = Path("data/artifacts/graph_metrics_status.json")


def check_memory_usage(subject_file_size_bytes: int) -> None:
    """Check available RAM before processing. Fail immediately if constraints violated."""
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    
    # Estimate subject load impact (conservative: 2x file size for processing overhead)
    estimated_load_gb = (subject_file_size_bytes * 2) / (1024 ** 3)
    
    logger.log("check_memory_usage", 
               available_gb=available_gb, 
               estimated_load_gb=estimated_load_gb,
               threshold_gb=RAM_THRESHOLD_GB)

    if available_gb < RAM_THRESHOLD_GB:
        raise RuntimeError(f"Available RAM ({available_gb:.2f} GB) is below threshold ({RAM_THRESHOLD_GB} GB). Failing immediately.")
    
    if estimated_load_gb > MAX_TOTAL_RAM_GB:
        raise RuntimeError(f"Estimated load for subject ({estimated_load_gb:.2f} GB) would exceed system limit ({MAX_TOTAL_RAM_GB} GB). Failing immediately.")


def read_eligible_subjects(path: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {path}")
    
    subjects = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assume column name 'subject_id' based on T017a/T017b schema
            subjects.append(row["subject_id"])
    return subjects


def load_connectivity(subject_id: str, conn_dir: Path) -> np.ndarray:
    """Load connectivity matrix for a specific subject."""
    # Expected filename pattern based on T018 output
    conn_file = conn_dir / f"{subject_id}_connectivity.npy"
    if not conn_file.exists():
        raise FileNotFoundError(f"Connectivity matrix not found for subject {subject_id} at {conn_file}")
    
    # Load using numpy
    matrix = np.load(conn_file)
    return matrix


def compute_subject_metrics(adjacency: np.ndarray) -> Dict[str, float]:
    """Compute graph metrics for a single adjacency matrix."""
    # Create NetworkX graph from adjacency matrix
    G = nx.from_numpy_array(adjacency)
    
    # Calculate metrics
    degree = calculate_degree_centrality(G)
    efficiency = calculate_global_efficiency(G)
    clustering = calculate_clustering_coefficient(G)
    path_len = calculate_shortest_path_length(G)
    
    return {
        "node_degree": degree,
        "global_efficiency": efficiency,
        "clustering_coeff": clustering,
        "path_length": path_len
    }


def process_subject_wrapper(subject_id: str, conn_dir: Path, results: List[Dict]) -> None:
    """Wrapper to process a single subject with error handling and memory checks."""
    try:
        # Check memory before loading
        conn_file = conn_dir / f"{subject_id}_connectivity.npy"
        if not conn_file.exists():
            raise FileNotFoundError(f"Connectivity file missing: {conn_file}")
        
        file_size = conn_file.stat().st_size
        check_memory_usage(file_size)
        
        # Load and compute
        logger.log("load_connectivity", subject_id=subject_id)
        adjacency = load_connectivity(subject_id, conn_dir)
        
        logger.log("compute_metrics", subject_id=subject_id)
        metrics = compute_subject_metrics(adjacency)
        
        # Store result
        result = {
            "subject_id": subject_id,
            **metrics
        }
        results.append(result)
        
        logger.log("subject_processed", subject_id=subject_id, status="success")
        
    except RuntimeError as e:
        # Memory/RAM errors - fail immediately as per spec
        logger.log("subject_failed", subject_id=subject_id, error=str(e), status="runtime_error")
        logger.log("exiting_due_to_memory", error=str(e))
        raise e
    except Exception as e:
        # Other errors - log and exclude
        logger.log("subject_failed", subject_id=subject_id, error=str(e), status="other_error")
        raise e


def write_metrics_csv(results: List[Dict], output_path: Path) -> None:
    """Write graph metrics to CSV."""
    if not results:
        logger.log("no_results", message="No results to write")
        return
    
    ensure_dir(output_path.parent)
    fieldnames = ["subject_id", "node_degree", "global_efficiency", "clustering_coeff", "path_length"]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.log("metrics_written", output=str(output_path), count=len(results))


def write_excluded_log(excluded_subjects: List[Dict]) -> None:
    """Write log of excluded subjects."""
    ensure_dir(EXCLUDED_LOG_PATH.parent)
    with open(EXCLUDED_LOG_PATH, "w") as f:
        if not excluded_subjects:
            f.write("subject_id,reason\n")
        else:
            f.write("subject_id,reason\n")
            for item in excluded_subjects:
                f.write(f"{item['subject_id']},{item['reason']}\n")
    logger.log("excluded_log_written", path=str(EXCLUDED_LOG_PATH))


def write_status(status: Dict) -> None:
    """Write status JSON."""
    ensure_dir(STATUS_PATH.parent)
    save_json(STATUS_PATH, status)
    logger.log("status_written", path=str(STATUS_PATH))


@log_operation("compute_graph_metrics_main")
def main() -> None:
    """Main entry point for graph metrics computation."""
    start_time = time.time()
    results = []
    excluded = []
    success_count = 0
    fail_count = 0
    
    try:
        logger.log("starting", input_file=str(ELIGIBLE_SUBJECTS_PATH))
        
        # Read eligible subjects
        subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_PATH)
        logger.log("subjects_loaded", count=len(subjects))
        
        if not subjects:
            logger.log("no_eligible_subjects")
            write_status({"status": "no_subjects", "count": 0})
            return
        
        # Process each subject
        for subject_id in subjects:
            try:
                process_subject_wrapper(subject_id, CONNECTIVITY_DIR, results)
                success_count += 1
            except RuntimeError as e:
                # Memory errors cause immediate exit per spec
                logger.log("critical_error", error=str(e))
                write_status({
                    "status": "failed",
                    "error": str(e),
                    "success_count": success_count,
                    "fail_count": fail_count
                })
                sys.exit(1)
            except Exception as e:
                # Other errors - log exclusion
                excluded.append({"subject_id": subject_id, "reason": str(e)})
                fail_count += 1
        
        # Write outputs
        write_metrics_csv(results, OUTPUT_PATH)
        write_excluded_log(excluded)
        
        end_time = time.time()
        duration = end_time - start_time
        
        status = {
            "status": "completed",
            "total_subjects": len(subjects),
            "success_count": success_count,
            "fail_count": fail_count,
            "output_file": str(OUTPUT_PATH),
            "duration_seconds": duration
        }
        write_status(status)
        
        logger.log("completed", duration=duration, success=success_count, failed=fail_count)
        
    except Exception as e:
        logger.log("critical_failure", error=str(e))
        write_status({"status": "failed", "error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()