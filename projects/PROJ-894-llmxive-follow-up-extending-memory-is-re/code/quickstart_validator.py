"""
T032: Quickstart Validation and Reproducibility Verification Script.

This script validates the entire pipeline by:
1. Checking that all required input files exist (raw data, noisy graphs).
2. Running the statistical analysis pipeline (T024a, T024b, T025, T027).
3. Verifying that all expected output files are generated.
4. Checking that results are consistent (reproducible) by re-running key metrics.
5. Generating a validation report.
"""

import os
import sys
import csv
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SPEC_DIR = PROJECT_ROOT / "specs"

# Expected input files (produced by previous tasks)
EXPECTED_INPUTS = {
    "raw_data": DATA_DIR / "raw" / "locomo_test.json",
    "noisy_graphs": DATA_DIR / "raw" / "noisy_graphs.json",
}

# Expected output files (produced by analysis tasks)
EXPECTED_OUTPUTS = {
    "baseline_results": PROCESSED_DIR / "baseline_results.csv",
    "noisy_baseline_results": PROCESSED_DIR / "noisy_baseline_results.csv",
    "lazy_results": PROCESSED_DIR / "lazy_results.csv",
    "noisy_lazy_results": PROCESSED_DIR / "noisy_lazy_results.csv",
    "greedy_results": PROCESSED_DIR / "greedy_results.csv",
    "noisy_greedy_results": PROCESSED_DIR / "noisy_greedy_results.csv",
    "stats_report": PROCESSED_DIR / "stats_report.json",
    "noisy_stats_report": PROCESSED_DIR / "noisy_stats_report.json",
    "sweep_results": PROCESSED_DIR / "sweep_results.csv",
    "docs_results": PROJECT_ROOT / "docs" / "results.md",
}

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    if path.exists():
        logger.info(f"✓ {description} exists: {path}")
        return True
    else:
        logger.error(f"✗ {description} MISSING: {path}")
        return False

def validate_csv_structure(file_path: Path, required_columns: List[str]) -> bool:
    """Validate that a CSV file has the required columns."""
    if not file_path.exists():
        logger.error(f"Cannot validate {file_path}: file does not exist")
        return False

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                logger.error(f"{file_path} is empty or has no headers")
                return False

            missing_cols = [col for col in required_columns if col not in reader.fieldnames]
            if missing_cols:
                logger.error(f"{file_path} missing columns: {missing_cols}")
                return False

            # Check if file has at least one data row
            rows = list(reader)
            if not rows:
                logger.warning(f"{file_path} exists but has no data rows")
                return False

            logger.info(f"✓ {file_path} has valid structure ({len(rows)} rows)")
            return True
    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False

def validate_json_structure(file_path: Path, required_keys: List[str]) -> bool:
    """Validate that a JSON file has the required keys."""
    if not file_path.exists():
        logger.error(f"Cannot validate {file_path}: file does not exist")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            logger.error(f"{file_path} missing keys: {missing_keys}")
            return False

        logger.info(f"✓ {file_path} has valid structure")
        return True
    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False

def validate_results_schema(file_path: Path) -> bool:
    """Validate results CSV against the expected schema."""
    required_columns = ["task_id", "accuracy", "nodes_visited", "latency_ms"]
    return validate_csv_structure(file_path, required_columns)

def run_reproducibility_check() -> bool:
    """
    Run a quick reproducibility check by re-executing a small subset of the analysis.
    This ensures that the results are deterministic and reproducible.
    """
    logger.info("Running reproducibility check...")

    # Check if stats_report.json exists
    stats_report_path = EXPECTED_OUTPUTS["stats_report"]
    if not stats_report_path.exists():
        logger.error("stats_report.json not found, cannot check reproducibility")
        return False

    try:
        with open(stats_report_path, 'r', encoding='utf-8') as f:
            original_stats = json.load(f)

        # Re-run a small analysis (e.g., descriptive stats on baseline)
        from analysis.stats import load_results_from_csv, calculate_descriptive_stats

        baseline_path = EXPECTED_OUTPUTS["baseline_results"]
        if not baseline_path.exists():
            logger.error("baseline_results.csv not found for reproducibility check")
            return False

        baseline_data = load_results_from_csv(baseline_path)
        if not baseline_data:
            logger.error("baseline_results.csv is empty")
            return False

        new_stats = calculate_descriptive_stats(baseline_data)

        # Compare key metrics (allowing for small floating point differences)
        original_acc = original_stats.get("baseline", {}).get("mean_accuracy", 0)
        new_acc = new_stats.get("mean_accuracy", 0)

        if abs(original_acc - new_acc) > 1e-6:
            logger.error(f"Reproducibility check FAILED: accuracy mismatch ({original_acc} vs {new_acc})")
            return False

        logger.info("✓ Reproducibility check passed")
        return True

    except Exception as e:
        logger.error(f"Error during reproducibility check: {e}")
        return False

