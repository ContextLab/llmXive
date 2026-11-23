import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.loader import load_config

logger = logging.getLogger(__name__)

REQUIRED_DIRS = [
    "data/raw/humaneval",
    "data/processed",
    "data/figures",
    "state",
    "logs"
]

REQUIRED_CSVS = [
    "data/processed/samples_all.csv",
    "data/processed/samples_valid.csv",
    "data/processed/metrics_all.csv",
    "data/processed/metrics_valid.csv"
]

def ensure_output_dirs(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Ensure all required output directories exist.
    Creates them if they don't exist.
    
    Args:
        config: Optional config dict (not strictly needed for this function)
        
    Returns:
        True if all directories were created or already exist, False otherwise.
    """
    try:
        for dir_path in REQUIRED_DIRS:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory: {path.absolute()}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory: {e}")
        return False

def validate_csv_structure(file_path: str, expected_headers: List[str]) -> bool:
    """
    Validate that a CSV file exists and has the expected header structure.
    
    Args:
        file_path: Path to the CSV file
        expected_headers: List of expected header names
        
    Returns:
        True if file exists and headers match, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"CSV file missing: {file_path}")
        return False
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            
            if headers is None:
                logger.error(f"CSV file is empty: {file_path}")
                return False
            
            if set(headers) != set(expected_headers):
                logger.error(f"CSV headers mismatch in {file_path}. Expected: {expected_headers}, Got: {headers}")
                return False
            
        return True
    except Exception as e:
        logger.error(f"Error validating CSV {file_path}: {e}")
        return False

def validate_all_artifacts(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate that all required CSV artifacts exist and have correct structure.
    
    Args:
        config: Optional config dict
        
    Returns:
        True if all artifacts are valid, False otherwise.
    """
    all_valid = True
    
    # Define expected headers for each CSV based on pipeline requirements
    csv_definitions = {
        "data/processed/samples_all.csv": [
            "task_id", "style", "sample_id", "code", "pass_status"
        ],
        "data/processed/samples_valid.csv": [
            "task_id", "style", "sample_id", "code", "pass_status"
        ],
        "data/processed/metrics_all.csv": [
            "task_id", "style", "metric_type", "value", "count"
        ],
        "data/processed/metrics_valid.csv": [
            "task_id", "style", "metric_type", "value", "count"
        ]
    }
    
    for file_path, expected_headers in csv_definitions.items():
        if not validate_csv_structure(file_path, expected_headers):
            all_valid = False
        else:
            logger.info(f"Validated: {file_path}")
    
    if all_valid:
        logger.info("All required CSV artifacts are present and valid.")
    else:
        logger.warning("Some required CSV artifacts are missing or invalid.")
        
    return all_valid

def create_sample_csvs(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Create empty sample CSV files with correct headers if they don't exist.
    This is a helper for initialization, not for populating data.
    
    Args:
        config: Optional config dict
        
    Returns:
        True if files were created or already exist, False otherwise.
    """
    if not ensure_output_dirs(config):
        return False
        
    csv_definitions = {
        "data/processed/samples_all.csv": ["task_id", "style", "sample_id", "code", "pass_status"],
        "data/processed/samples_valid.csv": ["task_id", "style", "sample_id", "code", "pass_status"],
        "data/processed/metrics_all.csv": ["task_id", "style", "metric_type", "value", "count"],
        "data/processed/metrics_valid.csv": ["task_id", "style", "metric_type", "value", "count"]
    }
    
    for file_path, headers in csv_definitions.items():
        path = Path(file_path)
        if not path.exists():
            try:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                logger.info(f"Created empty CSV: {file_path}")
            except Exception as e:
                logger.error(f"Failed to create CSV {file_path}: {e}")
                return False
        else:
            logger.debug(f"CSV already exists: {file_path}")
            
    return True

def run_directory_validation(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Main entry point for directory and artifact validation.
    Ensures directories exist and all required CSVs are valid.
    
    Args:
        config: Optional config dict
        
    Returns:
        True if validation passes, False otherwise.
    """
    logger.info("Running directory and artifact validation...")
    
    # Ensure directories exist
    if not ensure_output_dirs(config):
        logger.error("Failed to ensure output directories.")
        return False
        
    # Validate existing artifacts
    if not validate_all_artifacts(config):
        logger.warning("Artifact validation failed. Some files may be missing or malformed.")
        return False
        
    logger.info("Directory and artifact validation completed successfully.")
    return True

if __name__ == "__main__":
    # Simple test runner for this module
    logging.basicConfig(level=logging.INFO)
    result = run_directory_validation()
    if result:
        print("Validation passed.")
    else:
        print("Validation failed.")
        exit(1)