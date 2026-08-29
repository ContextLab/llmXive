import os
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

def load_validation_result(path: str) -> Dict[str, Any]:
    """
    Load the permutation test validation result from a JSON file.
    Raises FileNotFoundError if the file does not exist.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Validation result file not found: {path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_validation_result(data: Dict[str, Any], path: str) -> None:
    """
    Save the validation result to a JSON file.
    Creates parent directories if they do not exist.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def run_permutation_test_gate(validation_result_path: str = "data/results/proxy_validation.json",
                              output_path: str = "data/results/gate_result.json") -> bool:
    """
    Pre-Deployment Gate: Validates the permutation test p-value.
    
    Logic:
    1. Load the validation result containing the permutation test p-value.
    2. Check if p-value <= 0.05.
       - If p <= 0.05: The model has likely learned shuffled labels (overfitting).
         Block deployment by raising SystemExit.
       - If p > 0.05: The model is valid. Proceed.
    
    Args:
        validation_result_path: Path to the JSON file containing permutation test results.
        output_path: Path to save the gate decision result.
    
    Returns:
        True if the gate passes (p > 0.05).
    
    Raises:
        SystemExit: If p <= 0.05 (overfitting detected).
        FileNotFoundError: If the validation result file is missing.
    """
    logger.info(f"Loading validation result from {validation_result_path}")
    
    try:
        result = load_validation_result(validation_result_path)
    except FileNotFoundError as e:
        logger.error(f"Validation file missing: {e}")
        raise
    
    if 'permutation_test' not in result:
        logger.error("Permutation test results not found in validation file.")
        raise KeyError("Missing 'permutation_test' key in validation result.")
    
    p_value = result['permutation_test'].get('p_value')
    
    if p_value is None:
        logger.error("Permutation test p-value is missing.")
        raise KeyError("Missing 'p_value' in permutation test results.")
    
    logger.info(f"Permutation test p-value: {p_value}")
    
    gate_passed = True
    reason = ""
    
    if p_value <= 0.05:
        gate_passed = False
        reason = f"Overfitting detected: p-value ({p_value}) <= 0.05. Model learned shuffled labels."
        logger.error(reason)
        
        # Save gate failure status
        gate_result = {
            "status": "BLOCKED",
            "reason": reason,
            "p_value": p_value,
            "threshold": 0.05,
            "gate": "pre_deployment"
        }
        save_validation_result(gate_result, output_path)
        
        raise SystemExit(1)
    else:
        reason = f"Gate passed: p-value ({p_value}) > 0.05. No evidence of overfitting."
        logger.info(reason)
        
        # Save gate success status
        gate_result = {
            "status": "PASSED",
            "reason": reason,
            "p_value": p_value,
            "threshold": 0.05,
            "gate": "pre_deployment"
        }
        save_validation_result(gate_result, output_path)
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Pre-Deployment Gate: Check Permutation Test P-Value")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/results/proxy_validation.json",
        help="Path to the validation result JSON file containing permutation test data."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/results/gate_result.json",
        help="Path to save the gate decision result."
    )
    
    args = parser.parse_args()
    
    try:
        run_permutation_test_gate(args.input, args.output)
        logger.info("Pre-deployment gate PASSED. Deployment authorized.")
    except SystemExit as e:
        if e.code == 1:
            logger.error("Pre-deployment gate FAILED. Deployment BLOCKED.")
            sys.exit(1)
        raise
    except Exception as e:
        logger.error(f"Gate execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
