import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

import numpy as np

from config import Config
from utils.logging import setup_logging, log_provenance
from analysis.network import load_preprocessed_data, calculate_connectivity_matrix, calculate_network_metrics

logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure output directories exist."""
    metrics_dir = Path(Config.DATA_METRICS_DIR)
    matrices_dir = metrics_dir / "matrices"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    matrices_dir.mkdir(parents=True, exist_ok=True)
    return metrics_dir, matrices_dir

def save_matrix_to_npy(subject_id: str, matrix: np.ndarray, matrices_dir: Path):
    """Save a connectivity matrix as a .npy file."""
    file_path = matrices_dir / f"{subject_id}_connectivity.npy"
    np.save(file_path, matrix)
    logger.info(f"Saved connectivity matrix for {subject_id} to {file_path}")
    return file_path

def save_metrics_to_csv(subject_metrics: List[Dict[str, Any]], metrics_dir: Path):
    """
    Save network metrics to a CSV file.
    
    Args:
        subject_metrics: List of dictionaries containing metrics for each subject.
        metrics_dir: Directory where the CSV will be saved.
    """
    file_path = metrics_dir / "network_metrics.csv"
    
    if not subject_metrics:
        logger.warning("No metrics to save.")
        return file_path

    # Define standard columns expected by downstream tasks
    # Includes subject_id, modularity, global_efficiency, local_efficiency, and FD if present
    fieldnames = [
        "subject_id", 
        "modularity_q", 
        "global_efficiency", 
        "local_efficiency",
        "mean_fd", 
        "pre_treatment_score", 
        "post_treatment_score"
    ]
    
    # Dynamically add keys found in the first metric dict if they aren't in fieldnames
    first_metric = subject_metrics[0]
    for key in first_metric.keys():
        if key not in fieldnames:
            fieldnames.append(key)

    with open(file_path, mode='w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metric in subject_metrics:
            # Ensure numeric fields are clean (handle NaN/Inf if necessary, though network.py should handle)
            row = {}
            for k, v in metric.items():
                if isinstance(v, float):
                    if np.isnan(v) or np.isinf(v):
                        row[k] = "" # Save empty string for invalid floats in CSV
                    else:
                        row[k] = v
                else:
                    row[k] = v
            writer.writerow(row)
    
    logger.info(f"Saved network metrics to {file_path}")
    return file_path

def run_save_results():
    """
    Main entry point for saving results.
    Loads preprocessed data, computes metrics (if not already done by network.py main),
    saves matrices and aggregates metrics to CSV.
    
    Note: This task assumes network.py has already run or will run. 
    To be self-contained for this task, we re-run the analysis pipeline 
    on the available preprocessed data to ensure data is generated and saved.
    """
    config = Config()
    setup_logging()
    log_provenance("T024", "save_results")

    logger.info("Starting T024: Save connectivity matrices and metrics")
    
    metrics_dir, matrices_dir = ensure_directories()
    
    # Load available preprocessed data
    # This relies on the output of T014/T015 (preprocess.py)
    subjects_data = load_preprocessed_data()
    
    if not subjects_data:
        logger.error("No preprocessed subject data found. Ensure T014/T015 (preprocess) has run.")
        return

    all_metrics = []

    for subject_id, data in subjects_data.items():
        logger.info(f"Processing subject: {subject_id}")
        
        # Extract ROI timeseries
        roi_timeseries = data.get("timeseries")
        if roi_timeseries is None:
            logger.warning(f"No timeseries found for {subject_id}, skipping.")
            continue

        # Calculate Connectivity Matrix
        # network.py calculates this, but we do it here to ensure we have the object to save
        matrix = calculate_connectivity_matrix(roi_timeseries)
        
        # Save Matrix to disk
        save_matrix_to_npy(subject_id, matrix, matrices_dir)

        # Calculate Network Metrics
        metrics = calculate_network_metrics(matrix)
        
        # Enrich with subject info if available (from data dict or metadata)
        # We assume 'data' dict might contain metadata if passed through, 
        # otherwise we just save the computed metrics.
        final_row = {
            "subject_id": subject_id,
            "modularity_q": metrics.get("modularity_q"),
            "global_efficiency": metrics.get("global_efficiency"),
            "local_efficiency": metrics.get("local_efficiency")
        }
        
        # Attempt to grab motion/clinical data if present in the loaded data dict
        # This ensures the CSV has the columns required for US3 stats
        if "mean_fd" in data:
            final_row["mean_fd"] = data["mean_fd"]
        if "pre_treatment_score" in data:
            final_row["pre_treatment_score"] = data["pre_treatment_score"]
        if "post_treatment_score" in data:
            final_row["post_treatment_score"] = data["post_treatment_score"]
        
        all_metrics.append(final_row)
        logger.info(f"Computed metrics for {subject_id}: {metrics}")

    # Save aggregated metrics to CSV
    save_metrics_to_csv(all_metrics, metrics_dir)
    
    logger.info("T024 completed successfully.")
    return all_metrics

def main():
    """CLI entry point."""
    run_save_results()

if __name__ == "__main__":
    main()