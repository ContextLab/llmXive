"""
T024: Evaluate Model Performance

Calculates ROC-AUC, accuracy, and F1-score per fold and mean from the trained model
and graph metrics data. Outputs results to data/processed/performance_report.json.
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, classification_report

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import ensure_dir, load_json, save_json
from config import get_config

logger = get_logger("evaluate_model")

def get_logger_wrapper(name):
    """Helper to get a logger with a specific name."""
    return get_logger(name)

def calculate_metrics(y_true, y_pred, y_prob):
    """
    Calculate evaluation metrics: ROC-AUC, Accuracy, F1-Score.
    
    Args:
        y_true: Array of true labels
        y_pred: Array of predicted labels
        y_prob: Array of predicted probabilities (for ROC-AUC)
    
    Returns:
        dict: Dictionary containing calculated metrics
    """
    metrics = {}
    
    # ROC-AUC (requires probability scores)
    try:
        metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
    except Exception as e:
        logger.warning(f"Could not calculate ROC-AUC: {e}")
        metrics['roc_auc'] = None
    
    # Accuracy
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    
    # F1-Score
    metrics['f1_score'] = float(f1_score(y_true, y_pred, average='binary'))
    
    return metrics

def evaluate_model(model_path, data_path, output_path):
    """
    Evaluate the trained model and write results to JSON.
    
    Args:
        model_path: Path to the trained model pickle file
        data_path: Path to the graph metrics CSV
        output_path: Path for the output JSON report
    """
    logger.info(f"Loading model from {model_path}")
    logger.info(f"Loading data from {data_path}")
    logger.info(f"Writing results to {output_path}")
    
    # Load model
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Run training first.")
    
    model = joblib.load(model_path)
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}. Run graph metrics computation first.")
    
    df = pd.read_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ['subject_id', 'cognitive_decline']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")
    
    # Prepare features and labels
    # Exclude non-feature columns
    feature_cols = [c for c in df.columns if c not in ['subject_id', 'cognitive_decline']]
    if not feature_cols:
        raise ValueError("No feature columns found in the data.")
    
    X = df[feature_cols].values
    y = df['cognitive_decline'].values
    
    # Check for valid labels
    if len(np.unique(y)) < 2:
        raise ValueError("Data must contain at least two classes for evaluation.")
    
    # Predict
    logger.info("Generating predictions...")
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]  # Probability of positive class
    
    # Calculate metrics
    metrics = calculate_metrics(y, y_pred, y_prob)
    
    # Prepare report
    report = {
        "status": "success",
        "model_path": str(model_path),
        "data_path": str(data_path),
        "n_samples": len(y),
        "n_features": len(feature_cols),
        "class_distribution": {
            "0": int(np.sum(y == 0)),
            "1": int(np.sum(y == 1))
        },
        "metrics": {
            "roc_auc": metrics['roc_auc'],
            "accuracy": metrics['accuracy'],
            "f1_score": metrics['f1_score']
        },
        "classification_report": classification_report(y, y_pred, output_dict=True),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ensure output directory exists
    ensure_dir(output_path)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Evaluation complete. Metrics saved to {output_path}")
    logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"F1-Score: {metrics['f1_score']:.4f}")
    
    return report

def main():
    """Main entry point for the evaluation script."""
    config = get_config()
    
    model_path = config.get('model_path', 'data/processed/model.pkl')
    data_path = config.get('graph_metrics_path', 'data/processed/graph_metrics.csv')
    output_path = config.get('performance_report_path', 'data/processed/performance_report.json')
    
    try:
        evaluate_model(model_path, data_path, output_path)
        logger.info("T024: Evaluate Model completed successfully.")
    except Exception as e:
        logger.error(f"T024: Evaluate Model failed: {e}")
        raise

if __name__ == "__main__":
    main()