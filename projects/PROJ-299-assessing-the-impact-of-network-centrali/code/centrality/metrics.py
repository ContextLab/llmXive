"""
Centrality Metric Calculation

Calculates degree, betweenness, and closeness centrality for every ROI.
"""
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import networkx as nx
from code.utils.logging_config import setup_logging, get_logger
from code.utils.io_utils import write_json, read_json, write_dicts_to_csv, read_csv_as_dicts

def load_connectivity_matrix(participant_id):
    """
    Load connectivity matrix for a participant.
    """
    matrix_path = project_root / "data" / "processed" / "connectivity_matrices" / f"{participant_id}_matrix.csv"
    if not matrix_path.exists():
        return None
    
    matrix = []
    with open(matrix_path, "r") as f:
        for line in f:
            row = [float(x) for x in line.strip().split(",")]
            matrix.append(row)
    return matrix

def load_roi_labels():
    """
    Load ROI labels from AAL atlas.
    """
    # Mock labels
    return [f"ROI_{i}" for i in range(90)]

def calculate_centrality_metrics(matrix):
    """
    Calculate degree, betweenness, and closeness centrality.
    """
    G = nx.from_numpy_array(matrix)
    
    degree = dict(nx.degree(G))
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    
    return {
        "degree": degree,
        "betweenness": betweenness,
        "closeness": closeness
    }

def process_participant_centrality(participant_id):
    """
    Process centrality for a single participant.
    """
    logger = get_logger("centrality")
    logger.info(f"Processing centrality for {participant_id}")

    matrix = load_connectivity_matrix(participant_id)
    if matrix is None:
        logger.warning(f"Matrix not found for {participant_id}")
        return None

    metrics = calculate_centrality_metrics(matrix)
    roi_labels = load_roi_labels()

    results = []
    for i, label in enumerate(roi_labels):
        results.append({
            "participant_id": participant_id,
            "roi": label,
            "degree": metrics["degree"].get(i, 0),
            "betweenness": metrics["betweenness"].get(i, 0),
            "closeness": metrics["closeness"].get(i, 0)
        })
    
    return results

def run_centrality_pipeline():
    """
    Run centrality pipeline for all participants.
    """
    logger = get_logger("centrality")
    logger.info("Running Centrality Pipeline")

    # Read QC log to get included participants
    qc_log_path = project_root / "data" / "analysis" / "qc_log.json"
    if not qc_log_path.exists():
        logger.error("QC log not found.")
        return 1

    qc_log = read_json(qc_log_path)
    included = qc_log.get("included", [])

    all_results = []
    for pid in included:
        results = process_participant_centrality(pid)
        if results:
            all_results.extend(results)

    # Write raw centrality metrics
    output_path = project_root / "data" / "analysis" / "centrality_raw.csv"
    write_dicts_to_csv(output_path, all_results)

    # Aggregate and write final metrics
    # This is a simplified aggregation for the task
    aggregated = []
    for pid in included:
        pid_results = [r for r in all_results if r["participant_id"] == pid]
        if pid_results:
            aggregated.append({
                "participant_id": pid,
                "degree_mean": sum(r["degree"] for r in pid_results) / len(pid_results),
                "betweenness_mean": sum(r["betweenness"] for r in pid_results) / len(pid_results),
                "closeness_mean": sum(r["closeness"] for r in pid_results) / len(pid_results)
            })

    output_path = project_root / "data" / "analysis" / "centrality_metrics.csv"
    write_dicts_to_csv(output_path, aggregated)

    logger.info(f"Wrote centrality metrics to {output_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run Centrality Pipeline")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return run_centrality_pipeline()

if __name__ == "__main__":
    sys.exit(main())
