import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from config import get_config, ensure_dirs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the preprocessed dataset from the artifacts directory."""
    config = get_config()
    input_path = config['paths']['processed_data']
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed data not found at {input_path}. Run ingestion and preprocessing first.")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded processed data with shape {df.shape}")
    return df

def generate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate interaction features between Temperature and Composition elements."""
    logger.info("Generating interaction features...")
    temp_col = 'Temperature'
    composition_cols = ['Mg', 'Si', 'Cu', 'Zn', 'Mn']
    
    # Ensure columns exist
    missing_cols = [c for c in [temp_col] + composition_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns for interaction: {missing_cols}. Skipping interaction generation.")
        return df

    for col in composition_cols:
        feature_name = f"Temp_x_{col}"
        df[feature_name] = df[temp_col] * df[col]
        logger.debug(f"Created interaction: {feature_name}")
    
    logger.info(f"Interaction features generated. New shape: {df.shape}")
    return df

def normalize_features(df: pd.DataFrame, feature_cols: list = None) -> tuple[pd.DataFrame, StandardScaler]:
    """Normalize numeric features using StandardScaler."""
    logger.info("Normalizing features...")
    
    if feature_cols is None:
        # Select all numeric columns except target and grouping
        exclude_cols = ['Grain_Size', 'Alloy_Series', 'Study_ID', 'Temperature']
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude_cols]
    
    if not feature_cols:
        logger.warning("No features found to normalize.")
        return df, None

    scaler = StandardScaler()
    df_scaled = df.copy()
    df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])
    logger.info(f"Normalized {len(feature_cols)} features.")
    return df_scaled, scaler

def residualize_data(df: pd.DataFrame) -> pd.DataFrame:
    """Regress Grain Size against Alloy Series and Composition, store residuals."""
    logger.info("Residualizing Grain Size...")
    
    # Define predictors for main effects (excluding temperature interactions for now)
    # Assuming Alloy Series is categorical and Composition is numeric
    composition_cols = ['Mg', 'Si', 'Cu', 'Zn', 'Mn']
    available_comps = [c for c in composition_cols if c in df.columns]
    
    # One-hot encode Alloy Series if present
    if 'Alloy_Series' in df.columns:
        dummies = pd.get_dummies(df['Alloy_Series'], prefix='Series', drop_first=True)
        predictors = pd.concat([df[available_comps], dummies], axis=1)
    else:
        predictors = df[available_comps]
    
    if predictors.empty:
        logger.error("No predictors available for residualization.")
        return df

    target = df['Grain_Size']
    model = LinearRegression()
    model.fit(predictors, target)
    
    residuals = target - model.predict(predictors)
    df['Grain_Size_Residual'] = residuals
    
    logger.info(f"Residualization complete. Mean residual: {residuals.mean():.4f}")
    return df

def validate_data_quality(df: pd.DataFrame) -> bool:
    """Basic validation of data quality."""
    logger.info("Validating data quality...")
    if df.empty:
        logger.error("DataFrame is empty.")
        return False
    
    if 'Grain_Size_Residual' not in df.columns:
        logger.error("Residuals not found. Run residualization first.")
        return False
    
    if df['Grain_Size_Residual'].isna().any():
        logger.warning("Residuals contain NaN values.")
        return False
    
    return True

def detect_collinearity(df: pd.DataFrame, threshold: float = 0.8) -> dict:
    """
    Detect collinearity among numeric features and generate a report.
    
    Args:
        df: DataFrame containing the processed features.
        threshold: Correlation threshold above which features are considered collinear.
        
    Returns:
        dict: A dictionary containing the collinearity report with 'flagged_pairs'.
    """
    logger.info("Detecting collinearity...")
    
    # Select numeric columns only
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Exclude target variables and IDs if present
    exclude_cols = ['Grain_Size', 'Grain_Size_Residual', 'Study_ID', 'Alloy_Series']
    cols_to_check = [c for c in numeric_df.columns if c not in exclude_cols]
    
    if len(cols_to_check) < 2:
        logger.warning("Not enough numeric columns to check for collinearity.")
        return {"flagged_pairs": [], "threshold": threshold, "message": "Insufficient columns"}

    corr_matrix = numeric_df[cols_to_check].corr().abs()
    
    flagged_pairs = []
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    for col in upper_tri.columns:
        for row in upper_tri.index:
            if row == col:
                continue
            val = upper_tri.loc[row, col]
            if pd.notna(val) and val > threshold:
                pair = (row, col)
                # Avoid duplicates (since matrix is symmetric)
                if pair not in flagged_pairs and (col, row) not in flagged_pairs:
                    flagged_pairs.append(list(pair))
                    logger.warning(f"Collinearity detected: {row} & {col} (r={val:.3f})")
    
    report = {
        "flagged_pairs": flagged_pairs,
        "threshold": threshold,
        "total_pairs_checked": int(upper_tri.sum().sum()),
        "flagged_count": len(flagged_pairs)
    }
    
    return report

def run_preprocessing_pipeline():
    """Execute the full preprocessing pipeline including collinearity detection."""
    logger.info("Starting preprocessing pipeline...")
    
    try:
        # Load data
        df = load_processed_data()
        
        # Generate interactions
        df = generate_interaction_features(df)
        
        # Normalize
        df, scaler = normalize_features(df)
        
        # Residualize
        df = residualize_data(df)
        
        # Validate
        if not validate_data_quality(df):
            logger.error("Data validation failed. Stopping pipeline.")
            sys.exit(1)
        
        # Detect Collinearity (Task T023)
        collinearity_report = detect_collinearity(df)
        
        # Save Collinearity Report
        config = get_config()
        report_path = Path(config['paths']['artifacts']) / 'collinearity_report.json'
        ensure_dirs([report_path.parent])
        
        with open(report_path, 'w') as f:
            json.dump(collinearity_report, f, indent=2)
        
        logger.info(f"Collinearity report saved to {report_path}")
        
        # Save processed data
        output_path = Path(config['paths']['processed_data'])
        df.to_csv(output_path, index=False)
        logger.info(f"Processed data saved to {output_path}")
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline with collinearity detection.")
    args = parser.parse_args()
    run_preprocessing_pipeline()

if __name__ == "__main__":
    main()
