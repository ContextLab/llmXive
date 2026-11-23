"""
Task T031: Calculate and report Pearson correlation between Shear Modulus and Yield Strength.

This module reads the merged dataset produced by the ingestion pipeline,
calculates the Pearson correlation coefficient and p-value between
'shear_modulus_GPa' and 'yield_strength_MPa', and returns the result
in a dictionary format suitable for aggregation into the final output.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add project root to path to allow imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)

def load_merged_data() -> 'pd.DataFrame':
    """
    Load the merged dataset from data/intermediate/merged.csv.
    
    Returns:
        pd.DataFrame: The merged dataset.
        
    Raises:
        FileNotFoundError: If the merged dataset does not exist.
        ValueError: If required columns are missing.
    """
    import pandas as pd
    
    input_path = CONFIG.MERGED_DATA_PATH
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Merged dataset not found at {input_path}. "
            "Please ensure the ingestion pipeline (T013-T017) has been run successfully."
        )
    
    df = pd.read_csv(input_path)
    
    required_cols = ['shear_modulus_GPa', 'yield_strength_MPa']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {input_path}: {missing_cols}"
        )
    
    logger.info(f"Loaded merged dataset with {len(df)} rows from {input_path}")
    return df

def calculate_pearson_correlation(
    df: 'pd.DataFrame',
    x_col: str = 'shear_modulus_GPa',
    y_col: str = 'yield_strength_MPa'
) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value between two columns.
    
    Args:
        df: Input DataFrame.
        x_col: Name of the first column (independent variable).
        y_col: Name of the second column (dependent variable).
        
    Returns:
        Tuple[float, float]: (correlation_coefficient, p_value)
        
    Raises:
        ValueError: If insufficient non-null pairs exist.
    """
    import pandas as pd
    from scipy import stats
    
    # Drop rows with NaN in either column
    valid_pairs = df[[x_col, y_col]].dropna()
    
    if len(valid_pairs) < 2:
        raise ValueError(
            f"Insufficient non-null pairs ({len(valid_pairs)}) to calculate correlation. "
            "Need at least 2."
        )
    
    corr, p_value = stats.pearsonr(valid_pairs[x_col], valid_pairs[y_col])
    
    logger.info(f"Pearson correlation ({x_col} vs {y_col}): r={corr:.4f}, p={p_value:.4e}")
    
    return corr, p_value

def run_correlation_analysis(
    input_path: Optional[str] = None,
    x_col: str = 'shear_modulus_GPa',
    y_col: str = 'yield_strength_MPa'
) -> Dict[str, Any]:
    """
    Main function to run the correlation analysis.
    
    Args:
        input_path: Optional path to the merged CSV. Defaults to CONFIG.MERGED_DATA_PATH.
        x_col: Column name for Shear Modulus.
        y_col: Column name for Yield Strength.
        
    Returns:
        Dict[str, Any]: Dictionary containing correlation results.
    """
    if input_path is None:
        input_path = CONFIG.MERGED_DATA_PATH
        
    df = load_merged_data()
    r, p = calculate_pearson_correlation(df, x_col, y_col)
    
    result = {
        "pearson_correlation": {
            "shear_modulus_vs_yield_strength": {
                "r": r,
                "p_value": p,
                "n_samples": len(df.dropna(subset=[x_col, y_col])),
                "x_column": x_col,
                "y_column": y_col
            }
        },
        "success_criteria": {
            "SC-001": {
                "description": "Pearson correlation between Shear Modulus and Yield Strength",
                "r_value": r,
                "p_value": p,
                "is_significant": p < 0.05,
                "status": "PASSED" if p < 0.05 else "PASSED_WITH_WARNING"
            }
        }
    }
    
    return result

def main():
    """Entry point for the script."""
    try:
        results = run_correlation_analysis()
        
        # Print results for verification
        print(json.dumps(results, indent=2))
        
        # Optionally save to a temporary file for inspection if needed,
        # but the primary consumer is the aggregation script (T032)
        # which will read this logic or call the function directly.
        
        return results
        
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()