"""
code/validation_logic.py
Implements validation logic for T015: handling undefined imperative ratios.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import pandas as pd
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/validation_logic.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def flag_undefined_imperative_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows where the imperative ratio is undefined (zero total sentences).
    
    Args:
        df: DataFrame with feature columns.
        
    Returns:
        DataFrame with 'is_ratio_undefined' column added/updated.
    """
    if 'total_sentences' in df.columns:
        df['is_ratio_undefined'] = df['total_sentences'] == 0
    else:
        # Fallback: check if imperative_ratio is NaN
        df['is_ratio_undefined'] = df['imperative_ratio'].isna()
    
    # Count undefined rows
    undefined_count = df['is_ratio_undefined'].sum()
    if undefined_count > 0:
        logger.warning(f"Found {undefined_count} rows with undefined imperative ratio.")
    
    return df

def validate_features_for_imperative_ratio(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that undefined ratios are properly handled.
    
    Args:
        df: DataFrame with feature columns.
        
    Returns:
        Tuple of (is_valid, message).
    """
    # Check if flag exists
    if 'is_ratio_undefined' not in df.columns:
        return False, "Missing 'is_ratio_undefined' column"
    
    # Check if undefined rows have imputed values (0.0)
    if 'imperative_ratio' in df.columns:
        undefined_rows = df[df['is_ratio_undefined']]
        if len(undefined_rows) > 0:
            # Check if imputed values are 0.0
            non_zero_imputed = undefined_rows[undefined_rows['imperative_ratio'] != 0.0]
            if len(non_zero_imputed) > 0:
                return False, f"Found {len(non_zero_imputed)} undefined rows with non-zero imputed values"
    
    return True, "Validation passed: undefined ratios are properly flagged and imputed"

def run_t015_validation_pipeline(input_path: str, output_path: str) -> None:
    """
    Run T015 validation pipeline: load features, flag undefined ratios, validate, save.
    
    Args:
        input_path: Path to input features CSV.
        output_path: Path to output validated features CSV.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading features from {input_path}")
    df = pd.read_csv(input_path)
    
    # Flag undefined ratios
    logger.info("Flagging undefined imperative ratios...")
    df = flag_undefined_imperative_ratio(df)
    
    # Validate
    logger.info("Validating feature handling...")
    is_valid, message = validate_features_for_imperative_ratio(df)
    
    if not is_valid:
        logger.error(f"Validation failed: {message}")
        raise ValueError(message)
    
    logger.info(f"Validation passed: {message}")
    
    # Save updated features
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving validated features to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log summary
    undefined_count = df['is_ratio_undefined'].sum()
    logger.info(f"Validation pipeline complete. {len(df)} rows processed. "
               f"{undefined_count} rows flagged as undefined.")

def main():
    """
    CLI entry point for T015 validation.
    """
    config = get_config()
    input_path = config.get('paths', {}).get('features', 'data/processed/features.csv')
    output_path = config.get('paths', {}).get('features_validated', 'data/processed/features.csv')
    
    logger.info("Starting T015 validation pipeline")
    
    try:
        run_t015_validation_pipeline(input_path, output_path)
        logger.info("T015 validation pipeline completed successfully")
    except Exception as e:
        logger.error(f"T015 validation pipeline failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()