import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import config for paths
import config

def compute_lagged_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute lagged environmental variables (e.g., 30-day rolling mean SST).
    
    Args:
        df: DataFrame with 'date' and environmental columns.
    
    Returns:
        DataFrame with added lagged feature columns.
    """
    df = df.copy()
    if 'date' not in df.columns:
        return df
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['reef_id', 'date'])
    
    # 30-day rolling mean for SST
    if 'sst' in df.columns:
        df['sst_30d_mean'] = df.groupby('reef_id')['sst'].transform(
            lambda x: x.rolling(window='30D', min_periods=1).mean()
        )
    
    # 30-day rolling mean for DHW (if present)
    if 'dhw' in df.columns:
        df['dhw_30d_mean'] = df.groupby('reef_id')['dhw'].transform(
            lambda x: x.rolling(window='30D', min_periods=1).mean()
        )
    
    return df

def compute_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute interaction term: DHW * thermal_tolerance.
    
    Args:
        df: DataFrame with 'dhw' and 'thermal_tolerance' columns.
    
    Returns:
        DataFrame with added interaction column.
    """
    df = df.copy()
    if 'dhw' in df.columns and 'thermal_tolerance' in df.columns:
        df['dhw_thermal_interaction'] = df['dhw'] * df['thermal_tolerance']
    return df

def check_definitional_circularity(df: pd.DataFrame, log_path: Path) -> pd.DataFrame:
    """
    Check if DHW is derived from SST (definitional circularity).
    If derived, drop DHW from the feature set.
    
    Args:
        df: Input DataFrame.
        log_path: Path to log the decision.
    
    Returns:
        DataFrame with DHW dropped if circularity is detected.
    """
    df = df.copy()
    decision = "KEEP"
    reason = "No circularity detected or DHW not derived from SST in this context."
    
    # Logic: In many datasets, DHW (Degree Heating Weeks) is accumulated from SST anomalies.
    # If both SST and DHW are present and highly correlated (>0.95) or if the spec says so,
    # we drop DHW to avoid leakage.
    # Based on T018 requirement: "If derived, drop DHW".
    # We assume the standard NOAA definition where DHW is derived from SST.
    
    if 'dhw' in df.columns and 'sst' in df.columns:
        # Check correlation as a heuristic if we can't inspect the source derivation logic
        # However, the task T018 explicitly says: "Verify if DHW is derived from SST. If derived, drop DHW."
        # Since DHW is by definition derived from SST anomalies (accumulated heat stress),
        # we strictly follow the instruction to drop it to prevent circularity.
        decision = "DROP"
        reason = "DHW is derived from SST (Degree Heating Weeks calculation). Dropping to prevent definitional circularity."
        df = df.drop(columns=['dhw'])
    
    # Log the decision
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        f.write(f"Definitional Circularity Check:\n")
        f.write(f"Decision: {decision}\n")
        f.write(f"Reason: {reason}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Add a flag column to the dataframe
    df['circularity_check_flag'] = decision
    return df

def calculate_vif(df: pd.DataFrame, feature_cols: list = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    
    Args:
        df: DataFrame containing features.
        feature_cols: List of columns to calculate VIF for. If None, uses all numeric columns.
    
    Returns:
        DataFrame with VIF values for each feature.
    """
    if feature_cols is None:
        # Select only numeric columns that are likely predictors (exclude target and IDs)
        exclude_cols = ['reef_id', 'species_id', 'bleaching_label', 'date', 
                        'circularity_check_flag', 'trait_missing_flag']
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns 
                        if c not in exclude_cols]
    
    vif_data = []
    for col in feature_cols:
        if col not in df.columns:
            continue
        # Handle constant columns
        if df[col].std() == 0:
            vif = float('inf')
        else:
            try:
                # VIF calculation requires a model matrix. We use a simple OLS approach via statsmodels
                # or manual calculation: VIF = 1 / (1 - R^2) where R^2 is from regressing col on others.
                # Using statsmodels is robust.
                from statsmodels.stats.outliers_influence import variance_inflation_factor
                X = df[feature_cols].values
                vif = variance_inflation_factor(X, feature_cols.index(col))
            except Exception:
                vif = float('inf')
        
        vif_data.append({'feature': col, 'vif': vif})
    
    return pd.DataFrame(vif_data)

def filter_high_vif(vif_df: pd.DataFrame, threshold: float = 5.0) -> list:
    """
    Filter features with VIF > threshold.
    
    Args:
        vif_df: DataFrame with 'feature' and 'vif' columns.
        threshold: VIF threshold (default 5.0).
    
    Returns:
        List of feature names to KEEP (VIF <= threshold).
    """
    keep_features = vif_df[vif_df['vif'] <= threshold]['feature'].tolist()
    return keep_features

def main():
    """
    Main execution for T019: VIF Calculation and Filtering.
    Reads unified dataset, calculates VIF, drops high VIF features, and saves result.
    """
    print("Starting T019: VIF Calculation and Filtering...")
    
    # Paths
    input_path = config.PROJECT_ROOT / "data" / "processed" / "reef_species_unified.csv"
    output_path = config.PROJECT_ROOT / "data" / "processed" / "filtered_features.csv"
    log_path = config.PROJECT_ROOT / "data" / "processed" / "vif_log.md"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                f"Please ensure T014 (merge) is complete.")
    
    # Load data
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")
    
    # Step 1: Compute Lagged Features (T017)
    df = compute_lagged_features(df)
    
    # Step 2: Compute Interaction Features (T017)
    df = compute_interaction_features(df)
    
    # Step 3: Check Definitional Circularity (T018)
    df = check_definitional_circularity(df, log_path)
    
    # Identify feature columns for VIF
    # Exclude non-predictor columns
    exclude_cols = ['reef_id', 'species_id', 'bleaching_label', 'date', 
                    'circularity_check_flag', 'trait_missing_flag']
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns 
                    if c not in exclude_cols]
    
    print(f"Calculating VIF for {len(feature_cols)} features...")
    
    # Step 4: Calculate VIF (T019)
    vif_df = calculate_vif(df, feature_cols)
    
    # Display VIF results
    print("\nVIF Results:")
    print(vif_df.sort_values(by='vif', ascending=False).to_string(index=False))
    
    # Step 5: Filter High VIF (T019)
    keep_features = filter_high_vif(vif_df, threshold=5.0)
    print(f"\nFeatures to KEEP (VIF <= 5): {len(keep_features)}")
    print(f"Features DROPPED (VIF > 5): {len(feature_cols) - len(keep_features)}")
    
    # Construct final DataFrame
    # Keep predictors + target + IDs
    final_cols = keep_features + [c for c in df.columns if c in ['reef_id', 'species_id', 'bleaching_label']]
    
    # Ensure we don't drop IDs or target
    final_df = df[final_cols].copy()
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"Saved filtered features to {output_path}")
    
    # Save VIF report as a separate CSV for analysis
    vif_report_path = config.PROJECT_ROOT / "data" / "processed" / "vif_report.csv"
    vif_df.to_csv(vif_report_path, index=False)
    print(f"Saved VIF report to {vif_report_path}")
    
    print("T019 completed successfully.")

if __name__ == "__main__":
    main()
