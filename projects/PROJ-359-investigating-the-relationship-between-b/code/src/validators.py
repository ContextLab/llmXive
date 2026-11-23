"""
Validators for ID matching and behavioral column verification.

Implements FR-009 (ID matching) and FR-012 (behavioral column verification).
Exits with code 1 and logs fatal errors on mismatch.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import List, Set, Tuple, Optional

# Import from existing project utilities
from src.utils import get_log_path, load_existing_log, write_json_log, log_event

def parse_participant_ids_from_dirs(data_dir: Path) -> Set[str]:
    """
    Parse participant IDs from sub-*/ folders in the dataset directory.
    
    Args:
        data_dir: Path to the dataset root (e.g., data/raw/ds000278)
        
    Returns:
        Set of participant IDs (e.g., {'01', '02', '03'})
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    participant_ids = set()
    for item in data_dir.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            # Extract ID from sub-XX format
            participant_id = item.name.replace("sub-", "")
            participant_ids.add(participant_id)
    
    return participant_ids


def parse_participant_ids_from_behavioral(behavioral_path: Path) -> Set[str]:
    """
    Parse participant IDs from the behavioral TSV file.
    
    Args:
        behavioral_path: Path to the behavioral data TSV file
        
    Returns:
        Set of participant IDs from the behavioral file
    """
    if not behavioral_path.exists():
        raise FileNotFoundError(f"Behavioral file not found: {behavioral_path}")
    
    # Try to read the TSV file
    try:
        df = pd.read_csv(behavioral_path, sep='\t')
    except Exception as e:
        raise RuntimeError(f"Failed to read behavioral TSV: {e}")
    
    # Look for common participant ID column names
    id_columns = ['participant_id', 'participant', 'sub', 'subject', 'id']
    id_col = None
    
    for col in id_columns:
        if col in df.columns:
            id_col = col
            break
    
    if id_col is None:
        # Try case-insensitive match
        for col in df.columns:
            if col.lower() in id_columns:
                id_col = col
                break
    
    if id_col is None:
        raise ValueError(f"No participant ID column found in {behavioral_path}. Available columns: {list(df.columns)}")
    
    # Extract IDs, handling potential prefix (sub-)
    ids = set()
    for val in df[id_col].dropna().astype(str):
        if val.startswith("sub-"):
            ids.add(val.replace("sub-", ""))
        else:
            ids.add(val)
    
    return ids


