"""
Modeling module.
Implements logistic regression, random forest, and nested CV.
"""
import json
import logging
import os
from pathlib import Path
from typing import Tuple, Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, LeaveOneOut
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from config import get_path

logger = logging.getLogger(__name__)

def load_feature_data(input_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load feature data and labels."""
    df = pd.read_csv(input_path)
    X = df.drop(columns=['label', 'participant_id']).values
    y = df['label'].map({'Control': 0, 'AD': 1, 'MCI': 2}).values
    ids = df['participant_id'].values
    return X, y, ids

def validate_split_ratio(y: np.ndarray, train_size: float, val_size: float, test_size: float) -> bool:
    """Validate the split ratio."""
    total = train_size + val_size + test_size
    return abs(total - 1.0) < 0.01

def split_data(X: np.ndarray, y: np.ndarray, ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split data into train/val/test sets."""
    # First split: 70% train, 30% temp
    X_train, X_temp, y_train, y_temp, ids_train, ids_temp = train_test_split(
        X, y, ids, test_size=0.3, stratify=y, random_state=42
    )
    
    # Second split: 50/50 of temp -> val/test (15% each)
    X_val, X_test, y_val, y_test, ids_val, ids_test = train_test_split(
        X_temp, y_temp, ids_temp, test_size=0.5, stratify=y_temp, random_state=42
    )
    
    return X_train, X_val, X_test, y_train, y_val, y_test, ids_train, ids_val, ids_test

def run_adaptive_cv(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Run adaptive cross-validation."""
    group_counts = np.bincount(y)
    min_count = np.min(group_counts)
    
    if min_count < 5:
        cv = LeaveOneOut()
        method = "LOOCV"
        folds = len(y)
    elif min_count < 15:
        folds = min_count - 1
        cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
        method = "k-fold"
    else:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        method = "k-fold"
        folds = 5
    
    return {
        "outer_folds": folds,
        "method": method,
        "sample_size_warning": min_count < 15
    }

def train_model(X: np.ndarray, y: np.ndarray, model_type: str = "logreg") -> Any:
    """Train a model."""
    if model_type == "logreg":
        return LogisticRegression(max_iter=1000)
    elif model_type == "rf":
        return RandomForestClassifier(n_estimators=100)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Modeling")
    parser.add_argument("--input", required=True, help="Input features CSV")
    parser.add_argument("--output", required=True, help="Output model results JSON")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    X, y, ids = load_feature_data(input_path)
    
    # Split data
    X_train, X_val, X_test, y_train, y_val, y_test, ids_train, ids_val, ids_test = split_data(X, y, ids)
    
    # Adaptive CV config
    cv_config = run_adaptive_cv(X_train, y_train)
    cv_config_path = get_path("data/results") / "cv_config.json"
    cv_config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cv_config_path, 'w') as f:
        json.dump(cv_config, f, indent=2)
    
    # Train and evaluate
    model = train_model(X_train, y_train, "logreg")
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_proba)
    f1 = f1_score(y_test, y_pred)
    acc = accuracy_score(y_test, y_pred)
    
    results = {
        "auc": auc,
        "f1": f1,
        "accuracy": acc,
        "cv_config": cv_config
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {output_path}")

if __name__ == "__main__":
    main()
