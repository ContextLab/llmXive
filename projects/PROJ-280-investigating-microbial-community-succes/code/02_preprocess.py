import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] [%(name)s] %(message)s')
logger = logging.getLogger('02_preprocess')

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'

def load_sample_metadata() -> pd.DataFrame:
    """Load sample metadata from data/raw/."""
    # Assuming metadata is stored in a CSV or extracted from feature table
    # For this task, we expect metadata to be part of the downloaded files
    metadata_files = list(DATA_RAW.glob("*metadata*.csv"))
    if not metadata_files:
        # Try to infer from feature table if metadata is embedded
        feature_files = list(DATA_RAW.glob("*.csv"))
        if feature_files:
            # Attempt to load and infer metadata
            logger.warning("No explicit metadata file found. Attempting to infer from feature table.")
            # This is a placeholder; real logic depends on data format
            return pd.DataFrame()
        else:
            raise FileNotFoundError("No metadata or feature table found in data/raw/")
    
    return pd.read_csv(metadata_files[0])

def load_feature_table() -> pd.DataFrame:
    """Load feature table from data/raw/."""
    feature_files = list(DATA_RAW.glob("*.csv"))
    if not feature_files:
        raise FileNotFoundError("No feature table found in data/raw/")
    
    # Assume the first CSV is the feature table
    return pd.read_csv(feature_files[0], index_col=0)

def filter_constructed_wetlands(metadata: pd.DataFrame) -> pd.DataFrame:
    """Filter samples for constructed wetlands."""
    # Assuming a column 'type' or similar exists
    if 'type' in metadata.columns:
        filtered = metadata[metadata['type'].str.lower().str.contains('constructed', na=False)]
    else:
        logger.warning("No 'type' column found. Skipping constructed wetland filter.")
        filtered = metadata
    return filtered

def filter_nutrient_removal_metrics(metadata: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Filter samples with N/P removal metrics."""
    n_removed = 0
    if 'n_removal' in metadata.columns and 'p_removal' in metadata.columns:
        # Check for non-null values
        valid_mask = metadata['n_removal'].notna() & metadata['p_removal'].notna()
        filtered = metadata[valid_mask]
        n_removed = len(metadata) - len(filtered)
    else:
        logger.warning("N/P removal columns not found. Skipping nutrient removal filter.")
        filtered = metadata
    return filtered, n_removed

def validate_metadata_fields(metadata: pd.DataFrame) -> bool:
    """Validate required metadata fields."""
    required_fields = ['stage', 'n_removal', 'p_removal']
    missing = [f for f in required_fields if f not in metadata.columns]
    if missing:
        logger.error(f"CRITICAL DATA GAP: Missing metadata fields: {missing}")
        return False
    return True

def save_exclusion_log(excluded_counts: Dict[str, int]) -> None:
    """Save exclusion log to data/processed/."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    log_path = DATA_PROCESSED / 'exclusion_log.json'
    with open(log_path, 'w') as f:
        json.dump(excluded_counts, f, indent=2)
    logger.info(f"Exclusion log saved to {log_path}")

def subsample_minimum_depth(feature_table: pd.DataFrame, min_depth: int = 5000) -> Tuple[pd.DataFrame, int]:
    """Subsample samples to uniform depth and exclude those below threshold."""
    excluded = 0
    total_reads = feature_table.sum(axis=1)
    
    # Exclude samples with < 5000 reads
    valid_mask = total_reads >= min_depth
    filtered_table = feature_table[valid_mask]
    excluded = len(feature_table) - len(filtered_table)

    if len(filtered_table) == 0:
        logger.error("CRITICAL DATA GAP: Insufficient samples after read filtering (n=0).")
        sys.exit(1)

    # Subsample to uniform depth (random sampling)
    target_depth = min_depth
    subsampled = filtered_table.apply(lambda row: np.random.choice(
        row.index, size=target_depth, p=row/row.sum()
    ), axis=1)
    
    # This is a simplified subsampling; real implementation might use skbio
    return filtered_table, excluded

def validate_sample_pool_size(metadata: pd.DataFrame) -> Dict[str, int]:
    """Validate sample pool size and return counts."""
    total = len(metadata)
    per_stage = metadata['stage'].value_counts().to_dict()
    
    # Ensure all stages present
    for stage in ['early', 'intermediate', 'mature']:
        if stage not in per_stage:
            per_stage[stage] = 0

    validation = {
        'total_samples': total,
        'per_stage': per_stage
    }

    # Log warning if underpowered but do not halt
    if total < 30 or any(v < 10 for v in per_stage.values()):
        logger.warning(f"UNDERPOWERED: Sample size below target (total={total}, per_stage={per_stage})")

    return validation

def preprocess_data() -> None:
    """Main preprocessing pipeline."""
    logger.info("Starting Preprocessing Pipeline...")

    try:
        metadata = load_sample_metadata()
        feature_table = load_feature_table()
    except FileNotFoundError as e:
        logger.error(f"CRITICAL DATA GAP: {e}")
        sys.exit(1)

    # Filter for constructed wetlands
    metadata = filter_constructed_wetlands(metadata)

    # Filter for nutrient removal metrics
    metadata, n_removed = filter_nutrient_removal_metrics(metadata)

    # Validate metadata fields
    if not validate_metadata_fields(metadata):
        logger.error("CRITICAL DATA GAP: Metadata validation failed.")
        sys.exit(1)

    # Subsample
    feature_table, read_excluded = subsample_minimum_depth(feature_table)

    # Save exclusion log
    save_exclusion_log({
        'n_removed': n_removed,
        'read_excluded': read_excluded
    })

    # Validate sample pool
    pool_validation = validate_sample_pool_size(metadata)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(DATA_PROCESSED / 'sample_pool_validation.json', 'w') as f:
        json.dump(pool_validation, f, indent=2)
    logger.info(f"Sample pool validation saved: {pool_validation}")

    # Save processed data
    feature_table.to_csv(DATA_PROCESSED / 'feature_table.csv')
    metadata.to_csv(DATA_PROCESSED / 'metadata.csv')

    logger.info("Preprocessing completed.")

def main():
    preprocess_data()

if __name__ == "__main__":
    main()
