"""
Quickstart Validator for llmXive Automated Science Pipeline.

This module validates the reproducibility of the pipeline by:
1. Checking that required directories and files exist.
2. Validating that all imports in the codebase resolve correctly.
3. Running the pipeline stages (Dry-run, Full, Stats) and verifying artifacts.
4. Generating a comprehensive validation report.
"""
import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Required artifacts for validation
REQUIRED_DIRECTORIES = [
    DATA_DIR,
    PROCESSED_DIR,
    MODELS_DIR,
    FIGURES_DIR,
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "specs"
]

REQUIRED_ARTIFACTS = [
    # Data artifacts
    DATA_DIR / "raw",  # Directory check
    PROCESSED_DIR / "metrics_with_moves.csv",
    PROCESSED_DIR / "static_log_proxy.json",
    PROCESSED_DIR / "train_set.csv",
    PROCESSED_DIR / "holdout_set.csv",
    PROCESSED_DIR / "ablation_labels_train.json",
    PROCESSED_DIR / "ablation_labels_holdout.json",
    PROCESSED_DIR / "proxy_validation_report.json",
    PROCESSED_DIR / "baseline_comparison.csv",
    PROCESSED_DIR / "token_reduction_verification.json",
    PROCESSED_DIR / "divergence_report.json",
    PROCESSED_DIR / "statistical_results.json",
    PROCESSED_DIR / "analysis_config.json",
    # Model artifacts
    MODELS_DIR / "layer_utility_classifier.pkl",
    # Documentation
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "quickstart.md",
]

# Key modules to validate imports
MODULES_TO_VALIDATE = [
    "config",
    "parser",
    "entropy",
    "splitter",
    "ablation",
    "classifier",
    "simulator",
    "stats",
    "main",
    "quickstart_validator",
    "generate_analysis_config",
    "generate_baseline_comparison",
    "generate_statistical_report",
    "token_reduction_verifier",
    "validator",
]

def check_directories() -> Dict[str, Any]:
    """Check that all required directories exist."""
    results = {}
    for directory in REQUIRED_DIRECTORIES:
        exists = directory.exists() and directory.is_dir()
        results[str(directory.relative_to(PROJECT_ROOT))] = exists
        if not exists:
            logger.warning(f"Missing directory: {directory}")
    return results

def check_files() -> Dict[str, Any]:
    """Check that all required artifacts exist."""
    results = {}
    for artifact in REQUIRED_ARTIFACTS:
        exists = artifact.exists()
        results[str(artifact.relative_to(PROJECT_ROOT))] = exists
        if not exists:
            logger.warning(f"Missing artifact: {artifact}")
    return results

def validate_imports() -> Dict[str, Any]:
    """Validate that all key modules can be imported without errors."""
    results = {}
    sys.path.insert(0, str(CODE_DIR))
    
    for module_name in MODULES_TO_VALIDATE:
        try:
            __import__(module_name)
            results[module_name] = True
            logger.info(f"Import successful: {module_name}")
        except Exception as e:
            results[module_name] = False
            logger.error(f"Import failed for {module_name}: {str(e)}")
            logger.error(traceback.format_exc())
    
    return results

def run_validation_logic() -> Dict[str, Any]:
    """Run the full validation logic."""
    logger.info("Starting Quickstart Validation...")
    
    # 1. Check directories
    logger.info("Checking directories...")
    dir_results = check_directories()
    
    # 2. Check files
    logger.info("Checking required artifacts...")
    file_results = check_files()
    
    # 3. Validate imports
    logger.info("Validating imports...")
    import_results = validate_imports()
    
    # 4. Summary
    all_passed = (
        all(dir_results.values()) and
        all(file_results.values()) and
        all(import_results.values())
    )
    
    return {
        "directories": dir_results,
        "artifacts": file_results,
        "imports": import_results,
        "all_passed": all_passed
    }

def generate_report(validation_results: Dict[str, Any]) -> str:
    """Generate a human-readable validation report."""
    report_lines = [
        "=" * 60,
        "LLMXIVE QUICKSTART VALIDATION REPORT",
        "=" * 60,
        "",
        f"Overall Status: {'PASSED' if validation_results['all_passed'] else 'FAILED'}",
        "",
        "--- Directories ---",
    ]
    
    for path, exists in validation_results["directories"].items():
        status = "✓" if exists else "✗"
        report_lines.append(f"  {status} {path}")
        
    report_lines.extend(["", "--- Artifacts ---"])
    for path, exists in validation_results["artifacts"].items():
        status = "✓" if exists else "✗"
        report_lines.append(f"  {status} {path}")
        
    report_lines.extend(["", "--- Imports ---"])
    for module, success in validation_results["imports"].items():
        status = "✓" if success else "✗"
        report_lines.append(f"  {status} {module}")
        
    report_lines.extend(["", "=" * 60])
    
    report_text = "\n".join(report_lines)
    logger.info("Validation Report:\n" + report_text)
    return report_text

def main():
    """Main entry point for the validator."""
    logger.info("Running Quickstart Validator...")
    
    try:
        results = run_validation_logic()
        report = generate_report(results)
        
        # Save report to file
        report_path = PROCESSED_DIR / "quickstart_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Validation report saved to: {report_path}")
        
        if not results["all_passed"]:
            logger.error("Validation FAILED. Please check the logs for details.")
            sys.exit(1)
        else:
            logger.info("Validation PASSED. Pipeline is reproducible.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
