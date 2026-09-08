import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import from config if needed for paths, though we use relative paths from tasks.md
# Assuming config.py is importable as 'import config'
try:
    import config
except ImportError:
    config = None

# Constants
VIF_THRESHOLD = 5.0
INPUT_FEATURES_FILE = "data/processed/features.csv"
OUTPUT_FILTERED_FEATURES_FILE = "data/processed/filtered_features.csv"

def compute_lagged_features(df: pd.DataFrame, target_col: str, window: int = 30) -> pd.DataFrame:
    """
    Compute lagged environmental variables (rolling mean) for a specific column.
    """
    if target_col not in df.columns:
        warnings.warn(f"Column {target_col} not found in dataframe for lagging.")
        return df

    df = df.copy()
    # Ensure sorting by time if a date column exists, otherwise assume order
    if 'date' in df.columns:
        df = df.sort_values('date')
    
    df[f'{target_col}_lagged_{window}d'] = df[target_col].rolling(window=window, min_periods=1).mean()
    return df

def compute_interaction_features(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """
    Compute interaction term: col1 * col2.
    Specific task: DHW * thermal_tolerance
    """
    if col1 not in df.columns or col2 not in df.columns:
        missing = [c for c in [col1, col2] if c not in df.columns]
        warnings.warn(f"Columns {missing} not found for interaction feature.")
        return df

    df = df.copy()
    interaction_name = f"{col1}_x_{col2}"
    df[interaction_name] = df[col1] * df[col2]
    return df

def check_definitional_circularity(df: pd.DataFrame, derived_col: str, source_col: str) -> pd.DataFrame:
    """
    Check if a feature is definitionally circular (derived from another).
    If derived_col is derived from source_col, we drop derived_col or use residuals.
    For this task, if DHW is derived from SST, we drop DHW.
    """
    # In a real scenario, we would check the correlation or metadata.
    # Per task T018, we assume the decision was made to drop DHW if derived.
    # Here we implement the logic to drop it if source exists and we decide to drop.
    # For this implementation, we assume DHW is derived from SST and drop DHW.
    if derived_col in df.columns and source_col in df.columns:
        # Simple heuristic: if they are highly correlated, assume circularity
        corr = df[derived_col].corr(df[source_col])
        if abs(corr) > 0.95:
            warnings.warn(f"High correlation ({corr:.2f}) between {derived_col} and {source_col}. Dropping {derived_col} to avoid circularity.")
            df = df.drop(columns=[derived_col])
    
    return df

def calculate_vif(df: pd.DataFrame, feature_columns: list = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors in the dataframe.
    Returns a DataFrame with feature names and their VIF scores.
    """
    if feature_columns is None:
        # Exclude non-numeric and target columns (common targets: 'bleaching_label', 'susceptibility')
        exclude_cols = ['reef_id', 'species_id', 'date', 'bleaching_label', 'susceptibility', 'lat', 'lon']
        feature_columns = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude_cols]
    
    if len(feature_columns) == 0:
        return pd.DataFrame(columns=['feature', 'vif'])

    # Prepare matrix
    X = df[feature_columns].copy()
    X = X.dropna() # VIF calculation requires no NaNs
    
    if X.empty:
        return pd.DataFrame(columns=['feature', 'vif'])

    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    vif_data = []
    for col in X_const.columns:
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, X_const.columns.get_loc(col))
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            warnings.warn(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})

    return pd.DataFrame(vif_data)

def filter_high_vif(vif_df: pd.DataFrame, threshold: float = VIF_THRESHOLD) -> list:
    """
    Filter features with VIF > threshold.
    Returns a list of features to KEEP (VIF <= threshold).
    """
    if vif_df.empty:
        return []
    
    # Filter rows where VIF <= threshold
    filtered = vif_df[vif_df['vif'] <= threshold]
    return filtered['feature'].tolist()

def main():
    """
    Main execution for Task T019: Calculate VIF and filter features.
    """
    # Define paths relative to project root
    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / INPUT_FEATURES_FILE
    output_path = base_dir / OUTPUT_FILTERED_FEATURES_FILE

    if not input_path.exists():
        print(f"Error: Input file {input_path} not found. Run previous tasks first.")
        sys.exit(1)

    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)

    # Ensure numeric columns are numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate VIF
    print("Calculating VIF for all predictors...")
    vif_df = calculate_vif(df)
    
    if not vif_df.empty:
        print(f"VIF Calculation Results:\n{vif_df.sort_values('vif', ascending=False)}")
        
        # Determine features to keep
        keep_features = filter_high_vif(vif_df, VIF_THRESHOLD)
        print(f"Features to keep (VIF <= {VIF_THRESHOLD}): {len(keep_features)}")
        print(f"Features dropped (VIF > {VIF_THRESHOLD}): {len(vif_df) - len(keep_features)}")
    else:
        print("No numeric features found to calculate VIF. Keeping all columns.")
        keep_features = list(df.select_dtypes(include=[np.number]).columns)

    # Filter dataframe
    # We need to keep non-numeric columns (IDs, dates) as well
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    final_columns = non_numeric_cols + keep_features
    
    # Intersect with actual columns to avoid errors
    final_columns = [c for c in final_columns if c in df.columns]
    
    filtered_df = df[final_columns]

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    print(f"Filtered features saved to {output_path}")

    # Also save the VIF report for reference
    vif_report_path = base_dir / "data" / "processed" / "vif_report.csv"
    if not vif_df.empty:
        vif_df.to_csv(vif_report_path, index=False)
        print(f"VIF report saved to {vif_report_path}")

if __name__ == "__main__":
    main()
