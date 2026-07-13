import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return Path(file_path).exists()

def validate_csv_columns(file_path: str, required_columns: List[str]) -> bool:
    """Validate that a CSV file has the required columns."""
    if not check_file_exists(file_path):
        logging.error(f"File not found: {file_path}")
        return False
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logging.error(f"Missing columns in {file_path}: {missing}")
            return False
        return True
    except Exception as e:
        logging.error(f"Error validating CSV {file_path}: {e}")
        return False

def validate_json_structure(file_path: str, required_keys: List[str]) -> bool:
    """Validate that a JSON file has the required keys."""
    if not check_file_exists(file_path):
        logging.error(f"File not found: {file_path}")
        return False
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        missing = [key for key in required_keys if key not in data]
        if missing:
            logging.error(f"Missing keys in {file_path}: {missing}")
            return False
        return True
    except Exception as e:
        logging.error(f"Error validating JSON {file_path}: {e}")
        return False

def run_validation():
    """Run validation checks on all required artifacts."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Running quickstart validation...")

    # Define required files and their validation criteria
    validations = [
        {
            "type": "csv",
            "path": "data/derived/trial_data.csv",
            "columns": ["participant_id", "trial_id", "stimulus_modality", "source_label", "participant_response", "confidence_rating"]
        },
        {
            "type": "csv",
            "path": "data/derived/visual_trials.csv",
            "columns": ["participant_id", "trial_id", "stimulus_modality", "source_label", "participant_response", "confidence_rating"]
        },
        {
            "type": "csv",
            "path": "data/derived/auditory_trials.csv",
            "columns": ["participant_id", "trial_id", "stimulus_modality", "source_label", "participant_response", "confidence_rating"]
        },
        {
            "type": "json",
            "path": "data/results/bootstrap_config.json",
            "keys": ["correlation", "bootstrap_count", "ci_low", "ci_high"]
        },
        {
            "type": "json",
            "path": "data/results/primary_analysis.json",
            "keys": ["correlation", "methodology", "analysis_type"]
        },
        {
            "type": "json",
            "path": "data/results/regression_analysis.json",
            "keys": ["model_1", "model_2", "delta_r_squared", "f_change"]
        },
        {
            "type": "json",
            "path": "data/results/robustness_analysis.json",
            "keys": ["visual", "auditory", "corrected_p_values"]
        }
    ]

    all_passed = True
    for validation in validations:
        if validation["type"] == "csv":
            passed = validate_csv_columns(validation["path"], validation["columns"])
        elif validation["type"] == "json":
            passed = validate_json_structure(validation["path"], validation["keys"])
        else:
            logging.warning(f"Unknown validation type: {validation['type']}")
            passed = False

        status = "PASS" if passed else "FAIL"
        logger.info(f"Validation for {validation['path']}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        logger.info("All validations passed.")
        return 0
    else:
        logger.error("Some validations failed.")
        return 1

def main():
    """Main entry point for the validator."""
    sys.exit(run_validation())

if __name__ == "__main__":
    main()
