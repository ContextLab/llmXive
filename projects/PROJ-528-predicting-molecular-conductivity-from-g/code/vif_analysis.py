import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for numeric columns in a DataFrame.
    
    Args:
        df: DataFrame containing numeric features.
        exclude_cols: List of column names to exclude from VIF calculation (e.g., target, SMILES).
        
    Returns:
        DataFrame with columns 'feature' and 'vif'.
    """
    if exclude_cols is None:
        exclude_cols = []
        
    # Select only numeric columns not in exclude list
    numeric_df = df.select_dtypes(include=[np.number])
    if exclude_cols:
        numeric_df = numeric_df.drop(columns=[c for c in exclude_cols if c in numeric_df.columns], errors='ignore')
    
    if numeric_df.empty:
        logger.warning("No numeric features left to calculate VIF.")
        return pd.DataFrame(columns=['feature', 'vif'])
        
    # Remove columns with zero variance to avoid division by zero
    numeric_df = numeric_df.loc[:, numeric_df.var() > 0]
    
    if numeric_df.empty:
        logger.warning("All features have zero variance.")
        return pd.DataFrame(columns=['feature', 'vif'])

    vif_data = []
    for col in numeric_df.columns:
        try:
            vif = variance_inflation_factor(numeric_df.values, numeric_df.columns.get_loc(col))
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})
            
    return pd.DataFrame(vif_data)

def get_high_vif_features(vif_df: pd.DataFrame, threshold: float = 10.0) -> List[str]:
    """
    Identify features with VIF greater than the specified threshold.
    
    Args:
        vif_df: DataFrame with 'feature' and 'vif' columns.
        threshold: VIF threshold above which features are considered high.
        
    Returns:
        List of feature names with VIF > threshold.
    """
    if vif_df.empty:
        return []
    high_vif = vif_df[vif_df['vif'] > threshold]
    return high_vif['feature'].tolist()

def calculate_vif_pairwise(df: pd.DataFrame, feature_a: str, feature_b: str) -> float:
    """
    Calculate VIF for a specific pair of features (equivalent to 1/(1-R^2) for two variables).
    
    Args:
        df: DataFrame containing the features.
        feature_a: Name of the first feature.
        feature_b: Name of the second feature.
        
    Returns:
        VIF value for feature_a with respect to feature_b.
    """
    if feature_a not in df.columns or feature_b not in df.columns:
        raise ValueError(f"Columns {feature_a} or {feature_b} not found in DataFrame.")
        
    X = df[[feature_a, feature_b]].values
    try:
        vif_a = variance_inflation_factor(X, 0)
        return vif_a
    except Exception as e:
        logger.error(f"Error calculating pairwise VIF: {e}")
        return np.nan

def run_vif_analysis(
    df: pd.DataFrame, 
    exclude_cols: Optional[List[str]] = None, 
    threshold: float = 10.0
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Run full VIF analysis: calculate VIFs, identify high VIF features, and suggest removal order.
    
    Args:
        df: Input DataFrame.
        exclude_cols: Columns to exclude from analysis.
        threshold: VIF threshold for flagging high multicollinearity.
        
    Returns:
        Tuple of (vif_dataframe, list_of_high_vif_features, list_of_features_to_remove).
    """
    logger.info("Starting VIF analysis...")
    vif_df = calculate_vif(df, exclude_cols=exclude_cols)
    
    high_vif_features = get_high_vif_features(vif_df, threshold)
    
    features_to_remove = []
    current_df = df.copy()
    current_exclude = exclude_cols or []
    
    # Iteratively remove highest VIF feature until all are below threshold
    while True:
        vif_df_current = calculate_vif(current_df, exclude_cols=current_exclude)
        if vif_df_current.empty:
            break
            
        # Find max VIF
        max_vif_idx = vif_df_current['vif'].idxmax()
        max_vif_val = vif_df_current.loc[max_vif_idx, 'vif']
        
        if max_vif_val <= threshold:
            break
            
        feature_to_remove = vif_df_current.loc[max_vif_idx, 'feature']
        features_to_remove.append(feature_to_remove)
        
        # Remove from dataframe for next iteration
        if feature_to_remove in current_df.columns:
            current_df = current_df.drop(columns=[feature_to_remove])
            current_exclude.append(feature_to_remove)
            
        logger.debug(f"Removed {feature_to_remove} with VIF {max_vif_val:.2f}")
        
    logger.info(f"VIF analysis complete. Identified {len(high_vif_features)} high VIF features.")
    logger.info(f"Proposed removal sequence: {features_to_remove}")
    
    return vif_df, high_vif_features, features_to_remove