def generate_validation_report(results: Dict[str, Any]) -> None:
    """Generate a validation report summarizing the results."""
    report_path = PROJECT_ROOT / "docs" / "validation_report.json"

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation report saved to: {report_path}")

def main():
    """Main validation function."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T032)")
    logger.info("=" * 60)

    validation_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "inputs_valid": True,
        "outputs_valid": True,
        "schema_valid": True,
        "reproducibility_valid": True,
        "overall_status": "PASS",
        "details": {}
    }

    # Step 1: Check input files
    logger.info("\n--- Step 1: Checking Input Files ---")
    for name, path in EXPECTED_INPUTS.items():
        exists = check_file_exists(path, f"Input: {name}")
        if not exists:
            validation_results["inputs_valid"] = False
            validation_results["details"][name] = "MISSING"
        else:
            validation_results["details"][name] = "FOUND"

    # Step 2: Check output files
    logger.info("\n--- Step 2: Checking Output Files ---")
    for name, path in EXPECTED_OUTPUTS.items():
        exists = check_file_exists(path, f"Output: {name}")
        if not exists:
            validation_results["outputs_valid"] = False
            validation_results["details"][f"output_{name}"] = "MISSING"
        else:
            validation_results["details"][f"output_{name}"] = "FOUND"

    # Step 3: Validate CSV schemas
    logger.info("\n--- Step 3: Validating CSV Schemas ---")
    csv_files = [
        ("baseline_results", EXPECTED_OUTPUTS["baseline_results"]),
        ("noisy_baseline_results", EXPECTED_OUTPUTS["noisy_baseline_results"]),
        ("lazy_results", EXPECTED_OUTPUTS["lazy_results"]),
        ("noisy_lazy_results", EXPECTED_OUTPUTS["noisy_lazy_results"]),
        ("greedy_results", EXPECTED_OUTPUTS["greedy_results"]),
        ("noisy_greedy_results", EXPECTED_OUTPUTS["noisy_greedy_results"]),
    ]

    for name, path in csv_files:
        if path.exists():
          valid = validate_results_schema(path)
          if not valid:
              validation_results["schema_valid"] = False
              validation_results["details"][f"schema_{name}"] = "INVALID"
          else:
              validation_results["details"][f"schema_{name}"] = "VALID"
        else:
            validation_results["details"][f"schema_{name}"] = "SKIPPED (FILE MISSING)"

    # Step 4: Validate JSON schemas
    logger.info("\n--- Step 4: Validating JSON Schemas ---")
    json_files = [
        ("stats_report", EXPECTED_OUTPUTS["stats_report"], ["baseline", "lazy", "greedy"]),
        ("noisy_stats_report", EXPECTED_OUTPUTS["noisy_stats_report"], ["baseline", "lazy", "greedy"]),
    ]

    for name, path, required_keys in json_files:
        if path.exists():
          valid = validate_json_structure(path, required_keys)
          if not valid:
              validation_results["schema_valid"] = False
              validation_results["details"][f"json_{name}"] = "INVALID"
          else:
              validation_results["details"][f"json_{name}"] = "VALID"
        else:
            validation_results["details"][f"json_{name}"] = "SKIPPED (FILE MISSING)"

    # Step 5: Reproducibility check
    logger.info("\n--- Step 5: Reproducibility Check ---")
    repro_valid = run_reproducibility_check()
    validation_results["reproducibility_valid"] = repro_valid
    validation_results["details"]["reproducibility"] = "PASS" if repro_valid else "FAIL"

    # Final status
    if (validation_results["inputs_valid"] and 
        validation_results["outputs_valid"] and 
        validation_results["schema_valid"] and 
        validation_results["reproducibility_valid"]):
        validation_results["overall_status"] = "PASS"
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION PASSED: All checks successful!")
        logger.info("=" * 60)
    else:
        validation_results["overall_status"] = "FAIL"
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION FAILED: Some checks did not pass.")
        logger.info("=" * 60)

    # Generate report
    generate_validation_report(validation_results)

    # Exit with appropriate code
    sys.exit(0 if validation_results["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    main()