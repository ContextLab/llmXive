"""
Data ingestion module for loading and processing alloy phase data.
Implements streaming, filtering, checksumming, and state management.
"""
import os
import sys
import time
import json
import hashlib
import csv
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.checksum import compute_file_sha256, verify_file_checksum
from utils.config import get_config

logger = get_logger(__name__)

def check_data_source_availability() -> bool:
    """Check if data sources are available in config."""
    config = get_config()
    nist_url = config.get('nist_janaf_url', '')
    sgte_url = config.get('sgte_url', '')
    local_path = config.get('local_fallback_path', '')

    if not nist_url and not sgte_url and not local_path:
        log_error(ErrorCode.DATA_SOURCE_MISSING, "No data sources configured in config.yaml")
        return False
    return True

def stream_data(url: str, chunk_size: int = 10000) -> List[Dict[str, Any]]:
    """Stream data from URL in chunks to avoid memory overflow."""
    import requests
    all_data = []
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Read as CSV chunks
        text_io = response.iter_lines(decode_unicode=True)
        reader = csv.DictReader(text_io)
        
        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                all_data.extend(chunk)
                chunk = []
        
        if chunk:
            all_data.extend(chunk)
            
    except requests.exceptions.RequestException as e:
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Failed to stream data from {url}: {str(e)}")
        raise ValueError(f"DATA_SOURCE_MISSING: {str(e)}")
        
    return all_data

def load_data_from_url(url: str) -> pd.DataFrame:
    """Load data from a URL with retry logic."""
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            log_info(None, f"Attempting to load data from {url} (attempt {attempt + 1})")
            if url.startswith('http'):
                data = stream_data(url)
            else:
                # Local file path
                if not os.path.exists(url):
                    raise FileNotFoundError(f"Local file not found: {url}")
                data = pd.read_csv(url).to_dict('records')
            
            if data:
                log_info(None, f"Successfully loaded {len(data)} rows")
                return pd.DataFrame(data)
            else:
                raise ValueError("No data loaded")
                
        except Exception as e:
            if attempt == max_retries - 1:
                log_error(ErrorCode.DATA_SOURCE_MISSING, f"Failed to load data after {max_retries} attempts: {str(e)}")
                raise ValueError(f"DATA_SOURCE_MISSING: {str(e)}")
            time.sleep(base_delay * (2 ** attempt))
            
