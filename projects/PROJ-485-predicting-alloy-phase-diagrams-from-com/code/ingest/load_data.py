"""
Data ingestion module for loading alloy phase data.
Supports HTTP access with backoff, streaming, and local fallback.
"""
import os
import sys
import time
import json
import hashlib
import csv
import requests
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.checksum import compute_file_sha256, compute_and_store_checksum
from utils.config import get_config

logger = get_logger(__name__)

def check_data_source_availability():
    """Check if data sources are configured and available."""
    config = get_config()
    nist_url = config.get("nist_janaf_url", "")
    sgte_url = config.get("sgte_url", "")
    local_path = config.get("local_fallback_path", "")

    if not nist_url and not sgte_url and not local_path:
        log_error(logger, f"Error Code: {ErrorCode.DATA_SOURCE_MISSING.value}")
        raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: No data sources configured")

    return True

def stream_data(url: str, chunksize: int = 10000):
    """Stream data from a URL in chunks."""
    for chunk in pd.read_csv(url, chunksize=chunksize):
        yield chunk

def load_data_from_url(url: str) -> pd.DataFrame:
    """Load data from a URL with exponential backoff."""
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            log_info(logger, f"Attempting to fetch data from {url} (attempt {attempt + 1})")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Save to temp file and return dataframe
            temp_path = "data/raw/temp_ingestion.csv"
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            df = pd.read_csv(temp_path)
            log_info(logger, f"Successfully loaded {len(df)} rows from {url}")
            return df

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [429, 503]:
                delay = base_delay * (2 ** attempt)
                log_warning(logger, f"Rate limited. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                log_error(logger, f"HTTP Error: {str(e)}")
                raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: {str(e)}")
        except Exception as e:
            log_error(logger, f"Fetch failed: {str(e)}")
            if attempt == max_retries - 1:
                raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: {str(e)}")
            time.sleep(base_delay * (2 ** attempt))

    raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Max retries exceeded")

def load_data_from_local_fallback(local_path: str) -> pd.DataFrame:
    """Load data from a local CSV file."""
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Local file not found: {local_path}")

    # Verify checksum if available
    config = get_config()
    # In a real implementation, we would verify against stored checksums

    df = pd.read_csv(local_path)
    log_info(logger, f"Successfully loaded {len(df)} rows from local file: {local_path}")
    return df

def filter_missing_temperature(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows with missing temperature values."""
    initial_count = len(df)
    # Filter rows where temperature is not null/NaN
    df_filtered = df.dropna(subset=['temperature'])
    removed = initial_count - len(df_filtered)
    if removed > 0:
        log_warning(logger, f"Removed {removed} rows with missing temperature values")
        # Log specific errors
        for idx, row in df[df['temperature'].isna()].iterrows():
            log_error(logger, json.dumps({
                "timestamp": time.time(),
                "level": "ERROR",
                "code": ErrorCode.MISSING_TEMP_COORDS.value,
                "message": f"Row {idx} excluded: missing temperature-composition coordinates"
            }))
    return df_filtered

def compute_row_checksum(row: Dict) -> str:
    """Compute SHA-256 checksum for a single row."""
    row_str = json.dumps(row, sort_keys=True)
    return hashlib.sha256(row_str.encode()).hexdigest()

def compute_dataset_checksum(df: pd.DataFrame) -> str:
    """Compute SHA-256 checksum for the entire dataset."""
    # Convert to JSON string for consistent hashing
    data_str = df.to_json(orient='records', sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()

def update_state_with_checksum(state_file: str, artifact_name: str, file_path: str):
    """Update the state file with the checksum of an artifact."""
    import json
    state = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)

    checksum = compute_file_sha256(file_path)
    state["artifacts"][artifact_name] = {
        "path": file_path,
        "sha256": checksum,
        "timestamp": time.time()
    }

    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def verify_processed_data_integrity(state_file: str, artifact_name: str, expected_path: str):
    """Verify the integrity of processed data against stored checksum."""
    if not os.path.exists(state_file):
        log_warning(logger, "State file not found, skipping integrity check")
        return

    with open(state_file, 'r') as f:
        state = json.load(f)

    if artifact_name not in state.get("artifacts", {}):
        log_warning(logger, f"Artifact {artifact_name} not found in state")
        return

    expected_hash = state["artifacts"][artifact_name]["sha256"]
    actual_hash = compute_file_sha256(expected_path)

    if expected_hash != actual_hash:
        log_error(logger, f"{ErrorCode.DATA_INTEGRITY_VIOLATION.value}: Checksum mismatch for {artifact_name}")
        raise ValueError(f"{ErrorCode.DATA_INTEGRITY_VIOLATION.value}: Expected {expected_hash}, got {actual_hash}")

    log_info(logger, f"Integrity verified for {artifact_name}")

def load_data():
    """Main function to load and preprocess data."""
    check_data_source_availability()
    config = get_config()

    df = None
    local_path = config.get("local_fallback_path", "")
    nist_url = config.get("nist_janaf_url", "")
    sgte_url = config.get("sgte_url", "")

    if local_path and os.path.exists(local_path):
        df = load_data_from_local_fallback(local_path)
    elif nist_url:
        df = load_data_from_url(nist_url)
    elif sgte_url:
        df = load_data_from_url(sgte_url)
    else:
        raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: No valid data source found")

    # Filter missing temperatures
    df = filter_missing_temperature(df)

    # Save processed data
    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/descriptors.csv"
    df.to_csv(output_path, index=False)

    # Compute and store checksum
    state_file = "state/PROJ-485/pipeline_state.json"
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    update_state_with_checksum(state_file, "raw_data", output_path)

    log_info(logger, f"Data ingestion complete. Saved to {output_path}")
    return df

def main():
    """Entry point for data ingestion."""
    load_data()

if __name__ == "__main__":
    main()
