import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from config import get_results_path, setup_logging


def load_json_file(path: str) -> Any:
    """Load a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def load_markdown_file(path: str) -> str:
    """Load a markdown file."""
    with open(path, "r") as f:
        return f.read()


def validate_statistical_significance(json_path: str) -> bool:
    """Validate statistical significance JSON."""
    try:
        data = load_json_file(json_path)
        if "mcnemar_pvalues" not in data or "drop_off" not in data:
            logging.getLogger(__name__).error("Missing required fields in statistical significance JSON.")
            return False
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Validation failed: {e}")
        return False


def validate_logistic_regression(json_path: str) -> bool:
    """Validate logistic regression JSON."""
    try:
        data = load_json_file(json_path)
        if "coefficients" not in data or "vif_scores" not in data:
            logging.getLogger(__name__).error("Missing required fields in logistic regression JSON.")
            return False
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Validation failed: {e}")
        return False


def validate_sensitivity_report(md_path: str) -> bool:
    """Validate sensitivity report markdown."""
    try:
        content = load_markdown_file(md_path)
        if "Threshold" not in content or "FP Rate" not in content:
            logging.getLogger(__name__).error("Invalid sensitivity report format.")
            return False
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Validation failed: {e}")
        return False


def verify_results_completeness() -> bool:
    """Verify all required results artifacts exist and are valid."""
    logger = setup_logging(__name__)
    results_path = get_results_path()

    artifacts = [
        ("statistical_significance.json", validate_statistical_significance),
        ("logistic_regression.json", validate_logistic_regression),
        ("sensitivity_report.md", validate_sensitivity_report),
        ("sensitivity_metrics.json", lambda p: os.path.exists(p))
    ]

    all_valid = True
    for artifact, validator in artifacts:
        path = os.path.join(results_path, artifact)
        if not os.path.exists(path):
            logger.error(f"Missing artifact: {artifact}")
            all_valid = False
        elif not validator(path):
            logger.error(f"Invalid artifact: {artifact}")
            all_valid = False
        else:
            logger.info(f"Artifact valid: {artifact}")

    return all_valid


def main():
    """Main entry point for results verification."""
    if verify_results_completeness():
        print("All results artifacts are valid.")
        exit(0)
    else:
        print("Some results artifacts are missing or invalid.")
        exit(1)
