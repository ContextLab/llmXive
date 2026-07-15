from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd
import networkx as nx
import psutil

# Import from local utils and config
# Note: utils.graph and utils.io are expected to exist per project structure
try:
    from utils.graph import calculate_degree_centrality, calculate_global_efficiency, calculate_clustering_coefficient
except ImportError:
    # Fallback definitions if utils.graph is not fully implemented yet
    # This ensures the script can run even if the utility module is partially stubbed
    def calculate_degree_centrality(adj_matrix: np.ndarray) -> np.ndarray:
        G = nx.from_numpy_array(adj_matrix)
        deg = np.array([d for _, d in G.degree()])
        return deg

    def calculate_global_efficiency(adj_matrix: np.ndarray) -> float:
        G = nx.from_numpy_array(adj_matrix)
        return nx.global_efficiency(G)

    def calculate_clustering_coefficient(adj_matrix: np.ndarray) -> float:
        G = nx.from_numpy_array(adj_matrix)
        return nx.average_clustering(G)

try:
    from utils.io import ensure_dir, load_json, save_json
except ImportError:
    from pathlib import Path
    def ensure_dir(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
    def load_json(path: str) -> dict:
        with open(path, 'r') as f: return json.load(f)
    def save_json(data: dict, path: str) -> None:
        ensure_dir(str(Path(path).parent))
        with open(path, 'w') as f: json.dump(data, f)

# Configuration
RAM_LIMIT_GB = 7.0
INPUT_CONNECTIVITY_DIR = "data/processed/connectivity_matrices"
OUTPUT_METRICS_CSV = "data/processed/graph_metrics.csv"
OUTPUT_EXCLUDED_LOG = "data/processed/excluded_subjects.log"
OUTPUT_STATUS_JSON = "data/artifacts/data_gate_status.json"
ELIGIBLE_SUBJECTS_FILE = "data/processed/eligible_subjects.csv"


def check_memory_usage() -> bool:
    """Check if current memory usage is within the 7GB limit."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > RAM_LIMIT_GB:
        print(f"WARNING: Current memory usage {mem_gb:.2f} GB exceeds limit {RAM_LIMIT_GB} GB")
        return False
    return True


def read_eligible_subjects(file_path: str) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Eligible subjects file not found: {file_path}")
    df = pd.read_csv(file_path)
    # Handle potential column name variations
    if "subject_id" in df.columns:
        return df["subject_id"].astype(str).tolist()
    elif "participant_id" in df.columns:
        return df["participant_id"].astype(str).tolist()
    else:
        # Assume first column is subject ID if no standard name found
        return df.iloc[:, 0].astype(str).tolist()


def load_connectivity(subject_id: str, input_dir: str) -> Optional[np.ndarray]:
    """
    Load connectivity matrix for a subject.
    Expected file patterns: sub-<id>_connectivity.npy or sub-<id>_connectivity.csv
    """
    input_path = Path(input_dir)
    npy_path = input_path / f"sub-{subject_id}_connectivity.npy"
    csv_path = input_path / f"sub-{subject_id}_connectivity.csv"

    if npy_path.exists():
        return np.load(npy_path)
    elif csv_path.exists():
        return np.loadtxt(csv_path, delimiter=",")
    else:
        # Try alternative naming if standard fails
        for p in input_path.glob(f"*{subject_id}*.npy"):
            return np.load(p)
        for p in input_path.glob(f"*{subject_id}*.csv"):
            return np.loadtxt(p, delimiter=",")
    
    return None


def compute_subject_metrics(adj_matrix: np.ndarray) -> Dict[str, float]:
    """Compute graph metrics for a single adjacency matrix."""
    if adj_matrix is None or adj_matrix.size == 0:
        return {}

    # Ensure symmetric and zero diagonal for graph construction
    adj_matrix = np.asarray(adj_matrix, dtype=float)
    np.fill_diagonal(adj_matrix, 0.0)
    if not np.allclose(adj_matrix, adj_matrix.T):
        adj_matrix = (adj_matrix + adj_matrix.T) / 2.0

    # Thresholding: keep positive connections only (optional, but common)
    # adj_matrix[adj_matrix < 0] = 0.0 

    try:
        degree = calculate_degree_centrality(adj_matrix)
        mean_degree = float(np.mean(degree))
        
        global_eff = calculate_global_efficiency(adj_matrix)
        
        clustering = calculate_clustering_coefficient(adj_matrix)
        
        # Path length calculation (average shortest path)
        # Using networkx for robustness
        G = nx.from_numpy_array(adj_matrix)
        if nx.is_connected(G):
            avg_path_len = float(nx.average_shortest_path_length(G))
        else:
            # For disconnected graphs, use harmonic mean or infinity
            # Using efficiency-based path length proxy or inf
            avg_path_len = float('inf')
        
        return {
            "mean_degree": mean_degree,
            "global_efficiency": global_eff,
            "clustering_coefficient": clustering,
            "average_path_length": avg_path_len
        }
    except Exception as e:
        print(f"Error computing metrics: {e}")
        return {}


def process_subject_wrapper(subject_id: str, input_dir: str) -> Dict[str, Any]:
    """Process a single subject and return metrics or error status."""
    adj = load_connectivity(subject_id, input_dir)
    if adj is None:
        return {"subject_id": subject_id, "status": "missing_matrix"}
    
    metrics = compute_subject_metrics(adj)
    if not metrics:
        return {"subject_id": subject_id, "status": "computation_failed"}
    
    return {
        "subject_id": subject_id,
        "status": "success",
        **metrics
    }


def write_metrics_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write results to CSV."""
    if not results:
        print("No results to write.")
        return

    # Determine columns
    columns = ["subject_id", "status"]
    # Add metric columns dynamically
    if results[0].get("status") == "success":
        metric_cols = [k for k in results[0].keys() if k not in ["subject_id", "status"]]
        columns.extend(metric_cols)

    ensure_dir(output_path)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            # Handle infinity for path length
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float) and np.isinf(v):
                    clean_row[k] = "inf"
                else:
                    clean_row[k] = v
            writer.writerow(clean_row)


