"""
Preprocessing module for the Agentic Abstention dataset.

This module handles:
1. Mean imputation for missing numeric variables.
2. Validation logic to halt execution if missing data exceeds thresholds.
3. Generation of a validation report.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

import pandas as pd
import numpy as np

# Import project config utilities
from config import get_path, get_config, load_config
from logging_config import setup_logging

# Configure logging
logger = setup_logging(__name__)

# Critical columns that cannot have high missing rates
CRITICAL_COLUMNS = {
    "search_count",
    "error_frequency",
    "token_usage",
    "turn_number",
    "abstention_label"
}

MISSING_THRESHOLD = 0.05  # 5%

def load_preprocessing_config() -> Dict[str, Any]:
    """Load specific preprocessing config if available, otherwise return defaults."""
    try:
        config = load_config()
        return config.get("preprocessing", {})
    except Exception as e:
        logger.warning(f"Could not load preprocessing config: {e}. Using defaults.")
        return {}

def calculate_missing_statistics(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate missing value statistics for each column.
    
    Returns:
        Dict mapping column name to {'missing_count': int, 'missing_ratio': float}
    """
    stats = {}
    total_rows = len(df)
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_ratio = missing_count / total_rows if total_rows > 0 else 0.0
        stats[col] = {
            "missing_count": int(missing_count),
            "missing_ratio": float(missing_ratio)
        }
        
    return stats

def perform_mean_imputation(df: pd.DataFrame, config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Apply mean imputation for missing numeric variables.
    
    Args:
        df: Input DataFrame
        config: Optional configuration override
        
    Returns:
        DataFrame with imputed values
    """
    df_imputed = df.copy()
    
    # Identify numeric columns
    numeric_cols = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    logger.info(f"Identified {len(numeric_cols)} numeric columns for potential imputation.")
    
    for col in numeric_cols:
        missing_count = df_imputed[col].isna().sum()
        if missing_count > 0:
            mean_val = df_imputed[col].mean()
            
            # Handle case where all values are missing (mean would be NaN)
            if pd.isna(mean_val):
                mean_val = 0.0
                logger.warning(f"Column '{col}' has all missing values. Imputing with 0.0.")
            
            df_imputed[col] = df_imputed[col].fillna(mean_val)
            logger.info(f"Imputed {missing_count} missing values in '{col}' with mean {mean_val:.4f}")
            
    return df_imputed

def validate_dataset(df: pd.DataFrame, stats: Dict[str, Dict[str, float]]) -> bool:
    """
    Validate the dataset against missing data thresholds.
    
    Args:
        df: Input DataFrame
        stats: Pre-calculated missing statistics
        
    Returns:
        True if dataset is valid, False otherwise
    """
    is_valid = True
    critical_violations = []
    
    for col, col_stats in stats.items():
        if col_stats["missing_ratio"] > MISSING_THRESHOLD:
            if col in CRITICAL_COLUMNS:
                critical_violations.append(col)
                is_valid = False
                logger.error(f"CRITICAL: Column '{col}' has {col_stats['missing_ratio']*100:.2f}% missing values (threshold: {MISSING_THRESHOLD*100}%).")
            else:
                logger.warning(f"Column '{col}' has {col_stats['missing_ratio']*100:.2f}% missing values (threshold: {MISSING_THRESHOLD*100}%).")
                
    if critical_violations:
        logger.error(f"Dataset validation FAILED due to missing critical columns: {critical_violations}")
    else:
        logger.info("Dataset validation PASSED.")
        
    return is_valid

def generate_validation_report(
    stats: Dict[str, Dict[str, float]], 
    is_valid: bool, 
    output_path: Path
) -> None:
    """
    Generate a JSON validation report.
    
    Args:
        stats: Missing value statistics
        is_valid: Overall validation status
        output_path: Path to write the report
    """
    report = {
        "is_valid": is_valid,
        "threshold": MISSING_THRESHOLD,
        "total_records": 0,
        "columns": stats,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Validation report written to {output_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    
    # Load configuration
    config = load_preprocessing_config()
    
    # Determine input/output paths
    # Default to the processed features file from T015
    input_path = get_path("data/processed/features.parquet")
    output_path = get_path("data/processed/features_cleaned.parquet")
    report_path = get_path("data/validation_report.json")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T015 (extract_features) has completed successfully.")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading data from {input_path}...")
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns.")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    # Calculate statistics BEFORE imputation
    stats = calculate_missing_statistics(df)
    
    # Validate dataset
    is_valid = validate_dataset(df, stats)
    
    # Generate report (even if invalid, we need to report the failure)
    generate_validation_report(stats, is_valid, Path(report_path))
    
    if not is_valid:
        logger.error("HALTING EXECUTION: Dataset has >5% missing critical variables.")
        logger.error("Please check data ingestion and feature extraction steps.")
        sys.exit(1)
    
    # Perform imputation
    logger.info("Performing mean imputation...")
    df_cleaned = perform_mean_imputation(df, config)
    
    # Save cleaned data
    logger.info(f"Saving cleaned data to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_cleaned.to_parquet(output_path, index=False)
    
    logger.info(f"Preprocessing complete. Cleaned data saved to {output_path}")
    logger.info(f"Validation report saved to {report_path}")
    
    return df_cleaned

if __name__ == "__main__":
    main()