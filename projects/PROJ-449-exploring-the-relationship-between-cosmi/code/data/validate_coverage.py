"""
Data coverage validation module.

Validates that the dataset meets the minimum coverage threshold required
for statistically valid correlation analysis.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.config import CONFIG
from code.utils.logging import setup_logger

def load_unified_data() -> Optional[Dict]:
    """
    Load the unified timeseries data from disk.
    
    Returns:
        Dict containing the data or None if file doesn't exist.
    """
    logger = setup_logger("validate_coverage")
    data_path = Path(CONFIG.DATA_PROCESSED_DIR) / "unified_timeseries.csv"
    
    if not data_path.exists():
        logger.error(f"Unified timeseries file not found: {data_path}")
        return None
    
    try:
        import pandas as pd
        df = pd.read_csv(data_path, parse_dates=['date'])
        logger.info(f"Loaded {len(df)} rows from {data_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load unified timeseries: {str(e)}")
        return None

def calculate_coverage(df: 'pd.DataFrame') -> float:
    """
    Calculate the percentage of days with valid data coverage.
    
    Args:
        df: DataFrame containing the unified timeseries with 'date' column.
        
    Returns:
        Float representing the coverage percentage (0.0 to 1.0).
    """
    logger = setup_logger("validate_coverage")
    
    if df is None or len(df) == 0:
        logger.warning("Empty or None dataframe provided")
        return 0.0
    
    # Get date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    # Calculate total expected days in the range
    total_expected_days = (max_date - min_date).days + 1
    
    # Count unique dates in the dataset
    unique_dates = df['date'].dt.date.nunique()
    
    # Calculate coverage percentage
    coverage = unique_dates / total_expected_days
    
    logger.info(f"Date range: {min_date} to {max_date} ({total_expected_days} days)")
    logger.info(f"Unique dates in dataset: {unique_dates}")
    logger.info(f"Coverage: {coverage:.2%}")
    
    return coverage

def get_most_populated_bin(df: 'pd.DataFrame') -> Optional[Tuple[float, int]]:
    """
    Find the rigidity bin with the most data points.
    
    Args:
        df: DataFrame containing the unified timeseries.
        
    Returns:
        Tuple of (rigidity_bin, count) or None if no data.
    """
    if df is None or 'rigidity_bin' not in df.columns:
        return None
    
    bin_counts = df['rigidity_bin'].value_counts()
    if len(bin_counts) == 0:
        return None
    
    most_populated_bin = bin_counts.idxmax()
    count = bin_counts.max()
    
    return (most_populated_bin, count)

def validate_coverage(df: 'pd.DataFrame') -> bool:
    """
    Validate that data coverage meets the required threshold.
    
    Args:
        df: DataFrame containing the unified timeseries.
        
    Returns:
        True if coverage meets threshold, False otherwise.
    """
    logger = setup_logger("validate_coverage")
    
    coverage = calculate_coverage(df)
    threshold = CONFIG.get_coverage_threshold()
    
    logger.info(f"Coverage threshold: {threshold:.2%}")
    
    if coverage < threshold:
        logger.critical(
            f"DATA COVERAGE INSUFFICIENT: {coverage:.2%} < {threshold:.2%}. "
            f"Required minimum sample size: {CONFIG.get_minimum_sample_size()} days. "
            f"Exiting with error to prevent invalid statistical analysis."
        )
        return False
    else:
        logger.info(f"Data coverage VALID: {coverage:.2%} >= {threshold:.2%}")
        return True

def main():
    """Main entry point for coverage validation."""
    logger = setup_logger("validate_coverage")
    logger.info("Starting data coverage validation")
    
    # Load data
    df = load_unified_data()
    
    if df is None:
        logger.error("Failed to load unified data. Cannot validate coverage.")
        sys.exit(1)
    
    # Validate coverage
    is_valid = validate_coverage(df)
    
    # Get additional stats
    bin_info = get_most_populated_bin(df)
    if bin_info:
        logger.info(f"Most populated rigidity bin: {bin_info[0]} with {bin_info[1]} entries")
    
    # Exit with appropriate code
    if not is_valid:
        logger.error("Coverage validation FAILED. Pipeline cannot proceed.")
        sys.exit(1)
    else:
        logger.info("Coverage validation PASSED. Pipeline can proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
