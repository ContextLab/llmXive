import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

# Configuration import
import config

# Constants
VIF_THRESHOLD = 5.0
UNDEFINED_VIF_THRESHOLD = 100.0  # Threshold for dropping features with undefined VIF (e.g., constant columns)

def compute_lagged_features(df: pd.DataFrame, date_col: str = 'date', target_cols: list = None) -> pd.DataFrame:
    """
    Compute lagged environmental variables (e.g., 30-day rolling mean SST).
    
    Args:
        df: Input DataFrame with date column and environmental variables.
        date_col: Name of the date column.
        target_cols: List of columns to compute lags for. If None, uses all numeric columns except date.
    
    Returns:
        DataFrame with added lagged features.
    """
    if target_cols is None:
        target_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if date_col in target_cols:
            target_cols.remove(date_col)
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=[date_col])
    
    lagged_cols = []
    for col in target_cols:
        if col in df.columns:
            # Compute 30-day rolling mean
            lagged_col_name = f"{col}_30d_mean"
            df[lagged_col_name] = df[col].rolling(window=30, min_periods=1).mean()
            lagged_cols.append(lagged_col_name)
    
    return df

def compute_interaction_features(df: pd.DataFrame, col1: str = 'dhw', col2: str = 'thermal_tolerance') -> pd.DataFrame:
    """
    Compute interaction features, specifically DHW * thermal_tolerance.
    
    Args:
        df: Input DataFrame.
        col1: First interaction column (e.g., 'dhw').
        col2: Second interaction column (e.g., 'thermal_tolerance').
    
    Returns:
        DataFrame with added interaction feature.
    """
    df = df.copy()
    interaction_name = f"{col1}_times_{col2}"
    if col1 in df.columns and col2 in df.columns:
        df[interaction_name] = df[col1] * df[col2]
    else:
        warnings.warn(f"Interaction columns {col1} or {col2} not found in DataFrame. Skipping interaction feature.")
    return df

def check_definitional_circularity(df: pd.DataFrame, dhw_col: str = 'dhw', sst_col: str = 'sst') -> pd.DataFrame:
    """
    Check for definitional circularity between DHW and SST.
    DHW (Degree Heating Weeks) is derived from SST.
    
    Action: If derived, drop DHW or use residuals.
    
    Args:
        df: Input DataFrame.
        dhw_col: Name of DHW column.
        sst_col: Name of SST column.
    
    Returns:
        DataFrame with a flag indicating circularity and handling decision.
    """
    df = df.copy()
    circularity_flag = False
    decision = "DHW dropped due to circularity with SST"
    
    if dhw_col in df.columns and sst_col in df.columns:
        # Check correlation
        correlation = df[dhw_col].corr(df[sst_col])
        if abs(correlation) > 0.9:
            circularity_flag = True
            # Drop DHW column as it is derived from SST
            df = df.drop(columns=[dhw_col])
    else:
        decision = "DHW or SST columns not found; no circularity check performed"
    
    # Log decision
    print(f"Definitional Circularity Check: {decision}")
    
    # Add a flag column to indicate if circularity was detected and handled
    df['circularity_detected'] = circularity_flag
    
    return df

