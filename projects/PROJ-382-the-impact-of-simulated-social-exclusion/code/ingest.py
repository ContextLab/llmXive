"""
Data ingestion module for social exclusion prosociality study.

Handles OSF data download, schema validation, and condition mapping.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import requests

from logging_config import get_project_logger, log_mapping

# Configure logger
logger = get_project_logger()

# Standard column mappings
CONDITION_VARIANTS = {
    'ignored': 1, 'excluded': 1, 'ostracized': 1, 'exclusion': 1,
    'control': 0, 'included': 0, 'inclusion': 0, 'baseline': 0
}

AMOUNT_VARIANTS = ['donation', 'allocation', 'transfer', 'prosocial_amount', 'money_given']

def validate_schema(df: pd.DataFrame, dataset_id: str) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame has required columns.
    
    Args:
        df: DataFrame to validate
        dataset_id: Identifier for logging
        
    Returns:
        Tuple of (is_valid, list of missing columns)
    """
    required_cols = ['condition', 'prosocial_amount', 'randomized']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        logger.warning(f"Dataset {dataset_id} missing columns: {missing}")
        return False, missing
    
    logger.info(f"Dataset {dataset_id} passed schema validation")
    return True, []

def normalize_columns(df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    """
    Normalize column names and condition values.
    
    Args:
        df: DataFrame to normalize
        dataset_id: Identifier for logging
        
    Returns:
        Normalized DataFrame
    """
    df = df.copy()
    
    # Normalize amount column
    for variant in AMOUNT_VARIANTS:
        if variant in df.columns and variant != 'prosocial_amount':
            df.rename(columns={variant: 'prosocial_amount'}, inplace=True)
            logger.info(f"Renamed column '{variant}' to 'prosocial_amount' for {dataset_id}")
            break
    
    # Normalize condition column
    if 'condition' in df.columns:
        df['condition'] = df['condition'].astype(str).str.lower().str.strip()
        df['binary_condition'] = df['condition'].map(
            lambda x: CONDITION_VARIANTS.get(x, -1)
        )
        
        # Log mappings
        unique_conditions = df['condition'].unique()
        for cond in unique_conditions:
            if cond in CONDITION_VARIANTS:
                log_mapping(
                    logger,
                    dataset_id=dataset_id,
                    raw_condition=cond,
                    binary_condition=CONDITION_VARIANTS[cond],
                    message=f"Condition mapping for {dataset_id}"
                )
    
    return df

def download_dataset(url: str, dataset_id: str) -> Optional[pd.DataFrame]:
    """
    Download dataset from URL with error handling.
    
    Args:
        url: URL to download from
        dataset_id: Identifier for logging
        
    Returns:
        DataFrame or None if download fails
    """
    try:
        logger.info(f"Downloading dataset {dataset_id} from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Assume CSV format
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        logger.info(f"Successfully downloaded {dataset_id}: {len(df)} rows")
        return df
        
    except requests.RequestException as e:
        logger.error(f"Failed to download {dataset_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error processing {dataset_id}: {str(e)}")
        return None

def ingest_datasets(
    urls: List[Tuple[str, str]],
    output_path: Path = Path("data/processed/cleaned_data.parquet")
) -> Optional[pd.DataFrame]:
    """
    Main ingestion pipeline: download, validate, normalize, merge.
    
    Args:
        urls: List of (url, dataset_id) tuples
        output_path: Path to write cleaned data
        
    Returns:
        Merged DataFrame or None if insufficient valid data
    """
    valid_datasets = []
    
    for url, dataset_id in urls:
        df = download_dataset(url, dataset_id)
        if df is None:
            continue
        
        is_valid, missing = validate_schema(df, dataset_id)
        if not is_valid:
            continue
        
        df = normalize_columns(df, dataset_id)
        valid_datasets.append(df)
    
    if len(valid_datasets) < 3:
        logger.error(f"Insufficient valid datasets: {len(valid_datasets)} < 3")
        return None
    
    # Merge all valid datasets
    merged_df = pd.concat(valid_datasets, ignore_index=True)
    logger.info(f"Merged {len(valid_datasets)} datasets into {len(merged_df)} total rows")
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_parquet(output_path, index=False)
    logger.info(f"Wrote cleaned data to {output_path}")
    
    return merged_df

if __name__ == "__main__":
    # Example usage with test URLs (would be replaced with real OSF URLs in production)
    test_urls = [
        ("https://osf.io/download/abc123/", "test_dataset_1"),
        ("https://osf.io/download/def456/", "test_dataset_2"),
        ("https://osf.io/download/ghi789/", "test_dataset_3"),
    ]
    
    result = ingest_datasets(test_urls)
    if result is not None:
        print(f"Ingestion successful: {len(result)} rows")
    else:
        print("Ingestion failed: insufficient valid datasets")
        exit(1)