def write_excluded_log(excluded: List[Dict[str, str]], log_path: str) -> None:
    """Write excluded subjects to log."""
    ensure_dir(log_path)
    with open(log_path, "w") as f:
        f.write("SubjectID,Reason\n")
        for item in excluded:
            f.write(f"{item['subject_id']},{item['reason']}\n")


def write_status(eligible_count: int, processed_count: int, status: str, message: str) -> None:
    """Write status JSON."""
    status_data = {
        "eligible_subjects": eligible_count,
        "processed_subjects": processed_count,
        "status": status,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    save_json(status_data, OUTPUT_STATUS_JSON)


def main() -> int:
    """Main entry point."""
    start_time = time.time()
    excluded = []
    results = []

    # 1. Read eligible subjects
    try:
        subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        write_status(0, 0, "error", str(e))
        return 1
    except Exception as e:
        print(f"Error reading eligible subjects: {e}")
        write_status(0, 0, "error", str(e))
        return 1

    if not subjects:
        print("No eligible subjects found.")
        write_status(0, 0, "warning", "No eligible subjects found")
        return 0

    print(f"Processing {len(subjects)} subjects...")

    # 2. Process subject-by-subject
    for subj in subjects:
        # Check memory before processing
        if not check_memory_usage():
            excluded.append({"subject_id": subj, "reason": "memory_limit_exceeded"})
            continue

        result = process_subject_wrapper(subj, INPUT_CONNECTIVITY_DIR)
        
        if result["status"] == "success":
            results.append(result)
        else:
            reason = "missing_matrix" if result["status"] == "missing_matrix" else "computation_failed"
            excluded.append({"subject_id": subj, "reason": reason})

    # 3. Write outputs
    write_metrics_csv(results, OUTPUT_METRICS_CSV)
    if excluded:
        write_excluded_log(excluded, OUTPUT_EXCLUDED_LOG)

    elapsed = time.time() - start_time
    write_status(len(subjects), len(results), "success", f"Completed in {elapsed:.2f}s")

    print(f"Completed: {len(results)} processed, {len(excluded)} excluded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
