import os
import sys
import json
import logging
import argparse
import warnings
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

# Import from sibling modules based on API surface
from config import get_config, ensure_dirs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_prepare_data(data_path: str) -> pd.DataFrame:
    """
    Load the preprocessed dataset from the specified path.
    Expects a CSV file with interaction features and normalized columns.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data file not found at {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df

def stratified_split_by_study(df: pd.DataFrame, study_col: str = 'source_study', 
                              test_size: float = 0.2, random_state: int = 42):
    """
    Perform a stratified train/val/test split by source_study to prevent data leakage.
    If 'source_study' is missing or has too few unique values, falls back to random split.
    """
    if study_col not in df.columns:
        logger.warning(f"Column '{study_col}' not found. Falling back to random split.")
        train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
        return train_df, test_df

    unique_studies = df[study_col].nunique()
    if unique_studies < 5:
        logger.warning(f"Only {unique_studies} unique studies found. Stratification may be unreliable. Falling back to random split.")
        train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
        return train_df, test_df

    try:
        train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state, stratify=df[study_col])
        logger.info(f"Stratified split by '{study_col}' successful. Train: {len(train_df)}, Test: {len(test_df)}")
        return train_df, test_df
    except Exception as e:
        logger.warning(f"Stratified split failed ({e}). Falling back to random split.")
        train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
        return train_df, test_df

def train_baseline_model(train_df: pd.DataFrame, test_df: pd.DataFrame, 
                         target_col: str = 'grain_size') -> dict:
    """
    Train an OLS Linear Regression model with interaction terms.
    Assumes interaction features are already present in the dataframe.
    """
    # Identify feature columns (exclude target and non-numeric metadata)
    feature_cols = [col for col in train_df.columns if col != target_col and train_df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not feature_cols:
        raise ValueError("No numeric feature columns found for training.")

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    mae_test = mean_absolute_error(y_test, y_pred_test)

    logger.info(f"Model Training Complete. R2 Train: {r2_train:.4f}, R2 Test: {r2_test:.4f}, MAE Test: {mae_test:.4f}")

    return {
        'model': model,
        'feature_cols': feature_cols,
        'r2_train': r2_train,
        'r2_test': r2_test,
        'mae_test': mae_test,
        'coefficients': dict(zip(feature_cols, model.coef_.tolist())),
        'intercept': float(model.intercept_)
    }

def save_model_artifacts(results: dict, model_path: str, metrics_path: str):
    """
    Save the trained model artifact and log metrics to JSON.
    """
    # Ensure directories exist
    ensure_dirs(model_path)
    ensure_dirs(metrics_path)

    # Save the model object
    with open(model_path, 'wb') as f:
        joblib.dump(results['model'], f)
    logger.info(f"Model saved to {model_path}")

    # Prepare metrics report
    metrics_report = {
        'r2_test': results['r2_test'],
        'r2_train': results['r2_train'],
        'mae_test': results['mae_test'],
        'coefficients': results['coefficients'],
        'intercept': results['intercept'],
        'feature_count': len(results['feature_cols']),
        'timestamp': pd.Timestamp.now().isoformat()
    }

    # Save metrics JSON
    with open(metrics_path, 'w') as f:
        json.dump(metrics_report, f, indent=2)
    logger.info(f"Metrics logged to {metrics_path}")

def run_baseline_pipeline(data_path: str, output_model_path: str, output_metrics_path: str):
    """
    Orchestrate the baseline modeling pipeline: load, split, train, save.
    """
    logger.info("Starting Baseline Modeling Pipeline")
    
    df = load_and_prepare_data(data_path)
    train_df, test_df = stratified_split_by_study(df)
    results = train_baseline_model(train_df, test_df)
    save_model_artifacts(results, output_model_path, output_metrics_path)
    
    logger.info("Baseline Modeling Pipeline Complete")
    return results

def main():
    parser = argparse.ArgumentParser(description="Train and save baseline linear regression model.")
    parser.add_argument("--data", type=str, required=True, help="Path to the processed CSV data file.")
    parser.add_argument("--model-out", type=str, default="artifacts/models/baseline_model.joblib", help="Path to save the model artifact.")
    parser.add_argument("--metrics-out", type=str, default="artifacts/reports/baseline_metrics.json", help="Path to save the metrics JSON.")
    
    args = parser.parse_args()

    try:
        run_baseline_pipeline(args.data, args.model_out, args.metrics_out)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
