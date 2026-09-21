"""
Normalization module for High-Entropy Alloy composition data.

This module enforces the constraint that composition fractions sum to 1.0,
logs any adjustments made, and handles edge cases like zero-sum rows.
"""
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from utils.logging_config import get_logger
from utils.validators import normalize_compositions, ValidationError

# Get logger for this module
logger = get_logger(__name__)

def get_composition_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns in the DataFrame that represent composition fractions.
    
    Composition columns are typically named after chemical elements (e.g., 'Fe', 'Ni', 'Cr')
    and contain numeric values representing atomic or weight fractions.
    
    Args:
        df: Input DataFrame containing composition data
        
    Returns:
        List of column names identified as composition fractions
    """
    # Common element symbols that might appear in composition columns
    # We'll identify them by checking if the column name is a valid element symbol
    # and if the column contains numeric data
    from pymatgen.core import Element, PeriodicTable
    
    composition_cols = []
    for col in df.columns:
        try:
            # Check if column name is a valid element symbol
            Element(col)
            # Check if the column contains numeric data
            if pd.api.types.is_numeric_dtype(df[col]):
                composition_cols.append(col)
        except ValueError:
            # Not a valid element symbol
            continue
    
    return composition_cols

def normalize_composition_row(row: pd.Series, composition_cols: List[str]) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Normalize a single row's composition fractions to sum to 1.0.
    
    Args:
        row: A single row from the DataFrame
        composition_cols: List of columns representing composition fractions
        
    Returns:
        Tuple of (normalized_row, adjustment_info)
        adjustment_info contains details about what adjustments were made
    """
    adjustment_info = {
        'original_sum': 0.0,
        'adjusted': False,
        'adjustment_magnitude': 0.0,
        'issues': []
    }
    
    # Extract composition values
    comp_values = row[composition_cols].copy()
    
    # Calculate original sum
    original_sum = comp_values.sum()
    adjustment_info['original_sum'] = original_sum
    
    # Handle edge cases
    if original_sum == 0:
        # All zeros - cannot normalize, mark as invalid
        adjustment_info['issues'].append('Zero composition sum - cannot normalize')
        logger.warning(f"Zero composition sum found in row. Marking as invalid.")
        # Set all to NaN to indicate invalid data
        row[composition_cols] = np.nan
        return row, adjustment_info
    
    if original_sum < 0:
        # Negative sum - invalid data
        adjustment_info['issues'].append('Negative composition sum - invalid data')
        logger.warning(f"Negative composition sum found in row. Marking as invalid.")
        row[composition_cols] = np.nan
        return row, adjustment_info
    
    # Check if normalization is needed
    if abs(original_sum - 1.0) < 1e-9:
        # Already normalized within floating point tolerance
        adjustment_info['adjusted'] = False
        return row, adjustment_info
    
    # Normalize
    normalized_values = comp_values / original_sum
    row[composition_cols] = normalized_values
    
    adjustment_info['adjusted'] = True
    adjustment_info['adjustment_magnitude'] = abs(original_sum - 1.0)
    adjustment_info['new_sum'] = row[composition_cols].sum()
    
    # Log the adjustment
    logger.debug(
        f"Normalized composition row: original_sum={original_sum:.6f}, "
        f"adjustment={adjustment_info['adjustment_magnitude']:.6f}"
    )
    
    return row, adjustment_info

def normalize_dataframe(df: pd.DataFrame, composition_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalize composition fractions in a DataFrame to sum to 1.0 for each row.
    
    This function:
    1. Identifies composition columns if not provided
    2. Normalizes each row's composition to sum to 1.0
    3. Logs all adjustments made
    4. Returns summary statistics about the normalization process
    
    Args:
        df: Input DataFrame with composition data
        composition_cols: Optional list of composition column names. If None, auto-detected.
        
    Returns:
        Tuple of (normalized_dataframe, normalization_summary)
        normalization_summary contains statistics about adjustments made
    """
    if composition_cols is None:
        composition_cols = get_composition_columns(df)
    
    if not composition_cols:
        logger.warning("No composition columns found in DataFrame. Returning original data.")
        return df, {'rows_processed': 0, 'rows_adjusted': 0, 'issues': []}
    
    logger.info(f"Normalizing {len(composition_cols)} composition columns: {composition_cols}")
    
    summary = {
        'rows_processed': 0,
        'rows_adjusted': 0,
        'rows_zero_sum': 0,
        'rows_negative_sum': 0,
        'max_adjustment': 0.0,
        'avg_adjustment': 0.0,
        'adjustments': [],
        'issues': []
    }
    
    adjustments = []
    total_adjustment = 0.0
    
    # Process each row
    for idx, row in df.iterrows():
        summary['rows_processed'] += 1
        normalized_row, info = normalize_composition_row(row, composition_cols)
        df.loc[idx] = normalized_row
        
        if info['adjusted']:
            summary['rows_adjusted'] += 1
            adjustments.append(info['adjustment_magnitude'])
            total_adjustment += info['adjustment_magnitude']
            summary['max_adjustment'] = max(summary['max_adjustment'], info['adjustment_magnitude'])
            
            if info['adjustment_magnitude'] > 0.01:
                logger.warning(
                    f"Large normalization adjustment at row {idx}: "
                    f"original_sum={info['original_sum']:.6f}, "
                    f"adjustment={info['adjustment_magnitude']:.6f}"
                )
        elif info['issues']:
            if 'Zero composition sum' in str(info['issues']):
                summary['rows_zero_sum'] += 1
            elif 'Negative composition sum' in str(info['issues']):
                summary['rows_negative_sum'] += 1
            summary['issues'].extend(info['issues'])
    
    # Calculate average adjustment
    if adjustments:
        summary['avg_adjustment'] = total_adjustment / len(adjustments)
    
    # Log summary
    logger.info(
        f"Normalization complete: {summary['rows_processed']} rows processed, "
        f"{summary['rows_adjusted']} adjusted, "
        f"max adjustment: {summary['max_adjustment']:.6f}, "
        f"avg adjustment: {summary['avg_adjustment']:.6f}"
    )
    
    if summary['rows_zero_sum'] > 0:
        logger.warning(f"Found {summary['rows_zero_sum']} rows with zero composition sum (marked as invalid)")
    if summary['rows_negative_sum'] > 0:
        logger.warning(f"Found {summary['rows_negative_sum']} rows with negative composition sum (marked as invalid)")
    
    return df, summary

def main():
    """
    Main function to demonstrate normalization functionality.
    This is typically called by the pipeline orchestration script.
    """
    # Example usage
    logger.info("Starting normalization module demonstration")
    
    # Create a sample DataFrame with unnormalized compositions
    sample_data = {
        'Fe': [0.2, 0.25, 0.3],
        'Ni': [0.2, 0.25, 0.2],
        'Cr': [0.2, 0.25, 0.2],
        'Co': [0.2, 0.25, 0.2],
        'Mn': [0.2, 0.0, 0.1],
        'Bulk_Modulus': [150, 160, 170]
    }
    df = pd.DataFrame(sample_data)
    
    logger.info("Original DataFrame:")
    logger.info(df.to_string())
    
    # Normalize
    normalized_df, summary = normalize_dataframe(df)
    
    logger.info("\nNormalized DataFrame:")
    logger.info(normalized_df.to_string())
    
    logger.info("\nNormalization Summary:")
    for key, value in summary.items():
        if key != 'adjustments':  # Don't log full list of adjustments
            logger.info(f"  {key}: {value}")
    
    return normalized_df, summary

if __name__ == "__main__":
    main()