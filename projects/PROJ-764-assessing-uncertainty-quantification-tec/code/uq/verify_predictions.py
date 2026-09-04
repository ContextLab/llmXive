import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'sample_id', 'method', 'prediction', 'variance',
    'lower_50', 'upper_50', 'lower_90', 'upper_90'
]

def verify_schema(df: pd.DataFrame) -> bool:
    """
    Verifies that the DataFrame contains all required columns with correct dtypes.
    
    Args:
        df: The DataFrame to verify.
        
    Returns:
        True if schema is valid, False otherwise.
        
    Raises:
        ValueError: If schema validation fails.
    """
    logger.info("Verifying schema of predictions DataFrame...")
    
    # Check columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for extra columns (optional, but good for strict compliance)
    extra_cols = set(df.columns) - set(REQUIRED_COLUMNS)
    if extra_cols:
        logger.warning(f"Extra columns found (not in schema): {extra_cols}")
    
    # Check dtypes
    # sample_id should be integer
    if not np.issubdtype(df['sample_id'].dtype, np.integer):
        raise ValueError(f"Column 'sample_id' must be integer, got {df['sample_id'].dtype}")
    
    # method should be string/object
    if df['method'].dtype != 'object':
        raise ValueError(f"Column 'method' must be string/object, got {df['method'].dtype}")
    
    # Numeric columns
    numeric_cols = ['prediction', 'variance', 'lower_50', 'upper_50', 'lower_90', 'upper_90']
    for col in numeric_cols:
        if not np.issubdtype(df[col].dtype, np.floating):
            raise ValueError(f"Column '{col}' must be float, got {df[col].dtype}")
    
    # Check for NaN values in critical columns
    for col in numeric_cols:
        if df[col].isna().any():
            raise ValueError(f"Column '{col}' contains NaN values")
    
    logger.info("Schema verification passed.")
    return True

def verify_data_integrity(df: pd.DataFrame) -> bool:
    """
    Verifies logical consistency of the data (e.g., lower < prediction < upper).
    
    Args:
        df: The DataFrame to verify.
        
    Returns:
        True if data integrity is valid, False otherwise.
        
    Raises:
        ValueError: If data integrity check fails.
    """
    logger.info("Verifying data integrity...")
    
    # Check variance is non-negative
    if (df['variance'] < 0).any():
        raise ValueError("Variance must be non-negative.")
    
    # Check 50% bounds: lower_50 <= prediction <= upper_50
    if ((df['lower_50'] > df['prediction']) | (df['prediction'] > df['upper_50'])).any():
        raise ValueError("50% bounds violation: prediction must be between lower_50 and upper_50.")
    
    # Check 90% bounds: lower_90 <= prediction <= upper_90
    if ((df['lower_90'] > df['prediction']) | (df['prediction'] > df['upper_90'])).any():
        raise ValueError("90% bounds violation: prediction must be between lower_90 and upper_90.")
    
    # Check consistency between 50% and 90% bounds
    # lower_90 should be <= lower_50 and upper_50 should be <= upper_90
    if ((df['lower_90'] > df['lower_50']) | (df['upper_50'] > df['upper_90'])).any():
        raise ValueError("Bound consistency violation: 90% bounds must encompass 50% bounds.")
    
    logger.info("Data integrity verification passed.")
    return True

def main():
    """
    Main entry point for verifying the uq_predictions_base.csv file.
    """
    input_path = 'results/uq_predictions_base.csv'
    
    if not os.path.exists(input_path):
        logger.error(f"File not found: {input_path}")
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)
    
    try:
        logger.info(f"Loading file: {input_path}")
        df = pd.read_csv(input_path)
        
        # Run schema verification
        verify_schema(df)
        
        # Run data integrity verification
        verify_data_integrity(df)
        
        logger.info("Verification complete. All checks passed.")
        print(f"SUCCESS: {input_path} is valid.")
        print(f"  - Rows: {len(df)}")
        print(f"  - Columns: {list(df.columns)}")
        print(f"  - Methods: {df['method'].unique().tolist()}")
        
        # Write a success report
        report = {
            "status": "passed",
            "file": input_path,
            "row_count": len(df),
            "column_count": len(df.columns),
            "methods": df['method'].unique().tolist(),
            "checks": ["schema", "data_integrity"]
        }
        
        os.makedirs('logs', exist_ok=True)
        with open('logs/verification_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        sys.exit(0)
        
    except ValueError as e:
        logger.error(f"Verification failed: {e}")
        print(f"ERROR: Verification failed - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"ERROR: Unexpected error - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()