"""
Multi-Cohort Data Harmonization Module.

This module implements the logic to ingest separate public datasets (microbiome and sleep),
normalize their metadata, and merge them based on available keys (ID, Age, Sex, BMI)
or a synthetic linkage strategy if no direct patient ID exists.

Outputs:
  - data/processed/harmonized_data.parquet
  - data/metadata/harmonization_metadata.json
"""
import os
import sys
import json
import hashlib
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

# Ensure project root is in path for imports if run directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config, load_config
from ingest import load_schema, calculate_checksum, MissingDataError

# --- Custom Exceptions ---

class HarmonizationError(Exception):
    """Raised when harmonization logic fails."""
    pass

# --- Helper Functions ---

def calculate_checksum(df: pd.DataFrame) -> str:
    """Calculate a deterministic checksum of the dataframe content."""
    # Sort columns to ensure consistency
    sorted_df = df.sort_index(axis=1)
    # Convert to string representation for hashing
    content = sorted_df.to_csv(index=False).encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def load_microbiome_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load microbiome data from the configured source.
    Supports:
      1. A single CSV/Parquet file path.
      2. A directory containing multiple files to be merged.
    """
    source = config.get('microbiome_source')
    if not source:
        raise HarmonizationError("Microbiome source not specified in config.")

    source_path = Path(source)
    if not source_path.exists():
        raise HarmonizationError(f"Microbiome source path does not exist: {source_path}")

    df = None

    if source_path.is_file():
        if source_path.suffix == '.csv':
            df = pd.read_csv(source_path)
        elif source_path.suffix == '.parquet':
            df = pd.read_parquet(source_path)
        else:
            raise HarmonizationError(f"Unsupported file format: {source_path.suffix}")
    elif source_path.is_dir():
        # Merge all CSV/Parquet files in directory
        files = list(source_path.glob('*.csv')) + list(source_path.glob('*.parquet'))
        if not files:
            raise HarmonizationError(f"No CSV or Parquet files found in {source_path}")
        
        dfs = []
        for f in files:
            if f.suffix == '.csv':
                dfs.append(pd.read_csv(f))
            else:
                dfs.append(pd.read_parquet(f))
        df = pd.concat(dfs, ignore_index=True)
    
    # Standardize column names if needed (simple lowercasing for now)
    df.columns = [c.lower() for c in df.columns]
    return df

def load_sleep_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load sleep data from the configured source.
    Supports:
      1. A single CSV/Parquet file path.
      2. A directory containing multiple files to be merged.
    """
    source = config.get('sleep_source')
    if not source:
        raise HarmonizationError("Sleep source not specified in config.")

    source_path = Path(source)
    if not source_path.exists():
        raise HarmonizationError(f"Sleep source path does not exist: {source_path}")

    df = None

    if source_path.is_file():
        if source_path.suffix == '.csv':
            df = pd.read_csv(source_path)
        elif source_path.suffix == '.parquet':
            df = pd.read_parquet(source_path)
        else:
            raise HarmonizationError(f"Unsupported file format: {source_path.suffix}")
    elif source_path.is_dir():
        files = list(source_path.glob('*.csv')) + list(source_path.glob('*.parquet'))
        if not files:
            raise HarmonizationError(f"No CSV or Parquet files found in {source_path}")
        
        dfs = []
        for f in files:
            if f.suffix == '.csv':
                dfs.append(pd.read_csv(f))
            else:
                dfs.append(pd.read_parquet(f))
        df = pd.concat(dfs, ignore_index=True)

    # Standardize column names
    df.columns = [c.lower() for c in df.columns]
    return df

