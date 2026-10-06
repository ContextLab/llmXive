"""
Normalization utilities for High-Entropy Alloy (HEA) composition data.

This module enforces the constraint that composition fractions sum to 1.0
and logs any adjustments made during the normalization process.
"""

import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

# Import from project utilities using the defined API surface
from src.utils.logging_config import get_logger
from src.utils.validators import normalize_compositions, ValidationError

# Configuration
NORMALIZATION_TOLERANCE = 1e-9
COMPOSITION_SUFFIX = "_atomic_fraction"

def get_composition_columns(df: pd.DataFrame, prefix: str = "element_") -> List[str]:
    """
    Identify columns in the DataFrame that represent elemental compositions.

    Args:
        df: Input DataFrame.
        prefix: Prefix used for elemental columns (e.g., 'element_').

    Returns:
        List of column names representing elemental compositions.
    """
    composition_cols = [col for col in df.columns if col.startswith(prefix)]
    if not composition_cols:
        # Fallback: look for columns ending with '_atomic_fraction' or similar patterns
        composition_cols = [col for col in df.columns if 'atomic' in col.lower() or 'fraction' in col.lower()]
    
    # Filter out any non-numeric columns
    composition_cols = [col for col in composition_cols if pd.api.types.is_numeric_dtype(df[col])]
    
    return sorted(composition_cols)


def normalize_composition_row(row: pd.Series, composition_cols: List[str]) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Normalize a single row's composition values to sum to 1.0.

    Args:
        row: A single row from the DataFrame.
        composition_cols: List of columns representing elemental compositions.

    Returns:
        Tuple of (normalized_row, adjustment_log).
    """
    normalized_row = row.copy()
    adjustment_log = {}
    
    # Extract composition values
    comp_values = row[composition_cols].values.astype(float)
    
    # Check for invalid values (negative or NaN)
    if np.any(np.isnan(comp_values)) or np.any(comp_values < 0):
        # Mark row as invalid but return as-is to allow downstream filtering
        adjustment_log['status'] = 'invalid'
        adjustment_log['reason'] = 'contains_nan_or_negative'
        return normalized_row, adjustment_log
    
    current_sum = np.sum(comp_values)
    
    if current_sum == 0:
        # Cannot normalize zero-sum composition
        adjustment_log['status'] = 'invalid'
        adjustment_log['reason'] = 'zero_sum'
        return normalized_row, adjustment_log
    
    # Check if normalization is needed
    if abs(current_sum - 1.0) > NORMALIZATION_TOLERANCE:
        # Normalize
        normalized_values = comp_values / current_sum
        for i, col in enumerate(composition_cols):
            normalized_row[col] = normalized_values[i]
        
        adjustment_log['status'] = 'normalized'
        adjustment_log['original_sum'] = float(current_sum)
        adjustment_log['adjustment_magnitude'] = float(abs(current_sum - 1.0))
    else:
        adjustment_log['status'] = 'already_normalized'
        adjustment_log['original_sum'] = float(current_sum)
    
    return normalized_row, adjustment_log


def normalize_dataframe(df: pd.DataFrame, composition_cols: Optional[List[str]] = None, 
                      log_adjustments: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normalize composition columns in a DataFrame so they sum to 1.0.

    Args:
        df: Input DataFrame.
        composition_cols: Optional list of composition columns. If None, auto-detected.
        log_adjustments: If True, return a DataFrame with adjustment logs.

    Returns:
        Tuple of (normalized_dataframe, adjustment_logs_dataframe).
    """
    logger = get_logger(__name__)
    
    if composition_cols is None:
        composition_cols = get_composition_columns(df)
    
    if not composition_cols:
        logger.warning("No composition columns found in DataFrame. Returning original data.")
        return df, pd.DataFrame()
    
    logger.info(f"Normalizing {len(composition_cols)} composition columns: {composition_cols}")
    
    normalized_dfs = []
    adjustment_logs = []
    
    invalid_count = 0
    normalized_count = 0
    already_normalized_count = 0
    
    for idx, row in df.iterrows():
        norm_row, log = normalize_composition_row(row, composition_cols)
        normalized_dfs.append(norm_row)
        
        if log_adjustments:
            log['row_index'] = idx
            adjustment_logs.append(log)
        
        if log['status'] == 'invalid':
            invalid_count += 1
        elif log['status'] == 'normalized':
            normalized_count += 1
        else:
            already_normalized_count += 1
    
    normalized_df = pd.DataFrame(normalized_dfs)
    
    if log_adjustments and adjustment_logs:
        logs_df = pd.DataFrame(adjustment_logs)
    else:
        logs_df = pd.DataFrame()
    
    logger.info(f"Normalization complete: {normalized_count} rows normalized, "
               f"{already_normalized_count} already normalized, {invalid_count} invalid.")
    
    return normalized_df, logs_df


def main():
    """
    Main entry point for standalone execution.
    
    This function demonstrates the normalization process on a sample dataset
    and writes the results to disk.
    """
    # Initialize logging
    from src.utils.logging_config import init_script_logging
    init_script_logging(level=logging.INFO)
    logger = get_logger(__name__)
    
    logger.info("Starting composition normalization module demonstration.")
    
    # Create sample data for demonstration
    sample_data = {
        'sample_id': ['HEA_001', 'HEA_002', 'HEA_003', 'HEA_004'],
        'element_Fe': [0.2, 0.25, 0.18, 0.22],
        'element_Cr': [0.2, 0.25, 0.22, 0.18],
        'element_Ni': [0.2, 0.25, 0.20, 0.20],
        'element_Mn': [0.2, 0.25, 0.20, 0.20],
        'element_Al': [0.2, 0.0, 0.20, 0.20],  # HEA_002 has only 4 elements, sum=0.95
    }
    
    df = pd.DataFrame(sample_data)
    logger.info(f"Sample data created with {len(df)} rows.")
    logger.info(f"Original composition sums: {df[['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn', 'element_Al']].sum(axis=1).tolist()}")
    
    # Normalize
    normalized_df, logs_df = normalize_dataframe(df)
    
    logger.info(f"Normalized composition sums: {normalized_df[['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn', 'element_Al']].sum(axis=1).tolist()}")
    
    # Verify normalization
    composition_cols = [col for col in normalized_df.columns if col.startswith('element_')]
    sums = normalized_df[composition_cols].sum(axis=1)
    
    if not np.allclose(sums, 1.0, atol=NORMALIZATION_TOLERANCE):
        logger.error("Normalization failed: some rows do not sum to 1.0")
        return 1
    
    logger.info("All rows successfully normalized to sum to 1.0.")
    
    # Output logs
    if not logs_df.empty:
        logger.info("Adjustment logs:")
        logger.info(logs_df.to_string(index=False))
    
    logger.info("Normalization module demonstration completed successfully.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
