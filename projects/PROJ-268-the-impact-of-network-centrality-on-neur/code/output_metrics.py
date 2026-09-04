"""
Task T023: Output per-subject CSV files for centrality and synchrony metrics.

This script depends on T022 (process_all_subjects). It reads the aggregated
metrics computed in the previous step and writes them to individual CSV files
in the data/processed directory.

Output files:
- data/processed/centrality_<subject_id>.csv
- data/processed/synchrony_<subject_id>.csv
"""
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path to allow imports from sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from compute_metrics import process_all_subjects
from logging_config import get_logger
from error_handling import raise_storage_limit_error, check_and_raise_storage_limit
from utils import check_disk_usage

logger = get_logger(__name__)

def ensure_output_directory(output_dir: Path) -> None:
    """Ensure the output directory exists."""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

def write_centrality_csv(subject_id: str, metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Write centrality metrics to a CSV file.
    
    Args:
        subject_id: The unique identifier for the subject.
        metrics: Dictionary containing centrality metrics (degree, betweenness, eigenvector).
        output_path: Path to the output CSV file.
    """
    try:
        # Flatten the metrics dictionary if necessary
        # Expected structure: {node_id: {metric_name: value, ...}, ...}
        rows = []
        for node_id, node_metrics in metrics.items():
            row = {"node_id": node_id}
            row.update(node_metrics)
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        logger.info(f"Wrote centrality metrics for subject {subject_id} to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write centrality CSV for subject {subject_id}: {e}")
        raise

def write_synchrony_csv(subject_id: str, synchrony: Dict[str, float], output_path: Path) -> None:
    """
    Write functional synchrony metrics to a CSV file.
    
    Args:
        subject_id: The unique identifier for the subject.
        synchrony: Dictionary containing synchrony metrics (mean absolute correlation).
        output_path: Path to the output CSV file.
    """
    try:
        rows = []
        for metric_name, value in synchrony.items():
            rows.append({"metric": metric_name, "value": value})
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        logger.info(f"Wrote synchrony metrics for subject {subject_id} to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write synchrony CSV for subject {subject_id}: {e}")
        raise

def process_and_output_metrics() -> None:
    """
    Main function to process all subjects and output metrics to CSV files.
    
    This function:
    1. Checks disk usage to ensure we are within limits.
    2. Processes all subjects to compute metrics (T022).
    3. Writes centrality and synchrony metrics to individual CSV files.
    """
    # Check disk usage before processing
    check_and_raise_storage_limit()
    
    # Define paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    
    # Ensure output directory exists
    ensure_output_directory(processed_dir)
    
    # Process all subjects (this calls T022 logic)
    logger.info("Starting metric computation for all subjects...")
    centrality_metrics, synchrony_metrics = process_all_subjects()
    
    if not centrality_metrics and not synchrony_metrics:
        logger.warning("No metrics were computed. Check if data was available.")
        return
    
    # Output centrality metrics
    logger.info("Writing centrality metrics to CSV files...")
    for subject_id, metrics in centrality_metrics.items():
        output_path = processed_dir / f"centrality_{subject_id}.csv"
        write_centrality_csv(subject_id, metrics, output_path)
    
    # Output synchrony metrics
    logger.info("Writing synchrony metrics to CSV files...")
    for subject_id, metrics in synchrony_metrics.items():
        output_path = processed_dir / f"synchrony_{subject_id}.csv"
        write_synchrony_csv(subject_id, metrics, output_path)
    
    logger.info("All metrics have been successfully written to CSV files.")

def main():
    """Entry point for the script."""
    try:
        process_and_output_metrics()
    except Exception as e:
        logger.error(f"Fatal error in output_metrics: {e}")
        raise

if __name__ == "__main__":
    main()