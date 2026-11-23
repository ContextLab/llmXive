"""
T017: Output data/processed/raw_cleaned.csv.
Reads raw_processed.csv and vif_report.json, removes missing values, applies VIF exclusion.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from utils.logging_config import get_logger

logger = get_logger(__name__)

def standardize_column(series: pd.Series) -> pd.Series:
    """Standardize a column to 0-1 range."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(np.zeros(len(series)))
    return (series - min_val) / (max_val - min_val)

def run_cleaning_pipeline(
    processed_path: str = "data/processed/raw_processed.csv",
    vif_path: str = "data/processed/vif_report.json",
    output_path: str = "data/processed/raw_cleaned.csv"
):
    """
    1. Load processed data.
    2. Load VIF report.
    3. Filter columns based on VIF < 5.
    4. Drop rows with missing values.
    5. Save to output.
    """
    if not os.path.exists(processed_path):
        raise FileNotFoundError(f"Processed data not found: {processed_path}")
    if not os.path.exists(vif_path):
        raise FileNotFoundError(f"VIF report not found: {vif_path}")
    
    df = pd.read_csv(processed_path)
    with open(vif_path, 'r') as f:
        vif_report = json.load(f)
    
    # Identify excluded features
    excluded_features = vif_report.get("excluded_features", [])
    included_features = vif_report.get("included_features", [])
    
    logger.info(f"VIF Report: Excluded {excluded_features}, Included {included_features}")
    
    # Ensure required columns are present (agency_score, etc.)
    required_cols = ['participant_id', 'agency_score', 'user_response_trigger']
    motion_features = [c for c in included_features if c in df.columns]
    
    cols_to_keep = required_cols + motion_features
    # Filter to only existing columns in df
    cols_to_keep = [c for c in cols_to_keep if c in df.columns]
    
    df_clean = df[cols_to_keep].copy()
    
    # Drop missing values
    initial_len = len(df_clean)
    df_clean = df_clean.dropna()
    final_len = len(df_clean)
    
    logger.info(f"Dropped {initial_len - final_len} rows with missing values.")
    
    if len(df_clean) == 0:
        raise ValueError("No data remaining after cleaning.")
    
    # Save
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Wrote cleaned data to {output_path}")
    
    return df_clean

def main():
    try:
        run_cleaning_pipeline()
        return 0
    except Exception as e:
        logger.error(str(e))
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
