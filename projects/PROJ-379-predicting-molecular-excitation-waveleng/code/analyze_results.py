"""
T027: Aggregate metrics, collinearity flags, redundancy masks, and power status
into data/processed/metrics.json.

Dependencies:
  - T018: compute_power_analysis (produces power_status in metrics.json)
  - T023: check_collinearity (produces collinearity_flags in redundancy_masks.json)
  - T025: apply_redundancy_mask (produces final attribution results)
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-379-predicting-molecular-excitation-waveleng"

# Ensure logging is set up
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_json_file(file_path: Path, required: bool = True) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists. If required and missing, raise FileNotFoundError."""
    if not file_path.exists():
        if required:
            raise FileNotFoundError(f"Required artifact missing: {file_path}")
        logger.warning(f"Optional artifact missing: {file_path}")
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def aggregate_results() -> Dict[str, Any]:
    """
    Aggregate metrics from evaluate.py, collinearity checks from collinearity_check.py,
    and power analysis status into a unified metrics.json.
    
    Expected inputs:
      - data/processed/metrics.json (from T016/T018): contains mae, r2, wilcoxon_p_value, sc001_status, power_status
      - data/processed/redundancy_masks.json (from T023): contains collinearity_flags and redundancy_masks
    """
    metrics_path = DATA_PROCESSED_DIR / "metrics.json"
    redundancy_path = DATA_PROCESSED_DIR / "redundancy_masks.json"

    # Load primary metrics (from T016/T018)
    try:
        metrics_data = load_json_file(metrics_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Load redundancy and collinearity data (from T023)
    try:
        redundancy_data = load_json_file(redundancy_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Extract required fields
    mae = metrics_data.get("mae")
    r2 = metrics_data.get("r2")
    sc001_status = metrics_data.get("sc001_status")
    power_status = metrics_data.get("power_status")
    
    # Extract collinearity flags and masks
    collinearity_flags = redundancy_data.get("collinearity_flags", {})
    redundancy_masks = redundancy_data.get("redundancy_masks", {})

    # Construct final aggregated dictionary
    aggregated = {
        "mae": mae,
        "r2": r2,
        "collinearity_flags": collinearity_flags,
        "redundancy_masks": redundancy_masks,
        "power_status": power_status,
        "sc001_status": sc001_status
    }

    # Verify all required keys are present and not None
    required_keys = ["mae", "r2", "collinearity_flags", "redundancy_masks", "power_status", "sc001_status"]
    missing_keys = [k for k in required_keys if aggregated[k] is None]
    
    if missing_keys:
        raise ValueError(f"Aggregated metrics missing required keys: {missing_keys}")

    return aggregated

def main():
    """Entry point for T027."""
    logger.info("Starting T027: Aggregating results...")
    
    try:
        aggregated_metrics = aggregate_results()
        
        output_path = DATA_PROCESSED_DIR / "metrics.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(aggregated_metrics, f, indent=2)
        
        logger.info(f"Successfully aggregated results to {output_path}")
        logger.info(f"Keys present: {list(aggregated_metrics.keys())}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error in aggregation: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()