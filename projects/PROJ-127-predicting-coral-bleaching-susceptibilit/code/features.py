import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

def compute_lagged_features(df: pd.DataFrame, date_col: str = "date", target_col: str = "SST", lag_days: int = 30) -> pd.DataFrame:
    """
    Compute lagged environmental variables (e.g., 30-day rolling mean) for the specified target column.

    Args:
        df: Input dataframe with a date column and the target variable.
        date_col: Name of the date column.
        target_col: Name of the column to compute lags for.
        lag_days: Number of days for the rolling window.

    Returns:
        DataFrame with an additional column: f"{target_col}_lag_{lag_days}d"
    """
    df = df.copy()
    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in dataframe.")
    
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=[df.columns[0], date_col]) # Sort by location ID then date if available, else just date

    # Calculate rolling mean
    window_size = pd.Timedelta(days=lag_days)
    df[f"{target_col}_lag_{lag_days}d"] = df.groupby(df.columns[0])[target_col].transform(
        lambda x: x.rolling(window=window_size, min_periods=1).mean()
    )
    
    return df

def compute_interaction_features(df: pd.DataFrame, col1: str = "DHW", col2: str = "thermal_tolerance") -> pd.DataFrame:
    """
    Compute the specific interaction term: DHW * thermal_tolerance.

    Args:
        df: Input dataframe.
        col1: First feature name.
        col2: Second feature name.

    Returns:
        DataFrame with an additional column: f"{col1}_x_{col2}"
    """
    df = df.copy()
    if col1 not in df.columns or col2 not in df.columns:
        missing = [c for c in [col1, col2] if c not in df.columns]
        raise ValueError(f"Missing required columns for interaction: {missing}")
    
    df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
    return df

def check_definitional_circularity(df: pd.DataFrame, derived_col: str = "DHW", base_col: str = "SST") -> dict:
    """
    Check if a feature is derived from another (definitional circularity).
    For example, DHW is derived from SST.
    
    This function logs a warning if circularity is detected and suggests dropping the derived column
    or using residuals, depending on project policy.

    Args:
        df: Input dataframe.
        derived_col: Name of the potentially derived column.
        base_col: Name of the base column.

    Returns:
        Dictionary with 'is_circular' (bool), 'message' (str), and 'recommendation' (str).
    """
    result = {
        "is_circular": False,
        "message": "",
        "recommendation": ""
    }

    # In this specific domain, DHW (Degree Heating Weeks) is mathematically derived from SST.
    # We enforce a check based on known domain knowledge if both columns exist.
    if derived_col in df.columns and base_col in df.columns:
        result["is_circular"] = True
        result["message"] = f"Definitional Circularity Detected: '{derived_col}' is derived from '{base_col}'."
        result["recommendation"] = "Drop 'DHW' or use residuals to prevent data leakage. Proceeding with flag."
        warnings.warn(result["message"])
    
    return result

def calculate_vif(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.

    Args:
        df: Input dataframe.
        features: List of column names to calculate VIF for.

    Returns:
        DataFrame with columns 'feature' and 'VIF'.
    """
    # Add intercept for VIF calculation
    X = df[features].dropna()
    if X.empty:
        return pd.DataFrame(columns=['feature', 'VIF'])
    
    X = X.values
    # Add constant term for intercept
    from statsmodels.tools import add_constant
    X_const = add_constant(X)
    
    vif_data = []
    for i, col in enumerate(features):
        try:
            vif = variance_inflation_factor(X_const, i+1) # +1 because index 0 is constant
            vif_data.append({"feature": col, "VIF": vif})
        except Exception as e:
            warnings.warn(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({"feature": col, "VIF": np.nan})
    
    return pd.DataFrame(vif_data)

def filter_high_vif(df: pd.DataFrame, features: list, threshold: float = 5.0) -> tuple:
    """
    Filter features with VIF > threshold.

    Args:
        df: Input dataframe.
        features: List of all feature columns.
        threshold: VIF threshold (default 5.0).

    Returns:
        Tuple of (filtered_df, dropped_features_list).
    """
    vif_df = calculate_vif(df, features)
    
    high_vif_features = vif_df[vif_df['VIF'] > threshold]['feature'].tolist()
    low_vif_features = [f for f in features if f not in high_vif_features]
    
    dropped_features = high_vif_features
    
    # Filter dataframe
    # We only keep columns that are in low_vif_features plus any non-feature columns (like IDs/Targets)
    all_cols = set(df.columns)
    feature_cols = set(features)
    non_feature_cols = all_cols - feature_cols
    
    final_cols = list(non_feature_cols) + low_vif_features
    
    return df[final_cols], dropped_features

def main():
    """
    Main entry point for feature engineering pipeline.
    Reads data, computes lags, interactions, checks circularity, and filters VIF.
    Outputs to data/processed/features.csv and data/processed/filtered_features.csv.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / "data" / "processed" / "reef_species_unified.csv"
    output_features_path = base_dir / "data" / "processed" / "features.csv"
    output_filtered_path = base_dir / "data" / "processed" / "filtered_features.csv"
    circularity_log_path = base_dir / "data" / "processed" / "circularity_check.log"

    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}. Please run ingestion first.")
        sys.exit(1)

    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)

    # 1. Compute Lagged Features (30-day rolling mean SST)
    print("Computing lagged features (30-day rolling mean SST)...")
    df = compute_lagged_features(df, date_col="date", target_col="SST", lag_days=30)

    # 2. Compute Interaction Features (DHW * thermal_tolerance)
    print("Computing interaction features (DHW * thermal_tolerance)...")
    df = compute_interaction_features(df, col1="DHW", col2="thermal_tolerance")

    # 3. Check Definitional Circularity
    print("Checking definitional circularity...")
    circularity_result = check_definitional_circularity(df, derived_col="DHW", base_col="SST")
    
    # Save circularity check log
    with open(circularity_log_path, 'w') as f:
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Result: {circularity_result['message']}\n")
        f.write(f"Recommendation: {circularity_result['recommendation']}\n")
    
    # If circular, we might need to drop DHW later or handle it. 
    # For now, we proceed to VIF which will likely catch DHW if it's highly collinear with SST.

    # 4. Calculate VIF
    # Identify feature columns (exclude IDs, dates, targets, and non-numeric)
    # Assuming standard columns: reef_id, species_id, date, target, and numeric env/trait cols
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = ['reef_id', 'species_id', 'date', 'bleaching_label', 'susceptibility'] # Adjust based on actual schema
    feature_cols = [c for c in numeric_cols if c not in exclude_cols]

    print(f"Calculating VIF for {len(feature_cols)} features...")
    vif_results = calculate_vif(df, feature_cols)
    
    # Save raw VIF results
    vif_results.to_csv(base_dir / "data" / "processed" / "vif_results.csv", index=False)

    # 5. Filter High VIF
    print(f"Filtering features with VIF > 5.0...")
    df_filtered, dropped = filter_high_vif(df, feature_cols, threshold=5.0)

    # Save outputs
    df.to_csv(output_features_path, index=False)
    df_filtered.to_csv(output_filtered_path, index=False)

    print(f"Feature engineering complete.")
    print(f"  - Raw features saved to: {output_features_path}")
    print(f"  - Filtered features saved to: {output_filtered_path}")
    print(f"  - Dropped features (VIF > 5): {dropped}")

if __name__ == "__main__":
    main()