import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Import project configuration and logging
from config import load_config, get_config, get_path, get_seed, get_hyperparameter, get_simulation_config, save_config
from logging_config import setup_logging

# Configure logging to capture audit events
logger = logging.getLogger(__name__)

def load_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the processed features dataset."""
    data_path = get_path(config, "processed_features_path")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed features file not found at {data_path}")
    
    logger.info(f"Loading features from {data_path}")
    df = pd.read_parquet(data_path)
    
    # Ensure required columns exist
    required_cols = ['search_count', 'error_freq', 'token_usage', 'turn_number', 
                     'embedding_distance', 'abstention_label']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    return df

def prepare_features(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Prepare feature matrix and target vector."""
    feature_cols = ['search_count', 'error_freq', 'token_usage', 'turn_number', 'embedding_distance']
    X = df[feature_cols].values
    y = df['abstention_label'].values
    return X, y, feature_cols

def train_model(X_train: np.ndarray, y_train: np.ndarray, config: Dict[str, Any]) -> XGBClassifier:
    """Train the Meta-Critic XGBoost model."""
    seed = get_seed(config)
    np.random.seed(seed)
    
    # Get hyperparameters
    max_depth = get_hyperparameter(config, "max_depth", 4)
    learning_rate = get_hyperparameter(config, "learning_rate", 0.1)
    n_estimators = get_hyperparameter(config, "n_estimators", 100)
    
    model = XGBClassifier(
        max_depth=max_depth,
        learning_rate=learning_rate,
        n_estimators=n_estimators,
        objective='binary:logistic',
        random_state=seed,
        eval_metric='logloss',
        n_jobs=1  # CPU constraint
    )
    
    logger.info("Training Meta-Critic model...")
    model.fit(X_train, y_train)
    logger.info("Model training complete.")
    
    return model

def evaluate_model(model: XGBClassifier, X_test: np.ndarray, y_test: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate model performance and log abstention events for auditability."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Standard metrics
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)
    
    # Custom metrics for the Meta-Critic
    # Timely Abstention Recall: correctly predicting abstention when it should have abstained
    # Assuming abstention_label=1 means "should abstain"
    tp = cm[1, 1] if cm.shape[0] > 1 else 0
    fn = cm[1, 0] if cm.shape[0] > 1 else 0
    timely_abstention_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    metrics = {
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "timely_abstention_recall": timely_abstention_recall,
        "model_params": {
            "max_depth": config.get("max_depth", 4),
            "learning_rate": config.get("learning_rate", 0.1),
            "n_estimators": config.get("n_estimators", 100)
        }
    }
    
    return metrics

def log_abstention_events(model: XGBClassifier, df: pd.DataFrame, feature_cols: List[str], config: Dict[str, Any], output_path: Path):
    """
    Log specific turn number and feature vector when Meta-Critic triggers abstention.
    This satisfies T023: Auditability of abstention decisions.
    """
    logger.info("Generating abstention audit log...")
    
    X = df[feature_cols].values
    y_true = df['abstention_label'].values
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    
    abstention_logs = []
    
    for idx, row in df.iterrows():
        # Check if the model predicted abstention (label 1)
        if y_pred[idx] == 1:
            # Log the event
            event = {
                "record_id": idx,
                "turn_number": int(row['turn_number']),
                "feature_vector": {
                    "search_count": float(row['search_count']),
                    "error_freq": float(row['error_freq']),
                    "token_usage": float(row['token_usage']),
                    "turn_number": int(row['turn_number']),
                    "embedding_distance": float(row['embedding_distance'])
                },
                "prediction_confidence": float(y_proba[idx]),
                "true_label": int(y_true[idx]),
                "decision": "ABSTAIN"
            }
            abstention_logs.append(event)
    
    # Save to JSON for auditability
    with open(output_path, 'w') as f:
        json.dump(abstention_logs, f, indent=2)
    
    logger.info(f"Audit log written to {output_path} ({len(abstention_logs)} abstention events recorded)")
    return abstention_logs

def save_artifacts(model: XGBClassifier, metrics: Dict[str, Any], config: Dict[str, Any]):
    """Save model and metrics to disk."""
    model_path = get_path(config, "model_output_path")
    metrics_path = get_path(config, "metrics_output_path")
    
    # Ensure directory exists
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, model_path)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model saved to {model_path}")
    logger.info(f"Metrics saved to {metrics_path}")

def main():
    """Main entry point for training the Meta-Critic model."""
    config = load_config()
    setup_logging(config)
    
    logger.info("Starting Meta-Critic Model Training (T023: Audit Logging Enabled)")
    
    try:
        # Load data
        df = load_data(config)
        X, y, feature_cols = prepare_features(df, config)
        
        # Split data
        seed = get_seed(config)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=seed, stratify=y
        )
        
        # Train
        model = train_model(X_train, y_train, config)
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test, config)
        
        # T023: Log abstention events for auditability
        audit_output_path = get_path(config, "abstention_audit_log_path")
        log_abstention_events(model, df, feature_cols, config, Path(audit_output_path))
        
        # Save artifacts
        save_artifacts(model, metrics, config)
        
        logger.info("Meta-Critic training and evaluation complete.")
        return 0
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
