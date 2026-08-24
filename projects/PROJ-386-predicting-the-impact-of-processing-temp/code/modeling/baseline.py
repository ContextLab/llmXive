import os
import sys
import json
import logging
import argparse
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Import from local modules as per API surface
from config import get_config
from data.preprocessing import load_processed_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_prepare_data(processed_data_path: str) -> tuple:
    """
    Load preprocessed data and prepare feature/target matrices.
    
    Args:
        processed_data_path: Path to the processed CSV file.
        
    Returns:
        tuple: (X_df, y, feature_names)
    """
    logger.info(f"Loading processed data from {processed_data_path}")
    df = load_processed_data(processed_data_path)
    
    if df.empty:
        raise ValueError("Loaded dataframe is empty. Check preprocessing pipeline.")
    
    # Define target and features based on typical pipeline output
    # Assuming 'grain_size' is the target and residuals are stored if residualization was done
    target_col = 'grain_size_residual' if 'grain_size_residual' in df.columns else 'grain_size'
    y = df[target_col].values
    
    # Features: All numeric columns except target and ID/grouping columns
    exclude_cols = [target_col, 'alloy_series', 'sample_id', 'source_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols and np.issubdtype(df[col].dtype, np.number)]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataframe.")
        
    X_df = df[feature_cols]
    logger.info(f"Prepared {len(X_df)} samples with {len(feature_cols)} features.")
    logger.info(f"Features: {feature_cols}")
    
    return X_df, y, feature_cols

def train_baseline_model(X_df: pd.DataFrame, y: np.ndarray) -> tuple:
    """
    Train a Linear Regression model on the data.
    
    Args:
        X_df: Feature DataFrame.
        y: Target array.
        
    Returns:
        tuple: (model, r2, mae)
    """
    logger.info("Training baseline Linear Regression model...")
    
    # Split data for validation
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y, test_size=0.2, random_state=42
    )
    
    # Create pipeline with scaling
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression())
    ])
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    logger.info(f"Baseline Model Performance - R²: {r2:.4f}, MAE: {mae:.4f}")
    
    return model, r2, mae

def extract_coefficients_and_report(model: Pipeline, feature_names: list, r2: float, mae: float, collinearity_report_path: str) -> dict:
    """
    Extract coefficients, load collinearity report, and generate interpretation.
    
    Args:
        model: Fitted sklearn Pipeline.
        feature_names: List of feature names.
        r2: R² score.
        mae: MAE score.
        collinearity_report_path: Path to collinearity_report.json.
        
    Returns:
        dict: Report dictionary.
    """
    logger.info("Extracting coefficients and generating report...")
    
    # Get the linear regressor from the pipeline
    regressor = model.named_steps['regressor']
    scaler = model.named_steps['scaler']
    
    coefficients = regressor.coef_
    intercept = regressor.intercept_
    
    # Map coefficients to feature names
    coeff_dict = {}
    for name, coef in zip(feature_names, coefficients):
        coeff_dict[name] = float(coef)
    
    # Load collinearity report
    flagged_pairs = []
    collinearity_status = "No collinearity report found"
    
    if os.path.exists(collinearity_report_path):
        try:
            with open(collinearity_report_path, 'r') as f:
                collinearity_data = json.load(f)
            
            # Expecting a 'flagged_pairs' key based on T023 spec
            flagged_pairs = collinearity_data.get('flagged_pairs', [])
            collinearity_status = "Collinearity report loaded"
            logger.info(f"Loaded collinearity report. Flagged pairs: {flagged_pairs}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse collinearity report: {e}")
    else:
        logger.warning(f"Collinearity report not found at {collinearity_report_path}. Interpretation will be standard.")
    
    # Generate interpretation with collinearity awareness
    interpretation = {
        "summary": f"Model R²: {r2:.4f}, MAE: {mae:.4f}",
        "coefficients": coeff_dict,
        "collinearity_flags": flagged_pairs,
        "interpretation_notes": []
    }
    
    # Construct descriptive notes for flagged pairs
    if flagged_pairs:
        interpretation["interpretation_notes"].append(
            "WARNING: The following feature pairs exhibit high collinearity (>0.8). "
            "Independent interpretation of their coefficients is suppressed. "
            "They should be framed as joint effects:"
        )
        for pair in flagged_pairs:
            pair_str = f"{pair[0]} & {pair[1]}" if isinstance(pair, (list, tuple)) else str(pair)
            interpretation["interpretation_notes"].append(f"  - {pair_str}")
        
        interpretation["interpretation_notes"].append(
            "For unflagged features, coefficients represent the estimated change in the target "
            "per unit change in the feature, holding other features constant."
        )
    else:
        interpretation["interpretation_notes"].append(
            "No high collinearity detected. Coefficients can be interpreted independently "
            "as the effect of a single feature on the target, holding others constant."
        )
    
    return interpretation

def save_model_artifacts(model: Pipeline, r2: float, mae: float, interpretation: dict, output_path: str):
    """
    Save the model and report to disk.
    
    Args:
        model: Fitted model.
        r2: R² score.
        mae: MAE score.
        interpretation: Interpretation dictionary.
        output_path: Path to save the report JSON.
    """
    logger.info(f"Saving model artifacts to {output_path}")
    
    # Save model (using joblib or pickle, assuming standard sklearn serialization)
    # We will save the report as JSON and the model as a separate artifact if needed,
    # but the task specifically asks for logging and report generation.
    # Let's save the full report including metrics and interpretation.
    
    report = {
        "metrics": {
            "r2": r2,
            "mae": mae
        },
        "interpretation": interpretation
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Model report saved to {output_path}")

def run_baseline_pipeline(config: dict):
    """
    Run the full baseline modeling pipeline.
    
    Args:
        config: Configuration dictionary.
    """
    processed_data_path = config.get('processed_data_path', 'data/processed/processed_data.csv')
    collinearity_report_path = config.get('collinearity_report_path', 'data/artifacts/collinearity_report.json')
    output_report_path = config.get('baseline_report_path', 'data/artifacts/baseline_report.json')
    
    try:
        # 1. Load Data
        X_df, y, feature_names = load_and_prepare_data(processed_data_path)
        
        # 2. Train Model
        model, r2, mae = train_baseline_model(X_df, y)
        
        # 3. Extract Coefficients & Generate Report
        interpretation = extract_coefficients_and_report(model, feature_names, r2, mae, collinearity_report_path)
        
        # 4. Save Artifacts
        save_model_artifacts(model, r2, mae, interpretation, output_report_path)
        
        logger.info("Baseline pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Baseline pipeline failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Run Baseline Linear Regression Modeling")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    # Load config
    try:
        config = get_config(args.config)
    except FileNotFoundError:
        # Fallback to default paths if config file not found or parsing fails
        config = {
            'processed_data_path': 'data/processed/processed_data.csv',
            'collinearity_report_path': 'data/artifacts/collinearity_report.json',
            'baseline_report_path': 'data/artifacts/baseline_report.json'
        }
        logger.warning("Config file not found, using defaults.")
    
    run_baseline_pipeline(config)

if __name__ == "__main__":
    main()