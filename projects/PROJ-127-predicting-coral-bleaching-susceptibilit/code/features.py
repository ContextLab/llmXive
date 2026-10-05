import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

import config

def compute_lagged_features(df: pd.DataFrame, target_col: str, lags: list, date_col: str = 'date') -> pd.DataFrame:
    """
    Compute lagged features for a given target column.
    
    Args:
        df: Input DataFrame
        target_col: Column to create lags for
        lags: List of lag values (e.g., [1, 7, 30])
        date_col: Name of the date column for sorting
    
    Returns:
        DataFrame with new lagged columns
    """
    df = df.sort_values(by=[config.GEO_ID_COL, date_col]).copy()
    
    for lag in lags:
        new_col_name = f"{target_col}_lag_{lag}"
        df[new_col_name] = df.groupby(config.GEO_ID_COL)[target_col].shift(lag)
    
    return df

def compute_interaction_features(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """
    Compute interaction term between two columns.
    
    Args:
        df: Input DataFrame
        col1: First column name
        col2: Second column name
    
    Returns:
        DataFrame with new interaction column
    """
    interaction_name = f"{col1}_x_{col2}"
    df[interaction_name] = df[col1] * df[col2]
    return df

def check_definitional_circularity(df: pd.DataFrame, features: list) -> dict:
    """
    Check if any feature is derived from another (definitional circularity).
    
    Args:
        df: Input DataFrame
        features: List of feature columns to check
    
    Returns:
        Dictionary with circularity findings and flags
    """
    findings = {
        'circular_pairs': [],
        'warnings': [],
        'flags': {}
    }
    
    # Check for DHW derived from SST (common in oceanography)
    # DHW (Degree Heating Weeks) is typically derived from SST anomalies
    if 'DHW' in features and 'SST' in features:
        findings['circular_pairs'].append(('SST', 'DHW'))
        findings['warnings'].append("DHW is likely derived from SST. Flagging for potential removal.")
        findings['flags']['DHW'] = 'derived_from_SST'
    
    # Log warning if circularity detected
    if findings['circular_pairs']:
        warnings.warn(f"Definitional circularity detected: {findings['circular_pairs']}")
        # Mark the derived feature in the dataframe if it exists
        for pair in findings['circular_pairs']:
            if pair[1] in df.columns:
                df[f"{pair[1]}_circular_flag"] = 1
    
    return findings

def calculate_vif(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    
    Args:
        df: Input DataFrame
        features: List of feature columns to calculate VIF for
    
    Returns:
        DataFrame with columns: feature, vif
    """
    # Remove any constant columns or columns with zero variance
    valid_features = []
    for col in features:
        if col in df.columns and df[col].nunique() > 1:
            valid_features.append(col)
    
    if len(valid_features) < 2:
        raise ValueError("Need at least 2 features with variance to calculate VIF.")
    
    # Add constant column for intercept (statsmodels requires it)
    X = df[valid_features].dropna()
    if X.empty:
        raise ValueError("No valid data points after dropping NaNs.")
    
    # VIF calculation requires a constant term
    X_with_const = sm.add_constant(X)
    
    vif_data = []
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue
        vif = variance_inflation_factor(X_with_const.values, i)
        vif_data.append({
            'feature': col,
            'vif': vif
        })
    
    return pd.DataFrame(vif_data)

def filter_high_vif(vif_df: pd.DataFrame, threshold: float = 5.0) -> tuple:
    """
    Filter out features with VIF above a threshold.
    
    Args:
        vif_df: DataFrame with 'feature' and 'vif' columns
        threshold: VIF threshold for removal (default 5.0)
    
    Returns:
        Tuple of (filtered_features_list, dropped_features_list)
    """
    high_vif = vif_df[vif_df['vif'] > threshold]
    dropped = high_vif['feature'].tolist()
    kept = vif_df[vif_df['vif'] <= threshold]['feature'].tolist()
    
    return kept, dropped

def main():
    """
    Main function to execute VIF analysis and filtering.
    
    Steps:
    1. Load the unified dataset
    2. Compute lagged features and interaction terms
    3. Check for definitional circularity
    4. Calculate VIF for all predictors
    5. Drop features with VIF > 5
    6. Save filtered feature list and feature names
    """
    # Ensure output directory exists
    data_dir = Path(config.PROCESSED_DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load unified dataset
    unified_path = Path(config.PROCESSED_DATA_DIR) / 'reef_species_unified.csv'
    if not unified_path.exists():
        raise FileNotFoundError(f"Unified dataset not found at {unified_path}. Run T009 first.")
    
    df = pd.read_csv(unified_path)
    
    # Define feature columns (exclude non-feature columns)
    exclude_cols = [config.GEO_ID_COL, 'species_id', 'date', 'bleaching_label', 'trait_missing_flag']
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    # Step 1: Compute lagged features (example: SST lag 7, 30)
    # Assuming 'date' column exists, otherwise skip
    if 'date' in df.columns:
        df = compute_lagged_features(df, 'SST', [7, 30], 'date')
        feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    # Step 2: Compute interaction features (DHW * thermal_tolerance)
    if 'DHW' in df.columns and 'thermal_tolerance' in df.columns:
        df = compute_interaction_features(df, 'DHW', 'thermal_tolerance')
        feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    # Step 3: Check definitional circularity
    circularity_report = check_definitional_circularity(df, feature_cols)
    
    # Step 4: Calculate VIF
    vif_df = calculate_vif(df, feature_cols)
    
    # Save VIF results
    vif_output_path = data_dir / 'vif_analysis.csv'
    vif_df.to_csv(vif_output_path, index=False)
    print(f"VIF analysis saved to {vif_output_path}")
    
    # Step 5: Filter high VIF features
    kept_features, dropped_features = filter_high_vif(vif_df, threshold=5.0)
    
    # Remove circularity flags from kept features if they exist
    kept_features = [f for f in kept_features if not f.endswith('_circular_flag')]
    
    # Step 6: Save outputs
    # Save filtered feature list as CSV
    filtered_features_df = pd.DataFrame({
        'feature': kept_features,
        'status': ['kept'] * len(kept_features)
    })
    filtered_features_path = data_dir / 'filtered_features.csv'
    filtered_features_df.to_csv(filtered_features_path, index=False)
    print(f"Filtered features saved to {filtered_features_path}")
    
    # Save feature list as text file
    feature_list_path = data_dir / 'feature_list.txt'
    with open(feature_list_path, 'w') as f:
        for feature in kept_features:
            f.write(f"{feature}\n")
    print(f"Feature list saved to {feature_list_path}")
    
    # Log dropped features
    if dropped_features:
        print(f"Dropped {len(dropped_features)} features due to VIF > 5: {dropped_features}")
    
    # Log circularity warnings
    if circularity_report['warnings']:
        for warning in circularity_report['warnings']:
            print(f"Warning: {warning}")
    
    return kept_features, dropped_features

if __name__ == '__main__':
    main()
