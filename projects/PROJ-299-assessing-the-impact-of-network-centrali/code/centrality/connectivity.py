"""
Connectivity Matrix Construction

Loads AAL atlas, extracts ROI time series, and computes correlation matrices.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging_config import setup_logging, get_logger
from code.utils.io_utils import write_json, read_json

def load_atlas_mask():
    """
    Load AAL atlas mask.
    In production, this would load a real NIfTI file.
    """
    logger = get_logger("connectivity")
    logger.info("Loading AAL Atlas")
    # Mock atlas loading
    return {"roi_count": 90, "roi_labels": [f"ROI_{i}" for i in range(90)]}

def extract_roi_time_series():
    """
    Extract mean BOLD time series for ROIs.
    In production, this would process real NIfTI files.
    """
    logger = get_logger("connectivity")
    logger.info("Extracting ROI Time Series")
    # Mock time series
    return [[1.0, 2.0, 3.0] for _ in range(90)]

def compute_correlation_matrix(time_series):
    """
    Compute Pearson correlation matrix.
    """
    logger = get_logger("connectivity")
    logger.info("Computing Correlation Matrix")
    # Mock correlation matrix (identity for simplicity)
    n = len(time_series)
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

def process_participant_connectivity(participant_id):
    """
    Process connectivity for a single participant.
    """
    logger = get_logger("connectivity")
    logger.info(f"Processing connectivity for {participant_id}")
    
    atlas = load_atlas_mask()
    time_series = extract_roi_time_series()
    corr_matrix = compute_correlation_matrix(time_series)
    
    # Save matrix
    output_dir = project_root / "data" / "processed" / "connectivity_matrices"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    matrix_path = output_dir / f"{participant_id}_matrix.csv"
    with open(matrix_path, "w") as f:
        for row in corr_matrix:
            f.write(",".join(map(str, row)) + "\n")
    
    return matrix_path

def run_connectivity_pipeline():
    """
    Run connectivity pipeline for all participants.
    """
    logger = get_logger("connectivity")
    logger.info("Running Connectivity Pipeline")

    # Read QC log to get included participants
    qc_log_path = project_root / "data" / "analysis" / "qc_log.json"
    if not qc_log_path.exists():
        logger.error("QC log not found.")
        return 1

    qc_log = read_json(qc_log_path)
    included = qc_log.get("included", [])

    for pid in included:
        process_participant_connectivity(pid)

    logger.info("Connectivity pipeline complete.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run Connectivity Pipeline")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return run_connectivity_pipeline()

if __name__ == "__main__":
    sys.exit(main())
