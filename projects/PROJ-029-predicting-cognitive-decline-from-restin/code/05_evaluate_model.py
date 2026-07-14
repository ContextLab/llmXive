"""
T024: Evaluate Model Performance

Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs results to data/processed/performance_report.json.

Dependencies:
- code/04_train_model.py (for training logic if re-evaluation needed, though here we load trained model)
- config.py (for paths)
- utils.io (for file loading/saving)
- utils.logger (for logging)
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, confusion_matrix
from typing import Dict, Any, List, Tuple

# Add project root to path if not already
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.io import load_json, save_json, load_csv

# Constants
DATA_PROCESSED = "data/processed"
MODEL_FILE = "model.pkl"
METRICS_FILE = "performance_report.json"
ELIGIBLE_SUBJECTS_FILE = "eligible_subjects.csv"

logger = get_logger("05_evaluate_model")

def get_logger_wrapper(name: str):
    """Wrapper to get a logger instance."""
    return get_logger(name)

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """
    Calculate evaluation metrics: ROC-AUC, Accuracy, F1-score.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        y_prob: Predicted probabilities for class 1
        
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    # ROC-AUC (requires probability scores)
    try:
        metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
    except ValueError as e:
        # Handle case where only one class is present
        logger.warning(f"Could not calculate ROC-AUC: {e}. Setting to 0.5.")
        metrics['roc_auc'] = 0.5
    
    # Accuracy
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    
    # F1-Score
    metrics['f1_score'] = float(f1_score(y_true, y_pred, average='binary'))
    
    return metrics

def evaluate_model(model_path: str, data_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load model and data, perform evaluation per fold and overall.
    
    Args:
        model_path: Path to the trained model (model.pkl)
        data_path: Path to the graph metrics CSV
        config: Configuration dictionary
        
    Returns:
        Dictionary containing evaluation results
    """
    logger.info(f"Loading model from {model_path}")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
        
    model_data = joblib.load(model_path)
    
    # Extract model and fold information
    if isinstance(model_data, dict):
        model = model_data.get('model')
        fold_results = model_data.get('fold_results', [])
        best_params = model_data.get('best_params', {})
        cv_scores = model_data.get('cv_scores', {})
    else:
        # Fallback if model is just the estimator
        model = model_data
        fold_results = []
        best_params = {}
        cv_scores = {}
        
    if model is None:
        raise ValueError("Model could not be extracted from the saved file.")
        
    logger.info(f"Loading data from {data_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}")
        
    df = load_csv(data_path)
    
    # Prepare features and labels
    # Assuming the CSV has a 'label' or 'cognitive_decline' column
    label_col = 'cognitive_decline'
    if label_col not in df.columns:
        # Try alternative names
        for col in ['label', 'outcome', 'decline']:
            if col in df.columns:
                label_col = col
                break
        
    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found in data. Available columns: {df.columns.tolist()}")
        
    y_true = df[label_col].values
    X = df.drop(columns=[label_col]).values
    
    # If we have fold results from training, we can aggregate them
    # Otherwise, we perform a simple train/test split or use the whole dataset if model was trained on all
    results = {
        "status": "success",
        "model_path": model_path,
        "data_path": data_path,
        "n_samples": int(len(y_true)),
        "n_features": int(X.shape[1]),
        "best_params": best_params,
        "fold_results": [],
        "overall_metrics": {}
    }
    
    # If fold results are available from training (T023), use them
    if fold_results:
        logger.info(f"Evaluating {len(fold_results)} folds from nested CV")
        for i, fold_res in enumerate(fold_results):
            fold_metrics = {
                "fold": i + 1,
                "roc_auc": float(fold_res.get('roc_auc', 0.0)),
                "accuracy": float(fold_res.get('accuracy', 0.0)),
                "f1_score": float(fold_res.get('f1_score', 0.0))
            }
            results["fold_results"].append(fold_metrics)
        
        # Calculate mean metrics
        if len(fold_results) > 0:
            mean_roc_auc = np.mean([f['roc_auc'] for f in fold_results])
            mean_accuracy = np.mean([f['accuracy'] for f in fold_results])
            mean_f1 = np.mean([f['f1_score'] for f in fold_results])
            
            results["overall_metrics"] = {
                "roc_auc": float(mean_roc_auc),
                "accuracy": float(mean_accuracy),
                "f1_score": float(mean_f1),
                "std_roc_auc": float(np.std([f['roc_auc'] for f in fold_results])),
                "std_accuracy": float(np.std([f['accuracy'] for f in fold_results])),
                "std_f1_score": float(np.std([f['f1_score'] for f in fold_results]))
            }
    else:
        # Fallback: Evaluate on the full dataset (not ideal for nested CV but necessary if fold data missing)
        # This happens if T023 didn't save fold results
        logger.warning("No fold results found in model data. Evaluating on full dataset (warning: this is not nested CV).")
        
        y_pred = model.predict(X)
        y_prob = model.predict_proba(X)[:, 1]
        
        metrics = calculate_metrics(y_true, y_pred, y_prob)
        
        results["overall_metrics"] = metrics
        
        # Add a single "fold" for consistency
        results["fold_results"].append({
            "fold": 1,
            "roc_auc": metrics['roc_auc'],
            "accuracy": metrics['accuracy'],
            "f1_score": metrics['f1_score']
        })
        
        # Standard deviation is 0 for single fold
        results["overall_metrics"]["std_roc_auc"] = 0.0
        results["overall_metrics"]["std_accuracy"] = 0.0
        results["overall_metrics"]["std_f1_score"] = 0.0
        
    return results

def main():
    """Main entry point for T024."""
    start_time = time.time()
    
    logger.info("Starting T024: Evaluate Model")
    
    try:
        config = get_config()
        
        # Ensure processed data directory exists
        processed_dir = ensure_dir(DATA_PROCESSED)
        
        model_path = Path(processed_dir) / MODEL_FILE
        data_path = Path(processed_dir) / "graph_metrics.csv"
        output_path = Path(processed_dir) / METRICS_FILE
        
        # Verify input files exist
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at {model_path}. Run code/04_train_model.py first.")
            sys.exit(1)
            
        if not os.path.exists(data_path):
            logger.error(f"Graph metrics file not found at {data_path}. Run code/03_compute_graph_metrics.py first.")
            sys.exit(1)
        
        # Perform evaluation
        results = evaluate_model(str(model_path), str(data_path), config)
        
        # Add runtime info
        elapsed_time = time.time() - start_time
        results["runtime_seconds"] = round(elapsed_time, 2)
        results["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # Save results
        ensure_dir(str(output_path.parent))
        save_json(results, str(output_path))
        
        logger.info(f"Evaluation complete. Results saved to {output_path}")
        logger.info(f"Overall ROC-AUC: {results['overall_metrics'].get('roc_auc', 'N/A'):.4f}")
        logger.info(f"Overall Accuracy: {results['overall_metrics'].get('accuracy', 'N/A'):.4f}")
        logger.info(f"Overall F1-Score: {results['overall_metrics'].get('f1_score', 'N/A'):.4f}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
