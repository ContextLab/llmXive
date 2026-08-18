"""
Preprocessing script for GitHub issue resolution times.

Computes resolution_time_hours, applies log-transform, and excludes invalid issues.
Excludes issues with:
  - Missing created_at or closed_at
  - Negative resolution time
  - Zero or negative duration (handled via log-transform safety)

Outputs:
  - data/processed/preprocessed_issues.csv (cleaned dataset)
  - data/logs/preprocessing.log (JSON format log of excluded issues)

Dependencies:
  - T045: Repository Metadata Enrichment (ensures 'language' column exists)
  - T009c: Data Source Orchestrator (ensures raw data is available)
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from utils.config import get_config, set_seed

# Set random seed for reproducibility
config = get_config()
set_seed(config.get('random_seed', 42))

# Constants
RAW_DATA_PATH = Path("data/raw/github_issues_raw_hf.parquet")
API_RAW_PATH = Path("data/raw/github_issues_raw_api.parquet")
OUTPUT_PATH = Path("data/processed/preprocessed_issues.csv")
LOG_PATH = Path("data/logs/preprocessing.log")
METADATA_PATH = Path("data/processed/repo_metadata.json")

def parse_timestamp(ts_value: Any) -> Optional[datetime]:
    """
    Parse a timestamp string to a datetime object.
    
    Handles ISO 8601 format (e.g., "2023-01-01T12:00:00Z").
    Returns None if parsing fails or value is None/empty.
    """
    if pd.isna(ts_value) or ts_value is None or str(ts_value).strip() == "":
        return None
    
    try:
        ts_str = str(ts_value)
        # Handle 'Z' suffix by replacing with '+00:00' for fromisoformat
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None

def compute_resolution_time(created_at: Any, closed_at: Any) -> Optional[float]:
    """
    Compute resolution time in hours between created_at and closed_at.
    
    Returns None if either timestamp is invalid or if the result is negative.
    """
    created = parse_timestamp(created_at)
    closed = parse_timestamp(closed_at)
    
    if created is None or closed is None:
        return None
    
    delta = closed - created
    hours = delta.total_seconds() / 3600.0
    
    if hours < 0:
        return None
    
    return hours

def is_valid_issue(row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Check if an issue is valid for analysis.
    
    Valid issues must have:
      - Valid created_at and closed_at timestamps
      - Non-negative resolution time
      - Non-null language (enriched metadata)
      
    Returns:
      Tuple (is_valid, reason) where reason describes why it was excluded if invalid.
    """
    # Check timestamps
    created = parse_timestamp(row.get('created_at'))
    closed = parse_timestamp(row.get('closed_at'))
    
    if created is None:
        return False, "missing_created_at"
    if closed is None:
        return False, "missing_closed_at"
    
    # Compute resolution time
    hours = compute_resolution_time(row.get('created_at'), row.get('closed_at'))
    
    if hours is None:
        return False, "negative_resolution_time"
    
    # Check language (enriched metadata)
    language = row.get('language')
    if pd.isna(language) or language is None or str(language).strip() == "":
        return False, "missing_language"
    
    return True, None

def preprocess_issues(df: pd.DataFrame, log_path: Path) -> pd.DataFrame:
    """
    Preprocess the issues dataframe:
      1. Filter out invalid issues
      2. Compute resolution_time_hours
      3. Apply log-transform to resolution_time_hours (log1p for zero-safe)
      4. Log excluded issues to JSON file
    
    Args:
      df: Input dataframe with raw issues
      log_path: Path to write the exclusion log
    
    Returns:
      Preprocessed dataframe with new columns:
        - resolution_time_hours
        - log_resolution_time
    """
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logger = logging.getLogger("preprocessing")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create file handler for JSON logging
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Custom JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "message": record.getMessage()
            }
            if hasattr(record, 'extra_data'):
                log_entry.update(record.extra_data)
            return json.dumps(log_entry)
    
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Also log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    logger.info(f"Starting preprocessing of {len(df)} issues")
    
    # Validate and filter issues
    valid_indices = []
    excluded_issues = []
    
    for idx, row in df.iterrows():
        is_valid, reason = is_valid_issue(row.to_dict())
        if is_valid:
            valid_indices.append(idx)
        else:
            excluded_issues.append({
                "index": int(idx),
                "reason": reason,
                "created_at": str(row.get('created_at')),
                "closed_at": str(row.get('closed_at')),
                "repo": str(row.get('repository_name', 'unknown')),
                "issue_number": int(row.get('number', -1)) if not pd.isna(row.get('number')) else -1
            })
            logger.info("Excluded issue", extra={"extra_data": {"index": int(idx), "reason": reason}})
    
    logger.info(f"Excluded {len(excluded_issues)} issues, keeping {len(valid_indices)} issues")
    
    # Filter dataframe
    df_clean = df.loc[valid_indices].copy()
    
    # Compute resolution time
    df_clean['resolution_time_hours'] = df_clean.apply(
        lambda row: compute_resolution_time(row['created_at'], row['closed_at']), 
        axis=1
    )
    
    # Apply log-transform (log1p to handle zero values safely)
    # Note: resolution_time_hours should be >= 0 after filtering
    df_clean['log_resolution_time'] = np.log1p(df_clean['resolution_time_hours'])
    
    # Ensure required columns exist
    required_cols = [
        'created_at', 'closed_at', 'resolution_time_hours', 'log_resolution_time',
        'labels', 'assignee', 'comments_count', 'repository_name', 'number', 'language'
    ]
    
    for col in required_cols:
        if col not in df_clean.columns:
            logger.warning(f"Column {col} not found in dataset")
    
    logger.info(f"Preprocessing complete. Output shape: {df_clean.shape}")
    
    return df_clean

def load_raw_data() -> pd.DataFrame:
    """
    Load raw data from either HF parquet or API parquet file.
    
    Priority:
      1. HF parquet (if exists)
      2. API parquet (if exists)
      3. Raise error if neither exists
    """
    if RAW_DATA_PATH.exists():
        logging.info(f"Loading raw data from {RAW_DATA_PATH}")
        return pd.read_parquet(RAW_DATA_PATH)
    elif API_RAW_PATH.exists():
        logging.info(f"Loading raw data from {API_RAW_PATH}")
        return pd.read_parquet(API_RAW_PATH)
    else:
        raise FileNotFoundError(
            f"No raw data found. Expected {RAW_DATA_PATH} or {API_RAW_PATH}. "
            "Please run T009c (Orchestrator) first."
        )

def main():
    """
    Main entry point for preprocessing.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load raw data
        df_raw = load_raw_data()
        logging.info(f"Loaded {len(df_raw)} raw issues")
        
        # Preprocess
        df_clean = preprocess_issues(df_raw, LOG_PATH)
        
        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save cleaned data
        df_clean.to_csv(OUTPUT_PATH, index=False)
        logging.info(f"Saved preprocessed data to {OUTPUT_PATH}")
        
        # Verify output
        if not OUTPUT_PATH.exists():
            raise RuntimeError(f"Failed to write output file: {OUTPUT_PATH}")
        
        logging.info("Preprocessing completed successfully")
        
    except Exception as e:
        logging.error(f"Preprocessing failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()