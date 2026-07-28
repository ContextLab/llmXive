"""
Train Random Forest and Gradient Boosting classifiers for glass-forming prediction.

This script loads the filtered alloy dataset, performs stratified 5-fold cross-validation,
trains the models, saves the trained artifacts, records hyperparameters, and logs
accuracy issues if performance thresholds are not met.
"""
import argparse
import logging
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, make_scorer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Configuration paths
CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "env.yaml"
DATA_PATH = PROJECT_ROOT / "data" / "derived" / "filtered_alloys.csv"
MODEL_OUTPUT_DIR = PROJECT_ROOT / "models"
HYPERPARAMS_PATH = PROJECT_ROOT / "code" / "models" / "hyperparameters.yaml"
LOG_PATH = PROJECT_ROOT / "logs" / "model_accuracy_issue.log"
METRICS_LOG_PATH = PROJECT_ROOT / "logs" / "training_metrics.json"

# Default hyperparameters (can be overridden by config)
DEFAULT_RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": None,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
    "random_state": 42,
    "n_jobs": -1
}

DEFAULT_GB_PARAMS = {
    "n_estimators": 100,
    "learning_rate": 0.1,
    "max_depth": 3,
    "random_state": 42
}

def setup_logging():
    """Configure logging for the training script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(PROJECT_ROOT / "logs" / "training.log")
        ]
    )
    return logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load environment configuration."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f) or {}

def load_data(logger: logging.Logger) -> Tuple[pd.DataFrame, pd.Series]:
    """Load the filtered alloy dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}. "
                                "Run T018 (filter_labels.py) first.")
    
    df = pd.read_csv(DATA_PATH)
    
    # Ensure required columns exist
    required_cols = ['atomic_size_mismatch', 'mixing_enthalpy', 'electronegativity_variance', 'phase_label']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in data: {missing}")
    
    # Separate features and target
    feature_cols = ['atomic_size_mismatch', 'mixing_enthalpy', 'electronegativity_variance']
    X = df[feature_cols]
    y = df['phase_label']
    
    logger.info(f"Loaded {len(df)} samples with {len(X.columns)} features.")
    logger.info(f"Class distribution:\n{y.value_counts()}")
    
    return X, y

def train_and_evaluate(
    X: pd.DataFrame,
    y: pd.Series,
    model_class: type,
    params: Dict[str, Any],
    logger: logging.Logger,
    cv_folds: int = 5
) -> Tuple[Any, List[float], float]:
    """
    Train a model with cross-validation and return the trained model, scores, and mean AUC.
    """
    # Create pipeline with scaling
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', model_class(**params))
    ])
    
    # Setup cross-validation
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    # Calculate cross-validation scores (ROC-AUC)
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring='roc_auc')
    
    # Train final model on full data for saving
    pipeline.fit(X, y)
    
    mean_auc = float(np.mean(scores))
    std_auc = float(np.std(scores))
    
    logger.info(f"{model_class.__name__} Cross-validation ROC-AUC: {mean_auc:.4f} (+/- {std_auc:.4f})")
    
    return pipeline, scores.tolist(), mean_auc

def save_model(model: Pipeline, model_name: str, logger: logging.Logger):
    """Save the trained model to disk."""
    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = MODEL_OUTPUT_DIR / f"{model_name}.pkl"
    joblib.dump(model, output_path)
    logger.info(f"Model saved to {output_path}")
    return output_path

def save_hyperparameters(
    rf_params: Dict[str, Any],
    gb_params: Dict[str, Any],
    logger: logging.Logger
):
    """Save hyperparameters to YAML file (Constitution VII compliance)."""
    HYPERPARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    hyperparams = {
        "timestamp": datetime.now().isoformat(),
        "models": {
            "RandomForest": rf_params,
            "GradientBoosting": gb_params
        },
        "description": "Hyperparameters used for glass-forming region prediction models"
    }
    
    with open(HYPERPARAMS_PATH, 'w') as f:
        yaml.dump(hyperparams, f, default_flow_style=False)
    
    logger.info(f"Hyperparameters saved to {HYPERPARAMS_PATH}")

def log_accuracy_issue(model_name: str, mean_auc: float, logger: logging.Logger):
    """Log explanation if ROC-AUC < 0.80 (Constitution VII requirement)."""
    if mean_auc < 0.80:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        issue_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "mean_roc_auc": mean_auc,
            "threshold": 0.80,
            "explanation": (
                f"The {model_name} model achieved a mean ROC-AUC of {mean_auc:.4f}, "
                f"which is below the 0.80 threshold. This may indicate: "
                f"1) Insufficient signal in the current descriptors (atomic size mismatch, "
                f"mixing enthalpy, electronegativity variance) to fully capture the glass-forming region. "
                f"2) Data imbalance or noise in the labels. "
                f"3) The need for additional features such as cooling rate or thermal history, "
                f"as noted in reviewer concerns regarding structural determination vs. statistical correlation."
            )
        }
        
        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps(issue_entry) + '\n')
        
        logger.warning(f"Accuracy issue logged for {model_name}: ROC-AUC < 0.80")

def main():
    logger = setup_logging()
    logger.info("Starting model training pipeline (T020)...")
    
    # Load configuration
    config = load_config()
    seed = config.get('random_seed', {}).get('sklearn', 42)
    
    try:
        # Load data
        X, y = load_data(logger)
        
        # Define hyperparameters
        rf_params = DEFAULT_RF_PARAMS.copy()
        rf_params['random_state'] = seed
        
        gb_params = DEFAULT_GB_PARAMS.copy()
        gb_params['random_state'] = seed
        
        # Train Random Forest
        logger.info("Training Random Forest...")
        start_time = time.time()
        rf_model, rf_scores, rf_mean_auc = train_and_evaluate(
            X, y, RandomForestClassifier, rf_params, logger
        )
        rf_time = time.time() - start_time
        
        # Train Gradient Boosting
        logger.info("Training Gradient Boosting...")
        start_time = time.time()
        gb_model, gb_scores, gb_mean_auc = train_and_evaluate(
            X, y, GradientBoostingClassifier, gb_params, logger
        )
        gb_time = time.time() - start_time
        
        # Save models
        save_model(rf_model, "random_forest_glass_classifier", logger)
        save_model(gb_model, "gradient_boosting_glass_classifier", logger)
        
        # Save hyperparameters
        save_hyperparameters(rf_params, gb_params, logger)
        
        # Log accuracy issues if needed
        log_accuracy_issue("RandomForest", rf_mean_auc, logger)
        log_accuracy_issue("GradientBoosting", gb_mean_auc, logger)
        
        # Log training metrics
        metrics_log = {
            "timestamp": datetime.now().isoformat(),
            "models": {
                "RandomForest": {
                    "mean_roc_auc": rf_mean_auc,
                    "std_roc_auc": float(np.std(rf_scores)),
                    "cv_scores": rf_scores,
                    "training_time_seconds": rf_time
                },
                "GradientBoosting": {
                    "mean_roc_auc": gb_mean_auc,
                    "std_roc_auc": float(np.std(gb_scores)),
                    "cv_scores": gb_scores,
                    "training_time_seconds": gb_time
                }
            }
        }
        
        METRICS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(METRICS_LOG_PATH, 'w') as f:
            json.dump(metrics_log, f, indent=2)
        
        logger.info("Training pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train glass-forming prediction models")
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    args = parser.parse_args()
    
    main()
