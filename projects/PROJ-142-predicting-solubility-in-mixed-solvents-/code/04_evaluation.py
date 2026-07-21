"""
Evaluation module for solubility prediction models.

Implements evaluation logic to calculate RMSE, MAE, and R² for all models
on a hold-out test set. Reads trained models from data/artifacts/trained_models.pkl
and outputs detailed metrics to data/artifacts/evaluation_results.json.
"""
import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from utils.constants import DATA_DIR, ARTIFACTS_DIR
from utils.errors import CustomDataError

# Import evaluation utilities from training module to ensure consistency
# Note: We assume train_xgboost, train_random_forest, train_abraham_baseline
# and their evaluation logic are consistent with how models were saved.
# We will re-implement the metric calculations here to avoid circular deps if needed,
# or import if the training module exposes them cleanly.
# Given the API surface, we will implement metrics directly here to be safe.

def load_test_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the hold-out test set features and labels.
    Expects the processed dataset from T018: data/processed/solubility_features.csv
    and a predefined split or a separate test file if generated during training.
    For this implementation, we assume the training script saved a test split
    or we load the full processed data and re-split with a fixed seed if not found.
    
    However, T021/T022 should have saved the test set features/labels or the models
    were trained on a split. To be robust, we look for `data/processed/test_features.npy`
    and `data/processed/test_labels.npy` which are standard outputs of a split step.
    If not found, we attempt to load the full CSV and re-split (last resort).
    """
    test_feat_path = DATA_DIR / "processed" / "test_features.npy"
    test_lab_path = DATA_DIR / "processed" "test_labels.npy"
    
    if test_feat_path.exists() and test_lab_path.exists():
        X_test = np.load(test_feat_path)
        y_test = np.load(test_lab_path)
        return X_test, y_test
    
    # Fallback: Load full CSV and re-split (should ideally not happen in pipeline)
    import pandas as pd
    from sklearn.model_selection import train_test_split
    
    csv_path = DATA_DIR / "processed" / "solubility_features.csv"
    if not csv_path.exists():
        raise CustomDataError(f"Processed dataset not found at {csv_path}. "
                              "Ensure T018 has completed.")
    
    df = pd.read_csv(csv_path)
    # Assume last column is target 'solubility' or similar, and others are features
    # Adjust column names based on actual T018 output schema
    if 'solubility' not in df.columns:
        # Try to find target column
        target_col = [c for c in df.columns if 'solubility' in c.lower()][0]
    else:
        target_col = 'solubility'
        
    X = df.drop(columns=[target_col]).values
    y = df[target_col].values
    
    # Re-split with fixed seed for reproducibility
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Save the split for future runs
    np.save(test_feat_path, X_test)
    np.save(test_lab_path, y_test)
    
    return X_test, y_test

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate RMSE, MAE, and R².
    """
    if len(y_true) != len(y_pred):
        raise CustomDataError("y_true and y_pred must have the same length.")
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # RMSE
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    # MAE
    mae = np.mean(np.abs(y_true - y_pred))
    
    # R²
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2)
    }

def load_models() -> Dict[str, Any]:
    """
    Load trained models from data/artifacts/trained_models.pkl.
    """
    models_path = ARTIFACTS_DIR / "trained_models.pkl"
    if not models_path.exists():
        raise CustomDataError(
            f"Trained models not found at {models_path}. "
            "Ensure T021 and T022 have completed successfully."
        )
    
    with open(models_path, 'rb') as f:
        models = pickle.load(f)
    
    return models

def evaluate_models(models: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Dict[str, float]]:
    """
    Evaluate each model on the test set and return metrics.
    Expected model keys: 'xgboost', 'random_forest', 'abraham_baseline'
    """
    results = {}
    
    for name, model in models.items():
        try:
            predictions = model.predict(X_test)
            metrics = calculate_metrics(y_test, predictions)
            results[name] = metrics
            print(f"Evaluation for {name}: RMSE={metrics['rmse']:.4f}, "
                  f"MAE={metrics['mae']:.4f}, R²={metrics['r2']:.4f}")
        except Exception as e:
            print(f"Error evaluating {name}: {e}")
            results[name] = {"error": str(e)}
    
    return results

def save_results(results: Dict[str, Dict[str, float]], output_path: Path):
    """
    Save evaluation results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Evaluation results saved to {output_path}")

def main():
    """
    Main entry point for evaluation.
    """
    print("Starting model evaluation (T023)...")
    
    # Load models
    models = load_models()
    
    # Load test data
    X_test, y_test = load_test_data()
    
    # Evaluate
    results = evaluate_models(models, X_test, y_test)
    
    # Save results
    output_path = ARTIFACTS_DIR / "evaluation_results.json"
    save_results(results, output_path)
    
    print("Evaluation complete.")
    return results

if __name__ == "__main__":
    main()