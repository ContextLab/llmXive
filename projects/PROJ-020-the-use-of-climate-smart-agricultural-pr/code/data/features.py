"""
Feature engineering for CSA Index construction.

Implements the CSA Index formula defined in T007b:
CSA_Index = f(Conservation Tillage, Crop Diversification, Irrigation Efficiency, Digital Access, Finance Access)

Normalization: min-max scaling to [0, 1]
Weights: Configurable, default equal weighting (0.2 each)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
from utils.config import get_processed_data_dir, get_target_countries, get_target_years
from utils.logging import log_operation, ReproducibilityLogger

# Configure logger
logger = logging.getLogger(__name__)

# Default weights for CSA Index components
DEFAULT_WEIGHTS = {
    'conservation_tillage': 0.2,
    'crop_diversification': 0.2,
    'irrigation_efficiency': 0.2,
    'digital_access': 0.2,
    'finance_access': 0.2
}

@log_operation
def _min_max_normalize(series: pd.Series, min_val: Optional[float] = None, max_val: Optional[float] = None) -> pd.Series:
    """
    Normalize a series to [0, 1] using min-max scaling.
    
    If min/max not provided, compute from the series.
    Handles edge case where min == max by returning 0.5 for all values.
    """
    if min_val is None:
        min_val = series.min()
    if max_val is None:
        max_val = series.max()
    
    if min_val == max_val:
        # Edge case: constant value
        logger.warning(f"Constant value detected (min={min_val}, max={max_val}). Returning 0.5 for all.")
        return pd.Series([0.5] * len(series), index=series.index)
    
    normalized = (series - min_val) / (max_val - min_val)
    return normalized.clip(0, 1)

@log_operation
def _compute_conservation_tillage(df: pd.DataFrame) -> pd.Series:
    """
    Compute Conservation Tillage component.
    
    Assumes binary or categorical encoding where higher values indicate
    more conservation tillage practices.
    """
    # Check for common column names
    col_candidates = ['conservation_tillage', 'tillage_practice', 'conservation_practices']
    for col in col_candidates:
        if col in df.columns:
            logger.info(f"Using column '{col}' for conservation tillage")
            return df[col]
    
    # If not found, raise error
    raise ValueError("Conservation tillage column not found in dataframe. Expected one of: " + str(col_candidates))

@log_operation
def _compute_crop_diversification(df: pd.DataFrame) -> pd.Series:
    """
    Compute Crop Diversification component.
    
    Typically measured as number of crop types or Simpson's diversity index.
    """
    col_candidates = ['crop_diversification', 'num_crops', 'crop_count', 'diversity_index']
    for col in col_candidates:
        if col in df.columns:
            logger.info(f"Using column '{col}' for crop diversification")
            return df[col]
    
    raise ValueError("Crop diversification column not found in dataframe. Expected one of: " + str(col_candidates))

@log_operation
def _compute_irrigation_efficiency(df: pd.DataFrame) -> pd.Series:
    """
    Compute Irrigation Efficiency component.
    
    May be a binary indicator or a continuous efficiency score.
    """
    col_candidates = ['irrigation_efficiency', 'irrigation_method', 'water_use_efficiency']
    for col in col_candidates:
        if col in df.columns:
            logger.info(f"Using column '{col}' for irrigation efficiency")
            return df[col]
    
    raise ValueError("Irrigation efficiency column not found in dataframe. Expected one of: " + str(col_candidates))

@log_operation
def _compute_digital_access(df: pd.DataFrame) -> pd.Series:
    """
    Compute Digital Technology Access component.
    
    Measures access to digital tools (mobile, internet, advisory services).
    """
    col_candidates = ['digital_access', 'mobile_access', 'internet_access', 'digital_technology']
    for col in col_candidates:
        if col in df.columns:
            logger.info(f"Using column '{col}' for digital access")
            return df[col]
    
    raise ValueError("Digital access column not found in dataframe. Expected one of: " + str(col_candidates))

@log_operation
def _compute_finance_access(df: pd.DataFrame) -> pd.Series:
    """
    Compute Finance Access component.
    
    Measures access to credit, insurance, or financial services.
    """
    col_candidates = ['finance_access', 'credit_access', 'financial_access', 'insurance_access']
    for col in col_candidates:
        if col in df.columns:
            logger.info(f"Using column '{col}' for finance access")
            return df[col]
    
    raise ValueError("Finance access column not found in dataframe. Expected one of: " + str(col_candidates))

@log_operation
def construct_csa_index(
    df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    min_values: Optional[Dict[str, float]] = None,
    max_values: Optional[Dict[str, float]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Construct the CSA Index as a weighted composite score.
    
    Formula: CSA_Index = sum(w_i * normalized_component_i)
    
    Args:
        df: Input dataframe with raw component values.
        weights: Optional custom weights. Defaults to equal weighting (0.2 each).
        min_values: Optional pre-computed min values for normalization.
        max_values: Optional pre-computed max values for normalization.
    
    Returns:
        Tuple of (updated dataframe with csa_index column, metadata dict)
    
    Metadata includes:
        - component_stats: min/max/mean for each component
        - weights_used: the weights applied
        - normalization_params: min/max used for each component
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()
    
    # Validate weights sum to 1
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, atol=0.01):
        logger.warning(f"Weights sum to {weight_sum}, not 1.0. Normalizing weights.")
        weights = {k: v / weight_sum for k, v in weights.items()}
    
    # Compute components
    components = {}
    component_stats = {}
    normalization_params = {}
    
    try:
        components['conservation_tillage'] = _compute_conservation_tillage(df)
        components['crop_diversification'] = _compute_crop_diversification(df)
        components['irrigation_efficiency'] = _compute_irrigation_efficiency(df)
        components['digital_access'] = _compute_digital_access(df)
        components['finance_access'] = _compute_finance_access(df)
    except ValueError as e:
        logger.error(f"Missing required component column: {e}")
        raise
    
    # Normalize each component
    normalized_components = {}
    for name, series in components.items():
        # Handle missing values
        if series.isna().any():
            logger.warning(f"Missing values in {name}: {series.isna().sum()} rows. Dropping for index calculation.")
            # Drop rows with missing values in any component
            valid_mask = pd.Series([True] * len(df), index=df.index)
            for comp_name, comp_series in components.items():
                valid_mask &= ~comp_series.isna()
            df = df[valid_mask].copy()
            # Recompute series after drop
            series = components[name][valid_mask]
        
        min_val = min_values.get(name, None) if min_values else None
        max_val = max_values.get(name, None) if max_values else None
        
        normalized = _min_max_normalize(series, min_val, max_val)
        normalized_components[name] = normalized
        
        # Record stats
        component_stats[name] = {
            'min': float(series.min()),
            'max': float(series.max()),
            'mean': float(series.mean()),
            'count': int(len(series))
        }
        
        # Record normalization params used
        normalization_params[name] = {
            'min_used': float(normalized.min()) if min_val is None else min_val,
            'max_used': float(normalized.max()) if max_val is None else max_val
        }
    
    # Compute weighted composite
    csa_index = pd.Series(0.0, index=df.index)
    for name, normalized in normalized_components.items():
        weight = weights.get(name, 0.0)
        csa_index += weight * normalized
    
    # Round to 4 decimal places
    csa_index = csa_index.round(4)
    
    # Add to dataframe
    df['csa_index'] = csa_index
    
    # Log provenance
    logger.info(f"CSA Index constructed with {len(df)} valid records")
    logger.info(f"Weights used: {weights}")
    
    metadata = {
        'component_stats': component_stats,
        'weights_used': weights,
        'normalization_params': normalization_params,
        'final_count': len(df),
        'index_range': {
            'min': float(csa_index.min()),
            'max': float(csa_index.max())
        }
    }
    
    return df, metadata

@log_operation
def calculate_component_statistics(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate descriptive statistics for each CSA Index component.
    
    Args:
        df: Input dataframe with component columns.
    
    Returns:
        Dictionary mapping component name to stats (min, max, mean, std).
    """
    stats = {}
    
    component_funcs = {
        'conservation_tillage': _compute_conservation_tillage,
        'crop_diversification': _compute_crop_diversification,
        'irrigation_efficiency': _compute_irrigation_efficiency,
        'digital_access': _compute_digital_access,
        'finance_access': _compute_finance_access
    }
    
    for name, func in component_funcs.items():
        try:
            series = func(df)
            stats[name] = {
                'min': float(series.min()),
                'max': float(series.max()),
                'mean': float(series.mean()),
                'std': float(series.std()),
                'count': int(len(series)),
                'missing': int(series.isna().sum())
            }
        except ValueError:
            logger.warning(f"Could not compute stats for {name}: column not found")
            stats[name] = {
                'min': None,
                'max': None,
                'mean': None,
                'std': None,
                'count': 0,
                'missing': 0
            }
    
    return stats

