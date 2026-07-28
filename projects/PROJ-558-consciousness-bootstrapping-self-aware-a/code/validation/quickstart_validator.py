"""
Quickstart Validation Script for PROJ-558-consciousness-bootstrapping-self-aware-a.

This script validates that all artifacts required by the project specification
and the tasks.md file have been generated correctly. It checks for the existence
of required files, verifies their content structure, and ensures that the
project is in a valid state for execution.

Usage:
    python code/validation/quickstart_validator.py
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from config import get_config

logger = get_logger(__name__)

# Define required artifacts based on tasks.md and spec requirements
REQUIRED_FILES = {
    # Phase 1: Setup
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/raw": "Directory",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/processed": "Directory",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts": "Directory",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/checkpoints": "Directory",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results": "Directory",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/__init__.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/models/__init__.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/training/__init__.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/evaluation/__init__.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/analysis/__init__.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/utils/__init__.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/requirements.txt": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/pyproject.toml": "File",

    # Phase 2: Foundational
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/manifest.json": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/config.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/models/checkpoint.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/evaluation/results.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/models/base_llama.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/utils/logging.py": "File",

    # Phase 3: User Story 1
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/models/recursive_llama.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/evaluation/loss_functions.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/training/train.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/tests/unit/models/test_recursive_attention.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/tests/unit/training/test_loss_functions.py": "File",

    # Phase 4: User Story 2
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/evaluation/metrics.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/evaluation/run_benchmarks.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/tests/unit/evaluation/test_metrics.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results/error_detection_calibration.json": "File",

    # Phase 5: User Story 3
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/analysis/stats.py": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results/statistical_report.json": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results/sensitivity_analysis.csv": "File",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/tests/unit/analysis/test_stats.py": "File",

    # Polish & Cross-Cutting Concerns
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/docs/": "Directory",
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results/memory_profile.log": "File",
}

# Define required content checks
CONTENT_CHECKS = {
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/code/config.py": [
        "TOKEN_LIMIT",
        "recursion_depth",
        "seed",
        "batch_size",
        "learning_rate",
        "torch.device('cpu')"
    ],
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/manifest.json": [
        "checksum",
        "dataset_name",
        "file_path"
    ],
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results/statistical_report.json": [
        "p_values",
        "effect_sizes",
        "confidence_intervals",
        "percentage_difference"
    ],
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results/sensitivity_analysis.csv": [
        "threshold",
        "false_positive_rate",
        "false_negative_rate"
    ],
    "projects/PROJ-558-consciousness-bootstrapping-self-aware-a/artifacts/results/error_detection_calibration.json": [
        "bin_edges",
        "bin_counts",
        "predicted_error_rates",
        "observed_error_rates"
    ]
}

def check_file_exists(path: Path, file_type: str) -> Tuple[bool, str]:
    """Check if a file or directory exists."""
    if file_type == "Directory":
        if path.exists() and path.is_dir():
            return True, f"✓ Directory exists: {path}"
        else:
            return False, f"✗ Directory missing: {path}"
    else:  # File
        if path.exists() and path.is_file():
            return True, f"✓ File exists: {path}"
        else:
            return False, f"✗ File missing: {path}"

def check_content(path: Path, required_terms: List[str]) -> Tuple[bool, List[str]]:
    """Check if a file contains required content."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_terms = []
        for term in required_terms:
            if term not in content:
                missing_terms.append(term)
        
        if missing_terms:
            return False, missing_terms
        else:
            return True, []
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]

def validate_project_structure(base_path: Path) -> List[str]:
    """Validate the overall project structure."""
    errors = []
    
    # Check for required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "artifacts/checkpoints",
        "artifacts/results",
        "code",
        "tests",
        "docs"
    ]
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists() or not full_path.is_dir():
            errors.append(f"Missing required directory: {dir_path}")
    
    return errors

