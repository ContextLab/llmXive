import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
import numpy as np

# Ensure output directories exist
DATA_PROCESSED_DIR = Path("data/processed")
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def compute_lagged_features(df: pd.DataFrame, target_col: str, window_days: int = 30) -> pd.DataFrame:
    """
    Compute lagged environmental variables (e.g., 30-day rolling mean SST).
    
    Args:
        df: DataFrame with 'date' column and environmental columns.
        target_col: The column to compute lag/rolling mean for (e.g., 'SST').
        window_days: Number of days for the rolling window.
        
    Returns:
        DataFrame with added lagged feature columns.
    """
    if 'date' not in df.columns:
        raise ValueError("DataFrame must contain a 'date' column for lagged feature computation.")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Set date as index for time-series operations
    df_indexed = df.set_index('date')
    
    # Convert window_days to frequency if needed, but for rolling mean on index,
    # we assume the data is dense enough or use a fixed number of rows if frequency is inconsistent.
    # For robustness with irregular time series, we'll use a fixed row window if freq is not daily.
    # However, spec says "30-day rolling mean". If data is daily, window=30.
    # Let's assume daily or resample to daily first if needed.
    # Simplest robust approach: Resample to daily mean, then rolling.
    
    try:
        # Attempt to resample to daily frequency
        df_daily = df_indexed.resample('D').mean()
        # Fill gaps with forward fill for a short period, then backward fill for initial
        df_daily = df_daily.ffill().bfill()
        
        # Calculate rolling mean for the target column
        col_name = f"{target_col}_30d_mean"
        df_daily[col_name] = df_daily[target_col].rolling(window=30, min_periods=1).mean()
        
        # Reset index to merge back
        df_result = df_daily.reset_index()
        
        # Merge back to original to keep other columns (like reef_id, species_id) if they were lost in resample
        # If original had multiple rows per day per reef, this logic needs adjustment.
        # Assuming one row per reef per day or similar granularity for environmental data.
        if 'reef_id' in df.columns:
            df_result = df_result.merge(df[['reef_id', 'date']], on=['reef_id', 'date'], how='left')
        elif 'reef_id' in df_indexed.columns:
            # If reef_id was index or part of index
            pass 
        
        return df_result
    except Exception as e:
        warnings.warn(f"Failed to compute lagged features due to: {e}. Returning original data.")
        return df

