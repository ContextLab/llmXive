import os
import sys
import json
import hashlib
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
RAW_DATA_DIR = project_root / "data" / "raw"
PROCESSED_DATA_DIR = project_root / "data" / "processed"
ALIGNMENT_OUTPUT = PROCESSED_DATA_DIR / "aligned_timeseries.csv"
STATIONARITY_OUTPUT = PROCESSED_DATA_DIR / "stationarity_check.csv"
CHECKSUMS_FILE = PROCESSED_DATA_DIR / ".checksums.json"
MIN_COMPLETENESS = 0.95
MIN_DATA_LENGTH = 20

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def calculate_completeness(df: pd.DataFrame) -> float:
    """Calculate data completeness as ratio of non-null rows to total rows."""
    total_rows = len(df)
    if total_rows == 0:
        return 0.0
    non_null_rows = df.dropna(how='all').shape[0]
    return non_null_rows / total_rows

def load_processed_data() -> tuple:
    """
    Load the processed data from the preprocessing step.
    Expects stationarity_check.csv to exist with columns: date, news_zscore, anxiety_zscore
    """
    stationarity_file = PROCESSED_DATA_DIR / "stationarity_check.csv"
    if not stationarity_file.exists():
        logger.error(f"Processed data file not found: {stationarity_file}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(stationarity_file, parse_dates=['date'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        logger.info(f"Loaded {len(df)} rows from {stationarity_file}")
        return df
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        sys.exit(1)

def save_aligned_data(df: pd.DataFrame):
    """Save the aligned, stationary, normalized data."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(ALIGNMENT_OUTPUT, index=False)
    logger.info(f"Saved aligned data to {ALIGNMENT_OUTPUT}")

def save_stationarity_check(df: pd.DataFrame):
    """Save the stationarity check results (re-save for consistency)."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(STATIONARITY_OUTPUT, index=False)
    logger.info(f"Saved stationarity check to {STATIONARITY_OUTPUT}")

def save_checksums(file_path: Path, checksum: str):
    """Save checksums to JSON file."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    if CHECKSUMS_FILE.exists():
        try:
            with open(CHECKSUMS_FILE, 'r') as f:
                checksums = json.load(f)
        except json.JSONDecodeError:
            checksums = {}
    
    checksums[file_path.name] = {
        "md5": checksum,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    with open(CHECKSUMS_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Saved checksum for {file_path.name} to {CHECKSUMS_FILE}")

def validate_data_length(df: pd.DataFrame) -> bool:
    """Check if data length is sufficient for Granger causality (min 20)."""
    if len(df) < MIN_DATA_LENGTH:
        logger.error(f"Insufficient data for Granger causality: {len(df)} rows < {MIN_DATA_LENGTH}")
        return False
    return True

def main():
    """
    Main execution for T021: Save Aligned Data & Check Completeness.
    
    1. Load processed data from T020b output.
    2. Validate data length (min 20 rows).
    3. Save to aligned_timeseries.csv and stationarity_check.csv.
    4. Calculate completeness (non-null rows / total days).
    5. Verify completeness >= 95% (Spec SC-001). Exit 1 if not.
    6. Generate MD5 checksum for aligned_timeseries.csv and save to .checksums.json.
    """
    logger.info("Starting T021: Save Aligned Data & Check Completeness")
    
    # Step 1: Load processed data
    df = load_processed_data()
    
    # Step 2: Validate data length
    if not validate_data_length(df):
        sys.exit(1)
    
    # Step 3: Save outputs
    save_aligned_data(df)
    save_stationarity_check(df)
    
    # Step 4: Calculate completeness
    completeness = calculate_completeness(df)
    logger.info(f"Data completeness: {completeness:.2%} ({len(df.dropna(how='all'))}/{len(df)} rows)")
    
    # Step 5: Verify completeness threshold (Spec SC-001)
    if completeness < MIN_COMPLETENESS:
        logger.error(f"Data completeness {completeness:.2%} is below threshold {MIN_COMPLETENESS:.2%} (Spec SC-001). Exiting.")
        sys.exit(1)
    
    # Step 6: Generate and save checksum
    alignment_checksum = calculate_md5(ALIGNMENT_OUTPUT)
    save_checksums(ALIGNMENT_OUTPUT, alignment_checksum)
    
    logger.info("T021 completed successfully.")
    print(f"SUCCESS: Aligned data saved. Completeness: {completeness:.2%}. Checksum: {alignment_checksum}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