def validate_python_imports(base_path: Path) -> List[str]:
    """Validate that Python files can be imported without errors."""
    errors = []
    python_files = [
        "code/config.py",
        "code/data_loader.py",
        "code/models/base_llama.py",
        "code/models/recursive_llama.py",
        "code/models/checkpoint.py",
        "code/evaluation/results.py",
        "code/evaluation/metrics.py",
        "code/evaluation/loss_functions.py",
        "code/evaluation/run_benchmarks.py",
        "code/training/train.py",
        "code/analysis/stats.py",
        "code/utils/logging.py",
        "code/utils/memory_profiler.py",
        "code/utils/lint_check.py"
    ]
    
    for file_path in python_files:
        full_path = base_path / file_path
        if full_path.exists():
            try:
                # Try to compile the file
                with open(full_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(full_path), 'exec')
            except SyntaxError as e:
                errors.append(f"Syntax error in {file_path}: {str(e)}")
            except Exception as e:
                # Other errors might be due to missing dependencies, which is okay for validation
                logger.debug(f"Non-syntax error in {file_path}: {str(e)}")
        else:
            errors.append(f"Python file missing: {file_path}")
    
    return errors

def run_quickstart_validation(base_path: Path, verbose: bool = False) -> bool:
    """Run the complete quickstart validation."""
    logger.info("Starting Quickstart Validation for PROJ-558")
    
    all_passed = True
    validation_results = []
    
    # Step 1: Check project structure
    logger.info("Step 1: Validating project structure...")
    structure_errors = validate_project_structure(base_path)
    if structure_errors:
        all_passed = False
        for error in structure_errors:
            validation_results.append(f"✗ {error}")
            logger.error(error)
    else:
        validation_results.append("✓ Project structure is valid")
        logger.info("✓ Project structure is valid")
    
    # Step 2: Check required files
    logger.info("Step 2: Checking required files...")
    for file_path, file_type in REQUIRED_FILES.items():
        full_path = base_path / file_path
        exists, message = check_file_exists(full_path, file_type)
        validation_results.append(message)
        if not exists:
            all_passed = False
            logger.error(message)
        elif verbose:
            logger.info(message)
    
    # Step 3: Check file contents
    logger.info("Step 3: Validating file contents...")
    for file_path, required_terms in CONTENT_CHECKS.items():
        full_path = base_path / file_path
        if full_path.exists():
            content_valid, missing_terms = check_content(full_path, required_terms)
            if content_valid:
                validation_results.append(f"✓ {file_path} contains required content")
                if verbose:
                    logger.info(f"✓ {file_path} contains required content")
            else:
                all_passed = False
                missing_str = ", ".join(missing_terms)
                message = f"✗ {file_path} missing required content: {missing_str}"
                validation_results.append(message)
                logger.error(message)
        else:
            logger.warning(f"Skipping content check for {file_path} (file not found)")
    
    # Step 4: Validate Python imports
    logger.info("Step 4: Validating Python file syntax...")
    import_errors = validate_python_imports(base_path)
    if import_errors:
        all_passed = False
        for error in import_errors:
            validation_results.append(f"✗ {error}")
            logger.error(error)
    else:
        validation_results.append("✓ All Python files have valid syntax")
        logger.info("✓ All Python files have valid syntax")
    
    # Step 5: Check for configuration validity
    logger.info("Step 5: Validating configuration...")
    config_path = base_path / "code" / "config.py"
    if config_path.exists():
        try:
            # Try to import and validate config
            os.chdir(base_path)
            from config import get_config, validate_config
            config = get_config()
            if validate_config(config):
                validation_results.append("✓ Configuration is valid")
                logger.info("✓ Configuration is valid")
            else:
                all_passed = False
                validation_results.append("✗ Configuration validation failed")
                logger.error("✗ Configuration validation failed")
        except Exception as e:
            all_passed = False
            validation_results.append(f"✗ Configuration error: {str(e)}")
            logger.error(f"✗ Configuration error: {str(e)}")
    else:
        all_passed = False
        validation_results.append("✗ Configuration file missing")
        logger.error("✗ Configuration file missing")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*50)
    
    if all_passed:
        logger.info("✓ All validations passed! Project is ready for execution.")
        logger.info("You can now run the quickstart script to generate all artifacts.")
    else:
        logger.error("✗ Some validations failed. Please fix the issues above.")
        logger.error("Refer to the detailed results below for specific errors.")
    
    # Log detailed results
    logger.info("\nDetailed Results:")
    for result in validation_results:
        logger.info(f"  {result}")
    
    return all_passed

def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Quickstart validation script for PROJ-558"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base path of the project (defaults to parent of this script's parent)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Determine base path
    if args.base_path:
        base_path = Path(args.base_path)
    else:
        base_path = Path(__file__).parent.parent.parent
    
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)
    
    # Run validation
    success = run_quickstart_validation(base_path, args.verbose)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
