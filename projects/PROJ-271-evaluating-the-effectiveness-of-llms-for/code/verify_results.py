import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

from config import get_results_path, setup_logging

logger = logging.getLogger(__name__)

def load_json_file(path: str) -> dict:
    """Loads a JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def load_markdown_file(path: str) -> str:
    """Loads a markdown file."""
    with open(path, "r") as f:
        return f.read()

def validate_statistical_significance() -> bool:
    """Validates statistical significance results."""
    path = get_results_path("statistical_significance.json")
    if not os.path.exists(path):
        return False
    data = load_json_file(path)
    return "mcnemar_p_value" in data

def validate_logistic_regression() -> bool:
    """Validates logistic regression results."""
    path = get_results_path("logistic_regression.json")
    if not os.path.exists(path):
        return False
    data = load_json_file(path)
    return "coefficients" in data

def validate_sensitivity_report() -> bool:
    """Validates sensitivity report."""
    path = get_results_path("sensitivity_report.md")
    return os.path.exists(path)

def verify_results_completeness() -> bool:
    """Verifies completeness of results."""
    checks = [
        validate_statistical_significance(),
        validate_logistic_regression(),
        validate_sensitivity_report()
    ]
    return all(checks)

def main():
    setup_logging()
    if verify_results_completeness():
        logger.info("Results verification passed.")
    else:
        logger.error("Results verification failed.")

if __name__ == "__main__":
    main()
