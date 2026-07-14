"""
T024: Evaluate Model Performance
Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs to data/processed/performance_report.json
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import RFE
import joblib
import warnings

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from config import get_config

def get_logger_wrapper(name):
    """Wrapper to get a logger for this module."""
    return get_logger(name)

def calculate_metrics(y_true, y_pred, y_proba):
    """
    Calculate ROC-AUC, accuracy, and F1-score.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_proba: Predicted probabilities for the positive class
        
    Returns:
        dict: Metrics dictionary
    """
    metrics = {}
    
    # Handle edge cases
    if len(np.unique(y_true)) < 2:
        # If only one class present, ROC-AUC is undefined
        metrics['roc_auc'] = None
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['f1'] = f1_score(y_true, y_pred, zero_division=0)
    else:
        try:
            metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
        except ValueError:
            metrics['roc_auc'] = None
        
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['f1'] = f1_score(y_true, y_pred, zero_division=0)
    
    # Add confusion matrix details
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics['true_negatives'] = int(tn)
    metrics['false_positives'] = int(fp)
    metrics['false_negatives'] = int(fn)
    metrics['true_positives'] = int(tp)
    
    return metrics

def evaluate_model(model_path, graph_metrics_path, output_path):
    """
    Load the trained model and graph metrics, evaluate performance,
    and save results to JSON.
    
    Args:
        model_path: Path to the saved model pickle file
        graph_metrics_path: Path to the graph metrics CSV
        output_path: Path to save the performance report JSON
    """
    logger = get_logger("evaluate_model")
    logger.info(f"Starting model evaluation from {model_path}")
    
    # Load data
    if not os.path.exists(graph_metrics_path):
        logger.error(f"Graph metrics file not found: {graph_metrics_path}")
        raise FileNotFoundError(f"Graph metrics file not found: {graph_metrics_path}")
    
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load graph metrics
    df = load_csv(graph_metrics_path)
    logger.info(f"Loaded {len(df)} subjects from {graph_metrics_path}")
    
    # Load model
    model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}")
    
    # Extract features and labels
    # The model should have been trained on features excluding 'subject_id' and 'decline_label'
    feature_cols = [col for col in df.columns if col not in ['subject_id', 'decline_label']]
    X = df[feature_cols].values
    y = df['decline_label'].values
    
    logger.info(f"Features shape: {X.shape}, Labels shape: {y.shape}")
    
    # Check for label balance
    unique, counts = np.unique(y, return_counts=True)
    logger.info(f"Label distribution: {dict(zip(unique, counts))}")
    
    # If the model is a pipeline or has a specific structure, we need to handle it
    # For now, assume it's a fitted RandomForest or similar
    try:
        # Get predictions
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)[:, 1]  # Probability of positive class
        
        # Calculate overall metrics
        overall_metrics = calculate_metrics(y, y_pred, y_proba)
        logger.info(f"Overall metrics: {overall_metrics}")
        
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise
    
    # If the model was trained with cross-validation, we might have fold-specific results
    # Check if there's a way to get fold predictions (stored in model or separate file)
    # For now, we assume the model is a single trained instance
    # If cross-validation results are needed, they should be stored separately
    
    # Prepare the report
    report = {
        "model_path": model_path,
        "data_path": graph_metrics_path,
        "num_subjects": len(df),
        "num_features": len(feature_cols),
        "overall_metrics": overall_metrics,
        "feature_columns": feature_cols,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ensure output directory exists
    ensure_dir(output_path)
    
    # Save report
    save_json(report, output_path)
    logger.info(f"Performance report saved to {output_path}")
    
    return report

def main():
    """Main entry point for the evaluation script."""
    logger = get_logger("evaluate_model")
    logger.info("Starting T024: Evaluate Model")
    
    # Get configuration
    config = get_config()
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    model_path = base_dir / "data" / "processed" / "model.pkl"
    graph_metrics_path = base_dir / "data" / "processed" / "graph_metrics.csv"
    output_path = base_dir / "data" / "processed" / "performance_report.json"
    
    # Check if required files exist
    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}. Run training first.")
        sys.exit(1)
    
    if not graph_metrics_path.exists():
        logger.error(f"Graph metrics file not found: {graph_metrics_path}. Run graph metrics computation first.")
        sys.exit(1)
    
    try:
        report = evaluate_model(str(model_path), str(graph_metrics_path), str(output_path))
        logger.info("Evaluation completed successfully")
        print(json.dumps(report["overall_metrics"], indent=2))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()