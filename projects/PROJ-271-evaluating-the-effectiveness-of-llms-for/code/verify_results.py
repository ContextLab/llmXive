"""Verification script for statistical results."""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from config import get_results_path, setup_logging

logger = setup_logging(__name__)


def load_json_file(filepath: str) -> dict:
    """Load a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def load_markdown_file(filepath: str) -> str:
    """Load a markdown file."""
    with open(filepath, "r") as f:
        return f.read()


def validate_statistical_significance(data: dict) -> bool:
    """Validate statistical significance results."""
    if not isinstance(data, dict):
        return False
    return all(isinstance(v, (float, type(None))) for v in data.values())


def validate_logistic_regression(data: dict) -> bool:
    """Validate logistic regression results."""
    if not isinstance(data, dict):
        return False
    return "vif_scores" in data and "regression" in data


def validate_sensitivity_report(content: str) -> bool:
    """Validate sensitivity report content."""
    return "LOC Thresholds Analysis" in content and "Threshold" in content


def verify_results_completeness() -> bool:
    """Verify all result files exist and are valid."""
    files = {
        "statistical_significance.json": validate_statistical_significance,
        "logistic_regression.json": validate_logistic_regression,
        "sensitivity_report.md": validate_sensitivity_report,
    }

    all_valid = True
    for filename, validator in files.items():
        filepath = get_results_path(filename)
        if not os.path.exists(filepath):
            logger.error(f"Missing file: {filename}")
            all_valid = False
            continue

        try:
            if filename.endswith(".json"):
                data = load_json_file(filepath)
            else:
                data = load_markdown_file(filepath)

            if not validator(data):
                logger.error(f"Invalid content in {filename}")
                all_valid = False
            else:
                logger.info(f"Validated {filename}")
        except Exception as e:
            logger.error(f"Error validating {filename}: {e}")
            all_valid = False

    return all_valid


def main():
    """Main entry point."""
    if verify_results_completeness():
        print("All results verified.")
    else:
        print("Verification failed.")


if __name__ == "__main__":
    main()
