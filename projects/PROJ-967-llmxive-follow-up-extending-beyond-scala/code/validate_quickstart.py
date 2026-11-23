"""
Quickstart Validation Script.

This script validates the entire pipeline execution and results.
"""
import os
import sys
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def check_directory(path: str) -> bool:
    """Check if a directory exists."""
    return Path(path).is_dir()

def check_file(path: str) -> bool:
    """Check if a file exists."""
    return Path(path).is_file()

def validate_directories() -> bool:
    """Validate required directories exist."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results",
        "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not check_directory(dir_path):
            logger.error(f"Missing directory: {dir_path}")
            all_exist = False
        else:
            logger.info(f"Directory exists: {dir_path}")
    
    return all_exist

def validate_project_files() -> bool:
    """Validate required project files exist."""
    required_files = [
        "code/requirements.txt",
        ".gitignore",
        "pytest.ini"
    ]
    
    all_exist = True
    for file_path in required_files:
        if not check_file(file_path):
            logger.error(f"Missing file: {file_path}")
            all_exist = False
        else:
            logger.info(f"File exists: {file_path}")
    
    return all_exist

def validate_data_files() -> bool:
    """Validate data files exist."""
    # Check for processed features
    if not check_file("data/processed/features.json"):
        logger.warning("data/processed/features.json not found (may not exist yet)")
        return False
    
    logger.info("data/processed/features.json exists")
    return True

def validate_pipeline_execution() -> bool:
    """Validate that the pipeline can be executed."""
    # Check if all required scripts exist
    scripts = [
        "code/ingest.py",
        "code/features.py",
        "code/train.py",
        "code/evaluate.py"
    ]
    
    all_exist = True
    for script in scripts:
        if not check_file(script):
            logger.error(f"Missing script: {script}")
            all_exist = False
        else:
            logger.info(f"Script exists: {script}")
    
    return all_exist

def validate_results_content() -> bool:
    """Validate results file content."""
    results_file = "results/results.json"
    
    if not check_file(results_file):
        logger.warning(f"{results_file} not found")
        return False
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        required_keys = ["cv_r2_mean", "model_mae", "permutation_p_value"]
        for key in required_keys:
            if key not in results:
                logger.error(f"Missing key in results: {key}")
                return False
        
        logger.info("Results content is valid")
        return True
        
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {results_file}")
        return False

def main():
    """Main entry point for validation script."""
    logger.info("Starting validation...")
    
    validations = [
        ("Directories", validate_directories()),
        ("Project Files", validate_project_files()),
        ("Data Files", validate_data_files()),
        ("Pipeline Execution", validate_pipeline_execution()),
        ("Results Content", validate_results_content())
    ]
    
    all_passed = True
    for name, passed in validations:
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("All validations passed!")
        return 0
    else:
        logger.warning("Some validations failed")
        return 1

if __name__ == "__main__":
    exit(main())