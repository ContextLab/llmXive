"""
Regime classification logic for CBNRM vs State-Led management.

This module loads the validated CBNRM proxy metadata and applies
threshold-based classification to derive a binary regime_type variable.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import logging infrastructure from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logging_config import get_logger

logger = get_logger(__name__)


def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """
    Load the CBNRM proxy metadata containing indicator code and thresholds.
    
    Args:
        metadata_path: Path to the JSON metadata file.
        
    Returns:
        Dictionary containing indicator code, thresholds, and source info.
        
    Raises:
        FileNotFoundError: If metadata file does not exist.
        json.JSONDecodeError: If metadata file is not valid JSON.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        
    logger.info(f"Loaded metadata for indicator: {metadata.get('indicator_code', 'Unknown')}")
    return metadata


def classify_regime(df: pd.DataFrame, metadata: Dict[str, Any]) -> pd.DataFrame:
    """
    Classify regime type based on CBNRM proxy thresholds.
    
    The classification logic:
    - If CBNRM proxy value >= upper_threshold: 'CBNRM'
    - If CBNRM proxy value <= lower_threshold: 'State-Led'
    - If between thresholds: 'Mixed' (treated as 'State-Led' for binary output)
    
    Args:
        df: DataFrame containing the CBNRM proxy data with a 'value' column.
        metadata: Dictionary containing threshold values.
        
    Returns:
        DataFrame with added 'regime_type' column (binary: 0 or 1).
    """
    # Extract thresholds from metadata
    thresholds = metadata.get('thresholds', {})
    lower_threshold = thresholds.get('lower', 0.0)
    upper_threshold = thresholds.get('upper', 1.0)
    
    logger.info(f"Applying classification: lower={lower_threshold}, upper={upper_threshold}")
    
    # Ensure we have the value column
    if 'value' not in df.columns:
        raise ValueError("DataFrame must contain a 'value' column for classification")
    
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Apply classification logic directly to binary
    def classify_row(value):
        if pd.isna(value):
            return None
        if value >= upper_threshold:
            return 1  # CBNRM
        else:
            return 0  # State-Led or Mixed (both 0)
    
    result_df['regime_type'] = result_df['value'].apply(classify_row)
    
    # Log distribution
    regime_counts = result_df['regime_type'].value_counts()
    logger.info(f"Binary classification distribution:\n{regime_counts}")
    
    return result_df


def convert_to_binary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert regime_type to binary classification.
    
    This function is now a no-op for the main flow as classify_regime
    already returns binary values, but kept for API compatibility.
    
    Args:
        df: DataFrame with 'regime_type' column.
        
    Returns:
        DataFrame with binary 'regime_type' column (0 or 1).
    """
    # Since classify_regime already returns binary, we just return a copy
    return df.copy()


def main():
    """
    Main entry point for regime classification.
    
    This function:
    1. Loads the CBNRM proxy metadata from data/processed/cbnrm_proxy_metadata.json
    2. Loads the raw CBNRM proxy data from data/raw/cbnrm_proxy.csv
    3. Classifies each record into regime types (binary)
    4. Saves the classified data to data/processed/classified_regimes.csv
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    metadata_path = project_root / 'data' / 'processed' / 'cbnrm_proxy_metadata.json'
    raw_data_path = project_root / 'data' / 'raw' / 'cbnrm_proxy.csv'
    output_path = project_root / 'data' / 'processed' / 'classified_regimes.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting regime classification process")
    
    # Load metadata
    try:
        metadata = load_metadata(metadata_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load metadata: {e}")
        return 1
    
    # Load raw data
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        return 1
        
    try:
        df = pd.read_csv(raw_data_path)
        logger.info(f"Loaded {len(df)} records from {raw_data_path}")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return 1
    
    # Perform classification
    try:
        classified_df = classify_regime(df, metadata)
        # convert_to_binary is effectively a no-op now but called for flow
        binary_df = convert_to_binary(classified_df)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return 1
    
    # Save results
    try:
        binary_df.to_csv(output_path, index=False)
        logger.info(f"Saved classified data to {output_path}")
        logger.info(f"Output contains {len(binary_df)} records")
    except Exception as e:
        logger.error(f"Failed to save output: {e}")
        return 1
    
    logger.info("Regime classification completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())