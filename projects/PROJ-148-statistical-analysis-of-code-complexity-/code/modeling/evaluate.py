from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.calibration import CalibrationDisplay

# Ensure we can import from the project root if run as a script
# but rely on the project structure for normal execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger
from utils.config import get_seed

logger = get_logger(__name__)

def load_test_data() -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Load the preprocessed test dataset.
    Expects data to be at data/processed/test_data.csv
    Returns (X_test, y_test, project_ids)
    """
    path = Path("data/processed/test_data.csv")
    if not path.exists():
        raise FileNotFoundError(f"Test data not found at {path}. "
                                "Please run the data pipeline first.")
    
    df = pd.read_csv(path)
    
    # Identify feature columns (exclude target and project_id)
    exclude_cols = ['bug_label', 'project_id', 'file_path']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X_test = df[feature_cols]
    y_test = df['bug_label']
    project_ids = df['project_id']
    
    logger.info(f"Loaded test data: {len(X_test)} samples, {len(feature_cols)} features")
    return X_test, y_test, project_ids

def load_model(model_path: str = "data/model/primary.pkl"):
    """
    Load the trained primary model.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}. "
                                "Please run the training pipeline first.")
    
    model = joblib.load(path)
    logger.info(f"Loaded model from {path}")
    return model

def compute_metrics(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Compute ROC-AUC, PR-AUC, and Brier score.
    Asserts ROC-AUC >= 0.50 baseline.
    """
    # Get probability predictions
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    roc_auc = roc_auc_score(y_test, y_proba)
    pr_auc = average_precision_score(y_test, y_proba)
    brier = brier_score_loss(y_test, y_proba)
    
    logger.info(f"ROC-AUC: {roc_auc:.4f}")
    logger.info(f"PR-AUC: {pr_auc:.4f}")
    logger.info(f"Brier Score: {brier:.4f}")
    
    # Assert baseline requirement
    if roc_auc < 0.50:
        raise AssertionError(f"ROC-AUC ({roc_auc:.4f}) is below baseline (0.50). "
                             "Model is performing worse than random chance.")
    
    return {
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "brier_score": float(brier),
        "samples": int(len(y_test))
    }

def plot_calibration(model, X_test: pd.DataFrame, y_test: pd.Series, output_path: str):
    """
    Generate and save a calibration plot.
    """
    y_proba = model.predict_proba(X_test)[:, 1]
    
    plt.figure(figsize=(8, 6))
    disp = CalibrationDisplay.from_predictions(
        y_test, y_proba, n_bins=10, strategy='uniform', ax=plt.gca()
    )
    
    plt.title(f"Calibration Plot (ROC-AUC: {disp.y_score.mean():.3f})")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives")
    plt.legend(loc="lower right")
    plt.grid(True)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved calibration plot to {output_path}")

def evaluate_model(X_test: pd.DataFrame, y_test: pd.Series, model, metrics_path: str = "data/model/evaluation_metrics.json"):
    """
    Main evaluation routine: compute metrics, generate plots, save results.
    """
    # Compute metrics
    metrics = compute_metrics(model, X_test, y_test)
    
    # Generate calibration plot
    cal_plot_path = "figures/calibration_plot.png"
    plot_calibration(model, X_test, y_test, cal_plot_path)
    metrics["calibration_plot"] = cal_plot_path
    
    # Save metrics to JSON
    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Evaluation complete. Metrics saved to {metrics_path}")
    return metrics

def main():
    """
    Entry point for the evaluation script.
    """
    parser = argparse.ArgumentParser(description="Evaluate bug prediction model performance.")
    parser.add_argument("--model", type=str, default="data/model/primary.pkl",
                      help="Path to the model pickle file.")
    parser.add_argument("--test-data", type=str, default="data/processed/test_data.csv",
                      help="Path to the test data CSV.")
    parser.add_argument("--metrics-output", type=str, default="data/model/evaluation_metrics.json",
                      help="Path to save evaluation metrics JSON.")
    parser.add_argument("--plot-output", type=str, default="figures/calibration_plot.png",
                      help="Path to save calibration plot.")
    args = parser.parse_args()

    # Set random seed for reproducibility
    set_random_seed(get_seed())

    try:
        logger.info("Starting model evaluation...")
        
        # Load data and model
        X_test, y_test, _ = load_test_data()
        model = load_model(args.model)
        
        # Run evaluation
        metrics = evaluate_model(X_test, y_test, model, args.metrics_output)
        
        logger.info("Evaluation completed successfully.")
        print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"PR-AUC: {metrics['pr_auc']:.4f}")
        
    except FileNotFoundError as e:
        logger.error(f"Data or model not found: {e}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Model performance below baseline: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()