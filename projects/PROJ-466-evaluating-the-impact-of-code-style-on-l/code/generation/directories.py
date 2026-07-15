"""
Directory structure management for the llmXive research pipeline.

This module ensures that all required output directories exist and
validates that CSV artifacts are written correctly.
"""
import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.loader import load_config

logger = logging.getLogger(__name__)

# Required directories relative to project root
REQUIRED_DIRS = [
    "data/raw/humaneval",
    "data/processed",
    "data/figures",
    "state",
    "logs",
    "results",
]

# Required CSV artifacts and their expected headers
REQUIRED_CSVS = {
    "samples_all.csv": [
        "task_id",
        "style",
        "sample_id",
        "code",
        "pass_status",
        "timeout",
        "error_message",
    ],
    "samples_valid.csv": [
        "task_id",
        "style",
        "sample_id",
        "code",
        "pass_status",
    ],
    "metrics_all.csv": [
        "task_id",
        "style",
        "sample_id",
        "ngram_entropy",
        "ast_edit_distance",
        "is_valid",
    ],
    "metrics_valid.csv": [
        "task_id",
        "style",
        "sample_id",
        "ngram_entropy",
        "ast_edit_distance",
    ],
}

def ensure_output_dirs(base_path: Optional[Path] = None) -> List[str]:
    """
    Create all required output directories if they do not exist.
    
    Args:
        base_path: Base project directory. Defaults to current working directory.
        
    Returns:
        List of created directory paths.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    created_dirs = []
    
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_dirs.append(str(full_path))
        else:
            logger.debug(f"Directory already exists: {full_path}")
            
    return created_dirs

def validate_csv_structure(file_path: Path, expected_headers: List[str]) -> Dict[str, Any]:
    """
    Validate that a CSV file exists and has the expected structure.
    
    Args:
        file_path: Path to the CSV file.
        expected_headers: List of expected column headers.
        
    Returns:
        Dictionary with validation results:
        - exists: bool
        - valid_headers: bool
        - row_count: int
        - headers: List[str] (actual headers)
        - errors: List[str]
    """
    result = {
        "exists": False,
        "valid_headers": False,
        "row_count": 0,
        "headers": [],
        "errors": []
    }
    
    if not file_path.exists():
        result["errors"].append(f"File does not exist: {file_path}")
        return result
        
    result["exists"] = True
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            
            if headers is None:
                result["errors"].append("CSV file is empty (no headers)")
                return result
                
            result["headers"] = headers
            result["row_count"] = sum(1 for _ in reader)
            
            # Check if all expected headers are present
            missing_headers = set(expected_headers) - set(headers)
            extra_headers = set(headers) - set(expected_headers)
            
            if missing_headers:
                result["errors"].append(f"Missing headers: {missing_headers}")
            if extra_headers:
                logger.warning(f"Extra headers found (not required): {extra_headers}")
                
            if not missing_headers:
                result["valid_headers"] = True
                
    except Exception as e:
        result["errors"].append(f"Error reading CSV: {str(e)}")
        
    return result

def validate_all_artifacts(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Validate that all required CSV artifacts exist with correct structure.
    
    Args:
        base_path: Base project directory. Defaults to current working directory.
        
    Returns:
        Dictionary with validation results for all artifacts.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    results = {
        "all_valid": True,
        "artifacts": {}
    }
    
    for csv_name, expected_headers in REQUIRED_CSVS.items():
        csv_path = base_path / "data/processed" / csv_name
        validation = validate_csv_structure(csv_path, expected_headers)
        results["artifacts"][csv_name] = validation
        
        if not validation["exists"] or not validation["valid_headers"]:
            results["all_valid"] = False
            
    return results

def create_sample_csvs(base_path: Optional[Path] = None) -> Dict[str, Path]:
    """
    Create empty CSV files with correct headers if they don't exist.
    This is a utility for initialization, not for actual data generation.
    
    Args:
        base_path: Base project directory. Defaults to current working directory.
        
    Returns:
        Dictionary mapping CSV names to their file paths.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    processed_dir = base_path / "data/processed"
    ensure_output_dirs(base_path)
    
    created_files = {}
    
    for csv_name, expected_headers in REQUIRED_CSVS.items():
        csv_path = processed_dir / csv_name
        
        if not csv_path.exists():
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(expected_headers)
            logger.info(f"Created empty CSV with headers: {csv_path}")
        else:
            logger.debug(f"CSV already exists: {csv_path}")
            
        created_files[csv_name] = csv_path
        
    return created_files

def run_directory_validation(base_path: Optional[Path] = None) -> bool:
    """
    Run full validation of directory structure and CSV artifacts.
    
    Args:
        base_path: Base project directory. Defaults to current working directory.
        
    Returns:
        True if all validations pass, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    logger.info("Starting directory structure validation...")
    
    # Ensure directories exist
    ensure_output_dirs(base_path)
    
    # Validate artifacts
    validation_results = validate_all_artifacts(base_path)
    
    if validation_results["all_valid"]:
        logger.info("All directory and CSV validations passed.")
        return True
    else:
        logger.error("Validation failed:")
        for csv_name, result in validation_results["artifacts"].items():
            if not result["exists"] or not result["valid_headers"]:
                logger.error(f"  {csv_name}: {result['errors']}")
        return False

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    base = Path.cwd()
    if len(sys.argv) > 1:
        base = Path(sys.argv[1])
        
    success = run_directory_validation(base)
    sys.exit(0 if success else 1)