@log_operation
def validate_csa_components(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that all required CSA Index components are present in the dataframe.
    
    Args:
        df: Input dataframe to validate.
    
    Returns:
        Tuple of (is_valid, list_of_missing_columns)
    """
    required_cols = [
        'conservation_tillage',
        'crop_diversification',
        'irrigation_efficiency',
        'digital_access',
        'finance_access'
    ]
    
    missing = []
    for col in required_cols:
        if col not in df.columns:
            # Check if any alias exists
            aliases = {
                'conservation_tillage': ['tillage_practice', 'conservation_practices'],
                'crop_diversification': ['num_crops', 'crop_count', 'diversity_index'],
                'irrigation_efficiency': ['irrigation_method', 'water_use_efficiency'],
                'digital_access': ['mobile_access', 'internet_access', 'digital_technology'],
                'finance_access': ['credit_access', 'financial_access', 'insurance_access']
            }
            
            found_alias = False
            for alias in aliases.get(col, []):
                if alias in df.columns:
                    logger.info(f"Found alias '{alias}' for required column '{col}'")
                    found_alias = True
                    break
            
            if not found_alias:
                missing.append(col)
    
    is_valid = len(missing) == 0
    return is_valid, missing

@log_operation
def main():
    """
    Main entry point for CSA Index construction.
    
    Reads merged sample data, constructs the CSA Index, and saves:
        1. Updated dataframe with csa_index column to data/processed/merged_sample_with_csa.parquet
        2. Metadata JSON to data/processed/csa_index_metadata.json
    """
    logger.info("Starting CSA Index construction")
    
    # Get paths
    processed_dir = get_processed_data_dir()
    input_path = processed_dir / "merged_sample.parquet"
    output_path = processed_dir / "merged_sample_with_csa.parquet"
    metadata_path = processed_dir / "csa_index_metadata.json"
    
    # Check input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run data preprocessing pipeline first (T016-T018)")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Validate components
    is_valid, missing = validate_csa_components(df)
    if not is_valid:
        logger.error(f"Missing required components: {missing}")
        raise ValueError(f"Cannot construct CSA Index: missing columns {missing}")
    
    # Construct index
    logger.info("Constructing CSA Index")
    df_with_csa, metadata = construct_csa_index(df)
    
    # Save outputs
    logger.info(f"Saving updated dataframe to {output_path}")
    df_with_csa.to_parquet(output_path, index=False)
    
    logger.info(f"Saving metadata to {metadata_path}")
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    logger.info(f"CSA Index construction complete. Range: [{metadata['index_range']['min']}, {metadata['index_range']['max']}]")
    
    return df_with_csa, metadata

if __name__ == "__main__":
    main()