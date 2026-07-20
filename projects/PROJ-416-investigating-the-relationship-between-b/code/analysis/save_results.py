"""
Module to save network analysis results (matrices and metrics) to disk.
Implements T024: Save connectivity matrices and metrics.
"""
import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd

# Ensure imports match the API surface provided in the prompt
# The prompt lists 'code/config' as a valid import source for Config
from config import Config

logger = logging.getLogger(__name__)

def ensure_directories(output_dir: Path) -> None:
    """
    Ensure the output directory and the matrices subdirectory exist.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    matrices_dir = output_dir / "matrices"
    matrices_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {output_dir}, {matrices_dir}")

def save_matrix_to_npy(subject_id: str, matrix: np.ndarray, output_dir: Path) -> str:
    """
    Save a single subject's connectivity matrix to a .npy file.
    Returns the path to the saved file.
    """
    matrices_dir = output_dir / "matrices"
    file_path = matrices_dir / f"{subject_id}_connectivity.npy"
    try:
        np.save(file_path, matrix)
        logger.info(f"Saved connectivity matrix for {subject_id} to {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to save matrix for {subject_id}: {e}")
        raise

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save a list of metric dictionaries to a CSV file.
    Expected keys in each dict: subject_id, modularity_q, global_efficiency, local_efficiency, fd_mean, etc.
    """
    if not metrics_list:
        logger.warning("No metrics to save to CSV.")
        # Create an empty file with headers if list is empty to satisfy file existence requirement
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["subject_id", "modularity_q", "global_efficiency", "local_efficiency", "fd_mean"])
        return

    # Determine all unique keys to ensure consistent columns
    fieldnames = ["subject_id", "modularity_q", "global_efficiency", "local_efficiency", "fd_mean"]
    # Add any other keys found in the data that aren't in the standard set
    for item in metrics_list:
        for key in item.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_list:
            # Handle NaN/Inf by converting to string or None to avoid CSV errors
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float):
                    if np.isnan(v) or np.isinf(v):
                        clean_row[k] = ""
                    else:
                        clean_row[k] = v
                else:
                    clean_row[k] = v
            writer.writerow(clean_row)

    logger.info(f"Saved network metrics to {output_path}")

def run_save_results(metrics_data: List[Dict[str, Any]], config: Config) -> None:
    """
    Orchestrates the saving of matrices and metrics based on the provided metrics data.
    
    Args:
        metrics_data: List of dictionaries containing subject metrics and matrices.
                      Each dict should have 'subject_id', 'matrix' (np.ndarray), 
                      and other metric values.
        config: Configuration object containing output paths.
    """
    output_dir = Path(config.OUTPUT_DIR)
    csv_path = output_dir / "network_metrics.csv"
    
    logger.info(f"Starting save results for {len(metrics_data)} subjects.")
    
    ensure_directories(output_dir)
    
    metrics_list_for_csv = []
    
    for item in metrics_data:
        subject_id = item.get('subject_id')
        if not subject_id:
            logger.warning("Skipping item without subject_id.")
            continue
        
        matrix = item.get('matrix')
        if matrix is not None:
            save_matrix_to_npy(subject_id, matrix, output_dir)
        
        # Prepare row for CSV (exclude the matrix object itself)
        row = {k: v for k, v in item.items() if k != 'matrix'}
        metrics_list_for_csv.append(row)
    
    save_metrics_to_csv(metrics_list_for_csv, csv_path)
    logger.info("Finished saving results.")

def main():
    """
    Entry point for the save_results script.
    Loads configuration and runs the save process.
    """
    from utils.logging import setup_logging
    import sys
    
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_level=logging.INFO, log_file=str(log_dir / "save_results.log"))
    
    try:
        config = Config()
        
        # In a real pipeline, this data would come from the previous analysis step.
        # For T024 implementation, we assume the caller (e.g., main.py or a test)
        # passes the data structure. Here we just verify the config and paths.
        # If this is run standalone without data injection, it logs readiness.
        logger.info(f"Save results module initialized. Output dir: {config.OUTPUT_DIR}")
        logger.info("This module is designed to be called by the pipeline with metrics_data.")
        
    except Exception as e:
        logger.error(f"Error in save_results main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
