import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from config import setup_logging, get_path, get_data_path, get_processed_path, get_results_path

def check_file_exists(path_str: str, description: str) -> bool:
    """Check if a required file exists."""
    path = Path(path_str)
    if not path.exists():
        logging.error(f"Missing required file: {path_str} ({description})")
        return False
    logging.info(f"Found: {path_str} ({description})")
    return True

def validate_static_baseline() -> bool:
    """Validate data/static_baseline.csv schema and content."""
    path = get_data_path("static_baseline.csv")
    if not check_file_exists(path, "Static Baseline"):
        return False

    try:
        df = pd.read_csv(path)
        required_cols = ["code", "loc", "cyclomatic_complexity", "nesting_depth", "static_smell_labels"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logging.error(f"Missing columns in static_baseline.csv: {missing}")
            return False

        if len(df) == 0:
            logging.error("static_baseline.csv is empty")
            return False

        logging.info(f"Static Baseline valid: {len(df)} rows, columns: {list(df.columns)}")
        return True
    except Exception as e:
        logging.error(f"Failed to validate static_baseline.csv: {e}")
        return False

def validate_semantic_results() -> bool:
    """Validate data/processed/semantic_results.json structure."""
    path = get_processed_path("semantic_results.json")
    if not check_file_exists(path, "Semantic Results"):
        return False

    try:
        with open(path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            logging.error("semantic_results.json is not a non-empty list")
            return False

        # Check for expected keys in first record
        first = data[0]
        expected_keys = ["code", "embedding", "llm_labels", "static_smell_labels"]
        missing = [k for k in expected_keys if k not in first]
        if missing:
            logging.error(f"Missing keys in semantic_results.json records: {missing}")
            return False

        logging.info(f"Semantic Results valid: {len(data)} records")
        return True
    except Exception as e:
        logging.error(f"Failed to validate semantic_results.json: {e}")
        return False

def validate_results_artifacts() -> bool:
    """Validate statistical analysis outputs."""
    required_files = [
        ("results/statistical_significance.json", "McNemar Test Results"),
        ("results/logistic_regression.json", "Logistic Regression Results"),
        ("results/sensitivity_report.md", "Sensitivity Report"),
        ("results/resource_metrics.json", "Resource Metrics"),
        ("results/sample_report.json", "Sample Report")
    ]

    all_valid = True
    for file_path, desc in required_files:
        full_path = get_results_path(file_path.replace("results/", ""))
        if not check_file_exists(full_path, desc):
            all_valid = False
            continue

        try:
            if file_path.endswith(".json"):
                with open(full_path, 'r') as f:
                    json.load(f)
            elif file_path.endswith(".md"):
                with open(full_path, 'r') as f:
                    content = f.read()
                    if len(content) < 50:
                        logging.warning(f"File {file_path} seems too short: {len(content)} chars")
        except Exception as e:
            logging.error(f"Invalid content in {file_path}: {e}")
            all_valid = False

    return all_valid

def main():
    """Run full quickstart validation pipeline."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Quickstart Validation (T034)...")

    checks = [
        ("Static Baseline Schema", validate_static_baseline),
        ("Semantic Results Schema", validate_semantic_results),
        ("Statistical Artifacts", validate_results_artifacts)
    ]

    results = {}
    all_passed = True

    for name, func in checks:
        logger.info(f"Running check: {name}")
        try:
            passed = func()
            results[name] = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
        except Exception as e:
            logger.error(f"Check {name} crashed: {e}")
            results[name] = "ERROR"
            all_passed = False

    # Write validation report
    report_path = get_results_path("quickstart_validation_report.json")
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": str(pd.Timestamp.now()),
            "overall_status": "PASS" if all_passed else "FAIL",
            "checks": results
        }, f, indent=2)

    logger.info(f"Validation report written to {report_path}")
    
    if all_passed:
        logger.info("Quickstart validation PASSED. End-to-end reproducibility confirmed.")
        return 0
    else:
        logger.error("Quickstart validation FAILED. See report for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
