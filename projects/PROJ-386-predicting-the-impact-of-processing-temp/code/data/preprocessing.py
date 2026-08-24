import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """Load the preprocessed dataset from a CSV file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    logger.info(f"Loading processed data from {path}")
    df = pd.read_csv(path)
    return df

def generate_interaction_features(df: pd.DataFrame, temp_col: str = 'rolling_temperature', 
                                  element_cols: list = None) -> pd.DataFrame:
    """
    Generate interaction features between Temperature and composition elements.
    Creates columns like 'Temp_x_Mg', 'Temp_x_Si', etc.
    """
    if element_cols is None:
        element_cols = ['Mg', 'Si', 'Cu'] # Default common alloying elements
    
    # Ensure temp column exists
    if temp_col not in df.columns:
        raise ValueError(f"Temperature column '{temp_col}' not found in dataframe.")
    
    new_df = df.copy()
    for elem in element_cols:
        if elem in df.columns:
            interaction_name = f"Temp_x_{elem}"
            new_df[interaction_name] = df[temp_col] * df[elem]
            logger.info(f"Generated interaction feature: {interaction_name}")
        else:
            logger.warning(f"Element column '{elem}' not found, skipping interaction.")
    
    return new_df

def normalize_features(df: pd.DataFrame, cols: list = None) -> pd.DataFrame:
    """
    Normalize numeric features using StandardScaler logic (z-score).
    Returns a dataframe with normalized values.
    """
    if cols is None:
        # Select all numeric columns except target if present, or all numeric
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Assume last column is target or exclude specific known targets if needed
        # For safety, we normalize all numeric columns provided
        cols = numeric_cols
    
    new_df = df.copy()
    means = {}
    stds = {}
    
    for col in cols:
        if col in new_df.columns:
            col_data = new_df[col].dropna()
            if col_data.std() == 0:
                logger.warning(f"Standard deviation of {col} is 0. Skipping normalization for this column.")
                continue
            means[col] = col_data.mean()
            stds[col] = col_data.std()
            new_df[col] = (new_df[col] - means[col]) / stds[col]
            logger.info(f"Normalized column: {col}")
    
    return new_df, means, stds

def residualize_data(df: pd.DataFrame, target_col: str = 'grain_size', 
                     residualize_cols: list = None) -> pd.DataFrame:
    """
    Regress target against specified columns (e.g., Alloy Series, Composition)
    and replace target with residuals.
    This removes the main effects of those variables from the target.
    """
    if residualize_cols is None:
        # Default: use composition columns if available, or empty list
        residualize_cols = [c for c in df.columns if c in ['Mg', 'Si', 'Cu']]
    
    if not residualize_cols:
        logger.warning("No columns provided for residualization. Returning original data.")
        return df

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found.")
    
    # Prepare data for regression
    X = df[residualize_cols].dropna()
    y = df.loc[X.index, target_col]
    
    if len(X) == 0:
        logger.warning("No valid data for residualization after dropping NaNs.")
        return df

    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate residuals for the whole dataframe (where possible)
    residuals = model.predict(df[residualize_cols])
    df_residualized = df.copy()
    df_residualized[target_col] = df_residualized[target_col] - residuals
    
    logger.info(f"Residualized '{target_col}' against {residualize_cols}")
    return df_residualized

def validate_data_quality(df: pd.DataFrame) -> bool:
    """Basic validation: check for NaNs in critical columns."""
    critical_cols = ['rolling_temperature', 'grain_size']
    for col in critical_cols:
        if col in df.columns and df[col].isna().any():
            logger.warning(f"Column '{col}' contains NaN values.")
            return False
    return True

def detect_collinearity(df: pd.DataFrame, threshold: float = 0.8, 
                        output_path: str = "data/artifacts/collinearity_report.json") -> dict:
    """
    Detect collinearity among numeric features.
    Calculates correlation matrix and flags pairs with absolute correlation > threshold.
    Generates a JSON report with the schema:
    {
      "threshold": float,
      "flagged_pairs": [ ["col1", "col2"], ... ]
    }
    """
    logger.info(f"Detecting collinearity with threshold {threshold}...")
    
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        logger.warning("No numeric columns found for collinearity detection.")
        report = {
            "threshold": threshold,
            "flagged_pairs": [],
            "message": "No numeric columns found."
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return report

    corr_matrix = numeric_df.corr().abs()
    
    # Upper triangle of correlation matrix
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    flagged_pairs = []
    for col in upper.columns:
        for row in upper.index:
            if upper.loc[row, col] > threshold:
                flagged_pairs.append([row, col])
    
    logger.info(f"Found {len(flagged_pairs)} pairs with correlation > {threshold}")
    
    report = {
        "threshold": threshold,
        "flagged_pairs": flagged_pairs
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Collinearity report saved to {output_path}")
    return report

def run_preprocessing_pipeline(input_path: str, output_path: str, 
                               collinearity_report_path: str = "data/artifacts/collinearity_report.json"):
    """
    Orchestrates the preprocessing steps:
    1. Load data
    2. Generate interactions
    3. Normalize
    4. Residualize
    5. Detect collinearity and save report
    6. Save processed data
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load
    df = load_processed_data(input_path)
    
    # 2. Interactions
    df = generate_interaction_features(df)
    
    # 3. Normalize
    # Identify numeric columns to normalize (exclude target 'grain_size' if present)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cols_to_normalize = [c for c in numeric_cols if c != 'grain_size']
    df, means, stds = normalize_features(df, cols=cols_to_normalize)
    
    # 4. Residualize
    # Residualize grain_size against composition (and maybe series if present)
    comp_cols = [c for c in df.columns if c in ['Mg', 'Si', 'Cu']]
    if 'Alloy_Series' in df.columns:
        comp_cols.append('Alloy_Series')
    if comp_cols:
        df = residualize_data(df, target_col='grain_size', residualize_cols=comp_cols)
    
    # 5. Collinearity Detection
    detect_collinearity(df, threshold=0.8, output_path=collinearity_report_path)
    
    # 6. Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Preprocessed data saved to {output_path}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline with collinearity detection.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--report", type=str, default="data/artifacts/collinearity_report.json", 
                        help="Path to collinearity report JSON")
    args = parser.parse_args()
    
    try:
        run_preprocessing_pipeline(args.input, args.output, args.report)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()