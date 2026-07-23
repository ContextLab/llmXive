import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path

from utils.config import get_processed_data_dir

logger = logging.getLogger(__name__)

# ============================================================================
# CSA Index Calculation (T007c Implementation)
# ============================================================================
# This module implements the CSA Index calculation as defined in T007b.
# It supports:
# 1. Configurable weighting (default: equal weighting 0.2 each)
# 2. Dual role documentation for digital/finance variables:
#    (1) Included in the Primary CSA Index
#    (2) Tested as moderators in the statistical model (T023)
# ============================================================================

def _normalize_minmax(series: pd.Series, min_val: Optional[float] = None, max_val: Optional[float] = None) -> pd.Series:
    """
    Normalize a series using min-max scaling: (x - min) / (max - min).
    
    Args:
        series: Input pandas Series
        min_val: Minimum value (if None, uses series.min())
        max_val: Maximum value (if None, uses series.max())
        
    Returns:
        Normalized series in [0, 1] range
    """
    if min_val is None:
        min_val = series.min()
    if max_val is None:
        max_val = series.max()
        
    denominator = max_val - min_val
    if denominator == 0:
        # If all values are the same, return 0.5 (midpoint) or 0.0
        return pd.Series(0.5, index=series.index)
        
    return (series - min_val) / denominator

def construct_csa_index(
    df: pd.DataFrame, 
    weights: Optional[Dict[str, float]] = None,
    normalize: bool = True
) -> pd.DataFrame:
    """
    Construct the CSA Index based on the formula:
    CSA_Index = w1*(Conservation Tillage) + w2*(Crop Diversification) + 
                w3*(Irrigation Efficiency) + w4*(Digital Access) + w5*(Finance Access)
    
    Args:
        df: Input DataFrame with CSA component columns
        weights: Optional dictionary of weights. Default is equal weighting (0.2 each).
        normalize: If True, apply min-max normalization to each component before weighting.
        
    Returns:
        DataFrame with added 'csa_index' column
        
    Note:
        Digital Access and Finance Access serve a dual role:
        1. Included in the Primary CSA Index calculation (this function)
        2. Tested as moderators in the statistical model (T023)
    """
    # Default equal weighting strategy (0.2 each)
    default_weights = {
        "conservation_tillage": 0.2,
        "crop_diversity": 0.2,
        "irrigation_efficiency": 0.2,
        "digital_access": 0.2,
        "finance_access": 0.2
    }
    
    # Use provided weights or default
    effective_weights = weights if weights is not None else default_weights
    
    # Validate required columns
    required_cols = ["conservation_tillage", "crop_diversity", "irrigation_efficiency", 
                     "digital_access", "finance_access"]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for CSA Index: {missing_cols}")
    
    # Create normalized copies if requested
    df_calc = df.copy()
    
    if normalize:
        # Normalize each component to [0, 1] range
        for col in required_cols:
            norm_col = f"{col}_norm"
            df_calc[norm_col] = _normalize_minmax(df_calc[col])
            logger.debug(f"Normalized {col} using min-max scaling")
    else:
        # Use raw values
        for col in required_cols:
            norm_col = f"{col}_norm"
            df_calc[norm_col] = df_calc[col]
    
    # Calculate weighted sum
    csa_components = []
    for col, weight in effective_weights.items():
        norm_col = f"{col}_norm"
        component = weight * df_calc[norm_col]
        csa_components.append(component)
    
    df_calc["csa_index"] = sum(csa_components)
    
    # Log the weighting strategy used
    logger.info(f"CSA Index calculated with weights: {effective_weights}")
    
    return df_calc

def calculate_component_statistics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate mean statistics for each CSA component.
    
    Args:
        df: DataFrame with CSA component columns
        
    Returns:
        Dictionary of component names to their mean values
    """
    required_cols = ["conservation_tillage", "crop_diversity", "irrigation_efficiency", 
                     "digital_access", "finance_access"]
    
    available_cols = [col for col in required_cols if col in df.columns]
    if not available_cols:
        return {}
        
    return df[available_cols].mean().to_dict()

def validate_csa_components(df: pd.DataFrame) -> bool:
    """
    Validate that all required CSA component columns exist and have valid values.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if all validations pass, False otherwise
    """
    required_cols = ["conservation_tillage", "crop_diversity", "irrigation_efficiency", 
                     "digital_access", "finance_access"]
    
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
        if df[col].isna().any():
            logger.warning(f"Column {col} contains missing values")
            
    return True

def main():
    """
    Main entry point for feature construction.
    
    This script:
    1. Loads the merged dataset from data/processed/merged_sample.parquet
    2. Constructs the CSA Index using configurable weights (default: equal weighting)
    3. Saves the output to data/processed/features.parquet
    """
    logger.info("Starting feature construction...")
    
    input_path = get_processed_data_dir() / "merged_sample.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Construct CSA Index with default equal weighting
    df = construct_csa_index(df)
    
    output_path = get_processed_data_dir() / "features.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Features saved to {output_path}")
    
    # Log component statistics
    stats = calculate_component_statistics(df)
    logger.info(f"Component statistics: {stats}")

if __name__ == "__main__":
    main()