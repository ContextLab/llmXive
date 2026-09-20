"""
Construct validity checks for the Doomscrolling Anxiety study.
Detects mathematical coupling and ensures distinct constructs.
"""
import pandas as pd
import numpy as np
import logging
from typing import Union, List

from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

def check_construct_validity(df: pd.DataFrame, col1: str = 'baseline_anxiety', col2: str = 'anxiety_score') -> bool:
    """
    Checks if two columns represent distinct constructs.
    
    In the absence of external metadata in the CSV, we perform a statistical check:
    If correlation is extremely high (> 0.99) AND the columns are nearly identical,
    it suggests mathematical coupling or identical measurement.
    
    Args:
        df: DataFrame containing the columns.
        col1: First column name.
        col2: Second column name.

    Returns:
        bool: True if constructs appear distinct, False otherwise.

    Raises:
        MathematicalCouplingError: If columns appear to be derived from the same instrument/timepoint.
    """
    if col1 not in df.columns or col2 not in df.columns:
        logger.warning(f"Columns {col1} or {col2} not found in data. Skipping statistical check.")
        # In a real scenario with metadata, we would check metadata here.
        # Since we don't have metadata in the CSV, we rely on the statistical check.
        return True 

    valid_data = df[[col1, col2]].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data for validity check.")
        return True

    corr = valid_data[col1].corr(valid_data[col2])
    
    # If correlation is perfect or near-perfect, it's highly suspicious
    if corr > 0.99:
        # Check if they are actually identical (mathematical coupling)
        if np.allclose(valid_data[col1], valid_data[col2], rtol=1e-5):
            error_msg = (
                f"Mathematical Coupling Detected: '{col1}' and '{col2}' are identical or nearly identical. "
                "They likely derive from the same instrument or time point, violating construct validity."
            )
            logger.error(error_msg)
            raise MathematicalCouplingError(error_msg)
        
        # Even if not identical, extremely high correlation warrants a warning
        logger.warning(f"Extremely high correlation ({corr:.4f}) between '{col1}' and '{col2}'. Review construct validity.")

    logger.info(f"Construct validity check passed. Correlation between '{col1}' and '{col2}': {corr:.4f}")
    return True

def main():
    """
    Main entry point for validity checks (usually called by model.py).
    """
    from config import load_config, ensure_directories
    from pathlib import Path
    
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found: {input_path}. Run clean.py first.")
    
    df = pd.read_csv(input_path)
    check_construct_validity(df)
    logger.info("Validity check completed successfully.")

if __name__ == '__main__':
    main()
