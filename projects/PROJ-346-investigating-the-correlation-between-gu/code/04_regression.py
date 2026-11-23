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
    """
    Apply Centered Log-Ratio (CLR) transform to microbial taxa columns.
    Assumes numeric columns representing taxa abundances.
    """
    pseudo_count = 1e-6
    # Identify taxa columns (numeric, excluding covariates)
    # We assume non-covariate numeric columns are taxa
    covariates = {'age', 'sex', 'bmi', 'participant_id', 'sample_id', 'taxon_name', 'task_type', 'z_score'}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    taxa_cols = [col for col in numeric_cols if col not in covariates]
    
    if not taxa_cols:
        logger.warning("No taxa columns found for CLR transform.")
        return df

    df_transformed = df.copy()
    
    # Log transform with pseudo-count
    df_transformed[taxa_cols] = np.log(df_transformed[taxa_cols] + pseudo_count)
    
    # Centering: subtract the geometric mean (log of geometric mean is mean of logs)
    # CLR(x) = log(x/g(x)) = log(x) - mean(log(x))
    row_means = df_transformed[taxa_cols].mean(axis=1)
    df_transformed[taxa_cols] = df_transformed[taxa_cols].sub(row_means, axis=0)
    
    return df_transformed

def prepare_features(df):
    """
    Prepare features (CLR-transformed taxa + covariates) and target.
    """
    if 'z_score' not in df.columns:
        logger.error("Target column 'z_score' not found.")
        return None, None
    
    target = df['z_score']
    
    # Identify covariates to keep
    covariates = ['age', 'sex', 'bmi']
    # Ensure covariates exist, if not, drop them from the list to avoid errors
    available_covariates = [c for c in covariates if c in df.columns]
    
    # Drop non-feature columns
    drop_cols = ['participant_id', 'sample_id', 'taxon_name', 'task_type', 'z_score']
    drop_cols = [c for c in drop_cols if c in df.columns]
    
    # Get all numeric columns first
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Features = numeric cols - (covariates + drop_cols) - z_score
    # Actually, we want: taxa (numeric) + available_covariates
    # Let's just select available_covariates and all other numeric cols except z_score and drop_cols
    
    feature_cols = []
    for col in numeric_cols:
        if col == 'z_score':
            continue
        if col in drop_cols:
            continue
        feature_cols.append(col)
    
    # Explicitly ensure covariates are included if they are not already in numeric_cols (e.g. sex as string)
    for cov in available_covariates:
        if cov not in feature_cols:
            feature_cols.append(cov)
    
    # Filter to only existing columns
    feature_cols = [c for c in feature_cols if c in df.columns]
    
    if not feature_cols:
        logger.error("No feature columns found.")
        return None, None

    features = df[feature_cols].copy()
    
    # Apply CLR to taxa columns within features
    # Re-identify taxa cols within features
    taxa_in_features = [c for c in feature_cols if c not in available_covariates and c not in drop_cols]
    if taxa_in_features:
        # Apply CLR logic directly on the subset
        pseudo_count = 1e-6
        log_vals = np.log(features[taxa_in_features] + pseudo_count)
        row_means = log_vals.mean(axis=1)
        features[taxa_in_features] = log_vals.sub(row_means, axis=0)

    return features, target

def fit_lasso_elasticnet(X, y):
    """
    Fit LASSO/Elastic Net model.
    """
    if X is None or y is None or len(X) == 0:
        logger.warning("Empty input for model fitting.")
        return None
    
    # Handle non-numeric columns (e.g. 'sex' might be string)
    X_numeric = X.select_dtypes(include=[np.number])
    if X_numeric.empty:
        logger.error("No numeric features available after filtering.")
        return None
    
    # Drop rows with missing values in X or y
    valid_mask = X_numeric.notna().all(axis=1) & y.notna()
    X_clean = X_numeric[valid_mask]
    y_clean = y[valid_mask]
    
    if len(X_clean) == 0:
        logger.warning("No valid samples after cleaning.")
        return None

    # Use ElasticNet with l1_ratio=0.5 (Elastic Net)
    # Normalize=True to handle different scales (important for CLR + covariates)
    model = ElasticNet(l1_ratio=0.5, random_state=42, normalize=True, max_iter=10000)
    
    try:
        model.fit(X_clean, y_clean)
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None
    
    # Calculate R2
    try:
        r2 = model.score(X_clean, y_clean)
    except Exception:
        r2 = np.nan
    
    results = {
        "model_type": "ElasticNet (LASSO/Elastic Net)",
        "associational_framing": "This result is associational only. It does not imply causation.",
        "l1_ratio": 0.5,
        "alpha": model.alpha,
        "coefficients": dict(zip(X_clean.columns, model.coef_.tolist())),
        "intercept": float(model.intercept_),
        "r2_score": float(r2),
        "n_samples": int(len(X_clean)),
        "n_features": int(X_clean.shape[1])
    }
    
    return results

def save_results(results):
    """
    Save regression results to JSON with explicit associational labeling.
    """
    output_dir = get_data_processed_path()
    ensure_directory(output_dir)
    output_path = output_dir / "regression_results.json"
    
    if results is None:
        results = {
            "status": "N/A",
            "reason": "Data Gap - No merged dataset found",
            "associational_framing": "This result is associational only. It does not imply causation."
        }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved regression results to {output_path}")

def main():
    logger.info("Starting regression analysis (T023)")
    
    df = load_merged_data()
    if df is None:
        # Graceful exit as per spec: "exit gracefully with code 0 and log N/A - Data Gap"
        # We already logged "N/A - Data Gap" in load_merged_data
        # Save a result indicating N/A
        save_results(None)
        return

    X, y = prepare_features(df)
    if X is None or y is None:
        logger.warning("Could not prepare features. Skipping.")
        save_results(None)
        return

    results = fit_lasso_elasticnet(X, y)
    save_results(results)
    logger.info("Regression analysis complete.")

if __name__ == "__main__":
    main()