def validate_id_matching(data_dir: Path, behavioral_path: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that participant IDs match between directory structure and behavioral data.
    
    Implements FR-009: ID matching validation.
    
    Args:
        data_dir: Path to the dataset root
        behavioral_path: Path to the behavioral TSV file
        
    Returns:
        Tuple of (is_valid, missing_in_behavioral, missing_in_dirs)
    """
    try:
        dir_ids = parse_participant_ids_from_dirs(data_dir)
    except Exception as e:
        return False, [], [f"Error parsing directory IDs: {e}"]
    
    try:
        behavioral_ids = parse_participant_ids_from_behavioral(behavioral_path)
    except Exception as e:
        return False, [], [f"Error parsing behavioral IDs: {e}"]
    
    missing_in_behavioral = sorted(dir_ids - behavioral_ids)
    missing_in_dirs = sorted(behavioral_ids - dir_ids)
    
    is_valid = len(missing_in_behavioral) == 0 and len(missing_in_dirs) == 0
    
    return is_valid, missing_in_behavioral, missing_in_dirs


def validate_behavioral_columns(behavioral_path: Path, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that required behavioral columns exist in the behavioral TSV.
    
    Implements FR-012: Behavioral column verification.
    
    Args:
        behavioral_path: Path to the behavioral TSV file
        required_columns: List of required column names (e.g., ['nback_dprime', 'wm_accuracy'])
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    if not behavioral_path.exists():
        return False, [f"Behavioral file not found: {behavioral_path}"]
    
    try:
        df = pd.read_csv(behavioral_path, sep='\t')
    except Exception as e:
        return False, [f"Failed to read behavioral TSV: {e}"]
    
    # Normalize column names for comparison (case-insensitive)
    available_cols = {col.lower(): col for col in df.columns}
    
    missing_columns = []
    for req_col in required_columns:
        req_col_lower = req_col.lower()
        if req_col_lower not in available_cols:
            missing_columns.append(req_col)
    
    is_valid = len(missing_columns) == 0
    
    return is_valid, missing_columns


def run_validators(data_dir: str, behavioral_path: str, log_path: Optional[str] = None) -> int:
    """
    Run all validators and exit with appropriate code.
    
    Args:
        data_dir: Path to the dataset root
        behavioral_path: Path to the behavioral TSV file
        log_path: Optional path to the JSON log file
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    data_dir = Path(data_dir)
    behavioral_path = Path(behavioral_path)
    
    # Setup logging
    if log_path:
        log_path = Path(log_path)
    else:
        log_path = get_log_path("pipeline_log.json")
    
    # Load existing log or create new one
    log_data = load_existing_log(log_path) if log_path.exists() else {}
    
    exit_code = 0
    
    # --- ID Matching Validation (FR-009) ---
    id_valid, missing_beh, missing_dirs = validate_id_matching(data_dir, behavioral_path)
    
    if not id_valid:
        exit_code = 1
        error_msg = "ID_VALIDATION: FAIL"
        
        if missing_beh:
            error_msg += f" - Missing in behavioral: {missing_beh}"
        if missing_dirs:
            error_msg += f" - Missing in directories: {missing_dirs}"
        
        log_event(log_data, "id_validation", {
            "status": "FAIL",
            "missing_in_behavioral": missing_beh,
            "missing_in_directories": missing_dirs,
            "error": error_msg
        })
        
        print(f"ERROR: {error_msg}", file=sys.stderr)
    else:
        log_event(log_data, "id_validation", {
            "status": "PASS",
            "total_participants": len(parse_participant_ids_from_dirs(data_dir))
        })
        print("ID validation: PASS")
    
    # --- Behavioral Column Validation (FR-012) ---
    # Check for either nback_dprime OR wm_accuracy
    required_cols = ["nback_dprime", "wm_accuracy"]
    col_valid, missing_cols = validate_behavioral_columns(behavioral_path, required_cols)
    
    if not col_valid:
        exit_code = 1
        error_msg = "BEHAVIORAL_COLUMN: FAIL"
        
        # Check if we have at least one of the required columns
        available_cols = set(pd.read_csv(behavioral_path, sep='\t').columns.str.lower())
        has_nback = "nback_dprime" in available_cols
        has_wm = "wm_accuracy" in available_cols
        
        if not has_nback and not has_wm:
            error_msg += f" - Missing required working memory column (nback_dprime or wm_accuracy)"
        else:
            # We have one, but the specific check failed for some reason
            error_msg += f" - Missing: {missing_cols}"
        
        log_event(log_data, "behavioral_column_validation", {
            "status": "FAIL",
            "missing_columns": missing_cols,
            "error": error_msg
        })
        
        print(f"ERROR: {error_msg}", file=sys.stderr)
    else:
        # Determine which column was found
        available_cols = set(pd.read_csv(behavioral_path, sep='\t').columns.str.lower())
        found_col = "nback_dprime" if "nback_dprime" in available_cols else "wm_accuracy"
        
        log_event(log_data, "behavioral_column_validation", {
            "status": "PASS",
            "found_column": found_col
        })
        print(f"Behavioral column validation: PASS (found: {found_col})")
    
    # Write updated log
    write_json_log(log_data, log_path)
    
    return exit_code


def main():
    """Main entry point for validators."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate dataset IDs and behavioral columns")
    parser.add_argument("--data-dir", required=True, help="Path to dataset root directory")
    parser.add_argument("--behavioral", required=True, help="Path to behavioral TSV file")
    parser.add_argument("--log", help="Path to JSON log file (default: data/logs/pipeline_log.json)")
    
    args = parser.parse_args()
    
    exit_code = run_validators(args.data_dir, args.behavioral, args.log)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
