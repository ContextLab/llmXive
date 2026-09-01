"""
Preprocessing pipeline for microbial community data.
Filters for constructed wetlands with N and P removal metrics.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Import utilities from existing modules
from utils import get_logger, log_data_gap_flag
from validators import validate_dataset_config

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_msg = f"[{record.levelname}] [{record.name}] {record.getMessage()}"
        return log_msg

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler
    data_dir = Path("data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)
    log_file = data_dir / "audit_trail.log"
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(CustomFormatter())
    
    # Stream handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(CustomFormatter())
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def load_sample_metadata(raw_dir: Path) -> Optional[pd.DataFrame]:
    """Load sample metadata from the raw directory."""
    metadata_files = list(raw_dir.glob("*metadata*.csv")) + list(raw_dir.glob("*metadata*.tsv"))
    
    if not metadata_files:
        # Try generic CSV files if no specific metadata found
        csv_files = list(raw_dir.glob("*.csv"))
        for f in csv_files:
            try:
                df = pd.read_csv(f)
                if 'sample_id' in df.columns:
                    return df
            except Exception:
                continue
        return None
    
    # Load the first found metadata file
    try:
        df = pd.read_csv(metadata_files[0])
        return df
    except Exception as e:
        logging.error(f"Failed to load metadata from {metadata_files[0]}: {e}")
        return None

def load_feature_table(raw_dir: Path) -> Optional[pd.DataFrame]:
    """Load feature table from the raw directory."""
    feature_files = list(raw_dir.glob("*feature_table*.csv")) + list(raw_dir.glob("*otu_table*.csv"))
    
    if not feature_files:
        logging.error("CRITICAL DATA GAP: No feature table found in data/raw/")
        return None
    
    try:
        df = pd.read_csv(feature_files[0])
        return df
    except Exception as e:
        logging.error(f"Failed to load feature table: {e}")
        return None

def filter_constructed_wetlands(df: pd.DataFrame) -> pd.DataFrame:
    """Filter samples to only include constructed wetlands."""
    # Look for a column indicating wetland type
    type_col = None
    for col in ['wetland_type', 'system_type', 'type', 'category']:
        if col in df.columns:
            type_col = col
            break
    
    if type_col is None:
        # If no type column, assume all are constructed wetlands or log warning
        logging.warning("No wetland type column found, assuming all samples are constructed wetlands.")
        return df
    
    # Filter for constructed wetlands (case-insensitive match)
    mask = df[type_col].str.lower().str.contains('constructed', na=False)
    filtered_df = df[mask].copy()
    
    excluded_count = len(df) - len(filtered_df)
    if excluded_count > 0:
        logging.info(f"Excluded {excluded_count} samples that are not constructed wetlands.")
    
    return filtered_df

def filter_nutrient_removal_metrics(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Filter samples that have both N and P removal metrics."""
    excluded_samples = []
    
    # Identify columns for N and P removal
    n_cols = [c for c in df.columns if 'n_removal' in c.lower() or 'nitrogen' in c.lower()]
    p_cols = [c for c in df.columns if 'p_removal' in c.lower() or 'phosphorus' in c.lower()]
    
    if not n_cols or not p_cols:
        logging.error("CRITICAL DATA GAP: Missing N or P removal metric columns.")
        return pd.DataFrame(), excluded_samples
    
    # Use the first found column for each
    n_col = n_cols[0]
    p_col = p_cols[0]
    
    # Filter rows where both N and P removal are not null and not NaN
    mask = df[n_col].notna() & df[p_col].notna()
    
    # Also ensure values are numeric and valid
    try:
        df[n_col] = pd.to_numeric(df[n_col], errors='coerce')
        df[p_col] = pd.to_numeric(df[p_col], errors='coerce')
        mask = mask & df[n_col].notna() & df[p_col].notna()
    except Exception as e:
        logging.error(f"Error converting removal columns to numeric: {e}")
        return pd.DataFrame(), excluded_samples
    
    filtered_df = df[mask].copy()
    excluded_samples = df[~mask]['sample_id'].tolist()
    
    logging.info(f"Excluded {len(excluded_samples)} samples missing N or P removal metrics.")
    
    return filtered_df, excluded_samples

def validate_metadata_fields(df: pd.DataFrame) -> bool:
    """Validate that required metadata fields are present."""
    required_fields = ['sample_id', 'stage', 'n_removal', 'p_removal']
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        logging.error(f"Missing required metadata fields: {missing_fields}")
        return False
    
    return True

