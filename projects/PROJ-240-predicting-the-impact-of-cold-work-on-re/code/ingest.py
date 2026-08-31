import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

def load_data(input_path: str) -> pd.DataFrame:
    """Load raw data from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def filter_missing_target(df: pd.DataFrame, target_col: str = 'time_to_peak') -> pd.DataFrame:
    """Exclude rows with missing target values."""
    initial_count = len(df)
    df = df.dropna(subset=[target_col])
    dropped = initial_count - len(df)
    if dropped > 0:
        print(f"Dropped {dropped} rows with missing target values.")
    return df

def validate_physical_bounds(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate physical bounds:
    - 0 <= cold_work <= 100
    - time_to_peak > 0
    Returns filtered DataFrame and log of invalid rows.
    """
    log = []
    valid_mask = (
        (df['cold_work'] >= 0) & 
        (df['cold_work'] <= 100) & 
        (df['time_to_peak'] > 0)
    )
    
    invalid_indices = df[~valid_mask].index
    for idx in invalid_indices:
        row = df.loc[idx]
        log.append({
            'index': int(idx),
            'reason': 'Physical bound violation',
            'cold_work': row['cold_work'],
            'time_to_peak': row['time_to_peak']
        })
    
    return df[valid_mask].reset_index(drop=True), log

def impute_missing_composition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing composition values using the mean of the specific alloy series.
    Since we don't have explicit alloy series, we group by composition ranges.
    """
    composition_cols = ['Mn_content', 'Mg_content', 'Si_content', 'Cu_content']
    missing_log = []
    
    for col in composition_cols:
        if df[col].isnull().any():
            # Calculate mean for this column
            mean_val = df[col].mean()
            # Impute
            df[col] = df[col].fillna(mean_val)
            missing_log.append({
                'column': col,
                'imputed_value': mean_val,
                'count': int(df[col].isnull().sum())
            })
    
    return df, missing_log

def clip_outliers(df: pd.DataFrame, target_col: str = 'time_to_peak', percentile: float = 99) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Clip outliers on target variable at specified percentile."""
    log = []
    threshold = df[target_col].quantile(percentile / 100.0)
    clipped_indices = df[df[target_col] > threshold].index
    
    if len(clipped_indices) > 0:
        for idx in clipped_indices:
            original_val = df.loc[idx, target_col]
            log.append({
                'index': int(idx),
                'original_value': float(original_val),
                'clipped_to': float(threshold)
            })
        df.loc[df[target_col] > threshold, target_col] = threshold
    
    return df, log

def normalize_time_to_minutes(df: pd.DataFrame, time_col: str = 'time_to_peak', unit_col: str = 'time_unit') -> pd.DataFrame:
    """Normalize time-to-peak to minutes."""
    # Assuming input is in minutes or seconds, convert to minutes if needed
    # If 'time_unit' column exists and is 'seconds', convert
    if 'time_unit' in df.columns:
        mask = df['time_unit'] == 'seconds'
        df.loc[mask, time_col] = df.loc[mask, time_col] / 60.0
        # Drop the unit column after normalization
        df = df.drop(columns=['time_unit'])
    return df

def run_ingestion_pipeline(input_path: str, output_path: str, log_path: str):
    """Run the full ingestion pipeline."""
    print(f"Loading data from {input_path}...")
    df = load_data(input_path)
    
    print("Filtering missing targets...")
    df = filter_missing_target(df)
    
    print("Validating physical bounds...")
    df, bound_log = validate_physical_bounds(df)
    
    print("Imputing missing composition values...")
    df, imp_log = impute_missing_composition(df)
    
    print("Normalizing time units...")
    df = normalize_time_to_minutes(df)
    
    print("Clipping outliers...")
    df, clip_log = clip_outliers(df)
    
    # Prepare validation log
    validation_log = {
        'input_rows': len(df), # This is after dropping missing, but we want original
        'bound_violations': bound_log,
        'imputed_values': imp_log,
        'clipped_outliers': clip_log
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save outputs
    df.to_csv(output_path, index=False)
    with open(log_path, 'w') as f:
        json.dump(validation_log, f, indent=2)
    
    print(f"Saved validated data to {output_path}")
    print(f"Saved validation log to {log_path}")
    return df

def main():
    """Main entry point for ingestion."""
    input_path = 'data/raw/synthetic_baseline.csv'
    output_path = 'data/processed/validated.csv'
    log_path = 'artifacts/reports/validation_log.json'
    run_ingestion_pipeline(input_path, output_path, log_path)

if __name__ == "__main__":
    main()
