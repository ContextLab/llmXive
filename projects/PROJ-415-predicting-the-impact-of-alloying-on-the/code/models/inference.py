import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split

from config import PROJECT_ROOT, MODELS_DIR, DATA_DIR, RANDOM_SEED
from utils.logging import get_logger
from data.descriptors import compute_descriptors_dataframe

logger = get_logger(__name__)

def load_model(model_path: str):
    """Load a trained model from a pickle file."""
    logger.info(f"Loading model from {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def prepare_test_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the curated data, compute descriptors, and split into features/target
    using the same random state as the training phase to ensure consistency.
    """
    curated_path = DATA_DIR / "curated" / "filtered.csv"
    if not curated_path.exists():
        raise FileNotFoundError(f"Curated data not found at {curated_path}. Run T014 first.")
    
    df = pd.read_csv(curated_path)
    
    # Ensure necessary columns exist for descriptor calculation
    required_cols = ['solute_symbol', 'host_symbol', 'activation_energy_eV']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in curated data: {missing}")
    
    # Compute descriptors (size_mismatch, etc.)
    feature_df = compute_descriptors_dataframe(df)
    
    # Define target
    y = df['activation_energy_eV']
    
    # Use the defined random seed to replicate the split
    seed = RANDOM_SEED
    
    X = feature_df
    
    # Perform the split exactly as training likely did
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, shuffle=True
    )
    
    return X_test, y_test

def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluate a model on the test set and return R2, RMSE, MAE.
    """
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    
    return {
        "r2": float(r2),
        "rmse": float(rmse),
        "mae": float(mae)
    }

def run_inference():
    """
    Main entry point for T025.
    Loads RF and GB models, evaluates them on the held-out test set,
    and saves metrics to models/metrics.json.
    """
    logger.info("Starting inference and evaluation for T025")
    
    # Paths
    rf_model_path = MODELS_DIR / "final_rf.pkl"
    gb_model_path = MODELS_DIR / "final_gb.pkl"
    metrics_output_path = MODELS_DIR / "metrics.json"
    
    # Ensure output directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Load models
    try:
        rf_model = load_model(str(rf_model_path))
        logger.info("Random Forest model loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"RF Model not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading RF model: {e}")
        raise
    
    try:
        gb_model = load_model(str(gb_model_path))
        logger.info("Gradient Boosting model loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"GB Model not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading GB model: {e}")
        raise
    
    # Prepare test data
    try:
        X_test, y_test = prepare_test_data()
        logger.info(f"Test set prepared: {len(y_test)} samples")
    except Exception as e:
        logger.error(f"Error preparing test data: {e}")
        raise
    
    # Evaluate RF
    logger.info("Evaluating Random Forest...")
    rf_metrics = evaluate_model(rf_model, X_test, y_test)
    logger.info(f"RF Metrics: {rf_metrics}")
    
    # Evaluate GB
    logger.info("Evaluating Gradient Boosting...")
    gb_metrics = evaluate_model(gb_model, X_test, y_test)
    logger.info(f"GB Metrics: {gb_metrics}")
    
    # Compile results
    results = {
        "random_forest": rf_metrics,
        "gradient_boosting": gb_metrics
    }
    
    # Save to JSON
    with open(metrics_output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Metrics saved to {metrics_output_path}")
    print(f"Inference complete. Metrics saved to {metrics_output_path}")
    return results

if __name__ == "__main__":
    run_inference()
