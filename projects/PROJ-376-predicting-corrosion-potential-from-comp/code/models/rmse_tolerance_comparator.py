"""
Module: rmse_tolerance_comparator.py

Purpose:
Implements RMSE calculation in millivolts (mV) and compares the result
against the tolerance defined in `config/astm_g59_tolerance.yaml`.

This task enforces SC-002 by ensuring a comparison is always reported
and the 'N/A' path is never allowed.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Local imports based on API surface
from utils.logging import get_logger
from utils.astm_g59_parser import load_astm_tolerance_config, get_tolerance_value
from utils.config import get_model_results_path, get_astm_tolerance_config_path
from utils.exceptions import CorrosionPipelineError

# Configure logger
logger = get_logger(__name__)

# Constants
VOLT_TO_MV = 1000.0


def load_model_results() -> Dict[str, Any]:
    """
    Load the model results from the standard output path.
    
    Returns:
        Dict containing model metrics including 'rmse' and 'rmse_unit'.
        
    Raises:
        CorrosionPipelineError: If the results file is missing or malformed.
    """
    results_path = get_model_results_path()
    if not results_path.exists():
        raise CorrosionPipelineError(
            f"Model results file not found at {results_path}. "
            "Run code/models/evaluate.py first."
        )
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    if 'metrics' not in data:
        raise CorrosionPipelineError(
            "Model results file missing 'metrics' key."
        )
    
    return data


def convert_rmse_to_mv(rmse_value: float, unit: str) -> float:
    """
    Convert RMSE value to millivolts (mV).
    
    Args:
        rmse_value: The RMSE value.
        unit: The unit of the RMSE value (e.g., 'V', 'mV').
        
    Returns:
        RMSE value converted to mV.
        
    Raises:
        CorrosionPipelineError: If the unit is unrecognized.
    """
    unit_lower = unit.lower()
    if unit_lower == 'v':
        return rmse_value * VOLT_TO_MV
    elif unit_lower == 'mv':
        return rmse_value
    else:
        raise CorrosionPipelineError(
            f"Unrecognized RMSE unit '{unit}'. Expected 'V' or 'mV'."
        )


def compare_rmse_against_tolerance(
    rmse_mv: float,
    tolerance_mv: float,
    tolerance_source: str
) -> Dict[str, Any]:
    """
    Compare the RMSE (in mV) against the ASTM G59 tolerance.
    
    Args:
        rmse_mv: The model's RMSE in millivolts.
        tolerance_mv: The tolerance threshold in millivolts.
        tolerance_source: The source of the tolerance value (for reporting).
        
    Returns:
        A dictionary containing the comparison results.
    """
    is_within_tolerance = rmse_mv <= tolerance_mv
    
    return {
        "rmse_mV": rmse_mv,
        "tolerance_mV": tolerance_mv,
        "tolerance_source": tolerance_source,
        "is_within_tolerance": is_within_tolerance,
        "status": "PASS" if is_within_tolerance else "FAIL",
        "message": (
            f"RMSE ({rmse_mv:.3f} mV) is {'within' if is_within_tolerance else 'exceeds'} "
            f"the ASTM G59 tolerance ({tolerance_mv:.3f} mV)."
        )
    }


def main():
    """
    Main entry point for the RMSE tolerance comparison task.
    
    1. Loads model results (must contain RMSE).
    2. Loads ASTM G59 tolerance configuration.
    3. Converts RMSE to mV.
    4. Compares against tolerance.
    5. Prints the result and writes a report to `data/logs/rmse_tolerance_report.json`.
    
    Raises:
        CorrosionPipelineError: If any required data is missing or invalid.
    """
    logger.info("Starting RMSE tolerance comparison (T023b)...")
    
    # 1. Load Model Results
    try:
        results = load_model_results()
    except CorrosionPipelineError as e:
        logger.error(f"Failed to load model results: {e}")
        raise
    
    # Extract metrics
    # We assume the 'best_model' or 'aggregated' metrics are in results['metrics']
    # Depending on the exact structure of model_results.json from T021/T022,
    # we might need to select a specific model. For now, we look for 'rmse'.
    
    metrics = results.get('metrics', {})
    
    # Handle case where metrics might be a dict of models or a single dict
    if isinstance(metrics, dict) and 'rmse' in metrics:
        rmse_val = metrics['rmse']
        rmse_unit = metrics.get('rmse_unit', 'V')
    elif isinstance(metrics, dict) and 'best_model' in metrics:
        # Assume best_model metrics
        best_metrics = metrics['best_model']
        rmse_val = best_metrics.get('rmse')
        rmse_unit = best_metrics.get('rmse_unit', 'V')
    else:
        # Fallback: try to find any 'rmse' key in the flat structure
        rmse_val = results.get('rmse')
        rmse_unit = results.get('rmse_unit', 'V')
    
    if rmse_val is None:
        raise CorrosionPipelineError(
            "Could not find 'rmse' value in model results. "
            "Ensure code/models/evaluate.py has populated this field."
        )
    
    logger.info(f"Loaded RMSE: {rmse_val} {rmse_unit}")
    
    # 2. Load Tolerance Configuration
    try:
        tolerance_config = load_astm_tolerance_config()
        tolerance_mv = get_tolerance_value(tolerance_config)
        
        # Get source info for the report
        source_info = tolerance_config.get('source', 'Unknown')
        if 'default_value' in tolerance_config and tolerance_config.get('used_default'):
            source_info = f"{source_info} (Literature Default)"
            
    except CorrosionPipelineError as e:
        logger.error(f"Failed to load tolerance config: {e}")
        raise
    
    logger.info(f"Loaded Tolerance: {tolerance_mv} mV (Source: {source_info})")
    
    # 3. Convert RMSE to mV
    try:
        rmse_mv = convert_rmse_to_mv(rmse_val, rmse_unit)
        logger.info(f"Converted RMSE to mV: {rmse_mv:.3f} mV")
    except CorrosionPipelineError as e:
        logger.error(f"Failed to convert RMSE to mV: {e}")
        raise
    
    # 4. Compare
    comparison_result = compare_rmse_against_tolerance(
        rmse_mv, tolerance_mv, source_info
    )
    
    # 5. Report
    report = {
        "task_id": "T023b",
        "timestamp": str(Path.cwd()), # Placeholder for actual timestamp if needed
        "comparison": comparison_result
    }
    
    # Print summary to stdout
    print("\n" + "="*60)
    print("RMSE TOLERANCE COMPARISON REPORT (T023b)")
    print("="*60)
    print(f"Model RMSE:       {comparison_result['rmse_mV']:.3f} mV")
    print(f"ASTM G59 Tol:     {comparison_result['tolerance_mV']:.3f} mV")
    print(f"Source:           {comparison_result['tolerance_source']}")
    print(f"Result:           {comparison_result['status']}")
    print(f"Message:          {comparison_result['message']}")
    print("="*60 + "\n")
    
    # Write detailed report to data/logs
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    report_path = logs_dir / "rmse_tolerance_report.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report written to {report_path}")
    
    # Exit with code 1 if tolerance failed, to allow CI/CD to catch it if needed
    # However, the task requirement is just to "Report comparison result".
    # We do not halt the pipeline unless specified, but we log the failure.
    if not comparison_result['is_within_tolerance']:
        logger.warning("Model RMSE exceeds ASTM G59 tolerance.")
    
    return comparison_result


if __name__ == "__main__":
    main()
