"""
Data schemas and directory structure validation for the llmXive project.
Defines expected directory hierarchy and provides validation utilities.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

from config import (
    get_data_dir,
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
    ensure_directories
)

# Expected directory structure relative to project root
EXPECTED_DIRECTORIES = [
    "data",
    "data/raw",
    "data/processed",
    "data/stratified",
    "data/features",
    "data/results"
]

# Expected strata for stratified dataset
EXPECTED_STRATA = [
    "static_high",
    "static_low",
    "fast_high",
    "fast_low"
]

# Expected file extensions for each directory
EXPECTED_EXTENSIONS = {
    "data/raw": [".zip", ".tar", ".gz", ".parquet"],
    "data/processed": [".npy", ".pkl", ".csv"],
    "data/stratified": [".npy", ".pkl"],
    "data/features": [".npy"],
    "data/results": [".json", ".npy", ".md", ".csv"]
}

def validate_directory_structure(base_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate that all required directories exist.
    
    Args:
        base_path: Optional base path to validate from. Defaults to project root.
        
    Returns:
        Tuple of (is_valid, list_of_missing_directories)
    """
    if base_path is None:
        base_path = Path.cwd()
        
    missing_dirs = []
    for dir_path in EXPECTED_DIRECTORIES:
        full_path = base_path / dir_path
        if not full_path.exists():
            missing_dirs.append(str(full_path))
            
    return len(missing_dirs) == 0, missing_dirs

def create_directories(base_path: Optional[Path] = None) -> bool:
    """
    Create all required directories if they don't exist.
    
    Args:
        base_path: Optional base path to create directories from.
        
    Returns:
        True if all directories were created or already existed.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    for dir_path in EXPECTED_DIRECTORIES:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
    return True

def check_directory_contents(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Check the contents of each directory and report file counts by type.
    
    Args:
        base_path: Optional base path to check from.
        
    Returns:
        Dictionary with directory names as keys and file count stats as values.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    results = {}
    for dir_path in EXPECTED_DIRECTORIES:
        full_path = base_path / dir_path
        if full_path.exists():
            files = list(full_path.iterdir())
            results[dir_path] = {
                "exists": True,
                "file_count": len(files),
                "files": [f.name for f in files]
            }
        else:
            results[dir_path] = {
                "exists": False,
                "file_count": 0,
                "files": []
            }
            
    return results

def get_expected_strata() -> List[str]:
    """
    Return the list of expected strata names.
    
    Returns:
        List of strata names.
    """
    return EXPECTED_STRATA.copy()

def validate_strata_existence(stratified_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate that all expected strata directories exist in the stratified folder.
    
    Args:
        stratified_dir: Optional path to the stratified directory.
        
    Returns:
        Tuple of (all_exist, list_of_missing_strata)
    """
    if stratified_dir is None:
        stratified_dir = get_stratified_dir()
        
    missing_strata = []
    for stratum in EXPECTED_STRATA:
        stratum_path = stratified_dir / stratum
        if not stratum_path.exists():
            missing_strata.append(stratum)
            
    return len(missing_strata) == 0, missing_strata

def create_schema_report(output_path: Optional[Path] = None) -> str:
    """
    Create a JSON schema report of the current data directory structure.
    
    Args:
        output_path: Optional path to write the report. Defaults to data/results/schema_report.json.
        
    Returns:
        Path to the created report file.
    """
    if output_path is None:
        output_path = get_results_dir() / "schema_report.json"
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "expected_directories": EXPECTED_DIRECTORIES,
        "expected_strata": EXPECTED_STRATA,
        "expected_extensions": EXPECTED_EXTENSIONS,
        "directory_validation": {},
        "directory_contents": {}
    }
    
    # Validate structure
    is_valid, missing = validate_directory_structure()
    report["directory_validation"]["is_valid"] = is_valid
    report["directory_validation"]["missing_directories"] = missing
    
    # Check contents
    report["directory_contents"] = check_directory_contents()
    
    # Check strata
    strata_valid, missing_strata = validate_strata_existence()
    report["strata_validation"] = {
        "is_valid": strata_valid,
        "missing_strata": missing_strata
    }
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    return str(output_path)

def ensure_schema_compliance() -> bool:
    """
    Ensure the data directory structure is compliant with the schema.
    Creates directories if missing and validates strata.
    
    Returns:
        True if the structure is compliant, False otherwise.
    """
    # Create directories
    create_directories()
    
    # Validate structure
    is_valid, missing = validate_directory_structure()
    if not is_valid:
        return False
        
    # Validate strata exist (optional, may not exist yet)
    # We don't fail here as strata are created by stratify.py
    
    return True
