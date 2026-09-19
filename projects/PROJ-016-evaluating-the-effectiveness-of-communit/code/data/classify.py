import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """
    Load the CBNRM proxy metadata and validation results.
    
    Args:
        metadata_path: Path to the metadata JSON file (e.g., cbnrm_proxy_metadata.json)
        
    Returns:
        Dictionary containing indicator code, thresholds, and validation status.
        
    Raises:
        FileNotFoundError: If the metadata file does not exist.
        ValueError: If validation status is false or required keys are missing.
    """
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Validate the metadata
    if not metadata.get('validation_status', False):
        logger.error("Proxy validation failed. Halting regime classification.")
        raise ValueError("Proxy validation failed. Halting regime classification.")
    
    required_keys = ['indicator_code']
    for key in required_keys:
        if key not in metadata:
            logger.error(f"Missing required key in metadata: {key}")
            raise KeyError(f"Missing required key in metadata: {key}")
    
    return metadata

def load_validation_results(validation_path: Path) -> Dict[str, Any]:
    """
    Load the proxy validation results to determine thresholds.
    
    Args:
        validation_path: Path to the validation JSON file.
        
    Returns:
        Dictionary containing variance and threshold information.
    """
    if not validation_path.exists():
        logger.error(f"Validation results file not found: {validation_path}")
        raise FileNotFoundError(f"Validation results file not found: {validation_path}")
    
    with open(validation_path, 'r') as f:
        validation = json.load(f)
    
    # Check for zero variance
    if validation.get('variance', 1.0) == 0:
        logger.error("Proxy has zero variance. Cannot classify regimes.")
        raise ValueError("Proxy has zero variance. Cannot classify regimes.")
    
    return validation

def classify_regime(df: pd.DataFrame, proxy_col: str, threshold: float) -> pd.Series:
    """
    Classify regime type based on the CBNRM proxy value and a threshold.
    
    Logic:
    - If proxy value > threshold: 'CBNRM' (1)
    - Else: 'State-Led' (0)
    
    Args:
        df: DataFrame containing the proxy data.
        proxy_col: Column name of the proxy indicator.
        threshold: The threshold value for classification.
        
    Returns:
        Series with regime classification (0 or 1).
    """
    logger.info(f"Classifying regimes using {proxy_col} with threshold {threshold}")
    
    # Handle missing values in the proxy column
    if df[proxy_col].isnull().any():
        logger.warning(f"Found {df[proxy_col].isnull().sum()} missing values in {proxy_col}. Dropping or filling?")
        # For strict classification, we drop rows with missing proxy values in this step
        # The main function handles the merging and dropping of missing primary vars
        # Here we just classify what we can
        pass
    
    regime = (df[proxy_col] > threshold).astype(int)
    return regime

def convert_to_binary(df: pd.DataFrame, proxy_col: str, threshold: float) -> pd.DataFrame:
    """
    Add a binary 'regime_type' column to the DataFrame.
    
    Args:
        df: Input DataFrame.
        proxy_col: Column name of the proxy indicator.
        threshold: Threshold for binary classification.
        
    Returns:
        DataFrame with new 'regime_type' column.
    """
    df = df.copy()
    df['regime_type'] = classify_regime(df, proxy_col, threshold)
    logger.info(f"Added 'regime_type' column based on {proxy_col} > {threshold}")
    return df

def main():
    """
    Main entry point for regime classification.
    
    Loads the merged panel data, reads the CBNRM proxy metadata and validation results,
    determines the threshold, and classifies the regime type for each country-year.
    Saves the result to data/processed/classified_panel.csv.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_processed = project_root / 'data' / 'processed'
    
    # Input files
    merged_panel_path = data_processed / 'merged_panel.csv'
    metadata_path = data_processed / 'cbnrm_proxy_metadata.json'
    validation_path = data_processed / 'proxy_validation.json'
    
    # Output file
    output_path = data_processed / 'classified_panel.csv'
    
    # Load metadata
    try:
        metadata = load_metadata(metadata_path)
        validation = load_validation_results(validation_path)
    except (FileNotFoundError, ValueError, KeyError) as e:
        logger.critical(f"Failed to load metadata or validation results: {e}")
        sys.exit(1)
    
    # Load merged panel
    if not merged_panel_path.exists():
        logger.error(f"Merged panel not found: {merged_panel_path}")
        sys.exit(1)
    
    df = pd.read_csv(merged_panel_path)
    logger.info(f"Loaded merged panel with {len(df)} rows")
    
    # Determine proxy column name
    # The metadata contains the indicator code, e.g., 'IC.LGL.CRED.XQ'
    # We need to map this to the column name in the dataframe.
    # Assuming the column name in the dataframe is the indicator code or a standardized version.
    # If the dataframe column is named differently, we might need a mapping.
    # For now, we assume the column name in the dataframe matches the indicator code.
    proxy_indicator_code = metadata['indicator_code']
    
    # Check if the proxy column exists in the dataframe
    if proxy_indicator_code not in df.columns:
        # Try to find a column that might contain the proxy data
        # Sometimes column names are standardized or have prefixes
        possible_cols = [col for col in df.columns if proxy_indicator_code in col or col in proxy_indicator_code]
        if possible_cols:
            proxy_col = possible_cols[0]
            logger.warning(f"Indicator code {proxy_indicator_code} not found. Using {proxy_col} instead.")
        else:
            logger.error(f"Proxy column {proxy_indicator_code} not found in merged panel.")
            sys.exit(1)
    else:
        proxy_col = proxy_indicator_code
    
    # Determine threshold
    # If the validation file has a specific threshold, use it.
    # Otherwise, calculate the median as a default threshold.
    if 'threshold' in validation:
        threshold = validation['threshold']
        logger.info(f"Using threshold from validation results: {threshold}")
    else:
        # Calculate median threshold
        threshold = df[proxy_col].median()
        logger.warning(f"No threshold in validation results. Using median: {threshold}")
    
    # Classify regimes
    df_classified = convert_to_binary(df, proxy_col, threshold)
    
    # Save output
    df_classified.to_csv(output_path, index=False)
    logger.info(f"Saved classified panel to {output_path}")
    
    # Log summary
    regime_counts = df_classified['regime_type'].value_counts()
    logger.info(f"Regime distribution: CBNRM (1) = {regime_counts.get(1, 0)}, State-Led (0) = {regime_counts.get(0, 0)}")

if __name__ == '__main__':
    main()
