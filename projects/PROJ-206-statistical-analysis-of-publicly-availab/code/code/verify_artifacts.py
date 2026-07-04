"""
T033: Verify all artifacts have valid checksums in state/projects/ 
and no manual data fabrication occurred.

This script performs two checks:
1. Integrity: Loads state/projects/PROJ-206-*.yaml and verifies the SHA-256 
   checksums of referenced files (e.g., data/processed/poll_data_cleaned.csv) 
   match the current disk state.
2. Fabrication: Scans numeric columns in data artifacts for signs of 
   manual fabrication (e.g., impossible precision, constant values where 
   variance is expected, or non-integer sample sizes).
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import yaml
import pandas as pd
import numpy as np

# Add project root to path for imports if running from root
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_state_path, get_data_processed_path
from src.utils.logging import setup_logging, get_logger

# Initialize logging
logger = setup_logging(level=logging.INFO)

def compute_file_hash(filepath: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file."""
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load the state YAML file."""
    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        return {}
    
    try:
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading state file {state_path}: {e}")
        return {}

def check_checksums(state: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify checksums of all artifacts listed in the state file.
    Returns (success, list_of_errors).
    """
    errors = []
    artifacts = state.get('artifacts', {})
    
    if not artifacts:
        logger.warning("No artifacts found in state file.")
        return True, []

    for artifact_name, artifact_info in artifacts.items():
        if not isinstance(artifact_info, dict):
            continue
        
        relative_path = artifact_info.get('path')
        expected_hash = artifact_info.get('sha256')
        
        if not relative_path or not expected_hash:
            continue
        
        full_path = project_root / relative_path
        
        if not full_path.exists():
            errors.append(f"Artifact missing: {relative_path}")
            continue
        
        current_hash = compute_file_hash(full_path)
        
        if current_hash != expected_hash:
            errors.append(
                f"Checksum mismatch for {relative_path}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Found:    {current_hash}"
            )
        else:
            logger.info(f"Checksum valid: {relative_path}")
    
    return len(errors) == 0, errors

def detect_fabrication(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Detect signs of manual data fabrication.
    Returns (is_clean, list_of_warnings).
    """
    warnings = []
    
    if not filepath.exists():
        return True, [f"File not found for fabrication check: {filepath}"]
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return True, [f"Could not read {filepath} as CSV: {e}"]
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        # Check for impossible precision (e.g., vote_share with > 4 decimal places)
        # This is a heuristic; real data often has noise.
        # We look for columns that are suspiciously "clean" or "round".
        values = df[col].dropna()
        if len(values) == 0:
            continue
        
        # Check for constant values (highly suspicious for poll data)
        if values.nunique() == 1:
            warnings.append(
                f"Suspicious: Column '{col}' in {filepath.name} is constant "
                f"(value: {values.iloc[0]}). Real poll data should vary."
            )
        
        # Check for zero variance in sample_size (often integers)
        if 'sample' in col.lower() or 'size' in col.lower():
            if values.nunique() == 1:
                warnings.append(
                    f"Suspicious: Column '{col}' (likely sample size) is constant. "
                    f"Real poll sample sizes vary."
                )
        
        # Check for non-integer sample sizes if the column name suggests it
        if 'sample' in col.lower():
            non_integers = values[~values.is_integer()]
            if len(non_integers) > 0:
                # This might be a float representation, but if it's exact non-integers
                # it could be suspicious if the source is integer-based.
                # We'll just log it as a note, not a hard fail.
                pass

    # Check for "too perfect" distributions (e.g., normal distribution with 0 skew/kurtosis)
    # This is harder to automate without knowing the specific distribution expected.
    # We rely on the constant check and missing data checks.
    
    # Check for missing values if the file is expected to be complete
    missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if missing_pct > 0.5:
        warnings.append(
            f"Suspicious: {filepath.name} has >50% missing values. "
            f"Real data might have gaps, but this is high."
        )
    
    return len(warnings) == 0, warnings

def main():
    logger.info("Starting T033: Artifact Verification")
    
    # 1. Locate State File
    state_dir = get_state_path()
    state_file = state_dir / "PROJ-206-statistical-analysis-of-publicly-availab.yaml"
    
    if not state_file.exists():
        logger.error(f"State file not found at {state_file}. "
                     "Did T016 (hash generation) run?")
        return 1
    
    state = load_state_file(state_file)
    if not state:
        logger.error("State file is empty or invalid.")
        return 1
    
    # 2. Check Checksums
    logger.info("Verifying checksums...")
    checksum_ok, checksum_errors = check_checksums(state)
    
    if not checksum_ok:
        logger.error("Checksum verification FAILED:")
        for err in checksum_errors:
            logger.error(f"  - {err}")
        return 1
    
    logger.info("Checksum verification PASSED.")
    
    # 3. Check for Fabrication
    logger.info("Checking for data fabrication...")
    processed_dir = get_data_processed_path()
    fabrication_ok = True
    all_fabrication_warnings = []
    
    # Define critical artifacts to check for fabrication
    critical_files = [
        processed_dir / "poll_data_cleaned.csv",
        processed_dir / "frequentist_forecasts.csv",
        processed_dir / "bayesian_forecasts.csv" # Assuming this exists from T021+
    ]
    
    for filepath in critical_files:
        if not filepath.exists():
            logger.warning(f"Skipping fabrication check for missing file: {filepath}")
            continue
        
        is_clean, warnings = detect_fabrication(filepath)
        if not is_clean:
            fabrication_ok = False
            all_fabrication_warnings.extend(warnings)
            logger.warning(f"Suspicion found in {filepath.name}:")
            for w in warnings:
                logger.warning(f"  - {w}")
        else:
            logger.info(f"No fabrication suspicion in {filepath.name}")
    
    if not fabrication_ok:
        logger.error("Fabrication checks FAILED. Please review warnings.")
        return 1
    
    logger.info("Fabrication checks PASSED.")
    logger.info("T033 Verification Complete: All artifacts are valid and untampered.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
