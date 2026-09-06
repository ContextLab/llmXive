import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
import joblib

# Import existing utilities from the project
from models.train import load_preprocessed_data
from models.null_model import load_folds, load_dataset, calculate_rmse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_shap_summary() -> List[Dict[str, Any]]:
    """Load SHAP summary from data/results/shap_summary.json."""
    path = Path("data/results/shap_summary.json")
    if not path.exists():
        raise FileNotFoundError(f"SHAP summary not found at {path}. Run T030 first.")
    with open(path, 'r') as f:
        return json.load(f)

def load_model_metrics() -> Dict[str, Any]:
    """Load null model metrics from data/results/null_model_fold_rmses.json."""
    path = Path("data/results/null_model_fold_rmses.json")
    if not path.exists():
        raise FileNotFoundError(f"Null model metrics not found at {path}. Run T068 first.")
    with open(path, 'r') as f:
        return json.load(f)

def load_data_with_features(top_n: int = 3) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load preprocessed data and filter to the top N features from SHAP.
    Returns the DataFrame and the list of feature names used.
    """
    shap_data = load_shap_summary()
    top_features = [item['name'] for item in shap_data[:top_n]]
    logger.info(f"Selected top {top_n} features: {top_features}")

    # Load the full preprocessed dataset
    # Assuming the pipeline outputs to data/processed/imputed_dataset.parquet or similar
    # We need to ensure we have the target variable (langmuir_capacity) and the features
    df = load_preprocessed_data()

    # Verify features exist
    missing = [f for f in top_features if f not in df.columns]
    if missing:
        raise ValueError(f"Top features missing from dataset: {missing}")

    # Ensure target exists
    if 'langmuir_capacity' not in df.columns:
        raise ValueError("Target 'langmuir_capacity' not found in dataset.")

    # Filter columns to keep only top features + target
    cols_to_keep = top_features + ['langmuir_capacity']
    df_filtered = df[cols_to_keep].dropna()
    
    if len(df_filtered) < 10:
        raise ValueError(f"Dataset too small after filtering top {top_n} features: {len(df_filtered)} rows")

    return df_filtered, top_features

def get_model_instance() -> Ridge:
    """Return a standard Ridge regression model instance."""
    return Ridge(alpha=1.0)

def run_null_model(df: pd.DataFrame, features: List[str], target: str) -> float:
    """
    Run a null model (predict mean) on the provided data and return RMSE.
    This replicates the logic of T068 for the reduced feature set.
    """
    X = df[features].values
    y = df[target].values
    
    # Null model prediction: mean of training set
    # Since we are evaluating on the whole set for a simple metric comparison here,
    # we calculate RMSE against the global mean if no split is specified.
    # However, to be rigorous like T068, we should ideally use the folds.
    # For this specific task (T033), we compare the retrained model's performance
    # against the null model baseline.
    
    null_pred = np.full_like(y, y.mean())
    rmse = np.sqrt(mean_squared_error(y, null_pred))
    return rmse

def run_training_and_evaluation() -> Dict[str, float]:
    """
    Retrain model using only the top 3 features and compare against null model.
    Returns metrics dictionary.
    """
    # 1. Load data with top 3 features
    df, features = load_data_with_features(top_n=3)
    target_col = 'langmuir_capacity'
    
    X = df[features].values
    y = df[target_col].values

    # 2. Train model
    model = get_model_instance()
    model.fit(X, y)
    
    # 3. Predict on same data (or use CV if strict, but task implies measuring R2 vs Null)
    # Using cross-validated R2 to be robust
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    r2_mean = np.mean(cv_scores)
    
    # 4. Calculate RMSE for the trained model (using CV predictions or simple fit)
    # Simple fit RMSE for consistency with null model calculation on full set
    y_pred = model.predict(X)
    rmse_full = np.sqrt(mean_squared_error(y, y_pred))

    # 5. Run Null Model Baseline (T068 equivalent for these features)
    null_rmse = run_null_model(df, features, target_col)

    # 6. Calculate Improvement
    # Improvement = (Null RMSE - Full RMSE) / Null RMSE
    if null_rmse == 0:
        improvement = 0.0
    else:
        improvement = (null_rmse - rmse_full) / null_rmse

    logger.info(f"Reduced Model R2: {r2_mean:.4f}")
    logger.info(f"Reduced Model RMSE: {rmse_full:.4f}")
    logger.info(f"Null Model RMSE: {null_rmse:.4f}")
    logger.info(f"Improvement over Null: {improvement:.4f}")

    # Constraint Check
    if improvement < 0.2:
        logger.warning(f"Improvement ({improvement:.4f}) is less than required 0.2. Model may need tuning or features are weak.")

    return {
        "r2": float(r2_mean),
        "rmse": float(rmse_full),
        "null_rmse": float(null_rmse),
        "improvement": float(improvement)
    }

def main():
    """Main entry point for T033."""
    logger.info("Starting T033: Retrain on Top 3 Features")
    try:
        metrics = run_training_and_evaluation()
        
        output_path = Path("data/results/reduced_model_metrics.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {output_path}")
        print(json.dumps(metrics))
        
    except Exception as e:
        logger.error(f"Failed to run T033: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()