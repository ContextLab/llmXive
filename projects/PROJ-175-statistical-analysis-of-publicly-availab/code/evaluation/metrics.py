"""
Evaluation metrics calculation for logistic and Bayesian models.

Calculates AUC, Precision, Recall, and generates Calibration Plots.
"""
import os
import sys
import json
import pickle
import warnings
from pathlib import Path
from typing import Dict, Tuple, Optional, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_auc_score, 
    precision_score, 
    recall_score, 
    f1_score, 
    precision_recall_curve,
    roc_curve,
    brier_score_loss,
    calibration_curve
)
from sklearn.model_selection import cross_val_predict
from scipy.interpolate import interp1d

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.memory_monitor import check_memory_limit

# Constants
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Paths
DATA_DIR = project_root / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = project_root / "models"
EVALUATION_DIR = project_root / "evaluation"
FIGURES_DIR = DATA_DIR / "figures"

# Ensure directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

def load_test_data() -> pd.DataFrame:
    """
    Load the test split data.
    Expects the processed data split by T019 to be available.
    """
    test_path = PROCESSED_DIR / "test_split.parquet"
    if not test_path.exists():
        raise FileNotFoundError(f"Test split not found at {test_path}. Run T019 first.")
    
    df = pd.read_parquet(test_path)
    return df

def load_models() -> Dict[str, Any]:
    """
    Load the fitted logistic and Bayesian models.
    Expects models saved by T022 and T025.
    """
    logistic_path = MODELS_DIR / "logistic_model.pkl"
    bayesian_path = MODELS_DIR / "bayesian_model.pkl"
    
    if not logistic_path.exists():
        raise FileNotFoundError(f"Logistic model not found at {logistic_path}. Run T022 first.")
    
    # Note: Bayesian model loading depends on how T025 saves it. 
    # Assuming it saves the trace or a wrapper object.
    # If T025 saves a wrapper, we load it. If it saves just the trace, we might need to reconstruct.
    # For this implementation, we assume a wrapper object 'BayesianModel' exists or we load the trace.
    # Since T025 is implemented, we assume it saves a serializable object or we load the .pkl.
    
    if not bayesian_path.exists():
        # Fallback if Bayesian model is not yet saved or saved differently
        # This might happen if T025 hasn't run or failed.
        raise FileNotFoundError(f"Bayesian model not found at {bayesian_path}. Run T025 first.")
    
    with open(logistic_path, 'rb') as f:
        logistic_model = pickle.load(f)
    
    with open(bayesian_path, 'rb') as f:
        bayesian_model = pickle.load(f)
        
    return {
        "logistic": logistic_model,
        "bayesian": bayesian_model
    }

def get_predictions(
    df: pd.DataFrame, 
    models: Dict[str, Any]
) -> Tuple[pd.Series, pd.Series]:
    """
    Get predicted probabilities for the test set from both models.
    
    Args:
        df: Test dataframe with features and target 'compatible'
        models: Dictionary containing fitted models
        
    Returns:
        Tuple of (logistic_probs, bayesian_probs)
    """
    # Prepare features (assuming columns are consistent with training)
    # The target column is 'compatible' based on typical schema
    feature_cols = [col for col in df.columns if col not in ['compatible', 'pair_id', 'ingredient_a', 'ingredient_b']]
    X_test = df[feature_cols]
    
    # Logistic Regression
    # Assuming logistic_model is a fitted sklearn LogisticRegression or similar
    # with a predict_proba method.
    logistic_probs = models["logistic"].predict_proba(X_test)[:, 1]
    
    # Bayesian Model
    # Assuming bayesian_model is a wrapper that has a method to get posterior predictive means
    # or we compute it from the trace.
    # If T025 saved a 'predict_proba' compatible object:
    if hasattr(models["bayesian"], 'predict_proba'):
        bayesian_probs = models["bayesian"].predict_proba(X_test)[:, 1]
    else:
        # Fallback: if it's a raw trace or we need to compute manually
        # This part depends heavily on T025's output format.
        # Assuming a standard wrapper that takes X and returns probs.
        # If T025 output is just a trace, we might need to sample from it.
        # For robustness, let's assume T025 produced a 'predict_proba' method.
        # If not, we raise an error to force T025 to be fixed.
        raise NotImplementedError(
            "Bayesian model in T025 must expose a predict_proba(X) method returning probabilities."
        )
    
    return logistic_probs, bayesian_probs

def calculate_metrics(
    y_true: np.ndarray, 
    y_prob: np.ndarray, 
    model_name: str
) -> Dict[str, float]:
    """
    Calculate standard classification metrics.
    """
    # Threshold for binary classification (default 0.5)
    y_pred = (y_prob >= 0.5).astype(int)
    
    metrics = {
        "model": model_name,
        "auc": float(roc_auc_score(y_true, y_prob)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier": float(brier_score_loss(y_true, y_prob))
    }
    
    return metrics

def generate_calibration_plot(
    y_true: np.ndarray, 
    y_prob: np.ndarray, 
    model_name: str,
    save_path: Path
) -> None:
    """
    Generate and save a calibration plot.
    """
    plt.figure(figsize=(8, 6))
    
    # Calculate calibration curve
    # Using 10 bins
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, y_prob, n_bins=10
    )
    
    plt.plot(mean_predicted_value, fraction_of_positives, "s-", label=model_name)
    plt.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
    
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives")
    plt.title(f"Calibration Plot - {model_name}")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    
    print(f"Calibration plot saved to {save_path}")

def main():
    """
    Main execution function for T029.
    Calculates metrics and generates plots for both models.
    """
    print("Starting T029: Evaluation Metrics Calculation...")
    
    # Check memory limit
    check_memory_limit(6.0)
    
    # Load data
    print("Loading test data...")
    df = load_test_data()
    y_true = df['compatible'].values
    
    # Load models
    print("Loading models...")
    models = load_models()
    
    # Get predictions
    print("Generating predictions...")
    logistic_probs, bayesian_probs = get_predictions(df, models)
    
    # Calculate metrics
    print("Calculating metrics...")
    logistic_metrics = calculate_metrics(y_true, logistic_probs, "Logistic Regression")
    bayesian_metrics = calculate_metrics(y_true, bayesian_probs, "Bayesian Hierarchical")
    
    # Save metrics to JSON
    metrics_output = {
        "logistic": logistic_metrics,
        "bayesian": bayesian_metrics
    }
    
    metrics_path = EVALUATION_DIR / "model_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics_output, f, indent=2)
    
    print(f"Metrics saved to {metrics_path}")
    print(json.dumps(metrics_output, indent=2))
    
    # Generate calibration plots
    print("Generating calibration plots...")
    
    cal_logistic_path = FIGURES_DIR / "calibration_logistic.png"
    cal_bayesian_path = FIGURES_DIR / "calibration_bayesian.png"
    
    generate_calibration_plot(y_true, logistic_probs, "Logistic Regression", cal_logistic_path)
    generate_calibration_plot(y_true, bayesian_probs, "Bayesian Hierarchical", cal_bayesian_path)
    
    print("T029 completed successfully.")
    return metrics_output

if __name__ == "__main__":
    main()