def load_data_from_local_fallback(local_path: str) -> pd.DataFrame:
    """Load data from local fallback path."""
    if not local_path or not os.path.exists(local_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Local fallback path invalid: {local_path}")
        raise ValueError(f"DATA_SOURCE_MISSING: Local file not found: {local_path}")
    
    log_info(None, f"Loading data from local fallback: {local_path}")
    return pd.read_csv(local_path)

def filter_missing_temperature(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows with missing temperature values."""
    initial_count = len(df)
    
    # Handle binary systems: skip entries with missing temperature
    if 'temperature' in df.columns:
        df = df.dropna(subset=['temperature'])
    
    # Handle ternary systems: skip entries lacking temperature-composition coordinates
    ternary_mask = df['system_type'] == 'ternary' if 'system_type' in df.columns else pd.Series([False] * len(df))
    ternary_with_missing_temp = ternary_mask & (df['temperature'].isna() | (df['composition'].isna()))
    
    if ternary_with_missing_temp.any():
        log_warning(ErrorCode.MISSING_TEMP_COORDS, f"Excluded {ternary_with_missing_temp.sum()} ternary rows missing temperature-composition coordinates")
        # Log each excluded row to pipeline.log
        for idx in df[ternary_with_missing_temp].index:
            log_warning(ErrorCode.MISSING_TEMP_COORDS, f"Row {idx} excluded: ternary system missing temperature-composition coordinates")
    
    df = df[~ternary_with_missing_temp]
    final_count = len(df)
    log_info(None, f"Filtered {initial_count - final_count} rows with missing temperature data")
    
    return df.reset_index(drop=True)

def compute_row_checksum(row: Dict[str, Any]) -> str:
    """Compute SHA-256 checksum for a single row."""
    row_str = json.dumps(row, sort_keys=True)
    return hashlib.sha256(row_str.encode()).hexdigest()

def compute_dataset_checksum(df: pd.DataFrame) -> str:
    """Compute SHA-256 checksum for the entire dataset."""
    # Convert to JSON string for consistent hashing
    data_str = df.to_json(orient='records', date_format='iso')
    return hashlib.sha256(data_str.encode()).hexdigest()

def update_state_with_checksum(checksum: str, artifact_path: str):
    """Update state file with checksum."""
    state_path = 'state/PROJ-485/pipeline_state.yaml'
    state = {}
    
    if os.path.exists(state_path):
        import yaml
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    state['artifacts'] = state.get('artifacts', {})
    state['artifacts'][artifact_path] = {
        'checksum': checksum,
        'updated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    log_info(None, f"Updated state with checksum for {artifact_path}")

def verify_processed_data_integrity(artifact_path: str, expected_checksum: str) -> bool:
    """
    Verify the integrity of processed data by re-computing checksum and comparing.
    This is the final verification step for T061.
    """
    if not os.path.exists(artifact_path):
        log_error(ErrorCode.DATA_INTEGRITY_VIOLATION, f"Processed artifact not found: {artifact_path}")
        raise ValueError(f"DATA_INTEGRITY_VIOLATION: File not found - {artifact_path}")
    
    # Compute current checksum
    current_checksum = compute_file_sha256(artifact_path)
    
    if current_checksum != expected_checksum:
        log_error(ErrorCode.DATA_INTEGRITY_VIOLATION, 
                 f"Checksum mismatch for {artifact_path}. Expected: {expected_checksum}, Got: {current_checksum}")
        raise ValueError(f"DATA_INTEGRITY_VIOLATION: Checksum mismatch - {artifact_path}")
    
    log_info(None, f"Data integrity verified for {artifact_path}: {current_checksum}")
    return True

def load_data() -> pd.DataFrame:
    """Main function to load and process data."""
    config = get_config()
    
    # Check data source availability
    if not check_data_source_availability():
        raise ValueError("DATA_SOURCE_MISSING: No valid data sources configured")
    
    # Try to load from configured sources
    df = None
    
    # Try URL sources first
    nist_url = config.get('nist_janaf_url', '')
    sgte_url = config.get('sgte_url', '')
    
    if nist_url:
        try:
            df = load_data_from_url(nist_url)
        except Exception as e:
            log_warning(None, f"NIST-JANAF load failed: {str(e)}")
    
    if df is None and sgte_url:
        try:
            df = load_data_from_url(sgte_url)
        except Exception as e:
            log_warning(None, f"SGTE load failed: {str(e)}")
    
    # Fallback to local file
    if df is None:
        local_path = config.get('local_fallback_path', '')
        if local_path:
            try:
                df = load_data_from_local_fallback(local_path)
            except Exception as e:
                log_error(ErrorCode.DATA_SOURCE_MISSING, f"Local fallback failed: {str(e)}")
                raise ValueError(f"DATA_SOURCE_MISSING: {str(e)}")
        else:
            raise ValueError("DATA_SOURCE_MISSING: No valid data source found")
    
    # Filter missing temperature data
    df = filter_missing_temperature(df)
    
    # Compute and store checksum
    checksum = compute_dataset_checksum(df)
    log_info(None, f"Dataset checksum computed: {checksum}")
    
    # Update state
    update_state_with_checksum(checksum, 'data/processed/descriptors.csv')
    
    return df

def main():
    """Entry point for data ingestion."""
    try:
        log_info(None, "Starting data ingestion pipeline")
        df = load_data()
        
        # Save processed data
        output_path = 'data/processed/descriptors.csv'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        # Final integrity check (T061)
        config = get_config()
        state_path = 'state/PROJ-485/pipeline_state.yaml'
        
        if os.path.exists(state_path):
            import yaml
            with open(state_path, 'r') as f:
                state = yaml.safe_load(f) or {}
            
            expected_checksum = state.get('artifacts', {}).get('data/processed/descriptors.csv', {}).get('checksum')
            
            if expected_checksum:
                verify_processed_data_integrity(output_path, expected_checksum)
                log_info(None, "Final integrity check passed")
            else:
                log_warning(None, "No expected checksum found in state, skipping integrity verification")
        
        log_info(None, f"Data ingestion complete. Output: {output_path}")
        return df
        
    except Exception as e:
        log_error(None, f"Data ingestion failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
