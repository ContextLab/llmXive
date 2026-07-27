import os
import csv
import time
import json
import hashlib
import subprocess
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper Functions (Existing API Surface) ---

def get_project_root() -> str:
    """Returns the absolute path to the project root."""
    # Assuming the script is run from the project root or code/ directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level if in code/
    if os.path.basename(current_dir) == 'code':
        return os.path.dirname(current_dir)
    return current_dir

def ensure_output_directories():
    """Ensures that required output directories exist."""
    root = get_project_root()
    dirs = [
        os.path.join(root, 'data', 'raw'),
        os.path.join(root, 'data', 'state'),
        os.path.join(root, 'data', 'processed'),
        os.path.join(root, 'figures')
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def get_git_hash() -> Optional[str]:
    """Attempts to get the current git commit hash."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return None

def compute_sha256(filepath: str) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Loads a JSON file and returns its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]):
    """Saves a dictionary to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def load_csv_to_dicts(filepath: str) -> List[Dict[str, Any]]:
    """Loads a CSV file into a list of dictionaries."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(filepath: str, data: List[Dict[str, Any]]):
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file with headers if we know them, or just empty
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def parse_float_safe(value: Any) -> Optional[float]:
    """Safely parses a value to float, returning None if invalid."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def validate_schema(row: Dict[str, Any], required_fields: List[str]) -> bool:
    """Checks if a row contains all required fields with non-empty values."""
    for field in required_fields:
        if field not in row or row[field] is None or row[field] == '':
            return False
    return True

# --- Task Specific Logic: T016b Synthetic Data Validation ---

def run_synthetic_validation_step():
    """
    Implements Step 7 of User Story 1: Synthetic Data Validation.
    
    Dependencies:
      - data/state/data_source.json (from T015)
      - data/raw/synthetic_train.csv (from T013)
      - data/raw/synthetic_holdout.csv (from T015)
    
    Logic:
      1. Read data_source.json. If source_type is not 'synthetic', skip or log.
      2. Load synthetic_train.csv.
      3. Validate physical bounds:
         - conductivity > 0
         - defect_density in [low, 0.1] (assuming low is a small positive number or 0)
         - other fields if necessary (e.g., fracture_energy > 0)
      4. Exclude entries violating bounds.
      5. Save cleaned synthetic_train.csv.
      6. Save synthetic_exclusions.json with details.
    """
    root = get_project_root()
    ensure_output_directories()

    data_source_path = os.path.join(root, 'data', 'state', 'data_source.json')
    train_path = os.path.join(root, 'data', 'raw', 'synthetic_train.csv')
    holdout_path = os.path.join(root, 'data', 'raw', 'synthetic_holdout.csv')
    exclusions_path = os.path.join(root, 'data', 'state', 'synthetic_exclusions.json')

    # 1. Check data source
    try:
        data_source = load_json_file(data_source_path)
    except FileNotFoundError:
        logger.error(f"Cannot find {data_source_path}. Aborting T016b.")
        # Write empty exclusion log as per "Guaranteed Output"
        save_json_file(exclusions_path, {"status": "error", "reason": "data_source.json not found", "excluded_count": 0})
        # Ensure output file exists even if empty
        if not os.path.exists(train_path):
            save_to_csv(train_path, [])
        return

    source_type = data_source.get('source_type', '')
    
    if source_type != 'synthetic':
        logger.info(f"Source type is '{source_type}'. Synthetic validation (T016b) is not applicable. Skipping.")
        # Still write empty exclusion log and ensure train file exists if it doesn't
        save_json_file(exclusions_path, {"status": "skipped", "reason": "source_type_not_synthetic", "excluded_count": 0})
        if not os.path.exists(train_path):
            save_to_csv(train_path, [])
        return

    logger.info("Starting Synthetic Data Validation (T016b)...")

    # 2. Load synthetic_train.csv
    try:
        raw_data = load_csv_to_dicts(train_path)
    except FileNotFoundError:
        logger.error(f"Cannot find {train_path}. Creating empty output.")
        save_json_file(exclusions_path, {"status": "error", "reason": "synthetic_train.csv not found", "excluded_count": 0})
        save_to_csv(train_path, [])
        return

    logger.info(f"Loaded {len(raw_data)} rows from {train_path}")

    valid_rows = []
    excluded_rows = []
    exclusion_reasons = []

    # 3. Validate physical bounds
    # Define bounds based on task description:
    # - conductivity > 0
    # - defect_density in [low, 0.1] -> assuming low >= 0, so [0, 0.1]
    # - fracture_energy > 0 (implied by physics)
    
    for idx, row in enumerate(raw_data):
        is_valid = True
        reasons = []

        # Check conductivity
        conductivity = parse_float_safe(row.get('conductivity'))
        if conductivity is None or conductivity <= 0:
            is_valid = False
            reasons.append(f"conductivity invalid (got: {row.get('conductivity')})")

        # Check defect_density
        density = parse_float_safe(row.get('defect_density'))
        if density is None:
            is_valid = False
            reasons.append("defect_density is NaN")
        else:
            # Assuming bounds are [0, 0.1] based on "defect density ∈ [low, 0.1]"
            if density < 0 or density > 0.1:
                is_valid = False
                reasons.append(f"defect_density out of bounds [0, 0.1] (got: {density})")

        # Check fracture_energy (if present)
        fracture = parse_float_safe(row.get('fracture_energy'))
        if fracture is not None and fracture <= 0:
            is_valid = False
            reasons.append(f"fracture_energy <= 0 (got: {fracture})")
        
        # Check defect_type if present (should not be empty)
        if 'defect_type' in row and (not row['defect_type'] or row['defect_type'] == ''):
             is_valid = False
             reasons.append("defect_type is empty")

        if is_valid:
            valid_rows.append(row)
        else:
            excluded_rows.append({
                'row_index': idx,
                'original_data': row,
                'reasons': reasons
            })
            exclusion_reasons.extend(reasons)

    # 4. Save cleaned data
    save_to_csv(train_path, valid_rows)
    logger.info(f"Saved {len(valid_rows)} valid rows to {train_path}")

    # 5. Save exclusion log
    exclusion_log = {
        "status": "completed",
        "total_rows_processed": len(raw_data),
        "valid_rows_count": len(valid_rows),
        "excluded_rows_count": len(excluded_rows),
        "exclusions": excluded_rows,
        "summary_reasons": list(set(exclusion_reasons))
    }
    save_json_file(exclusions_path, exclusion_log)
    logger.info(f"Saved exclusion log to {exclusions_path}")

    logger.info("Synthetic Data Validation (T016b) completed successfully.")

# --- Main Entry Point ---

def main():
    """Main entry point for the script."""
    ensure_output_directories()
    run_synthetic_validation_step()

if __name__ == '__main__':
    main()