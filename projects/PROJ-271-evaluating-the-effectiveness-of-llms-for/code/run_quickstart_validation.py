import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path

from config import setup_logging, get_data_path, get_processed_path, get_results_path

logger = logging.getLogger(__name__)

def check_file_exists(path: str) -> bool:
    """Checks if a file exists."""
    return Path(path).exists()

def validate_static_baseline() -> bool:
    """Validates the static baseline CSV."""
    path = get_data_path("static_baseline.csv")
    if not check_file_exists(path):
        return False
    
    df = pd.read_csv(path)
    required_cols = ["code", "loc", "cyclomatic_complexity", "static_smell_labels"]
    return all(col in df.columns for col in required_cols)

def validate_semantic_results() -> bool:
    """Validates the semantic results JSON."""
    path = get_processed_path("semantic_results.json")
    if not check_file_exists(path):
        return False
    
    with open(path, "r") as f:
        data = json.load(f)
    
    return "embeddings" in data and "llm_labels" in data

def validate_results_artifacts() -> bool:
    """Validates results artifacts."""
    files = [
        get_results_path("statistical_significance.json"),
        get_results_path("logistic_regression.json"),
        get_results_path("sensitivity_report.md")
    ]
    return all(check_file_exists(f) for f in files)

def main():
    setup_logging()
    logger.info("Running quickstart validation...")
    
    checks = [
        ("Static Baseline", validate_static_baseline),
        ("Semantic Results", validate_semantic_results),
        ("Results Artifacts", validate_results_artifacts)
    ]
    
    all_pass = True
    for name, check in checks:
        if check():
            logger.info(f"{name}: PASSED")
        else:
            logger.error(f"{name}: FAILED")
            all_pass = False
    
    if all_pass:
        logger.info("All validations passed.")
    else:
        logger.error("Some validations failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