def normalize_metadata(microbiome_df: pd.DataFrame, sleep_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normalize column names to a common schema for matching.
    Maps common variations to standard keys: 'subject_id', 'age', 'sex', 'bmi'.
    """
    # Microbiome normalization
    mb_map = {}
    for col in microbiome_df.columns:
        if col in ['subject_id', 'subjectid', 'id', 'sample_id', 'pid']:
            mb_map[col] = 'subject_id'
        elif col in ['age']:
            mb_map[col] = 'age'
        elif col in ['sex', 'gender']:
            mb_map[col] = 'sex'
        elif col in ['bmi', 'body_mass_index']:
            mb_map[col] = 'bmi'
    
    if mb_map:
        microbiome_df = microbiome_df.rename(columns=mb_map)

    # Sleep normalization
    sl_map = {}
    for col in sleep_df.columns:
        if col in ['subject_id', 'subjectid', 'id', 'patient_id', 'pid']:
            sl_map[col] = 'subject_id'
        elif col in ['age']:
            sl_map[col] = 'age'
        elif col in ['sex', 'gender']:
            sl_map[col] = 'sex'
        elif col in ['bmi', 'body_mass_index']:
            sl_map[col] = 'bmi'

    if sl_map:
        sleep_df = sleep_df.rename(columns=sl_map)

    return microbiome_df, sleep_df

def match_by_id(microbiome_df: pd.DataFrame, sleep_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Attempt to merge datasets using a direct 'subject_id' match.
    Returns None if no 'subject_id' column exists in both or no matches found.
    """
    if 'subject_id' not in microbiome_df.columns or 'subject_id' not in sleep_df.columns:
        return None

    # Ensure subject_id is string for robust matching
    mb = microbiome_df.copy()
    sl = sleep_df.copy()
    mb['subject_id'] = mb['subject_id'].astype(str)
    sl['subject_id'] = sl['subject_id'].astype(str)

    merged = pd.merge(mb, sl, on='subject_id', how='inner', suffixes=('_mb', '_sl'))
    
    if merged.empty:
        return None
    
    return merged

def match_by_metadata(microbiome_df: pd.DataFrame, sleep_df: pd.DataFrame, 
                      age_tol: int = 5, bmi_tol: float = 2.0) -> Optional[pd.DataFrame]:
    """
    Attempt to merge datasets using fuzzy matching on Age and BMI.
    This is a synthetic linkage strategy used when no direct ID exists.
    Returns the best match for each subject in the microbiome dataset.
    """
    required_cols = ['age', 'bmi', 'sex']
    missing_mb = [c for c in required_cols if c not in microbiome_df.columns]
    missing_sl = [c for c in required_cols if c not in sleep_df.columns]
    
    if missing_mb or missing_sl:
        # Fallback: try only age if available
        if 'age' in microbiome_df.columns and 'age' in sleep_df.columns:
            warnings.warn(f"Missing metadata columns for full fuzzy match. Using Age only. Missing MB: {missing_mb}, Missing SL: {missing_sl}")
            return match_by_age_only(microbiome_df, sleep_df, age_tol)
        else:
            warnings.warn("Insufficient metadata columns (Age, Sex, BMI) for fuzzy matching.")
            return None

    mb = microbiome_df.copy()
    sl = sleep_df.copy()

    # Normalize Sex
    if 'sex' in mb.columns and 'sex' in sl.columns:
        # Simple normalization: M/F -> 1/0 or just string match
        mb['sex'] = mb['sex'].astype(str).str.upper().str.strip()
        sl['sex'] = sl['sex'].astype(str).str.upper().str.strip()

    # Create a list of matches
    matches = []
    
    # Iterate over microbiome subjects (assuming microbiome is the smaller dataset usually)
    for idx_mb, row_mb in mb.iterrows():
        best_match = None
        min_dist = float('inf')
        
        # Filter sleep data by Sex first (exact match)
        if 'sex' in row_mb.index:
            sl_filtered = sl[sl['sex'] == row_mb['sex']]
        else:
            sl_filtered = sl

        if sl_filtered.empty:
            continue

        # Calculate distance based on Age and BMI
        # Normalized distance: d = sqrt((da/age_tol)^2 + (db/bmi_tol)^2)
        for idx_sl, row_sl in sl_filtered.iterrows():
            da = abs(row_mb['age'] - row_sl['age'])
            db = abs(row_mb['bmi'] - row_sl['bmi'])
            
            dist = np.sqrt((da/age_tol)**2 + (db/bmi_tol)**2)
            
            if dist < min_dist:
                min_dist = dist
                best_match = row_sl
                best_idx_sl = idx_sl

        if min_dist < 2.0: # Threshold for "good enough" match
            matches.append({
                'microbiome_idx': idx_mb,
                'sleep_idx': best_idx_sl,
                'match_score': 1.0 - (min_dist / 2.0) # Higher is better
            })

    if not matches:
        return None

    # Construct merged dataframe
    merged_rows = []
    matched_sleep_indices = set()
    
    for m in matches:
        mb_row = mb.iloc[m['microbiome_idx']]
        sl_row = sl.iloc[m['sleep_idx']]
        
        # Combine columns, handling suffixes manually
        combined = {}
        for col in mb_row.index:
            combined[f'{col}_mb'] = mb_row[col]
        for col in sl_row.index:
            if col not in ['age', 'bmi', 'sex', 'subject_id']: # Avoid duplicates of keys
                combined[f'{col}_sl'] = sl_row[col]
        
        combined['match_score'] = m['match_score']
        merged_rows.append(combined)
        matched_sleep_indices.add(m['sleep_idx'])

    if not merged_rows:
        return None

    result = pd.DataFrame(merged_rows)
    return result

def match_by_age_only(microbiome_df: pd.DataFrame, sleep_df: pd.DataFrame, age_tol: int = 5) -> Optional[pd.DataFrame]:
    """Fallback matching using only Age."""
    if 'age' not in microbiome_df.columns or 'age' not in sleep_df.columns:
        return None

    mb = microbiome_df.copy()
    sl = sleep_df.copy()
    matches = []

    for idx_mb, row_mb in mb.iterrows():
        best_match = None
        min_diff = age_tol + 1
        
        for idx_sl, row_sl in sl.iterrows():
            diff = abs(row_mb['age'] - row_sl['age'])
            if diff < min_diff:
                min_diff = diff
                best_match = row_sl
                best_idx_sl = idx_sl
        
        if min_diff <= age_tol:
            matches.append({
                'microbiome_idx': idx_mb,
                'sleep_idx': best_idx_sl,
                'age_diff': min_diff
            })

    if not matches:
        return None

    merged_rows = []
    for m in matches:
        mb_row = mb.iloc[m['microbiome_idx']]
        sl_row = sl.iloc[m['sleep_idx']]
        combined = {}
        for col in mb_row.index:
            combined[f'{col}_mb'] = mb_row[col]
        for col in sl_row.index:
            if col != 'age':
                combined[f'{col}_sl'] = sl_row[col]
        combined['age_diff'] = m['age_diff']
        merged_rows.append(combined)

    return pd.DataFrame(merged_rows)

def run_harmonization(microbiome_df: pd.DataFrame, sleep_df: pd.DataFrame, 
                      strategy: str = 'auto') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main orchestration function for harmonization.
    
    Args:
        microbiome_df: Loaded microbiome dataframe.
        sleep_df: Loaded sleep dataframe.
        strategy: 'auto', 'id', 'metadata', 'age_only'.
    
    Returns:
        Tuple of (merged_df, metadata_dict)
    """
    metadata = {
        'strategy_used': None,
        'source_microbiome': None,
        'source_sleep': None,
        'sample_size_mb': len(microbiome_df),
        'sample_size_sl': len(sleep_df),
        'matched_sample_size': 0,
        'matching_details': {}
    }

    # Normalize first
    mb_norm, sl_norm = normalize_metadata(microbiome_df, sleep_df)

    merged = None
    strategy_order = []

    if strategy == 'auto':
        strategy_order = ['id', 'metadata', 'age_only']
    elif strategy == 'id':
        strategy_order = ['id']
    elif strategy == 'metadata':
        strategy_order = ['metadata']
    elif strategy == 'age_only':
        strategy_order = ['age_only']
    else:
        raise HarmonizationError(f"Unknown strategy: {strategy}")

    for s in strategy_order:
        if s == 'id':
            merged = match_by_id(mb_norm, sl_norm)
            if merged is not None:
                metadata['strategy_used'] = 'id_match'
                break
        elif s == 'metadata':
            merged = match_by_metadata(mb_norm, sl_norm)
            if merged is not None:
                metadata['strategy_used'] = 'fuzzy_metadata_match'
                break
        elif s == 'age_only':
            merged = match_by_age_only(mb_norm, sl_norm)
            if merged is not None:
                metadata['strategy_used'] = 'age_only_match'
                break

    if merged is None:
        raise HarmonizationError("Failed to match datasets using any available strategy.")

    metadata['matched_sample_size'] = len(merged)
    metadata['matching_details'] = {
        'matched_count': len(merged),
        'unmatched_mb_count': len(mb_norm) - len(merged),
        'unmatched_sl_count': len(sl_norm) - len(merged)
    }

    return merged, metadata

def main():
    """
    Entry point for the harmonization script.
    Expects configuration in data/config/harmonization_config.json
    """
    parser = argparse.ArgumentParser(description="Harmonize Multi-Cohort Data")
    parser.add_argument('--config', type=str, default='data/config/harmonization_config.json',
                        help='Path to harmonization configuration JSON')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                        help='Output directory for harmonized data')
    parser.add_argument('--metadata-dir', type=str, default='data/metadata',
                        help='Output directory for metadata')
    parser.add_argument('--strategy', type=str, default='auto',
                        choices=['auto', 'id', 'metadata', 'age_only'],
                        help='Matching strategy')
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        # Fallback to project root config if not in current dir
        config_path = Path('data/config/harmonization_config.json')
        if not config_path.exists():
            print("Error: Configuration file not found. Please create data/config/harmonization_config.json")
            sys.exit(1)

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Ensure output directories exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path(args.metadata_dir).mkdir(parents=True, exist_ok=True)

    print(f"Loading Microbiome data from: {config.get('microbiome_source')}")
    print(f"Loading Sleep data from: {config.get('sleep_source')}")

    try:
        mb_df = load_microbiome_data(config)
        sl_df = load_sleep_data(config)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    print(f"Loaded {len(mb_df)} microbiome samples, {len(sl_df)} sleep samples.")

    try:
        merged_df, metadata = run_harmonization(mb_df, sl_df, strategy=args.strategy)
    except HarmonizationError as e:
        print(f"Harmonization failed: {e}")
        sys.exit(1)

    # Save outputs
    output_file = Path(args.output_dir) / 'harmonized_data.parquet'
    metadata_file = Path(args.metadata_dir) / 'harmonization_metadata.json'

    merged_df.to_parquet(output_file, index=False)
    metadata['output_file_path'] = str(output_file)
    metadata['checksum'] = calculate_checksum(merged_df)
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Successfully saved harmonized data to {output_file}")
    print(f"Matched {metadata['matched_sample_size']} subjects.")
    print(f"Metadata saved to {metadata_file}")

if __name__ == '__main__':
    main()
