"""
Data Availability Validation Module.

This module validates that the processed dataset meets the FR-001 target.
"""
import logging
import sys
import os
import pandas as pd

from utils import get_logger

logger = get_logger(__name__)

def validate_data_availability(df: pd.DataFrame) -> None:
    """
    Validate data availability against FR-001 target.
    
    Args:
        df: Processed DataFrame
        
    Raises:
        ValueError: If N < 1000.
    """
    n = len(df)
    
    if n < 1000:
        raise ValueError(f"Data availability error: N < 1000. Target N >= 1000 required by FR-001.")
    
    if 1000 <= n < 5000:
        logger.info(f"Data is sufficient but below ideal: N={n}")
    else:
        logger.info(f"Data is sufficient: N={n}")

def run_validation():
    """
    Main function to run data availability validation.
    """
    input_path = "data/processed/processed_alloys.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed data not found at {input_path}. Run features.py first.")
    
    df = pd.read_csv(input_path)
    validate_data_availability(df)
    logger.info("Data availability validation passed")

if __name__ == "__main__":
    run_validation()
