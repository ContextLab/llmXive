import os
import sys
import logging
import pickle
import json
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
from utils.logging_config import get_logger

logger = get_logger(__name__)

def compute_null_model_r2(y_true: np.ndarray) -> float:
    """Compute R2 of null model (predicting mean)."""
    y_pred = np.full_like(y_true, np.mean(y_true))
    return r2_score(y_true, y_pred)

def evaluate_model(model, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """Evaluate model and return metrics."""
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    null_r2 = compute_null_model_r2(y)
    return {
        "r2": r2,
        "rmse": rmse,
        "null_r2": null_r2,
        "improvement": r2 - null_r2
    }

def load_evaluation_data(data_path: Path) -> Dict[str, np.ndarray]:
    """Load evaluation data from the test split parquet file."""
    if not data_path.exists():
        raise FileNotFoundError(f"Evaluation data file not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    
    # Ensure required columns exist
    required_cols = ['smiles', 'target']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in evaluation data: {missing_cols}")
    
    # Separate features from target
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in evaluation data")
    
    X = df[feature_cols].values
    y = df['target'].values
    
    return {"X": X, "y": y}

def run_evaluation(model_path: Path, data_path: Path, output_path: Path) -> None:
    """Run model evaluation and save results to JSON."""
    # Load model
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    # Load evaluation data
    data = load_evaluation_data(data_path)
    
    # Evaluate model
    metrics = evaluate_model(model, data["X"], data["y"])
    
    # Log results
    logger.info(f"Evaluation metrics: {metrics}")
    logger.info(f"R² score: {metrics['r2']:.4f}")
    logger.info(f"RMSE: {metrics['rmse']:.4f}")
    logger.info(f"Null model R²: {metrics['null_r2']:.4f}")
    logger.info(f"Improvement over null: {metrics['improvement']:.4f}")
    
    # Check if model outperforms null model
    if metrics['r2'] > metrics['null_r2']:
        logger.info("✓ Model outperforms null model (R² > 0)")
    else:
        logger.warning("✗ Model does not outperform null model (R² ≤ 0)")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save metrics to JSON
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")

def main() -> None:
    """Main entry point for model evaluation."""
    # Default paths
    model_path = Path("data/processed/model.pkl")
    data_path = Path("data/processed/splits_test.parquet")
    output_path = Path("data/processed/analysis/evaluation.json")
    
    # Run evaluation
    run_evaluation(model_path, data_path, output_path)

if __name__ == "__main__":
    main()