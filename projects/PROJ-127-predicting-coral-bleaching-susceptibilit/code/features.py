"""
features.py - Feature engineering for coral bleaching susceptibility prediction.

Implements:
- Lagged environmental variables (rolling means)
- Interaction terms (DHW * thermal_tolerance)
- Definitional Circularity Check (DHW vs SST)
- Variance Inflation Factor (VIF) calculation and filtering
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import warnings

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

import config

# Ensure output directories exist
Path(config.DATA_PROCESSED_DIR).mkdir(parents=True, exist_ok=True)


def compute_lagged_features(df: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    """
    Compute lagged environmental variables (e.g., 30-day rolling mean SST).

    Assumes the DataFrame has a 'date' column (datetime) and numeric environmental columns.
    Sorts by date and applies rolling mean.

    Args:
        df: Input dataframe with 'date' and environmental columns.
        window_days: Size of the rolling window in days.

    Returns:
        DataFrame with new lagged columns (e.g., 'SST_30d_mean').
    """
    df = df.copy()
    if 'date' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'date' column for lagged feature calculation.")

    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Identify environmental columns (numeric, not ID columns)
    env_cols = [c for c in df.columns if c.lower() in ['sst', 'dhw', 'chl', 'par'] and pd.api.types.is_numeric_dtype(df[c])]

    if not env_cols:
        warnings.warn("No environmental columns found for lagged feature calculation.")
        return df

    # Compute rolling mean for each environmental column
    for col in env_cols:
        # Rolling window in rows approximates days if data is daily; if not, we use a fixed window size
        # For simplicity, assuming daily data or using a fixed row count that approximates the window
        # If data is not daily, this might need adjustment based on actual frequency
        rolling_col = f"{col}_{window_days}d_mean"
        # Use min_periods=1 to allow calculation at the start
        df[rolling_col] = df[col].rolling(window=window_days, min_periods=1).mean()

    return df


def compute_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute specific interaction terms: DHW * thermal_tolerance.

    Args:
        df: Input dataframe containing 'dhw' and 'thermal_tolerance' columns.

    Returns:
        DataFrame with new interaction column 'dhw_thermal_interaction'.
    """
    df = df.copy()
    required_cols = ['dhw', 'thermal_tolerance']
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns for interaction term: {missing}")

    # Handle potential NaNs in interaction
    df['dhw_thermal_interaction'] = df['dhw'] * df['thermal_tolerance']

    return df


def check_definitional_circularity(df: pd.DataFrame, sst_col: str = 'sst', dhw_col: str = 'dhw') -> tuple[bool, str]:
    """
    Check if DHW is derived from SST (definitional circularity).

    DHW (Degree Heating Weeks) is by definition derived from SST (SST - baseline).
    If both are present, this indicates circularity.

    Args:
        df: Input dataframe.
        sst_col: Name of the SST column.
        dhw_col: Name of the DHW column.

    Returns:
        Tuple of (is_circular: bool, message: str).
    """
    if sst_col not in df.columns or dhw_col not in df.columns:
        return False, "Columns not present to check circularity."

    # By definition, DHW is derived from SST.
    # We flag this as circular and recommend dropping DHW or using residuals.
    is_circular = True
    msg = (
        "DEFINITIONAL CIRCULARITY DETECTED: DHW is derived from SST. "
        "Including both as predictors will cause multicollinearity and overfitting. "
        "ACTION: Dropping DHW column and retaining SST, or using SST residuals. "
        "Decision logged for feature selection."
    )
    return is_circular, msg


