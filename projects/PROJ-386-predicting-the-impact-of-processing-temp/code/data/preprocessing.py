"""
Preprocessing module for aluminum alloy grain size prediction.
Handles feature engineering, normalization, residualization, and collinearity detection.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

# Import config for paths
try:
    from config import get_config
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """Load the processed dataset from CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def generate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate interaction features between Temperature and composition elements.
    Expected columns: 'Temperature', 'Mg', 'Si', 'Cu', etc.
    """
    logger.info("Generating interaction features (Temp x Element)")
    
    # Identify composition columns (assuming they start with element symbols or are known)
    # We look for specific columns that represent composition percentages
    composition_cols = [col for col in df.columns if col in ['Mg', 'Si', 'Cu', 'Zn', 'Mn', 'Fe', 'Ti']]
    
    if 'Temperature' not in df.columns:
        logger.warning("Temperature column not found. Skipping interaction generation.")
        return df
    
    if not composition_cols:
        logger.warning("No composition columns found. Skipping interaction generation.")
        return df

    for col in composition_cols:
        new_col_name = f"Temp_x_{col}"
        df[new_col_name] = df['Temperature'] * df[col]
        logger.debug(f"Created interaction feature: {new_col_name}")

    logger.info(f"Added {len(composition_cols)} interaction features.")
    return df

def normalize_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, StandardScaler]:
    """
    Normalize numeric features using StandardScaler.
    Returns the transformed dataframe and the fitted scaler.
    """
    logger.info("Normalizing numeric features")
    
    # Select numeric columns, excluding target and categorical identifiers
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude target variable if present (commonly 'GrainSize' or 'grain_size')
    target_candidates = ['GrainSize', 'grain_size', 'Target']
    for t in target_candidates:
        if t in numeric_cols:
            numeric_cols.remove(t)
    
    if not numeric_cols:
        logger.warning("No numeric features found to normalize.")
        return df, None

    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    
    logger.info(f"Normalized {len(numeric_cols)} features.")
    return df, scaler

def residualize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regress Grain Size against Alloy Series and Composition to get residuals.
    This removes main effects of composition and series, leaving interaction effects.
    """
    logger.info("Residualizing Grain Size against main effects")
    
    if 'GrainSize' not in df.columns and 'grain_size' not in df.columns:
        raise ValueError("Target column 'GrainSize' or 'grain_size' not found in dataframe.")
    
    target_col = 'GrainSize' if 'GrainSize' in df.columns else 'grain_size'
    
    # Define predictors for main effects (Composition + Alloy Series if present)
    predictors = [col for col in df.columns if col in ['Mg', 'Si', 'Cu', 'Zn', 'Mn', 'Fe', 'Ti', 'AlloySeries']]
    
    # If no specific composition columns found, try to auto-detect numeric ones excluding target and Temp
    if not predictors:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        predictors = [c for c in numeric_cols if c != target_col and c != 'Temperature']
    
    if not predictors:
        logger.warning("No predictors found for residualization. Returning original target.")
        df['Residuals'] = df[target_col]
        return df

    X = df[predictors].dropna()
    y = df.loc[X.index, target_col]
    
    # Handle missing values in target
    valid_indices = y.dropna().index
    X = X.loc[valid_indices]
    y = y.loc[valid_indices]

    if len(X) == 0:
        logger.warning("No valid data points for residualization.")
        df['Residuals'] = np.nan
        return df

    model = LinearRegression()
    model.fit(X, y)
    
    # Predict and calculate residuals for the valid subset
    predictions = model.predict(X)
    residuals = y - predictions
    
    # Create a new column for residuals, filling NaN for rows excluded from fit
    df['Residuals'] = np.nan
    df.loc[valid_indices, 'Residuals'] = residuals.values

    logger.info(f"Residualization complete. R² of main effects model: {model.score(X, y):.4f}")
    return df

def validate_data_quality(df: pd.DataFrame) -> bool:
    """Basic validation of data quality."""
    logger.info("Validating data quality")
    
    if df.empty:
        logger.error("DataFrame is empty.")
        return False
    
    # Check for nulls in critical columns
    critical_cols = ['Temperature', 'GrainSize', 'Residuals']
    for col in critical_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"Column '{col}' has {null_count} null values.")
    
    return True

def detect_collinearity(df: pd.DataFrame, threshold: float = 0.8) -> Dict[str, Any]:
    """
    Detect collinearity among numeric features.
    Identifies pairs with absolute correlation > threshold.
    Generates a JSON report at data/artifacts/collinearity_report.json.
    
    Args:
        df: DataFrame with numeric features.
        threshold: Correlation threshold to flag pairs.
    
    Returns:
        Dictionary containing the report data.
    """
    logger.info(f"Detecting collinearity (threshold > {threshold})")
    
    # Select numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.shape[1] < 2:
        logger.warning("Not enough numeric columns to calculate correlations.")
        report = {
            "threshold": threshold,
            "flagged_pairs": [],
            "total_pairs_checked": 0,
            "message": "Insufficient data for collinearity check."
        }
        _save_collinearity_report(report)
        return report
    
    # Calculate correlation matrix
    corr_matrix = numeric_df.corr().abs()
    
    # Select upper triangle of correlation matrix
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Find features with correlation greater than threshold
    flagged_pairs = []
    for col in upper.columns:
        for row in upper.index:
            if upper.loc[row, col] > threshold:
                # Avoid self-correlation (though k=1 should handle it)
                if row != col:
                    pair = (row, col)
                    # Ensure unique pairs (sort to avoid duplicates like (A,B) and (B,A))
                    sorted_pair = tuple(sorted(pair))
                    if sorted_pair not in flagged_pairs:
                        flagged_pairs.append(sorted_pair)
    
    # Sort pairs for consistent output
    flagged_pairs.sort()
    
    logger.info(f"Found {len(flagged_pairs)} pairs with correlation > {threshold}")
    
    report = {
        "threshold": threshold,
        "flagged_pairs": [list(pair) for pair in flagged_pairs],
        "total_pairs_checked": int((numeric_df.shape[1] * (numeric_df.shape[1] - 1)) / 2),
        "message": f"Identified {len(flagged_pairs)} highly correlated feature pairs."
    }
    
    _save_collinearity_report(report)
    return report

def _save_collinearity_report(report: Dict[str, Any]) -> None:
    """Saves the collinearity report to the artifacts directory."""
    artifacts_dir = Path("data/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = artifacts_dir / "collinearity_report.json"
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Collinearity report saved to {output_path}")

def run_preprocessing_pipeline(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline:
    1. Load data
    2. Generate interactions
    3. Normalize features
    4. Residualize target
    5. Validate quality
    6. Detect collinearity
    """
    logger.info("Starting preprocessing pipeline")
    
    # 1. Load
    df = load_processed_data(input_path)
    
    # 2. Interactions
    df = generate_interaction_features(df)
    
    # 3. Normalize
    df, scaler = normalize_features(df)
    
    # 4. Residualize
    df = residualize_data(df)
    
    # 5. Validate
    if not validate_data_quality(df):
        logger.error("Data validation failed. Stopping pipeline.")
        sys.exit(1)
    
    # 6. Collinearity
    collinearity_report = detect_collinearity(df)
    if collinearity_report['flagged_pairs']:
        logger.warning(f"High collinearity detected: {collinearity_report['flagged_pairs']}")
    
    # Save processed data
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Preprocessed data saved to {output_path}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Preprocessing pipeline for aluminum alloy data")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    args = parser.parse_args()
    
    run_preprocessing_pipeline(args.input, args.output)

if __name__ == "__main__":
    main()
