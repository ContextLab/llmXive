import csv
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from utils.config import ensure_directories

logger = logging.getLogger(__name__)

# Schema definition for metrics.csv
# Columns: trajectory_id, model, mae_position, mae_rotation, convergence, sfm_failure_reason, scale_drift
METRICS_SCHEMA = {
    "trajectory_id": str,
    "model": str,
    "mae_position": float,  # null if SfM failed
    "mae_rotation": float,  # null if SfM failed
    "convergence": bool,
    "sfm_failure_reason": str,
    "scale_drift": float      # null if SfM failed
}

# Sentinel value documentation per Spec FR-004 reconciliation
# Note: We use Python's None (serialized as empty string in CSV) to represent null/missing values.
# This is the accepted convention for divergence to ensure statistical validity (Plan Phase 2).
NULL_VALUE_SENTINEL = ""

def write_metrics_csv(
    metrics: List[Dict[str, Any]],
    output_path: str,
    log_exception: bool = True
) -> None:
    """
    Write metrics to CSV file.

    Handles the reconciliation of Spec FR-004 'sentinel value' requirement
    with Plan 'null' convention by:
    1. Using empty string (None) for divergent/failed trajectories
    2. Logging this exception to ensure traceability
    3. Maintaining statistical validity by allowing proper filtering in downstream analysis

    Args:
        metrics: List of metric dictionaries matching METRICS_SCHEMA
        output_path: Path to output CSV file
        log_exception: If True, log the reconciliation exception (default: True)
    """
    ensure_directories(output_path)

    if log_exception:
        logger.info(
            "Reconciling Spec FR-004 'sentinel value' with Plan 'null' convention: "
            "Using empty string (None) for divergent trajectories to ensure statistical validity."
        )

    fieldnames = list(METRICS_SCHEMA.keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in metrics:
            # Ensure null values are written as empty strings
            sanitized_row = {}
            for key, value in row.items():
                if value is None:
                    sanitized_row[key] = NULL_VALUE_SENTINEL
                else:
                    sanitized_row[key] = value
            writer.writerow(sanitized_row)

    logger.info(f"Metrics written to {output_path} with {len(metrics)} rows")

def load_metrics_csv(input_path: str) -> List[Dict[str, Any]]:
    """
    Load metrics from CSV file.

    Converts empty strings back to None for proper statistical handling.

    Args:
        input_path: Path to input CSV file

    Returns:
        List of metric dictionaries with None for null values
    """
    if not os.path.exists(input_path):
        logger.error(f"Metrics file not found: {input_path}")
        return []

    metrics = []
    with open(input_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert empty strings back to None
            sanitized_row = {}
            for key, value in row.items():
                if value == NULL_VALUE_SENTINEL or value == '':
                    sanitized_row[key] = None
                elif key == 'convergence':
                    sanitized_row[key] = value.lower() == 'true'
                elif key in ['mae_position', 'mae_rotation', 'scale_drift']:
                    if value is not None and value != '':
                        sanitized_row[key] = float(value)
                    else:
                        sanitized_row[key] = None
                else:
                    sanitized_row[key] = value
            metrics.append(sanitized_row)

    logger.info(f"Loaded {len(metrics)} rows from {input_path}")
    return metrics

def main():
    """
    Main entry point for metrics writer.
    Creates a sample metrics.csv with proper null handling for testing.
    """
    import sys
    from pathlib import Path

    # Default output path
    output_path = "data/derived/metrics.csv"

    # Sample data demonstrating null handling
    sample_metrics = [
        {
            "trajectory_id": "traj_001",
            "model": "dreamx_lite",
            "mae_position": 0.123,
            "mae_rotation": 0.045,
            "convergence": True,
            "sfm_failure_reason": "",
            "scale_drift": 1.02
        },
        {
            "trajectory_id": "traj_002",
            "model": "dreamx_lite",
            "mae_position": None,  # SfM failed
            "mae_rotation": None,  # SfM failed
            "convergence": False,
            "sfm_failure_reason": "insufficient_features",
            "scale_drift": None    # SfM failed
        },
        {
            "trajectory_id": "traj_003",
            "model": "dreamx_lite",
            "mae_position": 0.089,
            "mae_rotation": 0.032,
            "convergence": True,
            "sfm_failure_reason": "",
            "scale_drift": 0.98
        }
    ]

    write_metrics_csv(sample_metrics, output_path, log_exception=True)

    # Verify by loading back
    loaded = load_metrics_csv(output_path)
    assert len(loaded) == 3
    assert loaded[1]["mae_position"] is None
    assert loaded[1]["convergence"] is False
    assert loaded[1]["sfm_failure_reason"] == "insufficient_features"

    print(f"Successfully wrote and verified metrics to {output_path}")

if __name__ == "__main__":
    main()
