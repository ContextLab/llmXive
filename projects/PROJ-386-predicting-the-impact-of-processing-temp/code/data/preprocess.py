"""
Data preprocessing module for grain size prediction.
Includes interaction feature generation, normalization, and residualization logic.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config

logger = logging.getLogger(__name__)

def load_processed_data(data_path):
    """Load processed data from CSV."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(data_path)

def generate_interaction_features(df, temp_col='Rolling_Temperature', composition_cols=None):
    """
    Generate interaction features between Temperature and Composition elements.
    
    Args:
        df: DataFrame with data
        temp_col: Name of the temperature column
        composition_cols: List of composition column names (e.g., ['Mg', 'Si', 'Cu'])
    
    Returns:
        DataFrame with added interaction columns
    """
    df = df.copy()
    if composition_cols is None:
        composition_cols = ['Mg', 'Si', 'Cu']
    
    for elem in composition_cols:
        if temp_col in df.columns and elem in df.columns:
            interaction_name = f"{temp_col}_x_{elem}"
            df[interaction_name] = df[temp_col] * df[elem]
            logger.info(f"Generated interaction: {interaction_name}")
        else:
            logger.warning(f"Columns {temp_col} or {elem} not found for interaction")
    
    return df

def normalize_features(df, feature_cols=None, exclude_cols=None):
    """
    Normalize numeric features using StandardScaler.
    
    Args:
        df: DataFrame
        feature_cols: List of columns to normalize (default: all numeric except target/exclude)
        exclude_cols: Columns to exclude from normalization
    
    Returns:
        DataFrame with normalized features and a scaler object
    """
    df = df.copy()
    if exclude_cols is None:
        exclude_cols = ['Grain_Size', 'Alloy_Series', 'Sample_ID']
    
    if feature_cols is None:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in feature_cols if c not in exclude_cols]
    
    scaler = StandardScaler()
    df_scaled = df.copy()
    
    if len(feature_cols) > 0:
        df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])
        logger.info(f"Normalized {len(feature_cols)} features")
    else:
        logger.warning("No features found to normalize")
    
    return df_scaled, scaler

def residualize_data(df, target_col='Grain_Size', group_cols=None):
    """
    Regress Grain Size vs. Alloy Series + Composition; store residuals.
    
    This function removes the linear effect of Alloy Series and Composition 
    from the Grain Size variable, creating a residual that represents the 
    variation not explained by these main effects.
    
    Args:
        df: DataFrame with data
        target_col: Name of the target column to residualize
        group_cols: List of columns to regress against (e.g., ['Alloy_Series', 'Mg', 'Si', 'Cu'])
    
    Returns:
        DataFrame with added residual column, and the fitted model
    """
    df = df.copy()
    if group_cols is None:
        group_cols = ['Alloy_Series', 'Mg', 'Si', 'Cu']
    
    # Ensure numeric
    for col in group_cols:
        if col not in df.columns:
            raise ValueError(f"Group column {col} not found in data")
    
    # Filter rows where target and groups are not null
    mask = df[target_col].notna() & df[group_cols].notna().all(axis=1)
    df_clean = df[mask]
    
    if len(df_clean) == 0:
        logger.warning("No valid data points for residualization")
        df[target_col + '_resid'] = np.nan
        return df, None
    
    X = df_clean[group_cols]
    y = df_clean[target_col]
    
    model = LinearRegression()
    model.fit(X, y)
    
    residuals = y - model.predict(X)
    
    # Assign residuals back to the original dataframe
    df[target_col + '_resid'] = np.nan
    df.loc[mask, target_col + '_resid'] = residuals.values
    
    logger.info(f"Residualization complete. R² of main effects: {model.score(X, y):.4f}")
    
    return df, model

def validate_data_quality(df):
    """
    Validate data quality after preprocessing.
    
    Checks:
    - No missing values in critical columns
    - Reasonable ranges for numeric columns
    - Residuals are uncorrelated with predictors
    """
    critical_cols = ['Rolling_Temperature', 'Grain_Size', 'Mg', 'Si', 'Cu']
    missing = df[critical_cols].isnull().sum()
    
    if missing.sum() > 0:
        logger.warning(f"Missing values in critical columns: {missing[missing > 0].to_dict()}")
    
    # Check residuals if they exist
    if 'Grain_Size_resid' in df.columns:
        group_cols = ['Alloy_Series', 'Mg', 'Si', 'Cu']
        valid_mask = df['Grain_Size_resid'].notna() & df[group_cols].notna().all(axis=1)
        if valid_mask.sum() > 0:
            residuals = df.loc[valid_mask, 'Grain_Size_resid']
            for col in group_cols:
                corr = residuals.corr(df.loc[valid_mask, col])
                if abs(corr) > 0.1:
                    logger.warning(f"Residuals still correlated with {col}: {corr:.4f}")
    
    logger.info("Data quality validation complete")
    return True

def run_preprocessing_pipeline(input_path, output_path):
    """
    Run the full preprocessing pipeline:
    1. Load data
    2. Generate interaction features
    3. Normalize features
    4. Residualize Grain Size
    5. Validate quality
    6. Save output
    """
    logger.info(f"Starting preprocessing pipeline for {input_path}")
    
    df = load_processed_data(input_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Generate interactions
    df = generate_interaction_features(df)
    
    # Residualize Grain Size
    df, model = residualize_data(df)
    
    # Normalize features (excluding target and residuals)
    exclude = ['Grain_Size', 'Grain_Size_resid', 'Alloy_Series', 'Sample_ID']
    df, scaler = normalize_features(df, exclude_cols=exclude)
    
    # Validate
    validate_data_quality(df)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved preprocessed data to {output_path}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Run data preprocessing pipeline")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    run_preprocessing_pipeline(args.input, args.output)

if __name__ == "__main__":
    main()