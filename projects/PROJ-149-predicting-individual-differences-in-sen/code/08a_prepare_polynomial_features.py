"""
T024a [US2] [FR-012] Implement code/08a_prepare_polynomial_features.py

Load features.csv and add polynomial terms for alpha and beta bands.
Output: data/interim/poly_features.csv

Dependencies: T012c (features.csv)
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs, POLY_DEGREE

def load_features(input_path: str) -> pd.DataFrame:
    """Load the features CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Features file not found: {input_path}")
    df = pd.read_csv(input_path)
    return df

def prepare_polynomial_features(df: pd.DataFrame, degree: int = 2) -> pd.DataFrame:
    """
    Add polynomial terms for alpha and beta bands.
    
    We create squared terms (degree 2) for alpha_rel and the beta bands.
    Based on FR-012, we focus on alpha and beta.
    """
    df_poly = df.copy()
    
    # Identify target bands
    alpha_col = 'alpha_rel'
    # Beta bands are low_beta_rel and high_beta_rel. 
    # We can create polynomials for each or a combined beta. 
    # Let's create polynomials for each individually to preserve granularity.
    beta_cols = ['low_beta_rel', 'high_beta_rel']
    
    # Ensure columns exist
    missing_cols = [c for c in [alpha_col] + beta_cols if c not in df_poly.columns]
    if missing_cols:
        raise ValueError(f"Required columns missing in input: {missing_cols}")
    
    # Create polynomial terms
    new_columns = {}
    
    # Alpha squared
    new_columns[f'{alpha_col}_sq'] = df_poly[alpha_col] ** 2
    
    # Beta squared
    for col in beta_cols:
        new_columns[f'{col}_sq'] = df_poly[col] ** 2
        
    # Optional: Interaction terms between alpha and betas if degree >= 2
    if degree >= 2:
        for col in beta_cols:
            new_columns[f'{alpha_col}_{col}_interaction'] = df_poly[alpha_col] * df_poly[col]

    # Append new columns
    for name, values in new_columns.items():
        if name not in df_poly.columns:
            df_poly[name] = values
    
    return df_poly

def main():
    parser = argparse.ArgumentParser(description="Prepare polynomial features for non-linear modeling.")
    parser.add_argument("--input", type=str, default=None, help="Path to features.csv. Uses config default if not provided.")
    parser.add_argument("--output", type=str, default=None, help="Path to output poly_features.csv. Uses config default if not provided.")
    parser.add_argument("--degree", type=int, default=None, help="Polynomial degree. Uses config default if not provided.")
    
    args = parser.parse_args()
    
    # Determine paths
    if args.input:
        input_path = args.input
    else:
        input_path = get_path("processed", "features.csv")
        
    if args.output:
        output_path = args.output
    else:
        output_path = get_path("interim", "poly_features.csv")
        
    if args.degree:
        degree = args.degree
    else:
        degree = POLY_DEGREE
    
    print(f"Loading features from {input_path}...")
    df = load_features(input_path)
    print(f"Loaded {len(df)} participants.")
    
    print(f"Generating polynomial features (degree={degree})...")
    df_poly = prepare_polynomial_features(df, degree=degree)
    
    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        ensure_dirs(out_dir)
    
    print(f"Saving polynomial features to {output_path}...")
    df_poly.to_csv(output_path, index=False)
    
    print(f"Success. Output shape: {df_poly.shape}")
    print(f"New columns added: {[c for c in df_poly.columns if c not in df.columns]}")

if __name__ == "__main__":
    main()
