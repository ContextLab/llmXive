from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import psutil
import networkx as nx

from utils.logger import get_logger, log_operation
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from utils.io import ensure_dir

# Constants
EXIT_CODE_RAM_EXCEEDED = 5
RAM_LIMIT_GB = 7.0
INPUT_DIR = Path("data/processed/connectivity_matrices")
ELIGIBLE_SUBJECTS_FILE = Path("data/processed/eligible_subjects.csv")
OUTPUT_CSV = Path("data/processed/graph_metrics.csv")
EXCLUDED_LOG = Path("data/processed/excluded_graph_metrics.log")
STATUS_FILE = Path("data/artifacts/graph_metrics_status.json")

logger = get_logger("compute_graph_metrics")


def check_memory_usage() -> float:
    """Check current RAM usage in GB. Raises if limit exceeded."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > RAM_LIMIT_GB:
        raise MemoryError(
            f"Peak RAM exceeded limit: {mem_gb:.2f} GB > {RAM_LIMIT_GB} GB"
        )
    return mem_gb


def read_eligible_subjects(file_path: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    subjects = []
    with open(file_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "subject_id" in row:
                subjects.append(row["subject_id"])
            elif "participant_id" in row:
                subjects.append(row["participant_id"])
    return subjects


def load_connectivity(subject_id: str, input_dir: Path) -> np.ndarray:
    """Load a single subject's connectivity matrix (npy)."""
    file_path = input_dir / f"{subject_id}_connectivity.npy"
    if not file_path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found: {file_path}")
    return np.load(file_path)


def compute_subject_metrics(
    adjacency_matrix: np.ndarray,
) -> Dict[str, float]:
    """Compute graph metrics for a single adjacency matrix."""
    # Ensure binary or weighted? Assuming weighted for efficiency, but
    # degree usually implies binary. We'll use the provided utils which
    # likely handle thresholds or binary conversion if needed.
    # For now, passing raw matrix to utils.

    # Degree (average degree centrality * (N-1) to get average degree)
    # Or directly sum connections. Let's use the utility which returns centrality.
    degree_centrality = calculate_degree_centrality(adjacency_matrix)
    node_degree = float(np.mean(degree_centrality) * (adjacency_matrix.shape[0] - 1))

    global_eff = calculate_global_efficiency(adjacency_matrix)
    clustering_coef = calculate_clustering_coefficient(adjacency_matrix)
    path_len = calculate_shortest_path_length(adjacency_matrix)

    return {
        "node_degree": node_degree,
        "global_efficiency": global_eff,
        "clustering_coeff": clustering_coef,
        "path_length": path_len,
    }


def process_subject_wrapper(
    subject_id: str, input_dir: Path
) -> Optional[Dict[str, Any]]:
    """Process a single subject, handling memory checks and errors."""
    try:
        check_memory_usage()
        adj_matrix = load_connectivity(subject_id, input_dir)
        metrics = compute_subject_metrics(adj_matrix)
        metrics["subject_id"] = subject_id
        return metrics
    except FileNotFoundError as e:
        logger.log("missing_connectivity_file", error=str(e))
        return None
    except MemoryError as e:
        logger.log("ram_exceeded", error=str(e))
        raise
    except Exception as e:
        logger.log("processing_error", subject=subject_id, error=str(e))
        return None


def write_metrics_csv(
    results: List[Dict[str, Any]], output_path: Path
) -> None:
    """Write results to CSV with the required schema."""
    ensure_dir(output_path.parent)
    fieldnames = [
        "subject_id",
        "node_degree",
        "global_efficiency",
        "clustering_coeff",
        "path_length",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def write_excluded_log(excluded_ids: List[str], log_path: Path) -> None:
    """Write excluded subjects log."""
    ensure_dir(log_path.parent)
    with open(log_path, "w") as f:
        f.write("subject_id,reason\n")
        for sub_id, reason in excluded_ids:
            f.write(f"{sub_id},{reason}\n")


def write_status(status: Dict[str, Any], status_path: Path) -> None:
    """Write execution status JSON."""
    ensure_dir(status_path.parent)
    with open(status_path, "w") as f:
        json.dump(status, f, indent=2)


@log_operation("compute_graph_metrics_main")
def main() -> int:
    """Main entry point for computing graph metrics."""
    start_time = time.time()
    excluded_records: List[tuple] = []
    results: List[Dict[str, Any]] = []

    logger.log("start", message="Starting graph metrics computation")

    # 1. Read eligible subjects
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.log("error", message=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
        return 1

    subject_ids = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    if not subject_ids:
        logger.log("error", message="No eligible subjects found")
        return 1

    logger.log("subjects_loaded", count=len(subject_ids))

    # 2. Process each subject
    for sub_id in subject_ids:
        try:
            metrics = process_subject_wrapper(sub_id, INPUT_DIR)
            if metrics:
                results.append(metrics)
            else:
                excluded_records.append((sub_id, "Failed to process or missing file"))
        except MemoryError:
            logger.log("fatal", message="RAM limit exceeded. Aborting.")
            write_status(
                {"status": "failed", "reason": "RAM_EXCEEDED", "runtime": time.time() - start_time},
                STATUS_FILE
            )
            return EXIT_CODE_RAM_EXCEEDED
        except Exception as e:
            logger.log("unexpected_error", subject=sub_id, error=str(e))
            excluded_records.append((sub_id, f"Unexpected error: {str(e)}"))

    # 3. Write outputs
    if results:
        write_metrics_csv(results, OUTPUT_CSV)
        logger.log("output_written", path=str(OUTPUT_CSV), count=len(results))
    else:
        logger.log("warning", message="No metrics computed. Output file not created.")
        excluded_records.append(("ALL", "No metrics computed"))

    write_excluded_log(excluded_records, EXCLUDED_LOG)

    elapsed = time.time() - start_time
    status = {
        "status": "success" if results else "partial_failure",
        "subjects_processed": len(results),
        "subjects_excluded": len(excluded_records),
        "runtime_seconds": elapsed,
        "output_path": str(OUTPUT_CSV),
    }
    write_status(status, STATUS_FILE)

    logger.log("finish", status=status)
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())