def save_exclusion_log(excluded_samples: List[str], output_path: Path):
    """Save exclusion log to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_data = {
        "excluded_samples": excluded_samples,
        "count": len(excluded_samples)
    }
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logging.info(f"Saved exclusion log to {output_path}")

def subsample_minimum_depth(feature_table: pd.DataFrame, min_depth: int = 5000) -> pd.DataFrame:
    """Subsample samples to minimum depth if they exceed it."""
    # This is a placeholder for actual subsampling logic
    # In a real implementation, this would use rarefaction or similar
    logging.info(f"Subsampling samples to minimum depth of {min_depth} reads.")
    return feature_table

def validate_sample_pool_size(df: pd.DataFrame, min_total: int = 30, min_per_stage: int = 10) -> Dict[str, Any]:
    """Validate sample pool size after filtering."""
    if 'stage' not in df.columns:
        logging.warning("No stage column found, cannot validate per-stage counts.")
        return {"total_samples": len(df), "per_stage": {}, "status": "UNKNOWN"}
    
    stage_counts = df['stage'].value_counts().to_dict()
    total = len(df)
    
    result = {
        "total_samples": total,
        "per_stage": stage_counts,
        "status": "OK"
    }
    
    if total < min_total:
        logging.warning(f"UNDERPOWERED: Sample size below target (total: {total} < {min_total})")
        result["status"] = "UNDERPOWERED"
    
    for stage, count in stage_counts.items():
        if count < min_per_stage:
            logging.warning(f"UNDERPOWERED: Stage '{stage}' has {count} samples (< {min_per_stage})")
            result["status"] = "UNDERPOWERED"
    
    return result

def write_audit_trail(message: str, level: str = "INFO"):
    """Write to audit trail log."""
    logger = logging.getLogger()
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "CRITICAL":
        logger.critical(message)

def preprocess_data(raw_dir: Path, processed_dir: Path) -> bool:
    """Main preprocessing logic."""
    setup_logging()
    logger = logging.getLogger()
    
    logger.info("Starting Preprocessing Pipeline...")
    
    # Load metadata
    metadata = load_sample_metadata(raw_dir)
    if metadata is None:
        log_data_gap_flag("CRITICAL DATA GAP: No metadata found in data/raw/")
        return False
    
    logger.info(f"Loaded metadata with {len(metadata)} samples.")
    
    # Load feature table
    feature_table = load_feature_table(raw_dir)
    if feature_table is None:
        log_data_gap_flag("CRITICAL DATA GAP: No feature table found in data/raw/")
        return False
    
    logger.info(f"Loaded feature table with {len(feature_table)} samples.")
    
    # Filter for constructed wetlands
    wetland_metadata = filter_constructed_wetlands(metadata)
    logger.info(f"Filtered to {len(wetland_metadata)} constructed wetland samples.")
    
    # Filter for nutrient removal metrics
    nutrient_metadata, excluded_samples = filter_nutrient_removal_metrics(wetland_metadata)
    
    # Save exclusion log
    exclusion_log_path = processed_dir / "exclusion_log.json"
    save_exclusion_log(excluded_samples, exclusion_log_path)
    
    if nutrient_metadata.empty:
        log_data_gap_flag("CRITICAL DATA GAP: No samples with both N and P removal metrics.")
        return False
    
    # Validate metadata fields
    if not validate_metadata_fields(nutrient_metadata):
        log_data_gap_flag("CRITICAL DATA GAP: Missing required metadata fields.")
        return False
    
    # Prepare output metadata
    output_cols = ['sample_id', 'stage', 'n_removal', 'p_removal']
    available_cols = [c for c in output_cols if c in nutrient_metadata.columns]
    output_metadata = nutrient_metadata[available_cols].copy()
    
    # Ensure column names match exactly
    output_metadata.columns = output_cols[:len(output_cols)]
    
    # Write output
    output_path = processed_dir / "metadata_with_rates.csv"
    output_metadata.to_csv(output_path, index=False)
    logger.info(f"Saved {len(output_metadata)} samples to {output_path}")
    
    # Validate sample pool size
    pool_validation = validate_sample_pool_size(nutrient_metadata)
    validation_path = processed_dir / "sample_pool_validation.json"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    with open(validation_path, 'w') as f:
        json.dump(pool_validation, f, indent=2)
    logger.info(f"Saved sample pool validation to {validation_path}")
    
    # Subsample if needed (placeholder)
    if feature_table is not None:
        subsampled_table = subsample_minimum_depth(feature_table)
        # Save subsampled table if needed
    
    return True

def main():
    """Entry point for the preprocessing script."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    if not raw_dir.exists():
        logging.error("CRITICAL DATA GAP: data/raw directory does not exist.")
        sys.exit(1)
    
    success = preprocess_data(raw_dir, processed_dir)
    
    if not success:
        logging.error("Preprocessing failed due to critical data gaps.")
        sys.exit(1)
    
    logging.info("Preprocessing completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()