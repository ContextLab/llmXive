"""
Validator script to check declared deliverables after the pipeline run.
This script ensures that T006 and subsequent tasks produce their required outputs.
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Base directory relative to project root
BASE_DIR = Path(__file__).resolve().parent

# Declared deliverables to check
DELIVERABLES = [
    "data/validation_report.json",       # T006
    "data/derived/trial_data.csv",       # T012
    "data/derived/visual_trials.csv",    # T026
    "data/derived/auditory_trials.csv",  # T026
    "data/results/bootstrap_config.json",# T015
    "data/results/primary_analysis.json",# T016
    "data/results/regression_analysis.json", # T022
    "data/results/robustness_analysis.json", # T028
]

def check_file_exists(relative_path: str) -> bool:
    full_path = BASE_DIR / relative_path
    exists = full_path.exists()
    if exists:
        logger.info(f"✓ Found: {relative_path}")
    else:
        logger.error(f"✗ Missing: {relative_path}")
    return exists

def validate_csv_columns(relative_path: str, required_cols: list) -> bool:
    import pandas as pd
    full_path = BASE_DIR / relative_path
    try:
        df = pd.read_csv(full_path)
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.error(f"✗ {relative_path} missing columns: {missing}")
            return False
        logger.info(f"✓ {relative_path} columns valid")
        return True
    except Exception as e:
        logger.error(f"✗ Error reading {relative_path}: {e}")
        return False

def validate_json_structure(relative_path: str, required_keys: list) -> bool:
    full_path = BASE_DIR / relative_path
    try:
        with open(full_path, 'r') as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        if missing:
            logger.error(f"✗ {relative_path} missing keys: {missing}")
            return False
        logger.info(f"✓ {relative_path} structure valid")
        return True
    except Exception as e:
        logger.error(f"✗ Error reading {relative_path}: {e}")
        return False

def run_validation():
    logger.info("Starting validation of declared deliverables...")
    all_passed = True

    # Check T006 output
    if not check_file_exists("data/validation_report.json"):
        all_passed = False
    else:
        if not validate_json_structure("data/validation_report.json", ["status"]):
            all_passed = False

    # Check T012 output
    if not check_file_exists("data/derived/trial_data.csv"):
        all_passed = False
    else:
        cols = ["participant_id", "trial_id", "stimulus_modality", "source_label", "participant_response", "confidence_rating"]
        if not validate_csv_columns("data/derived/trial_data.csv", cols):
            all_passed = False

    # Check T026 outputs
    for mod in ["visual_trials.csv", "auditory_trials.csv"]:
        path = f"data/derived/{mod}"
        if not check_file_exists(path):
            all_passed = False

    # Check T015 output
    if not check_file_exists("data/results/bootstrap_config.json"):
        all_passed = False
    else:
        if not validate_json_structure("data/results/bootstrap_config.json", ["bootstrap_count"]):
            all_passed = False

    # Check T016 output
    if not check_file_exists("data/results/primary_analysis.json"):
        all_passed = False
    else:
        if not validate_json_structure("data/results/primary_analysis.json", ["r", "p", "ci_lower", "ci_upper"]):
            all_passed = False

    # Check T022 output
    if not check_file_exists("data/results/regression_analysis.json"):
        all_passed = False
    else:
        if not validate_json_structure("data/results/regression_analysis.json", ["model_1", "model_2"]):
            all_passed = False

    # Check T028 output
    if not check_file_exists("data/results/robustness_analysis.json"):
        all_passed = False

    if all_passed:
        logger.info("All declared deliverables present and valid.")
        return 0
    else:
        logger.error("Some declared deliverables are missing or invalid.")
        return 1

def main():
    sys.exit(run_validation())

if __name__ == "__main__":
    main()