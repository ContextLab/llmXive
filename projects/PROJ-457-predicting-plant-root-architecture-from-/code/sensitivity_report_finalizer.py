"""
T028c: Report Sensitivity
Update artifacts/sensitivity/sensitivity_analysis.json with final sensitivity report.

This task consumes the output from T028b (sensitivity_analysis.json) and ensures
the final report is complete, valid, and ready for downstream consumption (T029a).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import utilities from sibling modules as per API surface
from sensitivity_analysis import load_json_file, save_json_file
from config import get_config, setup_logging


def finalize_sensitivity_report(
    input_path: Path,
    output_path: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Read the intermediate sensitivity analysis, validate required keys,
    perform any final aggregations if needed, and write the final report.
    
    Args:
        input_path: Path to artifacts/sensitivity/sensitivity_analysis.json
        output_path: Path to write the final report
        logger: Logger instance
        
    Returns:
        The final report dictionary
        
    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If required keys are missing
    """
    logger.info(f"Loading sensitivity analysis from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    try:
        data = load_json_file(input_path)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {input_path}: {e}")
    
    # Validate required keys from T028b specification
    required_keys = [
        "percent_deviation",
        "literature_mean",
        "observed_coefficient",
        "confidence_interval",
        "literature_overlap"
    ]
    
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        raise ValueError(f"Missing required keys in sensitivity analysis: {missing_keys}")
    
    # Ensure types are correct
    if not isinstance(data["confidence_interval"], list) or len(data["confidence_interval"]) != 2:
        raise ValueError("confidence_interval must be a list of 2 numbers")
        
    if not isinstance(data["literature_overlap"], bool):
        raise ValueError("literature_overlap must be a boolean")
        
    # Add metadata for final report
    data["report_status"] = "finalized"
    data["validation_passed"] = True
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing finalized sensitivity report to {output_path}")
    save_json_file(output_path, data)
    
    logger.info("Sensitivity report finalized successfully")
    return data


def main():
    """Main entry point for T028c."""
    config = get_config()
    logger = setup_logging("sensitivity_report_finalizer", config)
    
    # Paths
    input_path = Path(config.get("SENSITIVITY_INPUT_PATH", 
                               "artifacts/sensitivity/sensitivity_analysis.json"))
    output_path = Path(config.get("SENSITIVITY_OUTPUT_PATH", 
                                "artifacts/sensitivity/sensitivity_analysis.json"))
    
    try:
        finalize_sensitivity_report(input_path, output_path, logger)
        logger.info("T028c completed successfully")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())