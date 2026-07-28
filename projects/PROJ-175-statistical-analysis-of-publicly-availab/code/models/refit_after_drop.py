"""
Task T040b: Re-fit Model after Predictor Drop

If T040 drops a predictor (indicated by data/final_predictors.json),
re-fit the logistic regression with the reduced set.
If no predictor was dropped, pass through the original model results
(by loading the existing logistic_results.json).

Output: data/final/logistic_results_refit.json
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import pickle
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/model_fitting_refit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
FINAL_DIR = DATA_DIR / "final"

def load_final_predictors():
    """
    Load the list of predictors after T040 resolution.
    Returns a list of strings.
    """
    path = FINAL_DIR / "final_predictors.json"
    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"final_predictors.json not found. Run T040 first.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle potential schema variations
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'predictors' in data:
        return data['predictors']
    else:
        logger.error(f"Unexpected format in {path}: {data}")
        raise ValueError("final_predictors.json must contain a list of predictors")

def load_training_data():
    """
    Load the processed training data.
    Expected schema: rows are ingredient pairs, columns include predictors and 'compatibility_label'.
    """
    # T019 produces train_set.parquet
    path = DATA_DIR / "processed" / "train_set.parquet"
    if not path.exists():
        logger.error(f"Training data not found: {path}")
        raise FileNotFoundError(f"train_set.parquet not found. Run T019 first.")
    
    df = pd.read_parquet(path)
    
    # Verify required columns exist
    required_cols = ['compatibility_label']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in training data: {missing}")
    
    logger.info(f"Loaded training data with shape {df.shape}")
    return df

def prepare_features(df, predictors):
    """
    Prepare X and y for the model.
    """
    # Check if all predictors are in the dataframe
    available_predictors = [p for p in predictors if p in df.columns]
    dropped_predictors = [p for p in predictors if p not in df.columns]
    
    if dropped_predictors:
        logger.warning(f"Predictors in final list but not in data (dropped earlier?): {dropped_predictors}")
    
    if not available_predictors:
        raise ValueError("No predictors available to fit the model. Check data schema and final_predictors.json.")
    
    X = df[available_predictors].fillna(0)
    y = df['compatibility_label']
    
    # Handle potential all-zero columns (common after dropping correlated features)
    if X.std().min() == 0:
        logger.warning("Detected constant features. Removing them.")
        X = X.loc[:, X.std() > 0]
    
    return X, y, available_predictors

def fit_logistic_model(X, y, predictors):
    """
    Fit a regularized logistic regression model.
    """
    logger.info(f"Fitting Logistic Regression with predictors: {predictors}")
    
    # Standardize features for better regularization performance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit model with L2 regularization (default in sklearn)
    # C=1.0 is default, can be tuned if needed
    model = LogisticRegression(
        penalty='l2',
        C=1.0,
        solver='lbfgs',
        max_iter=1000,
        random_state=42
    )
    
    model.fit(X_scaled, y)
    
    # Generate predictions for metrics
    y_pred_proba = model.predict_proba(X_scaled)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # Calculate metrics
    auc = roc_auc_score(y, y_pred_proba)
    precision = precision_score(y, y_pred, zero_division=0)
    recall = recall_score(y, y_pred, zero_division=0)
    
    # Map coefficients back to predictor names
    coef_dict = {
        name: float(coef) 
        for name, coef in zip(predictors, model.coef_[0])
    }
    intercept = float(model.intercept_[0])
    
    results = {
        "model_type": "LogisticRegression_L2",
        "predictors_used": predictors,
        "n_samples": len(y),
        "metrics": {
            "auc": float(auc),
            "precision": float(precision),
            "recall": float(recall),
            "roc_auc": float(auc)
        },
        "coefficients": coef_dict,
        "intercept": intercept,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "converged": model.converged_,
        "status": "SUCCESS"
    }
    
    logger.info(f"Model fitted successfully. AUC: {auc:.4f}")
    return results, model, scaler

def main():
    logger.info("Starting T040b: Re-fit Model after Predictor Drop")
    
    # Ensure output directory exists
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load final predictors (post-T040)
        predictors = load_final_predictors()
        logger.info(f"Final predictors list: {predictors}")
        
        # 2. Load training data
        df = load_training_data()
        
        # 3. Prepare features
        X, y, used_predictors = prepare_features(df, predictors)
        logger.info(f"Features shape after preparation: {X.shape}")
        
        # 4. Fit the model
        results, model, scaler = fit_logistic_model(X, y, used_predictors)
        
        # 5. Save results
        output_path = FINAL_DIR / "logistic_results_refit.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
        # 6. Save model artifacts for downstream evaluation
        model_path = FINAL_DIR / "refitted_model.pkl"
        scaler_path = FINAL_DIR / "refitted_scaler.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        
        logger.info(f"Model and scaler saved to {model_path} and {scaler_path}")
        
        print(json.dumps({"status": "SUCCESS", "output_file": str(output_path)}))
        
    except Exception as e:
        logger.error(f"Error during T040b execution: {e}", exc_info=True)
        # Write a failure log so the pipeline knows what happened
        error_log_path = FINAL_DIR / "logistic_results_refit_error.json"
        with open(error_log_path, 'w') as f:
            json.dump({
                "status": "FAILED",
                "error": str(e),
                "traceback": str(sys.exc_info()[2])
            }, f, indent=2)
        raise

if __name__ == "__main__":
    main()