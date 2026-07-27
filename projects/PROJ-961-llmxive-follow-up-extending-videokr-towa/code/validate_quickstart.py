"""
Quickstart Validation Script for llmXive Project.

This script validates the reproducibility of the pipeline by:
1. Verifying the existence of all required directories and placeholder files.
2. Checking that all expected data artifacts exist (if previously generated).
3. Verifying that all Python scripts in code/ have module-level docstrings.
4. Running a dry-run or execution check on key scripts to ensure they import correctly.
5. Generating a validation report.

Author: llmXive Implementer
"""

import os
import sys
import json
import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration
REQUIRED_DIRS = [
    "code",
    "code/ingest",
    "code/analysis",
    "code/utils",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/processed",
    "docs"
]

REQUIRED_FILES = [
    "data/raw/.gitkeep",
    "data/processed/.gitkeep"
]

# Expected artifacts from completed tasks
EXPECTED_DATA_ARTIFACTS = [
    "data/processed/annotated_videokr.csv",
    "data/processed/annotation_coverage.json",
    "data/processed/accuracy_vs_hop_raw.csv",
    "data/processed/accuracy_vs_hop_raw.png",
    "data/processed/accuracy_binned.png",
    "data/processed/threshold_results.json",
    "data/processed/sensitivity_thresholds.csv",
    "data/processed/sensitivity_summary.md",
    "data/processed/sensitivity_overlay.png",
    "data/processed/sensitivity_report.md",
    "data/processed/stability_metric.json",
    "data/processed/runtime_log.json"
]

# Scripts expected to have docstrings
SCRIPT_SUBDIRS = ["ingest", "analysis", "utils"]


def check_directory_structure() -> Tuple[bool, List[str]]:
    """Verify all required directories exist."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
        elif not full_path.is_dir():
            missing.append(f"{full_path} (exists but not a directory)")

    return len(missing) == 0, missing


def check_placeholder_files() -> Tuple[bool, List[str]]:
    """Verify .gitkeep files and other required placeholders exist."""
    missing = []
    for file_path in REQUIRED_FILES:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing.append(str(full_path))

    return len(missing) == 0, missing


def check_data_artifacts() -> Tuple[bool, List[str]]:
    """Verify that expected data artifacts exist."""
    missing = []
    for file_path in EXPECTED_DATA_ARTIFACTS:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing.append(str(full_path))

    return len(missing) == 0, missing


def check_docstrings() -> Tuple[bool, List[str]]:
    """Check that all Python scripts in code/ have module-level docstrings."""
    issues = []
    scripts_checked = 0

    for subdir in SCRIPT_SUBDIRS:
        dir_path = PROJECT_ROOT / "code" / subdir
        if not dir_path.exists():
            logger.warning(f"Directory {dir_path} does not exist, skipping.")
            continue

        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            scripts_checked += 1
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                docstring = ast.get_docstring(tree)
                if not docstring:
                    issues.append(f"Missing docstring in {py_file.relative_to(PROJECT_ROOT)}")
            except SyntaxError as e:
                issues.append(f"Syntax error in {py_file.relative_to(PROJECT_ROOT)}: {e}")
            except Exception as e:
                issues.append(f"Error checking {py_file.relative_to(PROJECT_ROOT)}: {e}")

    logger.info(f"Checked {scripts_checked} scripts for docstrings.")
    return len(issues) == 0, issues


def check_imports() -> Tuple[bool, List[str]]:
    """Attempt to import all main scripts to verify no import errors."""
    issues = []
    scripts_checked = 0

    for subdir in SCRIPT_SUBDIRS:
        dir_path = PROJECT_ROOT / "code" / subdir
        if not dir_path.exists():
            continue

        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            # Construct module path
            rel_path = py_file.relative_to(PROJECT_ROOT)
            module_path = str(rel_path).replace(os.sep, '.').replace('/', '.')[:-3]

            scripts_checked += 1
            try:
                # Add project root to path
                sys.path.insert(0, str(PROJECT_ROOT))
                __import__(module_path)
                logger.info(f"Import successful: {module_path}")
            except ImportError as e:
                issues.append(f"Import error in {module_path}: {e}")
            except Exception as e:
                issues.append(f"Runtime error importing {module_path}: {e}")
            finally:
                # Clean up sys.path
                if str(PROJECT_ROOT) in sys.path:
                    sys.path.remove(str(PROJECT_ROOT))

    logger.info(f"Attempted imports for {scripts_checked} scripts.")
    return len(issues) == 0, issues


def run_quickstart_validation() -> Dict[str, Any]:
    """Run all validation checks and return a summary report."""
    logger.info("Starting Quickstart Validation...")

    results = {
        "timestamp": str(Path(__file__).resolve().parent),
        "project_root": str(PROJECT_ROOT),
        "checks": {}
    }

    all_passed = True

    # 1. Directory Structure
    logger.info("Checking directory structure...")
    passed, missing = check_directory_structure()
    results["checks"]["directory_structure"] = {
        "passed": passed,
        "missing": missing
    }
    if not passed:
        all_passed = False
        logger.error(f"Directory structure check failed. Missing: {missing}")
    else:
        logger.info("Directory structure check passed.")

    # 2. Placeholder Files
    logger.info("Checking placeholder files...")
    passed, missing = check_placeholder_files()
    results["checks"]["placeholder_files"] = {
        "passed": passed,
        "missing": missing
    }
    if not passed:
        all_passed = False
        logger.error(f"Placeholder files check failed. Missing: {missing}")
    else:
        logger.info("Placeholder files check passed.")

    # 3. Data Artifacts
    logger.info("Checking data artifacts...")
    passed, missing = check_data_artifacts()
    results["checks"]["data_artifacts"] = {
        "passed": passed,
        "missing": missing
    }
    if not passed:
        all_passed = False
        logger.warning(f"Data artifacts check failed. Missing: {missing}")
        # Note: This might be expected if the pipeline hasn't been run yet in a fresh env,
        # but for reproducibility validation, we expect them if the task claims completion.
    else:
        logger.info("Data artifacts check passed.")

    # 4. Docstrings
    logger.info("Checking docstrings...")
    passed, issues = check_docstrings()
    results["checks"]["docstrings"] = {
        "passed": passed,
        "issues": issues
    }
    if not passed:
        all_passed = False
        logger.error(f"Docstring check failed. Issues: {issues}")
    else:
        logger.info("Docstring check passed.")

    # 5. Imports
    logger.info("Checking imports...")
    passed, issues = check_imports()
    results["checks"]["imports"] = {
        "passed": passed,
        "issues": issues
    }
    if not passed:
        all_passed = False
        logger.error(f"Import check failed. Issues: {issues}")
    else:
        logger.info("Import check passed.")

    results["overall_status"] = "PASS" if all_passed else "FAIL"
    logger.info(f"Validation Complete. Status: {results['overall_status']}")

    return results


def main():
    """Main entry point for the validation script."""
    report = run_quickstart_validation()

    # Write report to data/processed
    report_path = PROJECT_ROOT / "data" / "processed" / "quickstart_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {report_path}")

    if report["overall_status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()