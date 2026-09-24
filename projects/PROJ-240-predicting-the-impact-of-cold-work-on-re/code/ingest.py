"""
T022: Implement validation and size check in code/ingest.py.

Logic:
1. Load data/processed/clipped.csv (from T021).
2. Fail-Fast: Check if dataset size < 50 rows (FR-008). If so, raise ValueError.
3. Transformation: Verify all required columns exist.
4. Save validated data to data/processed/validated_clipped.csv.
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from config import get_project_root, get_config_value

# Constants
REQUIRED_COLUMNS = [
    'cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 
    'annealing_temp_K', 'time_to_peak_min'
]
MIN_ROWS_THRESHOLD = 50

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value from config.py."""
    # Import dynamically to avoid circular imports if needed, 
    # though config is usually static.
    from config import get_config_value as gcv
    return gcv(key, default)

def load_data(file_path: Path) -> pd.DataFrame:
    """Load data from a CSV file with strict validation."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file {file_path} not found.")
    
    # Security hardening: explicit dtype enforcement and na_filter
    try:
        df = pd.read_csv(
            file_path,
            dtype={
                'cold_work_pct': float,
                'Mn_wt': float,
                'Mg_wt': float,
                'Si_wt': float,
                'Cu_wt': float,
                'annealing_temp_K': float,
                'time_to_peak_min': float
            },
            na_filter=True
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load data from {file_path}: {e}")
    
    return df

def validate_dataset_size(df: pd.DataFrame, min_rows: int = MIN_ROWS_THRESHOLD) -> None:
    """
    Fail-Fast: Check if dataset size is below the minimum threshold.
    Raises ValueError if rows < min_rows.
    """
    n_rows = len(df)
    if n_rows < min_rows:
        raise ValueError(
            f"FR-008 Violation: Dataset size ({n_rows} rows) is below the minimum "
            f"threshold ({min_rows} rows) required for 5-fold cross-validation "
            f"statistical power. Processing halted."
        )

def validate_columns(df: pd.DataFrame, required_cols: List[str] = REQUIRED_COLUMNS) -> None:
    """Verify all required columns exist in the DataFrame."""
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_yaml(checksum: str, artifact_path: str) -> None:
    """Update state YAML with the new checksum."""
    project_root = get_project_root()
    state_path = project_root / "state" / "projects" / "PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml"
    
    if not state_path.exists():
        # Create directory if it doesn't exist
        state_path.parent.mkdir(parents=True, exist_ok=True)
        # Initialize a basic state file if missing
        state_data = {"artifact_hashes": {}}
    else:
        import yaml
        with open(state_path, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {"artifact_hashes": {}}
            except yaml.YAMLError:
                state_data = {"artifact_hashes": {}}

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    # Update the checksum for this specific artifact
    state_data["artifact_hashes"][artifact_path.name] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f)

def run_ingestion_pipeline() -> pd.DataFrame:
    """
    Main pipeline logic for T022.
    1. Load clipped.csv.
    2. Validate size (Fail-Fast).
    3. Validate columns.
    4. Save to validated_clipped.csv.
    5. Update checksums and state.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "clipped.csv"
    output_path = project_root / "data" / "processed" / "validated_clipped.csv"
    
    print(f"T022: Loading data from {input_path}...")
    df = load_data(input_path)
    
    print(f"T022: Validating dataset size (threshold: {MIN_ROWS_THRESHOLD})...")
    validate_dataset_size(df)
    
    print(f"T022: Validating required columns...")
    validate_columns(df)
    
    print(f"T022: Saving validated data to {output_path}...")
    df.to_csv(output_path, index=False)
    
    # Data Hygiene: Compute checksum and update state
    checksum = compute_sha256(output_path)
    checksum_path = output_path.with_suffix('.csv.sha256')
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    
    update_state_yaml(checksum, output_path)
    
    print(f"T022: Successfully validated and saved {len(df)} rows.")
    print(f"T022: Checksum: {checksum}")
    
    return df

def main():
    """Entry point for T022."""
    try:
        run_ingestion_pipeline()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"VALIDATION ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()