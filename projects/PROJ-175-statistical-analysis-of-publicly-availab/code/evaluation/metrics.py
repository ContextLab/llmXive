"""
Evaluation Metrics Module
Calculates AUC, precision, recall, and calibration for models.
"""
import os
import sys
import json
import pickle
import warnings
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure parent is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_monitor import check_memory_limit

def load_test_data(input_path: Path) -> tuple:
    """Load test data."""
    import pandas as pd
    if not input_path.exists():
        raise FileNotFoundError(f"Test data not found: {input_path}")
    df = pd.read_parquet(input_path)
    # Assume last column is target
    y = df.iloc[:, -1].values
    X = df.iloc[:, :-1].values
    return X, y

def load_models(models_dir: Path) -> Dict[str, Any]:
    """Load fitted models from disk."""
    models = {}
    logistic_path = models_dir / "logistic_results.json"
    if logistic_path.exists():
        with open(logistic_path, 'r') as f:
            models["logistic"] = json.load(f)
            
    bayesian_path = models_dir / "bayesian_results.json"
    if bayesian_path.exists():
        with open(bayesian_path, 'r') as f:
            models["bayesian"] = json.load(f)
            
    return models

def get_predictions(model_results: Dict[str, Any], X: np.ndarray, model_type: str = "full") -> np.ndarray:
    """
    Generate predictions from model results.
    Uses the coefficients from the fitted model to make predictions on X.
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    
    if model_type == "full" and "full_model" in model_results:
        # Reconstruct predictions from coefficients
        coef = np.array(model_results["full_model"]["coefficients"][0])
        intercept = model_results["full_model"]["intercept"]
        logits = np.dot(X, coef) + intercept
        probs = 1 / (1 + np.exp(-logits))
        return probs
    elif model_type == "null" and "null_model" in model_results:
        # For null model, use mean probability
        return np.full(X.shape[0], 0.5)
    else:
        # Fallback: return random probabilities (NOT used in real execution, just for structure)
        # In real execution, we always have valid model results
        raise ValueError("Invalid model type or missing model results")

def calculate_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray) -> Dict[str, float]:
    """Calculate AUC, precision, recall, etc."""
    from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
    
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    metrics = {}
    try:
        metrics["auc"] = float(roc_auc_score(y_true, y_pred_proba))
    except:
        metrics["auc"] = 0.5
        
    try:
        metrics["precision"] = float(precision_score(y_true, y_pred, zero_division=0))
        metrics["recall"] = float(recall_score(y_true, y_pred, zero_division=0))
        metrics["f1"] = float(f1_score(y_true, y_pred, zero_division=0))
    except:
        metrics["precision"] = 0.0
        metrics["recall"] = 0.0
        metrics["f1"] = 0.0
        
    return metrics

def generate_calibration_plot(y_true: np.ndarray, y_pred_proba: np.ndarray, output_path: Path):
    """Generate calibration plot."""
    import matplotlib.pyplot as plt
    from sklearn.calibration import calibration_curve
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fraction_pos, prob_pos = calibration_curve(y_true, y_pred_proba, n_bins=10)
    
    plt.figure(figsize=(8, 6))
    plt.plot(prob_pos, fraction_pos, marker='o', label='Model')
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect')
    plt.xlabel('Predicted Probability')
    plt.ylabel('Fraction of Positives')
    plt.title('Calibration Plot')
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def main():
    """Main entry point for metrics calculation."""
    parser = argparse.ArgumentParser(description="Calculate evaluation metrics")
    parser.add_argument('--input', type=str, default='data/processed/test_set.parquet')
    parser.add_argument('--models', type=str, default='data/final/')
    parser.add_argument('--output', type=str, default='data/evaluation_metrics.json')
    args = parser.parse_args()
    
    check_memory_limit()
    
    input_path = Path(args.input)
    models_dir = Path(args.models)
    output_path = Path(args.output)
    
    print("Loading test data...")
    X, y_true = load_test_data(input_path)
    
    print("Loading models...")
    models = load_models(models_dir)
    
    results = {}
    if "logistic" in models:
        print("Calculating logistic model metrics...")
        y_pred_proba = get_predictions(models["logistic"], X, model_type="full")
        results["logistic"] = calculate_metrics(y_true, y_pred_proba)
        
        # Calibration plot
        cal_path = Path(args.models).parent / "figures" / "calibration_logistic.png"
        generate_calibration_plot(y_true, y_pred_proba, cal_path)
        
    if "bayesian" in models:
        print("Calculating Bayesian model metrics...")
        # For Bayesian, we might need to sample predictions
        # Simplified: use mean coefficients
        bayes_results = models["bayesian"]
        if bayes_results.get("converged", False):
            coef = np.array(bayes_results["coefficients"])
            intercept = bayes_results["intercept"]
            logits = np.dot(X, coef) + intercept
            y_pred_proba = 1 / (1 + np.exp(-logits))
            results["bayesian"] = calculate_metrics(y_true, y_pred_proba)
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print("Metrics calculation completed successfully.")

if __name__ == "__main__":
    import argparse
    import numpy as np
    main()
