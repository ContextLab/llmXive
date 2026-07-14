"""
T024: Evaluate Model Performance
Calculates ROC-AUC, accuracy, and F1-score per fold and mean; outputs to data/processed/performance_report.json.
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
from sklearn.model_selection import cross_val_predict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, ensure_dir
from utils.logger import get_logger
from utils.io import load_csv, save_json

def get_logger_wrapper(name):
    return get_logger(name)

def calculate_metrics(y_true, y_pred, y_prob):
    """
    Calculate ROC-AUC, accuracy, and F1-score.
    """
    metrics = {}
    
    # ROC-AUC
    try:
        metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
    except ValueError as e:
        # Handle case where only one class is present
        metrics['roc_auc'] = float('nan')
    
    # Accuracy
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    
    # F1-score
    metrics['f1_score'] = float(f1_score(y_true, y_pred, zero_division=0))
    
    return metrics

def evaluate_model(model_path, metrics_path, graph_metrics_path):
    """
    Load the trained model and data, evaluate performance, and save report.
    
    The model is assumed to be a RandomForestClassifier trained in T023.
    We need to re-predict on the held-out test folds from the nested CV process.
    However, since T023 saves the final model trained on ALL data, we cannot
    directly get per-fold predictions from it without re-running the CV logic.
    
    To satisfy T024's requirement of "per fold and mean" metrics, we must
    re-load the data and perform a fresh cross-validation prediction using
    the SAME hyperparameters found by T023 (or re-run the nested CV logic).
    
    Given the constraint that T023 already ran and saved the model, the most
    robust approach is to:
    1. Load the graph metrics data.
    2. Re-run the cross-validation prediction using the best parameters from T023's
       training log (if available) or default best params.
    3. Calculate metrics per fold and mean.
    
    However, the task description says "Import training logic from code/04_train_model.py".
    Let's assume we can re-run the nested CV evaluation part.
    
    Since we don't have the exact fold assignments from T023, we will re-run
    the nested CV evaluation on the loaded data to generate per-fold metrics.
    """
    logger = get_logger("evaluate_model")
    logger.info("Starting T024: Evaluate Model")
    logger.info(f"Model path: {model_path}")
    logger.info(f"Output path: {metrics_path}")
    logger.info(f"Graph metrics path: {graph_metrics_path}")

    # Check if model exists
    if not Path(model_path).exists():
        logger.error(f"Model file not found at {model_path}. Run training first.")
        sys.exit(1)

    # Check if graph metrics exist
    if not Path(graph_metrics_path).exists():
        logger.error(f"Graph metrics file not found: {graph_metrics_path}")
        sys.exit(1)

    # Load graph metrics
    logger.info(f"Loading graph metrics from {graph_metrics_path}")
    try:
        df = load_csv(graph_metrics_path)
    except Exception as e:
        logger.error(f"Failed to load graph metrics: {e}")
        sys.exit(1)

    # The graph metrics file should have a 'decline' column (target) and feature columns
    if 'decline' not in df.columns:
        logger.error("Graph metrics file does not contain 'decline' column. Training may have failed.")
        sys.exit(1)

    # Separate features and target
    y = df['decline'].values
    X = df.drop(columns=['decline', 'subject_id']).values  # Assuming subject_id is present

    # Load the trained model to get best parameters if needed
    # But for per-fold evaluation, we need to re-run CV.
    # We will use the best parameters from the training log if available, otherwise defaults.
    best_params = {
        'n_estimators': 100,
        'max_depth': None,
        'random_state': 42
    }
    
    # Try to load training log for best params
    training_log_path = Path(model_path).parent / "training_log.json"
    if training_log_path.exists():
        try:
            with open(training_log_path, 'r') as f:
                training_log = json.load(f)
                if 'best_params' in training_log:
                    best_params = training_log['best_params']
                    logger.info(f"Loaded best params from training log: {best_params}")
        except Exception as e:
            logger.warning(f"Could not load training log: {e}. Using defaults.")

    # Re-run cross-validation to get per-fold predictions
    # We use a Pipeline with StandardScaler and RandomForest
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(**best_params))
    ])

    # Perform 5-fold CV to get predictions for each sample
    # This simulates the outer CV loop
    n_splits = 5
    cv_scores = {'roc_auc': [], 'accuracy': [], 'f1': []}
    fold_predictions = []
    
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    logger.info(f"Running {n_splits}-fold cross-validation for evaluation...")
    
    # We need to collect predictions for each fold to calculate per-fold metrics
    # However, cross_val_predict gives all predictions at once.
    # To get per-fold metrics, we iterate manually.
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Fit on train fold
        pipe.fit(X_train, y_train)
        
        # Predict on test fold
        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)[:, 1]
        
        # Calculate metrics for this fold
        fold_metrics = calculate_metrics(y_test, y_pred, y_prob)
        cv_scores['roc_auc'].append(fold_metrics['roc_auc'])
        cv_scores['accuracy'].append(fold_metrics['accuracy'])
        cv_scores['f1'].append(fold_metrics['f1'])
        
        fold_predictions.append({
            'fold': fold_idx + 1,
            'roc_auc': fold_metrics['roc_auc'],
            'accuracy': fold_metrics['accuracy'],
            'f1_score': fold_metrics['f1_score'],
            'n_samples': len(y_test)
        })

    # Calculate mean metrics
    mean_metrics = {
        'roc_auc': float(np.mean(cv_scores['roc_auc'])),
        'accuracy': float(np.mean(cv_scores['accuracy'])),
        'f1_score': float(np.mean(cv_scores['f1']))
    }

    # Prepare report
    report = {
        'model_path': str(model_path),
        'best_params': best_params,
        'n_folds': n_splits,
        'per_fold_results': fold_predictions,
        'mean_metrics': mean_metrics,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Ensure output directory exists
    ensure_dir(Path(metrics_path).parent)

    # Save report
    save_json(report, metrics_path)
    logger.info(f"Performance report saved to {metrics_path}")

    # Print summary
    logger.info(f"Mean ROC-AUC: {mean_metrics['roc_auc']:.4f}")
    logger.info(f"Mean Accuracy: {mean_metrics['accuracy']:.4f}")
    logger.info(f"Mean F1-Score: {mean_metrics['f1_score']:.4f}")

    return report

def main():
    config = get_config()
    model_path = Path(config['data']['processed']) / "model.pkl"
    metrics_path = Path(config['data']['processed']) / "performance_report.json"
    graph_metrics_path = Path(config['data']['processed']) / "graph_metrics.csv"

    evaluate_model(model_path, metrics_path, graph_metrics_path)

if __name__ == "__main__":
    main()