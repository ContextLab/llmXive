import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config import get_stratified_dir, get_features_dir, get_results_dir

from config import (
    get_data_dir,
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
    ensure_directories
)


# Schema Definitions
DATA_SCHEMA = {
    "root": "data",
    "subdirectories": {
        "raw": {
            "description": "Raw downloaded datasets (RealEstate10K, dense baseline)",
            "required_files": [],
            "optional_files": ["dense_baseline_frames.npy"]
        },
        "processed": {
            "description": "Intermediate processed data (optional, for caching)",
            "required_files": [],
            "optional_files": []
        },
        "stratified": {
            "description": "Stratified subsets: Static/Slow/Fast x High/Low texture",
            "required_files": [],
            "subdirectories": {
                "static_high": {"description": "Static scenes, High texture"},
                "static_low": {"description": "Static scenes, Low texture"},
                "fast_high": {"description": "Fast motion, High texture"},
                "fast_low": {"description": "Fast motion, Low texture"}
            }
        },
        "features": {
            "description": "Extracted sparse features (SIFT/ORB) as .npy",
            "required_files": [],
            "subdirectories": {
                "static_high": {},
                "static_low": {},
                "fast_high": {},
                "fast_low": {}
            }
        },
        "results": {
            "description": "Final analysis results, metrics, and reports",
            "required_files": [
                "metrics.json",
                "anova_results.json",
                "sensitivity_results.json",
                "hypothesis_verification.md",
                "unsolvable_sequences.json"
            ],
            "optional_files": ["sparse_warped_frames.npy"]
        }
    }
}

EXPECTED_STRATA = ["static_high", "static_low", "fast_high", "fast_low"]


def create_directories() -> Dict[str, Path]:
    """
    Create the base data directory structure as defined in the schema.
    Returns a dictionary mapping directory names to their Path objects.
    """
    ensure_directories()
    
    paths = {
        "root": get_data_dir(),
        "raw": get_raw_dir(),
        "processed": get_processed_dir(),
        "stratified": get_stratified_dir(),
        "features": get_features_dir(),
        "results": get_results_dir()
    }

    # Ensure specific strata directories exist
    strata_dirs = {
        "static_high": get_stratified_dir() / "static_high",
        "static_low": get_stratified_dir() / "static_low",
        "fast_high": get_stratified_dir() / "fast_high",
        "fast_low": get_stratified_dir() / "fast_low"
    }

    for name, path in strata_dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        paths[name] = path

    # Ensure feature subdirectories match strata
    for name, path in strata_dirs.items():
        feature_path = get_features_dir() / name
        feature_path.mkdir(parents=True, exist_ok=True)
        paths[f"features_{name}"] = feature_path

    return paths


def get_expected_strata() -> List[str]:
    """Return the list of expected stratification folder names."""
    return EXPECTED_STRATA


def validate_strata_existence() -> Tuple[bool, List[str]]:
    """
    Check if all expected strata directories exist under data/stratified.
    Returns (is_valid, list_of_missing_strata).
    """
    missing = []
    for stratum in EXPECTED_STRATA:
        path = get_stratified_dir() / stratum
        if not path.exists() or not path.is_dir():
            missing.append(stratum)
    
    return len(missing) == 0, missing


def validate_directory_structure() -> Tuple[bool, List[str]]:
    """
    Validate the entire base data directory structure against the schema.
    Returns (is_valid, list_of_missing_paths).
    """
    missing = []
    
    # Check root directories
    root_dirs = ["raw", "processed", "stratified", "features", "results"]
    for d in root_dirs:
        path = get_data_dir() / d
        if not path.exists():
            missing.append(str(path))
    
    # Check strata existence
    is_valid_strata, missing_strata = validate_strata_existence()
    if not is_valid_strata:
        for s in missing_strata:
            missing.append(str(get_stratified_dir() / s))

    return len(missing) == 0, missing


def check_directory_contents(target_dir: Path, required_files: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if a specific directory contains the required files.
    Returns (is_valid, list_of_missing_files).
    """
    if not target_dir.exists():
        return False, [f"Directory {target_dir} does not exist"]

    missing = []
    for f in required_files:
        if not (target_dir / f).exists():
            missing.append(f)
    
    return len(missing) == 0, missing


def create_schema_report(output_path: Path) -> None:
    """
    Generate a JSON report of the current schema compliance status.
    """
    report = {
        "schema_version": "1.0",
        "root_path": str(get_data_dir()),
        "structure_valid": False,
        "strata_valid": False,
        "details": {}
    }

    # Validate structure
    structure_valid, missing_structure = validate_directory_structure()
    report["structure_valid"] = structure_valid
    report["details"]["missing_directories"] = missing_structure

    # Validate strata
    strata_valid, missing_strata = validate_strata_existence()
    report["strata_valid"] = strata_valid
    report["details"]["missing_strata"] = missing_strata

    # Check results directory for required files
    results_dir = get_results_dir()
    if results_dir.exists():
        required_results = DATA_SCHEMA["subdirectories"]["results"]["required_files"]
        valid_results, missing_results = check_directory_contents(results_dir, required_results)
        report["details"]["results_valid"] = valid_results
        report["details"]["missing_results_files"] = missing_results
    else:
        report["details"]["results_valid"] = False
        report["details"]["missing_results_files"] = DATA_SCHEMA["subdirectories"]["results"]["required_files"]

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)


def ensure_schema_compliance() -> bool:
    """
    Ensure the directory structure exists. Creates it if missing.
    Returns True if structure is valid after execution.
    """
    create_directories()
    structure_valid, _ = validate_directory_structure()
    return structure_valid