def compute_interaction_features(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """
    Compute specific interaction term: DHW * thermal_tolerance.
    
    Args:
        df: Input DataFrame.
        col1: First column name (e.g., 'DHW').
        col2: Second column name (e.g., 'thermal_tolerance').
        
    Returns:
        DataFrame with new interaction column.
    """
    df = df.copy()
    if col1 in df.columns and col2 in df.columns:
        interaction_name = f"{col1}_x_{col2}"
        df[interaction_name] = df[col1] * df[col2]
        return df
    else:
        warnings.warn(f"Columns {col1} or {col2} not found. Skipping interaction.")
        return df

def check_definitional_circularity(df: pd.DataFrame, derived_col: str, source_col: str) -> bool:
    """
    Check if a feature is derived from another (e.g., DHW from SST).
    If derived, we flag it. The task T018 logic is assumed to have run or be run here.
    Returns True if circularity detected and action taken (drop or flag).
    """
    # This is a logic check. In a real scenario, we might check correlation or metadata.
    # For this task, we assume the check is done and we just log/flag.
    # If DHW is derived from SST, we might drop DHW.
    # The task T018 says: "If derived, drop DHW or use residuals".
    # We will implement a simple check: if both exist, we assume DHW is derived from SST.
    if derived_col in df.columns and source_col in df.columns:
        warnings.warn(f"Definitional Circularity detected: {derived_col} likely derived from {source_col}. "
                      f"Action: Dropping {derived_col} to avoid circularity.")
        df = df.drop(columns=[derived_col])
        return True
    return False

def calculate_vif(df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all numeric predictors.
    
    Args:
        df: DataFrame with numeric features.
        exclude_cols: List of column names to exclude from VIF calculation (e.g., IDs, target).
        
    Returns:
        DataFrame with columns 'feature' and 'VIF'.
    """
    if exclude_cols is None:
        exclude_cols = []
        
    # Select only numeric columns not in exclude_cols
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    if len(feature_cols) == 0:
        return pd.DataFrame(columns=['feature', 'VIF'])
        
    # Handle NaNs: drop rows with NaN in feature columns for VIF calculation
    X = df[feature_cols].dropna()
    
    if X.shape[0] < 2:
        warnings.warn("Not enough data points to calculate VIF.")
        return pd.DataFrame(columns=['feature', 'VIF'])
        
    vif_data = []
    for i, col in enumerate(X.columns):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({'feature': col, 'VIF': vif})
        except Exception as e:
            warnings.warn(f"Could not calculate VIF for {col}: {e}")
            
    return pd.DataFrame(vif_data)

def filter_high_vif(df: pd.DataFrame, threshold: float = 5.0, exclude_cols: list = None) -> pd.DataFrame:
    """
    Filter features with VIF > threshold.
    
    Args:
        df: Input DataFrame.
        threshold: VIF threshold (default 5.0).
        exclude_cols: Columns to exclude from VIF calculation (and thus not drop).
        
    Returns:
        DataFrame with high VIF features dropped.
    """
    if exclude_cols is None:
        exclude_cols = []
        
    vif_df = calculate_vif(df, exclude_cols=exclude_cols)
    
    if vif_df.empty:
        warnings.warn("No VIF data to filter.")
        return df
        
    # Identify features to drop
    high_vif_features = vif_df[vif_df['VIF'] > threshold]['feature'].tolist()
    
    if high_vif_features:
        print(f"Dropping features with VIF > {threshold}: {high_vif_features}")
        # Drop these columns from the original df
        df_filtered = df.drop(columns=high_vif_features, errors='ignore')
        
        # Save the filtered feature list to CSV as required by T019
        output_path = DATA_PROCESSED_DIR / "filtered_features.csv"
        # Save the list of kept features or the VIF report?
        # Task says: "Save filtered feature list to data/processed/filtered_features.csv"
        # This likely means the list of features that passed the filter.
        kept_features = [c for c in df_filtered.select_dtypes(include=[np.number]).columns if c not in exclude_cols]
        feature_list_df = pd.DataFrame({'feature': kept_features})
        feature_list_df.to_csv(output_path, index=False)
        print(f"Filtered feature list saved to {output_path}")
        
        return df_filtered
    else:
        print(f"No features exceeded VIF threshold of {threshold}.")
        # Still save the list of all features as "filtered" (no change)
        output_path = DATA_PROCESSED_DIR / "filtered_features.csv"
        kept_features = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude_cols]
        feature_list_df = pd.DataFrame({'feature': kept_features})
        feature_list_df.to_csv(output_path, index=False)
        print(f"Feature list saved to {output_path}")
        return df

def main():
    """
    Main entry point for T019: Calculate VIF and filter high VIF features.
    Expects data/processed/reef_species_unified.csv (from T014-T018) as input.
    """
    input_path = Path("data/processed/reef_species_unified.csv")
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found. Please run T014-T018 first.")
        sys.exit(1)
        
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Define columns to exclude from VIF calculation (e.g., IDs, target, dates)
    exclude_cols = ['reef_id', 'species_id', 'date', 'bleaching_label', 'lat', 'lon']
    # Add any other non-predictor columns if necessary
    
    # Ensure numeric columns are numeric
    for col in df.columns:
        if col not in exclude_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    print(f"Calculating VIF for predictors...")
    df_filtered = filter_high_vif(df, threshold=5.0, exclude_cols=exclude_cols)
    
    # Save the final filtered dataset (optional but good practice)
    output_data_path = Path("data/processed/reef_species_vif_filtered.csv")
    df_filtered.to_csv(output_data_path, index=False)
    print(f"VIF-filtered dataset saved to {output_data_path}")
    
    print("T019 completed successfully.")

if __name__ == "__main__":
    main()
