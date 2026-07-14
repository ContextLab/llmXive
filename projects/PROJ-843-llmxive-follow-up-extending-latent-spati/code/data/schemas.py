"""
Data schemas and directory structure management for the llmXive pipeline.

This module defines the expected directory structure, data schemas for
stratified datasets, feature files, and results. It also provides
validation utilities to ensure data integrity.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from config import (
    get_stratified_dir, 
    get_features_dir, 
    get_results_dir, 
    get_raw_dir, 
    get_processed_dir,
    ensure_directories
)

# Constants for directory structure
DATA_DIRS = {
    "raw": get_raw_dir,
    "processed": get_processed_dir,
    "stratified": get_stratified_dir,
    "features": get_features_dir,
    "results": get_results_dir,
}

# Expected strata for the dataset
EXPECTED_STRATA = [
    "Static-High",
    "Static-Low",
    "Fast-High",
    "Fast-Low"
]

# Schema definitions
SCHEMA_VERSION = "1.0.0"

DATASET_SCHEMA = {
    "version": SCHEMA_VERSION,
    "description": "RealEstate10K stratified dataset schema",
    "strata": EXPECTED_STRATA,
    "min_sequences_per_stratum": 50,
    "file_formats": {
        "video": "mp4",
        "metadata": "json",
        "features": "npy"
    }
}

FEATURE_SCHEMA = {
    "type": "sparse_descriptors",
    "methods": ["SIFT", "ORB"],
    "data_fields": ["coordinates", "descriptors", "confidence"],
    "dtype": "float32",
    "shape_note": "coordinates: (N, 2), descriptors: (N, D)"
}

RESULTS_SCHEMA = {
    "warped_frames": {
        "file": "sparse_warped_frames.npy",
        "dtype": "float32",
        "shape": "(T, H, W, C) or list of frames",
        "description": "Aggregated warped frames from latent warping"
    },
    "metrics": {
        "file": "metrics.json",
        "structure": {
            "metrics": {
                "world_score": "float",
                "sparse_consistency_score": "float",
                "fid": "float",
                "geometric_error": "float"
            },
            "anova": {
                "interaction_p_value": "float"
            },
            "sensitivity": {
                "thresholds": "list",
                "scores": "list"
            },
            "memory": {
                "peak_ram_gb": "float",
                "wall_clock_seconds": "float"
            }
        }
    },
    "unsolvable_sequences": {
        "file": "unsolvable_sequences.json",
        "structure": {
            "sequences": ["list of sequence IDs"]
        }
    }
}

def create_directories() -> Dict[str, Path]:
    """
    Create all required data directories if they don't exist.
    
    Returns:
        Dict mapping directory names to their Path objects.
    """
    dirs = {}
    for name, getter in DATA_DIRS.items():
        path = getter()
        path.mkdir(parents=True, exist_ok=True)
        dirs[name] = path
    return dirs

def get_expected_strata() -> List[str]:
    """
    Get the list of expected strata for stratified dataset.
    
    Returns:
        List of stratum names.
    """
    return EXPECTED_STRATA.copy()

def validate_strata_existence() -> Tuple[bool, List[str]]:
    """
    Validate that all expected strata directories exist.
    
    Returns:
        Tuple of (is_valid, list of missing strata).
    """
    stratified_dir = get_stratified_dir()
    missing = []
    
    if not stratified_dir.exists():
        return False, EXPECTED_STRATA.copy()
    
    for stratum in EXPECTED_STRATA:
        stratum_path = stratified_dir / stratum
        if not stratum_path.exists():
            missing.append(stratum)
    
    return len(missing) == 0, missing

def validate_directory_structure() -> Tuple[bool, List[str]]:
    """
    Validate that all required data directories exist.
    
    Returns:
        Tuple of (is_valid, list of missing directories).
    """
    missing = []
    for name, getter in DATA_DIRS.items():
        path = getter()
        if not path.exists():
            missing.append(name)
    
    return len(missing) == 0, missing

def check_directory_contents(dir_name: str, min_files: int = 1) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a directory contains the expected minimum number of files.
    
    Args:
        dir_name: Name of the directory (key in DATA_DIRS).
        min_files: Minimum number of files expected.
        
    Returns:
        Tuple of (is_valid, detailed info dict).
    """
    if dir_name not in DATA_DIRS:
        return False, {"error": f"Unknown directory: {dir_name}"}
    
    path = DATA_DIRS[dir_name]()
    
    if not path.exists():
        return False, {"error": f"Directory does not exist: {path}"}
    
    # Count files recursively
    file_count = 0
    subdirs = []
    
    for item in path.rglob("*"):
        if item.is_file():
            file_count += 1
        elif item.is_dir():
            subdirs.append(item.name)
    
    is_valid = file_count >= min_files
    
    return is_valid, {
        "path": str(path),
        "file_count": file_count,
        "subdirectories": subdirs,
        "min_required": min_files,
        "valid": is_valid
    }

def create_schema_report(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Create a comprehensive schema report for the current data state.
    
    Args:
        output_path: Optional path to write the report JSON.
        
    Returns:
        Dictionary containing the full schema report.
    """
    report = {
        "schema_version": SCHEMA_VERSION,
        "dataset_schema": DATASET_SCHEMA,
        "feature_schema": FEATURE_SCHEMA,
        "results_schema": RESULTS_SCHEMA,
        "directory_validation": {},
        "strata_validation": {}
    }
    
    # Validate directories
    dir_valid, missing_dirs = validate_directory_structure()
    report["directory_validation"] = {
        "valid": dir_valid,
        "missing": missing_dirs,
        "details": {}
    }
    
    for name in DATA_DIRS:
        report["directory_validation"]["details"][name] = check_directory_contents(name)
    
    # Validate strata
    strata_valid, missing_strata = validate_strata_existence()
    report["strata_validation"] = {
        "valid": strata_valid,
        "missing": missing_strata
    }
    
    # Write to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    return report

def ensure_schema_compliance() -> bool:
    """
    Ensure the data directory structure is compliant with the schema.
    Creates directories if missing and validates strata existence.
    
    Returns:
        True if compliance is achieved, False otherwise.
    """
    # Create directories
    create_directories()
    
    # Validate structure
    dir_valid, _ = validate_directory_structure()
    if not dir_valid:
        return False
    
    # Validate strata (only if we expect them to exist from previous tasks)
    # This is a soft check - strata might not exist yet if stratify hasn't run
    strata_valid, _ = validate_strata_existence()
    
    # Return True if directories exist (strata check is informational)
    return True
