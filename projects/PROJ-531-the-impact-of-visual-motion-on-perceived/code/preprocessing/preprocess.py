"""
Preprocessing pipeline for motion features and agency scores.
Includes VIF calculation and data cleaning.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor

def calculate_vif(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for given features.
    """
    vif_data = pd.DataFrame()
    vif_data["Feature"] = features
    vif_data["VIF"] = [variance_inflation_factor(df[features].values, i) 
                       for i in range(len(features))]
    return vif_data

def run_preprocessing(input_path: str = "data/raw/synthetic_raw.csv", 
                      output_dir: str = "data/processed") -> dict:
    """
    Main preprocessing function.
    1. Loads data.
    2. Handles missing values.
    3. Calculates VIF and flags high collinearity.
    4. Standardizes features if needed.
    5. Saves cleaned data and diagnostics.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = pd.read_csv(input_path)
    
    # 1. Handle missing values (drop or impute)
    initial_count = len(df)
    df = df.dropna(subset=["latency", "smoothness", "lead_time", "agency_score"])
    dropped_count = initial_count - len(df)
    
    # 2. Feature selection for VIF
    features = ["latency", "smoothness", "lead_time"]
    vif_df = calculate_vif(df, features)
    
    # 3. Flag high VIF (>= 5)
    high_vif_features = vif_df[vif_df["VIF"] >= 5]["Feature"].tolist()
    vif_status = "clean" if not high_vif_features else "collinearity_detected"
    
    # 4. Standardization (0-1 scaling for features)
    for col in features:
        min_val = df[col].min()
        max_val = df[col].max()
        if max_val > min_val:
            df[f"{col}_std"] = (df[col] - min_val) / (max_val - min_val)
        else:
            df[f"{col}_std"] = 0.0
    
    # 5. Prepare output
    cleaned_df = df[["participant_id", "latency", "smoothness", "lead_time", "agency_score"] + 
                    [f"{f}_std" for f in features]].copy()
    
    output_csv = Path(output_dir) / "cleaned_data.csv"
    cleaned_df.to_csv(output_csv, index=False)
    
    # Save diagnostics
    diag_path = Path(output_dir) / "preprocessing_diagnostics.json"
    diagnostics = {
        "input_file": input_path,
        "initial_rows": initial_count,
        "final_rows": len(df),
        "rows_dropped": dropped_count,
        "vif_results": vif_df.to_dict(orient="records"),
        "high_vif_features": high_vif_features,
        "vif_status": vif_status,
        "output_file": str(output_csv)
    }
    
    with open(diag_path, 'w') as f:
        json.dump(diagnostics, f, indent=2)
        
    return diagnostics
