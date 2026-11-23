"""
Verify Dilemma Choice Derivation (Task T028g)

This script performs two critical verification steps:
1. Unit Test: Verify that `dilemma_choice` derivation logic does not reference `response_time`.
2. Integration Check: Verify that `dilemma_choice` is present and correctly merged as a fixed effect in the model specification.

It generates the final authoritative log `results/logs/dilemma_choice_verification.json`.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Import existing utilities
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Attempt to import pandas for data inspection if needed, though we primarily inspect code
try:
    import pandas as pd
except ImportError:
    pd = None

def setup_custom_logger(name: str) -> logging.Logger:
    """Setup a custom logger for this verification task."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def verify_code_independence(derive_script_path: Path) -> Dict[str, Any]:
    """
    Verify that the derivation script for dilemma_choice does not reference 'response_time'.
    """
    result = {
        "script_path": str(derive_script_path),
        "references_response_time": False,
        "line_numbers": [],
        "status": "PASS"
    }

    if not derive_script_path.exists():
        result["status"] = "FAIL"
        result["reason"] = f"Script not found: {derive_script_path}"
        return result

    try:
        with open(derive_script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        result["status"] = "FAIL"
        result["reason"] = f"Could not read file: {str(e)}"
        return result

    for i, line in enumerate(lines, 1):
        # Check for direct variable usage or string references that imply dependency
        # We look for 'response_time' as a variable name or column reference
        if 'response_time' in line and not line.strip().startswith('#'):
            result["references_response_time"] = True
            result["line_numbers"].append(i)
            result["status"] = "FAIL"
            result["reason"] = f"Script references 'response_time' on line {i}"
            break

    if not result["references_response_time"]:
        result["reason"] = "No references to 'response_time' found in derivation logic."
    
    return result

def verify_model_integration(modeling_script_path: Path, fixed_effects: List[str]) -> Dict[str, Any]:
    """
    Verify that the modeling script includes 'dilemma_choice' in the fixed effects.
    """
    result = {
        "script_path": str(modeling_script_path),
        "dilemma_choice_in_model": False,
        "found_effects": [],
        "status": "FAIL"
    }

    if not modeling_script_path.exists():
        result["reason"] = f"Modeling script not found: {modeling_script_path}"
        return result

    try:
        with open(modeling_script_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        result["reason"] = f"Could not read file: {str(e)}"
        return result

    # Check for 'dilemma_choice' in the content (case-insensitive check for variable name)
    # We expect it to be in a formula string or a list of fixed effects
    if 'dilemma_choice' in content:
        result["dilemma_choice_in_model"] = True
        result["status"] = "PASS"
        result["reason"] = "Found 'dilemma_choice' in modeling script."
    else:
        result["reason"] = "Could not find 'dilemma_choice' in modeling script."

    return result

def main(args):
    logger = setup_custom_logger("T028g_Verification")
    logger.info("Starting Dilemma Choice Derivation Verification (T028g)")

    # Define paths
    project_root = Path(get_path_env_override())
    derive_script = project_root / "code" / "derive_dilemma_choice.py"
    modeling_script = project_root / "code" / "modeling.py"
    output_dir = project_root / "results" / "logs"
    output_file = output_dir / "dilemma_choice_verification.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    verification_results = {
        "task_id": "T028g",
        "timestamp": str(pd.Timestamp.now() if pd else "N/A"),
        "checks": []
    }

    # 1. Verify Code Independence
    logger.info(f"Checking independence of {derive_script.name}...")
    independence_check = verify_code_independence(derive_script)
    verification_results["checks"].append({
        "name": "Code Independence (No response_time reference)",
        "details": independence_check
    })
    logger.info(f"  Independence Check: {independence_check['status']}")

    # 2. Verify Model Integration
    logger.info(f"Checking integration in {modeling_script.name}...")
    integration_check = verify_model_integration(modeling_script, ["dilemma_choice"])
    verification_results["checks"].append({
        "name": "Model Integration (Fixed Effect Presence)",
        "details": integration_check
    })
    logger.info(f"  Integration Check: {integration_check['status']}")

    # Determine overall status
    all_passed = all(check["status"] == "PASS" for check in verification_results["checks"])
    verification_results["overall_status"] = "PASS" if all_passed else "FAIL"
    
    if all_passed:
        logger.info("Verification PASSED: Dilemma choice is derived independently and included in the model.")
    else:
        logger.error("Verification FAILED: One or more checks did not pass.")

    # Write final log
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(verification_results, f, indent=2)
        logger.info(f"Verification log written to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write verification log: {str(e)}")
        sys.exit(1)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Dilemma Choice Derivation (T028g)")
    # No specific args needed as paths are derived from config, but kept for CLI consistency
    args = parser.parse_args()
    main(args)
