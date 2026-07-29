"""
Quickstart Validator for PROJ-558-consciousness-bootstrapping-self-aware-a.

This module validates that all required artifacts for the project have been
generated correctly, as specified in the quickstart.md and tasks.md.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import importlib.util

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

# Define required artifacts based on tasks.md and quickstart.md
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "code/models",
    "code/training",
    "code/evaluation",
    "code/analysis",
    "code/utils",
    "code/validation",
    "tests",
    "artifacts",
    "artifacts/checkpoints",
    "artifacts/results",
    "docs",
]

REQUIRED_FILES = [
    # Core config and structure
    "code/__init__.py",
    "code/models/__init__.py",
    "code/training/__init__.py",
    "code/evaluation/__init__.py",
    "code/analysis/__init__.py",
    "code/utils/__init__.py",
    "code/config.py",
    "code/models/checkpoint.py",
    "code/evaluation/results.py",
    "code/models/base_llama.py",
    "code/models/recursive_llama.py",
    "code/evaluation/loss_functions.py",
    "code/evaluation/metrics.py",
    "code/evaluation/run_benchmarks.py",
    "code/training/train.py",
    "code/analysis/stats.py",
    "code/utils/logging.py",
    "code/utils/memory_profiler.py",
    "code/utils/lint_check.py",
    "code/validation/quickstart_validator.py",
    "code/data_loader.py",
    "tests/__init__.py",
    "docs/README.md", # Placeholder for docs content
    # Data and Manifests
    "data/manifest.json",
    # Expected outputs from execution (if scripts ran successfully)
    "artifacts/results/statistical_report.json",
    "artifacts/results/sensitivity_analysis.csv",
    "artifacts/results/memory_profile.log",
    # Lint/Format config
    "pyproject.toml",
    "requirements.txt",
]

# Specific content checks
CONTENT_CHECKS = {
    "data/manifest.json": ["checksum"],
    "artifacts/results/statistical_report.json": ["p_values", "effect_sizes"],
    "artifacts/results/memory_profile.log": ["peak_memory_mb"],
}


def check_file_exists(file_path: Path) -> Tuple[bool, str]:
    """Check if a file exists."""
    if file_path.exists():
        return True, f"Found: {file_path}"
    return False, f"Missing: {file_path}"


def check_content(file_path: Path, required_keys: List[str]) -> Tuple[bool, str]:
    """Check if a JSON file contains required keys."""
    if not file_path.exists():
        return False, f"Cannot check content of missing file: {file_path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        missing_keys = []
        for key in required_keys:
            if key not in data:
                missing_keys.append(key)

        if missing_keys:
            return False, f"Missing keys in {file_path}: {missing_keys}"
        return True, f"Content valid: {file_path} contains required keys"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {file_path}: {e}"
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"


def validate_project_structure(root: Path) -> List[str]:
    """Validate directory structure and file existence."""
    errors = []

    # Check directories
    for dir_name in REQUIRED_DIRS:
        dir_path = root / dir_name
        if not dir_path.exists():
            errors.append(f"Directory missing: {dir_path}")
        elif not dir_path.is_dir():
            errors.append(f"Not a directory: {dir_path}")

    # Check files
    for file_name in REQUIRED_FILES:
        file_path = root / file_name
        exists, msg = check_file_exists(file_path)
        if not exists:
            errors.append(msg)

    # Check content of specific files
    for file_name, keys in CONTENT_CHECKS.items():
        file_path = root / file_name
        if file_path.exists():
            valid, msg = check_content(file_path, keys)
            if not valid:
                errors.append(msg)
        else:
            # If file is required but missing, it's already caught in file check
            # But we might want to be explicit about content checks for optional files
            pass

    return errors


def validate_python_imports(root: Path) -> List[str]:
    """Validate that Python files can be imported without errors (basic syntax check)."""
    errors = []
    python_files = list(root.glob("code/**/*.py"))

    for file_path in python_files:
        try:
            # Simple syntax check
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), str(file_path), 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            # Import errors might happen due to missing deps, but syntax should be fine
            # We only care about syntax for this basic check
            pass

    return errors


def run_quickstart_validation(root: Path) -> Tuple[bool, List[str]]:
    """Run all validation checks."""
    logger.info(f"Starting quickstart validation for project at: {root}")

    all_errors = []

    # 1. Validate Structure
    logger.info("Validating project structure...")
    struct_errors = validate_project_structure(root)
    all_errors.extend(struct_errors)
    if struct_errors:
        logger.warning(f"Found {len(struct_errors)} structural errors.")
    else:
        logger.info("Project structure is valid.")

    # 2. Validate Python Syntax
    logger.info("Validating Python imports/syntax...")
    import_errors = validate_python_imports(root)
    all_errors.extend(import_errors)
    if import_errors:
        logger.warning(f"Found {len(import_errors)} import/syntax errors.")
    else:
        logger.info("Python syntax is valid.")

    # 3. Check Manifest and Results
    manifest_path = root / "data/manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            if "datasets" in manifest:
                logger.info(f"Manifest contains {len(manifest['datasets'])} dataset entries.")
            else:
                logger.warning("Manifest does not contain 'datasets' key.")
        except Exception as e:
            logger.error(f"Failed to read manifest: {e}")
            all_errors.append(f"Manifest read error: {e}")
    else:
        logger.warning("data/manifest.json not found (expected if data loading not run).")

    # 4. Check Artifacts
    stats_report_path = root / "artifacts/results/statistical_report.json"
    if stats_report_path.exists():
        logger.info("Statistical report found.")
    else:
        logger.warning("Statistical report not found (expected if analysis not run).")

    memory_log_path = root / "artifacts/results/memory_profile.log"
    if memory_log_path.exists():
        logger.info("Memory profile log found.")
    else:
        logger.warning("Memory profile log not found (expected if profiling not run).")

    is_valid = len(all_errors) == 0

    if is_valid:
        logger.info("Quickstart validation PASSED.")
    else:
        logger.error(f"Quickstart validation FAILED with {len(all_errors)} errors.")

    return is_valid, all_errors


def main():
    parser = argparse.ArgumentParser(description="Quickstart Validator for PROJ-558")
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory of the project (default: current directory)"
    )
    args = parser.parse_args()

    root_path = Path(args.root).resolve()

    if not root_path.exists():
        print(f"Error: Root path does not exist: {root_path}")
        sys.exit(1)

    is_valid, errors = run_quickstart_validation(root_path)

    if errors:
        print("\nValidation Errors:")
        for err in errors:
            print(f"  - {err}")
        print(f"\nTotal errors: {len(errors)}")
        sys.exit(1)
    else:
        print("\nAll validations passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()