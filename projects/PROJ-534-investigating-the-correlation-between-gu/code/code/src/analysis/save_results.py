import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Import from existing API surface
from code.src.utils.config import get_results_dir, ensure_directories, setup_logging
from code.src.analysis.correlation import run_correlation_analysis

logger = logging.getLogger(__name__)

def validate_result_structure(result: Dict[str, Any]) -> bool:
    """
    Validates that a single result dictionary contains the required keys
    as per contracts/analysis_output.schema.yaml.
    """
    required_keys = [
        "correlation_coefficient",
        "p_value",
        "adjusted_p_value",
        "confidence_interval"
    ]
    for key in required_keys:
        if key not in result:
            logger.error(f"Missing required key '{key}' in result structure.")
            return False
    
    # Validate types
    if not isinstance(result["correlation_coefficient"], (int, float)):
        logger.error("correlation_coefficient must be a number.")
        return False
    if not isinstance(result["p_value"], (int, float)):
        logger.error("p_value must be a number.")
        return False
    if not isinstance(result["adjusted_p_value"], (int, float)):
        logger.error("adjusted_p_value must be a number.")
        return False
    if not isinstance(result["confidence_interval"], (list, tuple)) or len(result["confidence_interval"]) != 2:
        logger.error("confidence_interval must be a list/tuple of two numbers.")
        return False
    
    return True

def save_correlation_results(
    results: List[Dict[str, Any]],
    output_filename: str = "correlation_results.json"
) -> Path:
    """
    Saves the correlation analysis results to a JSON file in the results directory.
    
    Args:
        results: List of dictionaries containing correlation statistics.
        output_filename: Name of the output file.
        
    Returns:
        Path to the saved file.
        
    Raises:
        ValueError: If any result fails schema validation.
    """
    results_dir = get_results_dir()
    ensure_directories()
    output_path = results_dir / output_filename

    # Validate all results before saving
    for i, res in enumerate(results):
        if not validate_result_structure(res):
            raise ValueError(f"Result at index {i} failed schema validation.")
        
        # Ensure confidence_interval is a list for JSON serialization
        if isinstance(res["confidence_interval"], tuple):
            res["confidence_interval"] = list(res["confidence_interval"])

    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Successfully saved correlation results to {output_path}")
        return output_path
    except IOError as e:
        logger.error(f"Failed to write results to {output_path}: {e}")
        raise

def main():
    """
    Main entry point to run correlation analysis and save results.
    This script is designed to be run after filtering (T013) and diversity calculation (T019).
    """
    setup_logging("save_results")
    logger.info("Starting correlation results generation and saving.")

    try:
        # Run the correlation analysis logic (T020/T021)
        # This assumes the filtered cohort exists at the expected path
        # and diversity metrics have been calculated and merged.
        # The run_correlation_analysis function handles the logic and returns structured results.
        results = run_correlation_analysis()
        
        if not results:
            logger.warning("No correlation results were generated.")
            return

        # Save to JSON
        output_path = save_correlation_results(results)
        logger.info(f"Task T023 complete. Output: {output_path}")

    except Exception as e:
        logger.error(f"Task T023 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
