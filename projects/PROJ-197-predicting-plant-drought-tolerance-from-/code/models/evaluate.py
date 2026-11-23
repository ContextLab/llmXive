"""
Model evaluation module for calculating metrics and selecting best model.

Implements ROC-AUC calculation and DeLong's test.
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, ensure_directories
from utils.logging import DataPipelineLog
from utils.stats import delong_test_auc, calculate_roc_auc

logger = DataPipelineLog("evaluate")

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_LOGS = PROJECT_ROOT / "data" / "logs"

ensure_directories()

def load_test_data() -> Tuple[np.ndarray, np.ndarray]:
    """Load test data from saved npz file."""
    path = DATA_PROCESSED / "test_data.npz"
    if not path.exists():
        raise FileNotFoundError(f"Test data not found at {path}")
    
    data = np.load(path, allow_pickle=True)
    return data['X'], data['y']

def load_models() -> Dict[str, Any]:
    """Load trained models."""
    models = {}
    paths = {
        "rf": DATA_PROCESSED / "rf_model.joblib",
        "xgb": DATA_PROCESSED / "xgb_model.joblib",
        "knn": DATA_PROCESSED / "knn_model.joblib"
    }
    
    for name, path in paths.items():
        if path.exists():
            models[name] = joblib.load(path)
        else:
            logger.warning(f"Model {name} not found at {path}")
    
    return models

def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray) -> float:
    """
    Evaluate model and return ROC-AUC.
    
    Args:
        model: Trained model.
        X: Test features.
        y: Test labels.
    
    Returns:
        ROC-AUC score.
    """
    # Get probabilities
    if hasattr(model, 'predict_proba'):
        y_prob = model.predict_proba(X)[:, 1]
    else:
        y_prob = model.predict(X) # Fallback
    
    return calculate_roc_auc(y, y_prob)

def select_best_model(metrics: Dict[str, float]) -> str:
    """Select best model based on AUC."""
    return max(metrics, key=metrics.get)

def save_metrics(metrics: Dict[str, Any]) -> None:
    """Save metrics to JSON."""
    path = DATA_LOGS / "metrics.json"
    
    if path.exists():
        with open(path, 'r') as f:
            existing = json.load(f)
    else:
        existing = {}
    
    existing.update(metrics)
    
    with open(path, 'w') as f:
        json.dump(existing, f, indent=2)
    
    logger.info(f"Metrics saved to {path}")

def main():
    """Main entry point for evaluation."""
    logger.info("Starting model evaluation")
    
    # Load data
    X_test, y_test = load_test_data()
    
    # Load models
    models = load_models()
    
    if not models:
        raise RuntimeError("No models found. Ensure training has completed.")
    
    # Evaluate
    results = {}
    for name, model in models.items():
        auc = evaluate_model(model, X_test, y_test)
        results[f"{name}_auc"] = auc
        logger.info(f"{name} AUC: {auc:.4f}")
    
    # Select best
    best_model_name = select_best_model({k: v for k, v in results.items() if k.endswith('_auc')})
    logger.info(f"Best model: {best_model_name}")
    
    # DeLong's test: RF vs XGBoost vs KNN
    # We need probabilities for DeLong's test
    rf_model = models.get('rf')
    xgb_model = models.get('xgb')
    knn_model = models.get('knn')
    
    if rf_model and xgb_model:
        rf_prob = rf_model.predict_proba(X_test)[:, 1]
        xgb_prob = xgb_model.predict_proba(X_test)[:, 1]
        
        # DeLong's test RF vs XGBoost
        z_stat, p_val = delong_test_auc(y_test, rf_prob, xgb_prob)
        logger.record("delong_rf_vs_xgb", {"z_stat": float(z_stat), "p_val": float(p_val)})
        
        results["delong_rf_vs_xgb_p"] = float(p_val)
    
    # Save metrics
    save_metrics(results)
    
    logger.info("Evaluation complete.")

if __name__ == "__main__":
    main()
