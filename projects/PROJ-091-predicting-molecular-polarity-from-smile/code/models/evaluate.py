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
    """Load evaluation data."""
    df = pd.read_parquet(data_path)
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    X = df[feature_cols].values
    y = df['target'].values
    return {"X": X, "y": y}

def run_evaluation(model_path: Path, data_path: Path, output_path: Path) -> None:
    """Run model evaluation."""
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    data = load_evaluation_data(data_path)
    metrics = evaluate_model(model, data["X"], data["y"])
    
    logger.info(f"Evaluation metrics: {metrics}")
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

def main() -> None:
    """Main entry point."""
    model_path = Path("data/processed/model.pkl")
    data_path = Path("data/processed/splits_test.parquet")
    output_path = Path("data/processed/analysis/evaluation.json")
    run_evaluation(model_path, data_path, output_path)

if __name__ == "__main__":
    main()
