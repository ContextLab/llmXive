from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, calibration_curve, ConfusionMatrixDisplay
from sklearn.calibration import calibration_curve
import joblib

from utils.config import get_seed, get_config, set_random_seed
from utils.logging import get_logger

logger = get_logger(__name__)

def load_test_data() -> pd.DataFrame:
    """
    Load the preprocessed test dataset.
    Expects the file to be at data/processed/test.csv based on pipeline flow.
    """
    config = get_config()
    # The split_dataset task saves the test set here
    test_path = Path(config.data_dir) / "processed" / "test.csv"
    
    if not test_path.exists():
        # Fallback if processed directory structure differs, try direct path
        alt_path = Path(config.data_dir) / "test.csv"
        if alt_path.exists():
            test_path = alt_path
        else:
            raise FileNotFoundError(f"Test data not found at {test_path} or {alt_path}")
    
    logger.info(f"Loading test data from {test_path}")
    df = pd.read_csv(test_path)
    
    # Ensure target column exists
    if 'bug_label' not in df.columns:
        raise ValueError("Test data must contain 'bug_label' column")
        
    return df

def load_model(model_path: str = None):
    """
    Load the trained primary model.
    """
    config = get_config()
    if model_path is None:
        model_path = Path(config.output_dir) / "primary.pkl"
    else:
        model_path = Path(model_path)
        
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
        
    logger.info(f"Loading model from {model_path}")
    return joblib.load(model_path)

def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """
    Compute ROC-AUC and PR-AUC.
    Asserts ROC-AUC >= 0.50 as per requirement.
    """
    roc_auc = roc_auc_score(y_true, y_prob)
    
    # Precision-Recall AUC
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = auc(recall, precision)
    
    logger.info(f"ROC-AUC: {roc_auc:.4f}")
    logger.info(f"PR-AUC: {pr_auc:.4f}")
    
    # ASSERTION: ROC-AUC must be >= 0.50
    if roc_auc < 0.50:
        raise AssertionError(f"ROC-AUC ({roc_auc:.4f}) is below the required baseline of 0.50. "
                             f"The model performs no better than random chance.")
                             
    return {
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc)
    }

def plot_calibration(y_true: np.ndarray, y_prob: np.ndarray, model_name: str = "Primary Model") -> Path:
    """
    Generate and save a calibration plot.
    """
    config = get_config()
    figures_dir = Path(config.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Compute calibration curve
    # Use 10 bins for better visualization
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
    
    plt.figure(figsize=(8, 8))
    plt.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
    plt.plot(prob_pred, prob_true, marker='.', label=model_name)
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives")
    plt.title(f"Calibration Plot: {model_name}")
    plt.legend(loc="upper left")
    plt.grid(True, alpha=0.3)
    
    output_path = figures_dir / "calibration_plot.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Calibration plot saved to {output_path}")
    return output_path

def evaluate_model(
    df: pd.DataFrame,
    model,
    feature_cols: list,
    target_col: str = "bug_label"
) -> Tuple[Dict[str, float], Path]:
    """
    Full evaluation routine: compute metrics and plot calibration.
    """
    logger.info("Starting model evaluation...")
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Get probabilities for the positive class
    y_prob = model.predict_proba(X)[:, 1]
    
    # Compute metrics
    metrics = compute_metrics(y.values, y_prob)
    
    # Plot calibration
    cal_path = plot_calibration(y.values, y_prob)
    
    return metrics, cal_path

def main():
    """
    Entry point for the evaluation script.
    Expects preprocessed test data and a trained model to exist.
    """
    parser = argparse.ArgumentParser(description="Evaluate the trained model.")
    parser.add_argument("--model-path", type=str, default=None, help="Path to the model pickle file.")
    parser.add_argument("--features", type=str, nargs="+", default=None, 
                        help="List of feature column names. If not provided, inferred from config or defaults.")
    args = parser.parse_args()
    
    set_random_seed()
    
    try:
        # Load data
        df = load_test_data()
        
        # Determine features
        if args.features:
            feature_cols = args.features
        else:
            # Heuristic: assume all numeric columns except 'bug_label' and metadata
            exclude_cols = {'bug_label', 'project_name', 'file_path', 'commit_hash'}
            feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['int64', 'float64']]
            
        logger.info(f"Using features: {feature_cols}")
        
        if not feature_cols:
            raise ValueError("No feature columns found. Please specify --features.")
        
        # Load model
        model = load_model(args.model_path)
        
        # Evaluate
        metrics, cal_path = evaluate_model(df, model, feature_cols)
        
        # Save metrics to JSON
        config = get_config()
        metrics_path = Path(config.output_dir) / "evaluation_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Evaluation complete. Metrics saved to {metrics_path}")
        logger.info(f"Calibration plot saved to {cal_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data or model file missing: {e}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Model evaluation failed baseline check: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()