"""
Classifier module for training and loading models.
Extends existing functionality to support model loading for the simulator.
"""
import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from config import load_config_from_file, ensure_directories, validate_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_utility_labels(path: str = 'data/processed/utility_labels.csv') -> pd.DataFrame:
    """Load utility labels from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Utility labels not found at {path}")
    return pd.read_csv(path)

def prepare_features(df: pd.DataFrame, target_col: str = 'utility_score') -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features and target for training."""
    # Assuming features are numeric columns excluding target
    feature_cols = [col for col in df.columns if col != target_col and df[col].dtype in ['int64', 'float64']]
    if not feature_cols:
        raise ValueError("No numeric feature columns found.")
    
    X = df[feature_cols]
    y = df[target_col]
    return X, y

def train_classifier(X: pd.DataFrame, y: pd.Series, model_type: str = 'decision_tree') -> Any:
    """Train a lightweight classifier."""
    if model_type == 'decision_tree':
        model = DecisionTreeClassifier(max_depth=5, random_state=42)
    elif model_type == 'logistic_regression':
        model = LogisticRegression(max_iter=1000, random_state=42)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X, y)
    return model

def save_model(model: Any, path: str):
    """Save model to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def load_model(path: str) -> Any:
    """Load model from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def run_training():
    """Main training pipeline."""
    config = load_config_from_file('config.yaml')
    ensure_directories()
    
    labels_path = config.get('utility_labels_path', 'data/processed/utility_labels.csv')
    model_path = config.get('model_path', 'models/layer_utility_classifier.pkl')
    
    df = load_utility_labels(labels_path)
    X, y = prepare_features(df)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = train_classifier(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info(f"Training complete. Accuracy: {acc:.4f}")
    
    save_model(model, model_path)
    return model

def main():
    """Entry point for training."""
    run_training()

if __name__ == '__main__':
    main()
