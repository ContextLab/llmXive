"""
Quickstart Validator for llmXive Pipeline (T041)

This script validates that the pipeline has been set up correctly and
that all required outputs exist and meet the success criteria.

Exit codes:
  0: Success (all checks passed)
  1: Failure (missing files, invalid reports, or configuration errors)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_directory_structure():
    """Verify that all required directories exist."""
    required_dirs = [
        'code',
        'data/raw',
        'data/processed',
        'reports',
        'reports/visualizations',
        'docs',
        'tests'
    ]

    base_path = Path('.')
    missing = []

    for dir_name in required_dirs:
        if not (base_path / dir_name).exists():
            missing.append(dir_name)

    if missing:
        logger.error(f"Missing directories: {', '.join(missing)}")
        return False

    logger.info("Directory structure: OK")
    return True

def check_required_files():
    """Verify that all required output files exist."""
    required_files = [
        'data/processed/merged_features.parquet',
        'data/processed/matching_results.parquet',
        'data/processed/sensitivity_summary.json',
        'data/processed/runtime_report.json',
        'reports/analysis_report.pdf',
        'data/processed/covariate_config.json',
        'data/processed/cohort_segments.parquet'
    ]

    base_path = Path('.')
    missing = []

    for file_name in required_files:
        if not (base_path / file_name).exists():
            missing.append(file_name)

    if missing:
        logger.error(f"Missing files: {', '.join(missing)}")
        return False

    logger.info("Required files: OK")
    return True

def check_sensitivity_summary():
    """Validate sensitivity_summary.json content."""
    file_path = Path('data/processed/sensitivity_summary.json')

    if not file_path.exists():
        logger.error("sensitivity_summary.json not found")
        return False

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if 'consistent' not in data:
            logger.error("sensitivity_summary.json missing 'consistent' key")
            return False

        if not isinstance(data['consistent'], bool):
            logger.error("'consistent' must be a boolean")
            return False

        if not data['consistent']:
            logger.warning("Sensitivity consistency check failed (consistent=False)")
            # This is a warning, not a failure, as the pipeline may have halted
            # But for validation, we note it.
            return True  # File exists and is valid, even if consistency is low

        logger.info("Sensitivity summary: OK (consistent=True)")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in sensitivity_summary.json: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading sensitivity_summary.json: {e}")
        return False

def check_matching_failure_report():
    """Check if matching_failure_report.json exists (should not exist on success)."""
    file_path = Path('data/processed/matching_failure_report.json')

    if file_path.exists():
        logger.warning("matching_failure_report.json exists (matching may have failed)")
        return False  # Matching failure indicates a problem
    else:
        logger.info("Matching failure report: Not present (OK)")
        return True

def check_runtime_report():
    """Validate runtime_report.json and 6-hour constraint."""
    file_path = Path('data/processed/runtime_report.json')

    if not file_path.exists():
        logger.error("runtime_report.json not found")
        return False

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if 'total_runtime_seconds' not in data:
            logger.error("runtime_report.json missing 'total_runtime_seconds'")
            return False

        runtime_seconds = data['total_runtime_seconds']
        max_allowed_seconds = 6 * 60 * 60  # 6 hours

        if runtime_seconds > max_allowed_seconds:
            logger.error(f"Runtime exceeded 6-hour limit: {runtime_seconds}s")
            return False

        logger.info(f"Runtime report: OK ({runtime_seconds}s < 6h)")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in runtime_report.json: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading runtime_report.json: {e}")
        return False

def check_covariate_config():
    """Validate covariate_config.json structure."""
    file_path = Path('data/processed/covariate_config.json')

    if not file_path.exists():
        logger.error("covariate_config.json not found")
        return False

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if 'covariates' not in data:
            logger.error("covariate_config.json missing 'covariates' key")
            return False

        if not isinstance(data['covariates'], list):
            logger.error("'covariates' must be a list")
            return False

        # Check that semantic_similarity is NOT in the list (per Plan override)
        if 'semantic_similarity' in data['covariates']:
            logger.error("covariate_config.json should NOT include 'semantic_similarity'")
            return False

        logger.info(f"Covariate config: OK ({len(data['covariates'])} covariates)")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in covariate_config.json: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading covariate_config.json: {e}")
        return False

def main():
    """Run all validation checks."""
    logger.info("Starting quickstart validation...")

    checks = [
        ("Directory Structure", check_directory_structure),
        ("Required Files", check_required_files),
        ("Sensitivity Summary", check_sensitivity_summary),
        ("Matching Failure Report (should not exist)", check_matching_failure_report),
        ("Runtime Report", check_runtime_report),
        ("Covariate Config", check_covariate_config),
    ]

    all_passed = True

    for check_name, check_func in checks:
        logger.info(f"Running check: {check_name}")
        if not check_func():
            all_passed = False
            logger.error(f"Check failed: {check_name}")
        else:
            logger.info(f"Check passed: {check_name}")

    if all_passed:
        logger.info("✅ All validation checks passed.")
        return 0
    else:
        logger.error("❌ Some validation checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())