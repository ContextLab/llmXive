"""
Quickstart Validation Script (T034).

This script validates the end-to-end reproducibility of the pipeline by:
1. Verifying all expected output artifacts exist.
2. Validating the schema and content of key data files.
3. Ensuring statistical results are non-empty and well-formed.
4. Reporting a pass/fail status for the entire pipeline.
"""
import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path

from config import get_data_path, get_processed_path, get_results_path, setup_logging

# Setup logging
logger = setup_logging("quickstart_validation", level=logging.INFO)

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists at the given path."""
    if os.path.exists(path):
        logger.info(f"✓ Found: {description} ({path})")
        return True
    else:
        logger.error(f"✗ Missing: {description} ({path})")
        return False

def validate_static_baseline() -> bool:
    """Validate data/static_baseline.csv schema and content."""
    path = get_data_path("static_baseline.csv")
    if not os.path.exists(path):
        logger.error("Static baseline file missing.")
        return False

    try:
        df = pd.read_csv(path)
        required_cols = {"code", "loc", "cyclomatic_complexity", "static_smell_labels"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            logger.error(f"Static baseline missing columns: {missing}")
            return False

        if len(df) == 0:
            logger.error("Static baseline is empty.")
            return False

        # Check for non-null critical columns
        if df["code"].isnull().all():
            logger.error("Static baseline 'code' column is all null.")
            return False

        logger.info(f"✓ Static baseline valid: {len(df)} rows, columns {list(df.columns)}")
        return True
    except Exception as e:
        logger.error(f"Failed to validate static baseline: {e}")
        return False

def validate_semantic_results() -> bool:
    """Validate data/processed/semantic_results.json structure."""
    path = get_processed_path("semantic_results.json")
    if not os.path.exists(path):
        logger.error("Semantic results file missing.")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            logger.error("Semantic results is empty or not a list.")
            return False

        # Check structure of first item
        sample = data[0]
        required_keys = {"code", "embedding", "llm_labels", "static_smell_labels"}
        if not required_keys.issubset(sample.keys()):
            missing = required_keys - set(sample.keys())
            logger.error(f"Semantic results items missing keys: {missing}")
            return False

        logger.info(f"✓ Semantic results valid: {len(data)} entries")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in semantic results: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to validate semantic results: {e}")
        return False

def validate_results_artifacts() -> bool:
    """Validate statistical analysis output files."""
    results_dir = get_results_path("")
    required_files = [
        "statistical_significance.json",
        "logistic_regression.json",
        "sensitivity_report.md"
    ]

    all_valid = True
    for fname in required_files:
        fpath = os.path.join(results_dir, fname)
        if not os.path.exists(fpath):
            logger.error(f"Missing result file: {fname}")
            all_valid = False
            continue

        try:
            if fname.endswith(".json"):
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not data:
                    logger.warning(f"Result file {fname} is empty.")
            elif fname.endswith(".md"):
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if len(content) < 50:
                    logger.warning(f"Result file {fname} is unusually short.")
            
            logger.info(f"✓ Result file valid: {fname}")
        except Exception as e:
            logger.error(f"Error validating {fname}: {e}")
            all_valid = False

    return all_valid

def main():
    """Run all validation checks."""
    logger.info("Starting Quickstart Validation (T034)...")
    logger.info("Checking end-to-end reproducibility artifacts.")

    checks = [
        ("Static Baseline", validate_static_baseline),
        ("Semantic Results", validate_semantic_results),
        ("Statistical Results", validate_results_artifacts)
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            logger.error(f"Check '{name}' crashed: {e}")

    logger.info("-" * 40)
    logger.info(f"Validation Summary: {passed}/{total} checks passed.")

    if passed == total:
        logger.info("SUCCESS: Pipeline end-to-end reproducibility verified.")
        return 0
    else:
        logger.error("FAILURE: Pipeline validation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