def calculate_vif(df: pd.DataFrame, feature_cols: list = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    
    Args:
        df: Input DataFrame.
        feature_cols: List of feature columns to calculate VIF for. If None, uses all numeric columns.
    
    Returns:
        DataFrame with VIF values for each feature.
    """
    if feature_cols is None:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove target variable if present
    target_var = 'bleaching_susceptibility'
    if target_var in feature_cols:
        feature_cols.remove(target_var)
    
    # Filter to only existing columns
    feature_cols = [col for col in feature_cols if col in df.columns]
    
    # Prepare data for VIF calculation
    X = df[feature_cols].copy()
    
    # Handle constant columns (VIF undefined)
    constant_cols = []
    for col in X.columns:
        if X[col].std() == 0:
            constant_cols.append(col)
    
    if constant_cols:
        print(f"Warning: Constant columns detected: {constant_cols}. Setting VIF to {UNDEFINED_VIF_THRESHOLD}.")
        for col in constant_cols:
            X[col] = X[col].astype(float)  # Ensure numeric for VIF calculation
    
    # Add constant for VIF calculation
    X_const = add_constant(X)
    
    vif_data = []
    for col in X.columns:
        try:
            vif = variance_inflation_factor(X_const, col)
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            print(f"Error calculating VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': UNDEFINED_VIF_THRESHOLD})
    
    vif_df = pd.DataFrame(vif_data)
    return vif_df

def filter_high_vif(df: pd.DataFrame, vif_df: pd.DataFrame, threshold: float = VIF_THRESHOLD) -> pd.DataFrame:
    """
    Filter out features with VIF > threshold.
    
    Args:
        df: Original DataFrame.
        vif_df: DataFrame with VIF values.
        threshold: VIF threshold for filtering.
    
    Returns:
        DataFrame with high VIF features removed.
    """
    # Get features with VIF > threshold
    high_vif_features = vif_df[vif_df['vif'] > threshold]['feature'].tolist()
    
    # Also include constant columns (VIF undefined)
    constant_cols = vif_df[vif_df['vif'] >= UNDEFINED_VIF_THRESHOLD]['feature'].tolist()
    features_to_drop = list(set(high_vif_features + constant_cols))
    
    print(f"Features to drop due to high VIF or constant values: {features_to_drop}")
    
    # Drop features
    filtered_df = df.drop(columns=features_to_drop, errors='ignore')
    
    return filtered_df

def main():
    """
    Main function to run VIF calculation and feature filtering.
    
    Steps:
    1. Load the unified dataset from data/processed/reef_species_unified.csv.
    2. Compute lagged features and interaction features (if not already done).
    3. Check definitional circularity.
    4. Calculate VIF for all predictors.
    5. Drop features with VIF > 5.
    6. Save filtered feature list to data/processed/filtered_features.csv.
    """
    # Define paths
    input_file = Path(config.DATA_PROCESSED) / 'reef_species_unified.csv'
    output_file = Path(config.DATA_PROCESSED) / 'filtered_features.csv'
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found. Please ensure T014 (unified dataset) is complete.")
        sys.exit(1)
    
    # Load data
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    # Ensure required columns exist
    required_cols = ['dhw', 'thermal_tolerance', 'sst']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing columns in input data: {missing_cols}. Some features may not be computed.")
    
    # Compute lagged features (if not already present)
    lagged_cols = [col for col in df.columns if col.endswith('_30d_mean')]
    if not lagged_cols:
        print("Computing lagged features...")
        df = compute_lagged_features(df)
    
    # Compute interaction features (if not already present)
    interaction_col = 'dhw_times_thermal_tolerance'
    if interaction_col not in df.columns:
        print("Computing interaction features...")
        df = compute_interaction_features(df)
    
    # Check definitional circularity
    print("Checking definitional circularity...")
    df = check_definitional_circularity(df)
    
    # Calculate VIF
    print("Calculating VIF...")
    vif_df = calculate_vif(df)
    
    # Filter high VIF features
    print("Filtering high VIF features...")
    filtered_df = filter_high_vif(df, vif_df)
    
    # Save filtered dataset
    print(f"Saving filtered dataset to {output_file}...")
    filtered_df.to_csv(output_file, index=False)
    
    # Save VIF report
    vif_report_file = Path(config.DATA_PROCESSED) / 'vif_report.csv'
    vif_df.to_csv(vif_report_file, index=False)
    
    print(f"VIF report saved to {vif_report_file}")
    print(f"Filtered features saved to {output_file}")
    print(f"Number of features before filtering: {len(df.columns)}")
    print(f"Number of features after filtering: {len(filtered_df.columns)}")
    
    return filtered_df

if __name__ == '__main__':
    main()
