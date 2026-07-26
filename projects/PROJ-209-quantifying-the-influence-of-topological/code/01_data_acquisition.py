import os
import csv
import time
import json
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# Utility Functions (Shared across steps)
# ---------------------------------------------------------------------------

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    current = Path(__file__).resolve()
    # Assuming code/01_data_acquisition.py is at code/
    return current.parent.parent

def ensure_output_directories():
    """Creates necessary output directories if they don't exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "state",
        root / "data" / "validation",
        root / "code",
        root / "tests",
        root / "notebooks"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_git_hash() -> str:
    """Attempts to get the current git commit hash."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: str) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json_file(path: Path) -> Dict[str, Any]:
    """Loads a JSON file, returning empty dict if not found."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: Path, data: Dict[str, Any]):
    """Saves a dictionary to a JSON file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_to_dicts(path: Path) -> List[Dict[str, str]]:
    """Loads a CSV file into a list of dictionaries."""
    if not path.exists():
        return []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(data: List[Dict[str, Any]], path: Path, fieldnames: Optional[List[str]] = None):
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file with headers if possible, or just empty
        with open(path, 'w', newline='', encoding='utf-8') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            else:
                f.write("")
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

def parse_float_safe(value: Any) -> Optional[float]:
    """Safely parses a value to float, returning None on failure."""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def validate_schema(data: List[Dict[str, Any]], required_fields: List[str]) -> List[Dict[str, Any]]:
    """Validates that all required fields exist and are non-null in the data."""
    valid_data = []
    for row in data:
        if all(field in row and row[field] is not None and row[field] != '' for field in required_fields):
            valid_data.append(row)
    return valid_data

# ---------------------------------------------------------------------------
# Step 7: Synthetic Data Validation (T016b)
# ---------------------------------------------------------------------------

def run_synthetic_validation():
    """
    Step 7: Synthetic Data Validation.
    Dependency: T013, T012 (synthetic flag).
    Condition: Only if data_source is synthetic.
    Action: Validate physical bounds, exclude violations, log exclusions.
    """
    root = get_project_root()
    ensure_output_directories()

    data_source_path = root / "data" / "state" / "data_source.json"
    data_source = load_json_file(data_source_path)

    source_type = data_source.get("source_type", "unknown")
    
    # Check if we are in synthetic mode
    if source_type != "synthetic":
        # If not synthetic, this step is not applicable, but we must still produce outputs
        # to satisfy the "Guaranteed Output" requirement (empty logs if not applicable)
        exclusion_log_path = root / "data" / "state" / "synthetic_exclusions.json"
        save_json_file(exclusion_log_path, {"status": "skipped", "reason": "source_not_synthetic", "excluded_count": 0})
        
        # Ensure cleaned files exist (empty if not applicable)
        train_path = root / "data" / "raw" / "synthetic_train.csv"
        holdout_path = root / "data" / "raw" / "synthetic_holdout.csv"
        
        # If files don't exist, create empty ones
        if not train_path.exists():
            save_to_csv([], train_path)
        if not holdout_path.exists():
            save_to_csv([], holdout_path)
            
        return

    # Define physical bounds based on task description and physics
    # Conductivity > 0
    # Defect density > 0 (implied by physics, though task said "∈ [, ]" which is ambiguous, assuming > 0)
    # Fracture energy > 0
    # Young's Modulus > 0
    
    bounds = {
        "conductivity": {"min": 0.0, "max": None},
        "defect_density": {"min": 0.0, "max": None},
        "fracture_energy": {"min": 0.0, "max": None},
        "youngs_modulus": {"min": 0.0, "max": None}
    }

    exclusion_log = {
        "status": "completed",
        "total_rows_checked": 0,
        "excluded_count": 0,
        "excluded_rows": []
    }

    def validate_row(row: Dict[str, str], row_idx: int) -> bool:
        """Validates a single row against physical bounds."""
        for field, limits in bounds.items():
            val = parse_float_safe(row.get(field))
            if val is None:
                # Missing value is a violation for physical bounds check
                exclusion_log["excluded_rows"].append({
                    "row_index": row_idx,
                    "field": field,
                    "reason": f"missing_or_invalid_{field}"
                })
                return False
            
            if limits["min"] is not None and val <= limits["min"]:
                exclusion_log["excluded_rows"].append({
                    "row_index": row_idx,
                    "field": field,
                    "value": val,
                    "reason": f"below_min_{field}"
                })
                return False
            
            if limits["max"] is not None and val >= limits["max"]:
                exclusion_log["excluded_rows"].append({
                    "row_index": row_idx,
                    "field": field,
                    "value": val,
                    "reason": f"above_max_{field}"
                })
                return False
        return True

    # Process Train Set
    train_path = root / "data" / "raw" / "synthetic_train.csv"
    if train_path.exists():
        train_data = load_csv_to_dicts(train_path)
        exclusion_log["total_rows_checked"] += len(train_data)
        valid_train_data = []
        for idx, row in enumerate(train_data):
            if validate_row(row, idx):
                valid_train_data.append(row)
            else:
                exclusion_log["excluded_count"] += 1
        
        # Save cleaned train data
        save_to_csv(valid_train_data, train_path)
    else:
        # If file doesn't exist, create empty one
        save_to_csv([], train_path)

    # Process Hold-out Set
    holdout_path = root / "data" / "raw" / "synthetic_holdout.csv"
    if holdout_path.exists():
        holdout_data = load_csv_to_dicts(holdout_path)
        # Note: Task description specifically asks to log exclusions to synthetic_exclusions.json
        # and write cleaned synthetic_train.csv. It implies we validate both but output log for both.
        # We will also clean holdout for consistency, though task emphasizes train output.
        valid_holdout_data = []
        for idx, row in enumerate(holdout_data):
            if validate_row(row, idx + exclusion_log["total_rows_checked"]): # Unique index
                valid_holdout_data.append(row)
            else:
                exclusion_log["excluded_count"] += 1
        
        save_to_csv(valid_holdout_data, holdout_path)
    else:
        save_to_csv([], holdout_path)

    # Write exclusion log
    exclusion_log_path = root / "data" / "state" / "synthetic_exclusions.json"
    save_json_file(exclusion_log_path, exclusion_log)

    print(f"Synthetic Validation Complete: {exclusion_log['excluded_count']} rows excluded.")

def main():
    """Main entry point for the data acquisition script."""
    ensure_output_directories()
    run_synthetic_validation()

if __name__ == "__main__":
    main()