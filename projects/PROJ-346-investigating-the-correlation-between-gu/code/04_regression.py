import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNet
from utils import get_data_processed_path, ensure_directory, get_logger

logger = get_logger(__name__)

def load_merged_data():
    processed_dir = get_data_processed_path()
    data_path = processed_dir / "merged_dataset.parquet"
    if not data_path.exists():
        logger.info("N/A - Data Gap")
        return None
    return pd.read_parquet(data_path)

def apply_clr_transform(df):
    # Centered Log Ratio transform
    # Add a small pseudo-count to avoid log(0)
    pseudo_count = 1e-6
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df_transformed = df.copy()
    for col in numeric_cols:
        df_transformed[col] = np.log(df[col] + pseudo_count)
    # Centering
    row_sums = df_transformed[numeric_cols].sum(axis=1)
    df_transformed[numeric_cols] = df_transformed[numeric_cols] - (row_sums / len(numeric_cols)).values.reshape(-1, 1)
    return df_transformed

def prepare_features(df):
    # Separate features and target
    # Assuming 'z_score' is the target and others are features
    if 'z_score' not in df.columns:
        logger.error("Target column 'z_score' not found.")
        return None, None
    
    target = df['z_score']
    features = df.drop(columns=['z_score', 'participant_id', 'sample_id', 'taxon_name', 'task_type'], errors='ignore')
    return features, target

def fit_lasso_elasticnet(X, y):
    if X is None or y is None or len(X) == 0:
        return None
    
    model = ElasticNet(l1_ratio=0.5, random_state=42)
    try:
        model.fit(X, y)
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None
    
    return {
        "coefficients": dict(zip(X.columns, model.coef_.tolist())),
        "intercept": float(model.intercept_),
        "r2_score": float(model.score(X, y))
    }

def save_results(results):
    output_dir = get_data_processed_path()
    ensure_directory(output_dir)
    output_path = output_dir / "regression_results.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved regression results to {output_path}")

def main():
    logger.info("Starting regression analysis (T023)")
    
    df = load_merged_data()
    if df is None:
        # Graceful exit as per spec
        return

    X, y = prepare_features(df)
    if X is None or y is None:
        logger.warning("Could not prepare features. Skipping.")
        return

    results = fit_lasso_elasticnet(X, y)
    if results:
        save_results(results)
    else:
        logger.warning("No results to save.")

if __name__ == "__main__":
    main()
