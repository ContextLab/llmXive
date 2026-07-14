import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config import get_stratified_dir, get_features_dir, get_results_dir

EXPECTED_STRATA = [
    "Static-High",
    "Static-Low",
    "Fast-High",
    "Fast-Low",
]

def get_expected_strata() -> List[str]:
    return EXPECTED_STRATA

def create_directories() -> None:
    """Create directory structure for stratified data."""
    stratified_dir = get_stratified_dir()
    for stratum in EXPECTED_STRATA:
        (stratified_dir / stratum).mkdir(parents=True, exist_ok=True)

def check_directory_contents(path: Path) -> Tuple[bool, str]:
    """Check if a directory has content."""
    if not path.exists():
        return False, "Path does not exist"
    if not path.is_dir():
        return False, "Path is not a directory"
    if not any(path.iterdir()):
        return False, "Directory is empty"
    return True, "OK"

def validate_directory_structure() -> bool:
    """Validate the entire data structure."""
    stratified_dir = get_stratified_dir()
    if not stratified_dir.exists():
        return False
    for stratum in EXPECTED_STRATA:
        sub = stratified_dir / stratum
        if not sub.exists() or not any(sub.iterdir()):
            return False
    return True

def validate_strata_existence() -> bool:
    """Check if all expected strata directories exist."""
    stratified_dir = get_stratified_dir()
    for stratum in EXPECTED_STRATA:
        if not (stratified_dir / stratum).exists():
            return False
    return True

def create_schema_report() -> Dict[str, Any]:
    """Generate a schema compliance report."""
    return {
        "expected_strata": EXPECTED_STRATA,
        "strata_exist": validate_strata_existence(),
        "structure_valid": validate_directory_structure(),
    }

def ensure_schema_compliance() -> bool:
    """Ensure schema compliance, create dirs if missing."""
    if not validate_strata_existence():
        create_directories()
    return validate_strata_existence()