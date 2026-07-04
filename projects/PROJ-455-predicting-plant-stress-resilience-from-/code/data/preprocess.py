from typing import Optional
import pandas as pd
import numpy as np
from utils.logging import DataRejectionError, get_logger

logger = get_logger(__name__)

def check_missing_threshold(df: pd.DataFrame, threshold: float = 0.1) -> None:
    """
    Check if the percentage of missing values exceeds the threshold.
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed fraction of missing values (default 0.1)
        
    Raises:
        DataRejectionError: If missing values exceed the threshold
    """
    missing_pct = df.isnull().sum() / len(df)
    max_missing = missing_pct.max()
    
    if max_missing > threshold:
        logger.error(f"Missing data threshold exceeded: {max_missing:.2%} > {threshold:.2%}")
        raise DataRejectionError(f"Dataset rejected: Missing values ({max_missing:.2%}) exceed threshold ({threshold:.2%})")
    
    logger.info(f"Missing data check passed: {max_missing:.2%} <= {threshold:.2%}")

def impute_half_min(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace NaN values with half the column minimum for numeric columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with imputed values
    """
    df_imputed = df.copy()
    numeric_cols = df_imputed.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        col_min = df_imputed[col].min()
        if pd.isna(col_min) or col_min == 0:
            # If min is NaN or 0, use a small positive value or skip
            # Standard practice: use half of the smallest non-zero positive value if available
            non_zero_vals = df_imputed[col][df_imputed[col] > 0]
            if len(non_zero_vals) > 0:
                col_min = non_zero_vals.min()
            else:
                col_min = 0.0
        
        impute_val = col_min / 2.0
        df_imputed[col] = df_imputed[col].fillna(impute_val)
        logger.debug(f"Imputed column '{col}' with half-min: {impute_val}")
        
    return df_imputed

def normalize_tic_and_log(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Total Ion Current (TIC) normalization and natural log transformation.
    
    Steps:
    1. Calculate TIC (sum of all metabolite intensities per sample)
    2. Normalize each metabolite by TIC
    3. Apply natural log (ln) transformation with zero-handling
    
    Args:
        df: Input DataFrame with metabolite columns
        
    Returns:
        DataFrame with normalized and log-transformed values
    """
    df_processed = df.copy()
    numeric_cols = df_processed.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found for TIC normalization")
        return df_processed
    
    # Calculate TIC (sum across metabolite columns for each row)
    tic = df_processed[numeric_cols].sum(axis=1)
    
    # Avoid division by zero
    tic = tic.replace(0, np.nan)
    if tic.isna().all():
        logger.error("All TIC values are zero or NaN, cannot normalize")
        raise DataRejectionError("Cannot normalize: All TIC values are zero or NaN")
        
    # Normalize by TIC
    for col in numeric_cols:
        df_processed[col] = df_processed[col] / tic
        
    # Apply natural log transformation
    # Add small epsilon to avoid log(0) if any zeros remain after normalization
    epsilon = 1e-10
    for col in numeric_cols:
        # Ensure no negative values before log (shouldn't happen with TIC norm, but safe guard)
        df_processed[col] = df_processed[col].clip(lower=epsilon)
        df_processed[col] = np.log(df_processed[col])
        logger.debug(f"Applied ln transformation to column '{col}'")
        
    return df_processed

def aggregate_population(df: pd.DataFrame, group_cols: Optional[list] = None) -> pd.DataFrame:
    """
    Compute mean pre-stress and mean recovery per group if individual pairing is missing.
    
    This function handles scenarios where individual sample pairing (pre-stress vs post-stress
    for the same biological unit) is not available. It aggregates data at the population level
    by grouping samples based on provided columns (e.g., stress_type, treatment_group) and
    computing mean values for pre-stress metabolite profiles and recovery metrics.
    
    Args:
        df: Input DataFrame containing metabolite and recovery columns.
            Expected columns include:
            - Grouping columns (if group_cols is provided, otherwise infers from context)
            - Pre-stress metabolite columns (typically numeric columns not in recovery)
            - Recovery columns (e.g., 'recovery_index', 'biomass', 'survival')
        group_cols: List of column names to group by. If None, attempts to infer common
                    grouping columns like 'stress_type', 'treatment_group', or 'experiment_id'.
                    
    Returns:
        DataFrame with aggregated mean values per group.
        
    Raises:
        ValueError: If no valid grouping columns can be identified or if required
                    recovery columns are missing.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to aggregate_population")
        return df
    
    df_agg = df.copy()
    
    # Determine grouping columns
    if group_cols is None:
        # Infer potential grouping columns
        potential_groups = [col for col in df.columns if col in ['stress_type', 'treatment_group', 'experiment_id', 'genotype']]
        if not potential_groups:
            # Fallback: try to find categorical columns that aren't ID-like
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            potential_groups = [col for col in categorical_cols if len(df[col].unique()) > 1 and len(df[col].unique()) < len(df) * 0.9]
        
        if not potential_groups:
            raise ValueError("Could not determine grouping columns. Please provide 'group_cols' argument.")
        
        group_cols = potential_groups
        logger.info(f"Inferred grouping columns: {group_cols}")
    
    # Verify grouping columns exist
    missing_cols = [col for col in group_cols if col not in df_agg.columns]
    if missing_cols:
        raise ValueError(f"Grouping columns not found in DataFrame: {missing_cols}")
    
    # Identify numeric columns for aggregation (metabolites and recovery metrics)
    numeric_cols = df_agg.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic to separate recovery columns from metabolite columns
    # Recovery columns often have specific names
    recovery_keywords = ['recovery', 'biomass', 'survival', 'index', 'rate']
    recovery_cols = [col for col in numeric_cols if any(kw in col.lower() for kw in recovery_keywords)]
    metabolite_cols = [col for col in numeric_cols if col not in recovery_cols]
    
    # If no specific recovery columns found, assume the last few numeric columns are recovery
    # or rely on the presence of 'recovery_index' if it exists
    if not recovery_cols:
        if 'recovery_index' in df_agg.columns:
            recovery_cols = ['recovery_index']
        else:
            # Fallback: assume all numeric columns except metabolites (which we can't distinguish)
            # This is risky, so we log a warning
            logger.warning("Could not distinguish recovery columns from metabolite columns. Aggregating all numeric columns.")
            recovery_cols = numeric_cols
            metabolite_cols = []
    
    # Perform aggregation
    agg_dict = {col: 'mean' for col in metabolite_cols + recovery_cols}
    
    if not agg_dict:
        logger.warning("No columns found to aggregate.")
        return df_agg
        
    try:
        result = df_agg.groupby(group_cols).agg(agg_dict).reset_index()
        logger.info(f"Aggregated {len(df_agg)} rows into {len(result)} groups based on {group_cols}")
    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}")
        raise
        
    return result