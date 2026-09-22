"""
Fidelity Check Module for Visualizing Phase Diagrams.

Implements MAE check for visual fidelity (T036).
Calculates MAE between predicted and experimental phase boundary lines.
Logs warnings if MAE > 50K with error code LOW_DATA_FIDELITY.
Marks research outcome as 'FAILED' for systems exceeding threshold.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

# Fidelity threshold in Kelvin
FIDELITY_THRESHOLD_K = 50.0
FIDELITY_LOG_PATH = "data/artifacts/fidelity_check.log"
FINAL_REPORT_PATH = "data/artifacts/fidelity_report.json"


def load_loso_results(results_path: str = "data/artifacts/loso_results.json") -> Dict[str, Any]:
    """
    Load LOSO cross-validation results containing predictions and experimental values.
    
    Args:
        results_path: Path to LOSO results JSON file.
        
    Returns:
        Dictionary containing LOSO results with fold-level data.
        
    Raises:
        FileNotFoundError: If results file does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"LOSO results file not found: {results_path}")
        
    with open(results_path, 'r') as f:
        return json.load(f)


def calculate_aggregate_mae(
    predictions: List[float], 
    experimental: List[float]
) -> float:
    """
    Calculate Mean Absolute Error between predicted and experimental values.
    
    Args:
        predictions: List of predicted temperature values.
        experimental: List of experimental temperature values.
        
    Returns:
        MAE value in Kelvin.
        
    Raises:
        ValueError: If input lists have different lengths or are empty.
    """
    if len(predictions) != len(experimental):
        raise ValueError(
            f"Prediction and experimental lists must have same length. "
            f"Got {len(predictions)} and {len(experimental)}"
        )
        
    if len(predictions) == 0:
        raise ValueError("Cannot calculate MAE for empty lists")
        
    mae = sum(abs(p - e) for p, e in zip(predictions, experimental)) / len(predictions)
    return mae


def log_fidelity_check(
    system_id: str,
    mae: float,
    status: str,
    log_path: str = FIDELITY_LOG_PATH
) -> None:
    """
    Log fidelity check results to JSON lines file.
    
    Args:
        system_id: Identifier for the alloy system (e.g., "Cu-Zn").
        mae: Calculated Mean Absolute Error in Kelvin.
        status: "PASSED" or "FAILED" based on threshold comparison.
        log_path: Path to the log file.
    """
    # Ensure directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    entry = {
        "system": system_id,
        "mae": mae,
        "status": status,
        "threshold_k": FIDELITY_THRESHOLD_K,
        "error_code": ErrorCode.LOW_DATA_FIDELITY.value if status == "FAILED" else None
    }
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')
        
    if status == "FAILED":
        log_warning(
            f"Fidelity check FAILED for {system_id}: MAE={mae:.2f}K > {FIDELITY_THRESHOLD_K}K",
            error_code=ErrorCode.LOW_DATA_FIDELITY
        )
    else:
        log_info(f"Fidelity check PASSED for {system_id}: MAE={mae:.2f}K")


def update_final_report(
    system_id: str,
    mae: float,
    status: str,
    report_path: str = FINAL_REPORT_PATH
) -> None:
    """
    Update the final fidelity report with system results.
    
    Args:
        system_id: Identifier for the alloy system.
        mae: Calculated Mean Absolute Error.
        status: "PASSED" or "FAILED".
        report_path: Path to the final report JSON file.
    """
    # Ensure directory exists
    report_dir = os.path.dirname(report_path)
    if report_dir and not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    # Load existing report or create new one
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report = json.load(f)
    else:
        report = {
            "systems": [],
            "summary": {
                "total_systems": 0,
                "passed": 0,
                "failed": 0
            }
        }
        
    # Add system result
    system_result = {
        "system_id": system_id,
        "mae": mae,
        "status": status,
        "sc_004_met": status == "PASSED"
    }
    
    # Check if system already exists and update, or append
    existing_system = next(
        (s for s in report["systems"] if s["system_id"] == system_id),
        None
    )
    
    if existing_system:
        existing_system.update(system_result)
    else:
        report["systems"].append(system_result)
        
    # Update summary
    report["summary"]["total_systems"] = len(report["systems"])
    report["summary"]["passed"] = sum(
        1 for s in report["systems"] if s["status"] == "PASSED"
    )
    report["summary"]["failed"] = sum(
        1 for s in report["systems"] if s["status"] == "FAILED"
    )
    
    # Save updated report
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    log_info(f"Updated final fidelity report: {report_path}")


def run_fidelity_check(
    system_id: str,
    predictions: List[float],
    experimental: List[float],
    log_path: str = FIDELITY_LOG_PATH,
    report_path: str = FINAL_REPORT_PATH
) -> Dict[str, Any]:
    """
    Run the complete fidelity check for a single system.
    
    Args:
        system_id: Identifier for the alloy system.
        predictions: List of predicted temperature values.
        experimental: List of experimental temperature values.
        log_path: Path to the fidelity log file.
        report_path: Path to the final report file.
        
    Returns:
        Dictionary containing check results.
    """
    logger.info(f"Running fidelity check for system: {system_id}")
    
    # Calculate MAE
    mae = calculate_aggregate_mae(predictions, experimental)
    
    # Determine status
    status = "PASSED" if mae <= FIDELITY_THRESHOLD_K else "FAILED"
    
    # Log result
    log_fidelity_check(system_id, mae, status, log_path)
    
    # Update final report
    update_final_report(system_id, mae, status, report_path)
    
    result = {
        "system_id": system_id,
        "mae": mae,
        "status": status,
        "threshold_k": FIDELITY_THRESHOLD_K,
        "sc_004_met": status == "PASSED"
    }
    
    logger.info(f"Fidelity check completed for {system_id}: {result}")
    return result


def main():
    """
    Main entry point for fidelity check script.
    
    Usage:
        python code/viz/fidelity_check.py --system Cu-Zn \
            --predictions data/artifacts/predictions.json \
            --experimental data/artifacts/experimental.json
    """
    parser = argparse.ArgumentParser(
        description="Run fidelity check for phase diagram predictions"
    )
    parser.add_argument(
        "--system",
        type=str,
        required=True,
        help="System identifier (e.g., Cu-Zn)"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to JSON file containing predicted values"
    )
    parser.add_argument(
        "--experimental",
        type=str,
        required=True,
        help="Path to JSON file containing experimental values"
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default=FIDELITY_LOG_PATH,
        help="Path to fidelity log file"
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default=FINAL_REPORT_PATH,
        help="Path to final report file"
    )
    
    args = parser.parse_args()
    
    try:
        # Load predictions
        with open(args.predictions, 'r') as f:
            predictions = json.load(f)
            
        # Load experimental values
        with open(args.experimental, 'r') as f:
            experimental = json.load(f)
            
        # Run fidelity check
        result = run_fidelity_check(
            system_id=args.system,
            predictions=predictions,
            experimental=experimental,
            log_path=args.log_path,
            report_path=args.report_path
        )
        
        # Exit with appropriate code
        if result["status"] == "FAILED":
            logger.warning(f"Fidelity check failed for {args.system}")
            sys.exit(1)
        else:
            logger.info(f"Fidelity check passed for {args.system}")
            sys.exit(0)
            
    except FileNotFoundError as e:
        log_error(f"File not found: {e}", error_code=ErrorCode.DATA_SOURCE_MISSING)
        sys.exit(1)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON format: {e}", error_code=ErrorCode.INVALID_DATA_SCHEMA)
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error during fidelity check: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()