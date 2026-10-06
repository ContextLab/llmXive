"""
T012e: MMSE Exclusion and Robustness Prep

Implements logic to:
1. Read `has_mmse` from data/processed/mmse_flag.json.
2. If has_mmse=True: Filter data/processed/cleaned_score_filtered.csv for MMSE >= 24 -> data/processed/cleaned_dataset.csv.
3. If has_mmse=False: Copy data/processed/cleaned_score_filtered.csv -> data/processed/cleaned_dataset.csv.
4. ALWAYS generate data/processed/cleaned_dataset_no_mmse.csv by copying data/processed/cleaned_score_filtered.csv.
5. Update data/processed/exclusion_counts.json with exclusion counts.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_config, get_config_value
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Setup logging
logger = setup_logging("T012e")

def get_config_paths() -> Dict[str, Path]:
    """Get all necessary file paths from config."""
    config = get_config()
    base = Path(config['paths']['root'])
    return {
        'processed_dir': base / config['paths']['processed'],
        'raw_dir': base / config['paths']['raw'],
        'mmse_flag_path': base / config['paths']['processed'] / 'mmse_flag.json',
        'score_filtered_path': base / config['paths']['processed'] / 'cleaned_score_filtered.csv',
        'cleaned_dataset_path': base / config['paths']['processed'] / 'cleaned_dataset.csv',
        'cleaned_no_mmse_path': base / config['paths']['processed'] / 'cleaned_dataset_no_mmse.csv',
        'exclusion_counts_path': base / config['paths']['processed'] / 'exclusion_counts.json',
    }

def load_score_filtered_dataset(path: Path) -> pd.DataFrame:
    """Load the score-filtered dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Score filtered dataset not found at {path}")
    logger.info(f"Loading score filtered dataset from {path}")
    return pd.read_csv(path)

def load_mmse_flag(path: Path) -> bool:
    """Load the MMSE flag from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"MMSE flag not found at {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('has_mmse', False)

def filter_mmse(df: pd.DataFrame, threshold: int = 24) -> pd.DataFrame:
    """Filter dataframe for MMSE >= threshold."""
    if 'MMSE' not in df.columns:
        log_warning("MMSE column not found in dataframe. Returning original dataframe.")
        return df
    
    # Filter out nulls first, then apply threshold
    valid_mmse = df['MMSE'].notna()
    df_valid = df[valid_mmse].copy()
    filtered = df_valid[df_valid['MMSE'] >= threshold].copy()
    
    excluded_count = len(df) - len(filtered)
    log_info(f"Filtered MMSE >= {threshold}: {excluded_count} records excluded.")
    return filtered

def save_cleaned_dataset(df: pd.DataFrame, path: Path) -> None:
    """Save the primary cleaned dataset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log_info(f"Saved cleaned dataset to {path} ({len(df)} records)")

def save_no_mmse_dataset(df: pd.DataFrame, path: Path) -> None:
    """Save the robustness dataset (without MMSE exclusion)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log_info(f"Saved cleaned dataset (no MMSE) to {path} ({len(df)} records)")

def load_exclusion_counts(path: Path) -> Dict[str, Any]:
    """Load existing exclusion counts."""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def update_exclusion_counts(current_counts: Dict[str, Any], mmse_excluded: int) -> Dict[str, Any]:
    """Update exclusion counts with MMSE exclusion data."""
    if 'ERR_MMSE_IMPAIRED' not in current_counts:
        current_counts['ERR_MMSE_IMPAIRED'] = 0
    current_counts['ERR_MMSE_IMPAIRED'] += mmse_excluded
    return current_counts

def save_exclusion_counts(counts: Dict[str, Any], path: Path) -> None:
    """Save updated exclusion counts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(counts, f, indent=2)
    log_info(f"Updated exclusion counts saved to {path}")

def main():
    """Main entry point for T012e."""
    log_info("Starting T012e: MMSE Exclusion and Robustness Prep")
    
    try:
        paths = get_config_paths()
        
        # Load MMSE flag
        has_mmse = load_mmse_flag(paths['mmse_flag_path'])
        log_info(f"MMSE Flag loaded: has_mmse={has_mmse}")
        
        # Load score filtered dataset
        df_score_filtered = load_score_filtered_dataset(paths['score_filtered_path'])
        initial_count = len(df_score_filtered)
        
        # Determine exclusion count
        mmse_excluded = 0
        
        if has_mmse:
            # Apply MMSE filter
            df_cleaned = filter_mmse(df_score_filtered, threshold=24)
            mmse_excluded = initial_count - len(df_cleaned)
            save_cleaned_dataset(df_cleaned, paths['cleaned_dataset_path'])
        else:
            # No MMSE data, copy as primary
            df_cleaned = df_score_filtered.copy()
            save_cleaned_dataset(df_cleaned, paths['cleaned_dataset_path'])
            log_warning("MMSE flag is False. Skipping MMSE exclusion for primary dataset.")
        
        # Always generate robustness dataset (without MMSE exclusion)
        save_no_mmse_dataset(df_score_filtered, paths['cleaned_no_mmse_path'])
        
        # Update exclusion counts
        counts = load_exclusion_counts(paths['exclusion_counts_path'])
        counts = update_exclusion_counts(counts, mmse_excluded)
        save_exclusion_counts(counts, paths['exclusion_counts_path'])
        
        log_info(f"T012e completed successfully. Primary dataset: {len(df_cleaned)} records, Robustness dataset: {len(df_score_filtered)} records")
        
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error in T012e: {e}")
        raise

if __name__ == "__main__":
    main()