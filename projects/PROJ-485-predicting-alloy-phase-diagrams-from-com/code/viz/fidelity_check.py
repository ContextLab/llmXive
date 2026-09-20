import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_loso_results(results_path: str) -> List[Dict[str, Any]]:
    """Load LOSO evaluation results from JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"LOSO results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def calculate_aggregate_mae(results: List[Dict[str, Any]]) -> float:
    """
    Calculate aggregate MAE from LOSO results.
    Assumes results is a list of fold dicts with 'mae' key.
    """
    if not results:
        raise ValueError("No results provided for MAE calculation")
    
    mae_values = [fold.get('mae', 0.0) for fold in results if 'mae' in fold]
    
    if not mae_values:
        raise ValueError("No valid MAE values found in results")
    
    return sum(mae_values) / len(mae_values)

def log_fidelity_check(
    system_id: str,
    mae: float,
    threshold: float = 50000.0,
    output_path: str = "data/artifacts/fidelity_check.log"
) -> bool:
    """
    Log MAE check for visual fidelity to JSON lines file.
    
    Args:
        system_id: Identifier for the alloy system (e.g., "Cu-Zn")
        mae: Mean Absolute Error value
        threshold: Maximum allowed MAE (default 50K as per spec)
        output_path: Path to the log file
    
    Returns:
        True if check passes, False if it fails
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    status = "PASS" if mae <= threshold else "FAIL"
    error_code = None
    
    if status == "FAIL":
        error_code = ErrorCode.LOW_DATA_DENSITY
        log_error(
            logger,
            f"MAE {mae:.2f} exceeds threshold {threshold} for system {system_id}",
            error_code
        )
    else:
        log_info(logger, f"MAE check passed for system {system_id}: {mae:.2f}")
    
    log_entry = {
        "system": system_id,
        "mae": round(mae, 2),
        "status": status
    }
    
    # Append to log file
    with open(output_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    if status == "FAIL":
        logger.error(f"Halting due to failed fidelity check for {system_id}")
        return False
    
    return True

def run_fidelity_check(
    results_path: str,
    system_id: str = "Cu-Zn",
    threshold: float = 50000.0,
    output_path: str = "data/artifacts/fidelity_check.log"
) -> bool:
    """
    Main function to run fidelity check on LOSO results.
    
    Args:
        results_path: Path to LOSO evaluation results JSON
        system_id: System identifier to log
        threshold: MAE threshold for pass/fail
        output_path: Path to fidelity check log file
    
    Returns:
        True if check passes, False otherwise
    """
    try:
        log_info(logger, f"Loading LOSO results from {results_path}")
        results = load_loso_results(results_path)
        
        log_info(logger, f"Calculating aggregate MAE from {len(results)} folds")
        aggregate_mae = calculate_aggregate_mae(results)
        
        log_info(logger, f"Aggregate MAE: {aggregate_mae:.2f}")
        
        success = log_fidelity_check(
            system_id=system_id,
            mae=aggregate_mae,
            threshold=threshold,
            output_path=output_path
        )
        
        if not success:
            log_error(
                logger,
                f"Fidelity check failed for {system_id}: MAE={aggregate_mae:.2f}",
                ErrorCode.LOW_DATA_DENSITY
            )
            return False
        
        log_info(logger, f"Fidelity check completed successfully for {system_id}")
        return True
        
    except FileNotFoundError as e:
        log_error(logger, str(e), ErrorCode.DATA_SOURCE_MISSING)
        return False
    except Exception as e:
        log_error(logger, f"Unexpected error during fidelity check: {str(e)}", None)
        return False

def main():
    """Command-line entry point for fidelity check."""
    parser = argparse.ArgumentParser(
        description="Run MAE fidelity check for visual phase diagram assessment"
    )
    parser.add_argument(
        "--results",
        type=str,
        default="data/artifacts/loso_results.json",
        help="Path to LOSO evaluation results JSON"
    )
    parser.add_argument(
        "--system",
        type=str,
        default="Cu-Zn",
        help="System identifier for logging"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=50000.0,
        help="MAE threshold for pass/fail (default: 50000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/artifacts/fidelity_check.log",
        help="Path to fidelity check log file"
    )
    
    args = parser.parse_args()
    
    success = run_fidelity_check(
        results_path=args.results,
        system_id=args.system,
        threshold=args.threshold,
        output_path=args.output
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()