def calculate_vif(df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all numeric predictors.

    Args:
        df: DataFrame containing numeric predictor columns.
        exclude_cols: List of column names to exclude from VIF calculation (e.g., IDs, targets).

    Returns:
        DataFrame with columns: 'feature', 'vif'.
    """
    if exclude_cols is None:
        exclude_cols = []

    # Select numeric columns
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude_cols]

    if len(numeric_cols) < 2:
        raise ValueError("Need at least two numeric columns to calculate VIF.")

    # Create a matrix for VIF calculation (handle NaNs by dropping rows)
    X = df[numeric_cols].dropna()

    if X.shape[0] == 0:
        raise ValueError("No valid rows after dropping NaNs for VIF calculation.")

    # Add constant for intercept
    X_with_const = sm.add_constant(X)

    vif_data = []
    for col in X_with_const.columns:
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            warnings.warn(f"Could not calculate VIF for {col}: {e}")

    return pd.DataFrame(vif_data)


def filter_high_vif(df: pd.DataFrame, vif_threshold: float = 5.0, exclude_cols: list = None) -> tuple[pd.DataFrame, list]:
    """
    Filter out features with VIF > threshold.

    Iteratively removes the feature with the highest VIF until all remaining features are below threshold.

    Args:
        df: Input DataFrame.
        vif_threshold: Maximum allowed VIF.
        exclude_cols: Columns to exclude from VIF calculation (e.g., target, IDs).

    Returns:
        Tuple of (filtered_df, dropped_features_list).
    """
    df = df.copy()
    if exclude_cols is None:
        exclude_cols = []

    dropped_features = []
    current_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude_cols]

    # Iterative VIF filtering
    while len(current_cols) > 1:
        vif_df = calculate_vif(df[current_cols])
        if vif_df.empty:
            break

        max_vif_row = vif_df.loc[vif_df['vif'].idxmax()]
        max_vif = max_vif_row['vif']
        feature = max_vif_row['feature']

        if max_vif <= vif_threshold:
            break

        # Drop the feature with highest VIF
        df = df.drop(columns=[feature])
        dropped_features.append(feature)
        current_cols.remove(feature)

    return df, dropped_features


def main():
    """
    Main execution flow for feature engineering.
    1. Load unified dataset (from ingest).
    2. Compute lagged features.
    3. Compute interaction terms.
    4. Perform Definitional Circularity Check.
    5. Calculate VIF and filter.
    6. Save outputs.
    """
    print("Starting feature engineering pipeline...")

    # Load unified dataset
    input_path = Path(config.DATA_PROCESSED_DIR) / "reef_species_unified.csv"
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("Please run ingest.py first to generate the unified dataset.")
        sys.exit(1)

    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")

    # 1. Lagged Features
    print("Computing lagged features...")
    try:
        df = compute_lagged_features(df)
        print(f"Added lagged features. New columns: {[c for c in df.columns if 'mean' in c]}")
    except Exception as e:
        print(f"Warning: Lagged feature calculation failed: {e}")

    # 2. Interaction Features
    print("Computing interaction features...")
    try:
        df = compute_interaction_features(df)
        print("Added interaction feature: dhw_thermal_interaction")
    except Exception as e:
        print(f"Warning: Interaction feature calculation failed: {e}")

    # 3. Definitional Circularity Check
    print("Performing Definitional Circularity Check...")
    is_circular, circular_msg = check_definitional_circularity(df)
    print(circular_msg)

    if is_circular:
        # Drop DHW to break circularity, keep SST
        if 'dhw' in df.columns:
            df = df.drop(columns=['dhw'])
            print("Action: Dropped 'dhw' column to resolve circularity.")

    # 4. VIF Calculation and Filtering
    print("Calculating VIF and filtering high-correlation features...")
    exclude_cols = ['bleaching_label', 'reef_id', 'species_id', 'date'] # Exclude target and IDs
    try:
        df_filtered, dropped = filter_high_vif(df, vif_threshold=5.0, exclude_cols=exclude_cols)
        print(f"VIF Filtering complete. Dropped {len(dropped)} features: {dropped}")
    except Exception as e:
        print(f"Warning: VIF filtering failed: {e}")
        df_filtered = df

    # Save outputs
    output_features_path = Path(config.DATA_PROCESSED_DIR) / "features.csv"
    output_filtered_path = Path(config.DATA_PROCESSED_DIR) / "filtered_features.csv"

    df_filtered.to_csv(output_features_path, index=False)
    print(f"Saved full feature set to {output_features_path}")

    # Save the filtered list (just the columns)
    filtered_cols = list(df_filtered.columns)
    pd.DataFrame({'feature': filtered_cols}).to_csv(output_filtered_path, index=False)
    print(f"Saved filtered feature list to {output_filtered_path}")

    print("Feature engineering complete.")


if __name__ == "__main__":
    main()
