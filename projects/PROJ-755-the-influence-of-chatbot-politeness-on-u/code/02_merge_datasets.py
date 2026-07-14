"""
Merge Persona-Chat, EmpatheticDialogues, and HCI_P2 datasets into a unified DataFrame.

This script implements the merging logic for User Story 1 (T016).
It combines raw data from multiple sources, preserves required fields,
and outputs a unified DataFrame for downstream processing.

Dependencies:
- T015: Must have completed downloading and storing raw datasets in data/raw/
- T012: Demographic verification must have been performed
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/merge_datasets.log')
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Required fields for merging
REQUIRED_FIELDS = ['user_id', 'dialogue_id', 'quality_rating']
DEMOGRAPHIC_FIELDS = ['age', 'gender']
ALL_REQUIRED_FIELDS = REQUIRED_FIELDS + DEMOGRAPHIC_FIELDS

# Dataset file mappings (updated to match T015 output)
DATASET_FILES = {
    'personachat': 'personachat_raw.parquet',
    'empatheticdialogues': 'empatheticdialogues_raw.parquet',
    'hci_p2': 'hci_p2_raw.parquet'  # Fallback dataset
}

def ensure_directories():
    """Ensure output directories exist."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)

def load_dataset(filepath: Path) -> Optional[pd.DataFrame]:
    """
    Load a dataset from parquet file.
    
    Args:
        filepath: Path to the parquet file
        
    Returns:
        DataFrame if successful, None if file doesn't exist or loading fails
    """
    if not filepath.exists():
        logger.warning(f"Dataset file not found: {filepath}")
        return None
    
    try:
        df = pd.read_parquet(filepath)
        logger.info(f"Loaded {filepath.name}: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {str(e)}")
        return None

def validate_and_prepare_dataset(df: pd.DataFrame, source_name: str) -> Optional[pd.DataFrame]:
    """
    Validate dataset has required fields and prepare for merging.
    
    Args:
        df: Input DataFrame
        source_name: Name of the source dataset
        
    Returns:
        Prepared DataFrame or None if validation fails
    """
    if df is None or df.empty:
        logger.warning(f"Empty or None DataFrame for {source_name}")
        return None
    
    # Check for required fields
    missing_required = [field for field in REQUIRED_FIELDS if field not in df.columns]
    if missing_required:
        logger.error(f"Missing required fields in {source_name}: {missing_required}")
        return None
    
    # Normalize column names to lowercase
    df = df.rename(columns=lambda x: x.lower().strip() if isinstance(x, str) else x)
    
    # Ensure required fields exist with proper types
    for field in REQUIRED_FIELDS:
        if field in df.columns:
            df[field] = df[field].astype(str)
            # Handle NaN values
            df[field] = df[field].replace(['nan', 'None', ''], np.nan)
    
    # Add source identifier
    df['source_dataset'] = source_name
    
    logger.info(f"Prepared {source_name}: {len(df)} rows")
    return df

def merge_datasets(dfs: List[Tuple[pd.DataFrame, str]]) -> pd.DataFrame:
    """
    Merge multiple datasets into a unified DataFrame.
    
    Args:
        dfs: List of tuples containing (DataFrame, source_name)
        
    Returns:
        Merged DataFrame
    """
    if not dfs:
        raise ValueError("No datasets to merge")
    
    valid_dfs = [(df, name) for df, name in dfs if df is not None and not df.empty]
    
    if not valid_dfs:
        raise ValueError("No valid datasets to merge")
    
    logger.info(f"Merging {len(valid_dfs)} datasets...")
    
    # Concatenate all DataFrames
    merged_df = pd.concat(
        [df for df, _ in valid_dfs],
        ignore_index=True,
        sort=False
    )
    
    logger.info(f"Merged DataFrame: {len(merged_df)} rows, {len(merged_df.columns)} columns")
    logger.info(f"Unique sources: {merged_df['source_dataset'].unique()}")
    
    return merged_df

def handle_missing_demographics(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing demographic fields (age, gender) according to T012 logic.
    
    Args:
        df: Merged DataFrame
        
    Returns:
        Tuple of (processed DataFrame, validation report)
    """
    validation_report = {
        'status': 'full',
        'missing_fields': [],
        'demographic_coverage': {},
        'notes': []
    }
    
    # Check for demographic fields
    missing_demographics = [field for field in DEMOGRAPHIC_FIELDS if field not in df.columns]
    
    if missing_demographics:
        validation_report['status'] = 'partial'
        validation_report['missing_fields'] = missing_demographics
        validation_report['notes'].append(
            f"Demographic fields missing: {missing_demographics}. "
            "US3 (subgroup analysis) will be skipped per FR-006."
        )
        logger.warning(f"Missing demographic fields: {missing_demographics}")
    else:
        # Calculate coverage statistics
        for field in DEMOGRAPHIC_FIELDS:
            non_null_count = df[field].notna().sum()
            coverage = (non_null_count / len(df)) * 100
            validation_report['demographic_coverage'][field] = {
                'non_null_count': int(non_null_count),
                'total_count': int(len(df)),
                'coverage_percentage': round(coverage, 2)
            }
        
        logger.info(f"Demographic coverage: {validation_report['demographic_coverage']}")
    
    # Ensure demographic fields exist (with NaN if missing)
    for field in DEMOGRAPHIC_FIELDS:
        if field not in df.columns:
            df[field] = np.nan
        else:
            # Convert to appropriate types
            if field == 'age':
                df[field] = pd.to_numeric(df[field], errors='coerce')
            else:
                df[field] = df[field].astype(str)
                df[field] = df[field].replace(['nan', 'None', ''], np.nan)
    
    return df, validation_report

def save_merged_data(df: pd.DataFrame, validation_report: Dict[str, Any]):
    """
    Save merged data and validation report to disk.
    
    Args:
        df: Merged DataFrame
        validation_report: Validation report dictionary
    """
    # Save merged DataFrame
    output_path = PROCESSED_DATA_DIR / "merged_dialogues.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved merged data to {output_path}")
    
    # Save validation report
    report_path = RAW_DATA_DIR / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    logger.info(f"Saved validation report to {report_path}")

def main():
    """Main function to execute the merge process."""
    logger.info("Starting dataset merge process...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load all datasets
    datasets = []
    for source_name, filename in DATASET_FILES.items():
        filepath = RAW_DATA_DIR / filename
        df = load_dataset(filepath)
        if df is not None:
            prepared_df = validate_and_prepare_dataset(df, source_name)
            if prepared_df is not None:
                datasets.append((prepared_df, source_name))
    
    if not datasets:
        logger.error("No datasets were successfully loaded. Aborting merge.")
        sys.exit(1)
    
    # Merge datasets
    try:
        merged_df = merge_datasets(datasets)
    except Exception as e:
        logger.error(f"Failed to merge datasets: {str(e)}")
        sys.exit(1)
    
    # Handle missing demographics
    processed_df, validation_report = handle_missing_demographics(merged_df)
    
    # Save results
    save_merged_data(processed_df, validation_report)
    
    # Log summary
    logger.info("Merge process completed successfully!")
    logger.info(f"Final dataset: {len(processed_df)} dialogues")
    logger.info(f"Validation status: {validation_report['status']}")
    
    if validation_report['missing_fields']:
        logger.warning(f"Missing fields: {validation_report['missing_fields']}")
    
    return processed_df

if __name__ == "__main__":
    main()