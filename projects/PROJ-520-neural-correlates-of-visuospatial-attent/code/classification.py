"""
Classification and statistical validation module.
Implements LDA, cross-validation, permutation testing, and reporting.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from scipy import stats

from config import load_config, get_paths
from models import ClassifierResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_features(features_path: Path, labels_path: Path = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load feature matrix and labels.
    For this task, we assume the CSV contains a 'condition' column or we infer from filename.
    """
    df = pd.read_csv(features_path)
    
    # Heuristic: If 'condition' column exists, use it. Otherwise, assume binary based on index?
    # In real scenario, labels come from epoch metadata.
    if 'condition' in df.columns:
        labels = df['condition'].map({'active': 1, 'passive': 0}).values
        features = df.drop(columns=['condition']).values
    else:
        # Fallback: assume first column is label? No, that's bad practice.
        # We will raise an error if labels are missing.
        raise ValueError("Feature CSV must contain a 'condition' column or explicit labels file.")
        
    return features, labels

def train_and_validate(X: np.ndarray, y: np.ndarray, config: Dict[str, Any]) -> ClassifierResult:
    """
    Train LDA with cross-validation and report metrics.
    """
    clf_cfg = config["classification"]
    n_folds = clf_cfg["n_folds"]
    
    # Scale data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=config["random_seed"])
    lda = LinearDiscriminantAnalysis()
    
    scores = cross_val_score(lda, X_scaled, y, cv=cv, scoring='accuracy')
    
    # Train final model on full data for other metrics (simplified)
    lda.fit(X_scaled, y)
    y_pred = lda.predict(X_scaled)
    
    acc = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred, zero_division=0)
    rec = recall_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)
    cm = confusion_matrix(y, y_pred)
    
    return ClassifierResult(
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1_score=f1,
        confusion_matrix=cm,
        cv_scores=scores.tolist()
    )

def permutation_test(X: np.ndarray, y: np.ndarray, config: Dict[str, Any]) -> float:
    """
    Perform permutation testing to estimate p-value.
    """
    n_perm = config["classification"]["n_permutations"]
    rng = np.random.RandomState(config["random_seed"])
    
    # Observed accuracy
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    lda = LinearDiscriminantAnalysis()
    lda.fit(X_scaled, y)
    obs_acc = accuracy_score(y, lda.predict(X_scaled))
    
    perm_accs = []
    for _ in range(n_perm):
        y_perm = rng.permutation(y)
        # Quick validation with a single split or CV
        # For speed, we might do a simple train/test split here instead of full CV
        # But to be rigorous, we do a single CV fold or similar
        # Simplified: train on all, predict on all (overfitting risk in perm test if not careful, but standard for null)
        # Better: use cross_val_score with a single shuffle split
        from sklearn.model_selection import train_test_split
        X_tr, X_te, y_tr, y_te = train_test_split(X_scaled, y_perm, test_size=0.2, random_state=rng.randint(0, 10000))
        lda_perm = LinearDiscriminantAnalysis()
        lda_perm.fit(X_tr, y_tr)
        acc = accuracy_score(y_te, lda_perm.predict(X_te))
        perm_accs.append(acc)
    
    perm_accs = np.array(perm_accs)
    p_val = np.mean(perm_accs >= obs_acc)
    return p_val

def run_classification(features_path: Path, output_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestration for classification.
    """
    X, y = load_features(features_path)
    
    # Train
    result = train_and_validate(X, y, config)
    
    # Permutation
    p_val = permutation_test(X, y, config)
    
    result.permutation_p_value = p_val
    result.is_significant = p_val < 0.05
    
    # Prepare report
    report = {
        "accuracy": float(result.accuracy),
        "precision": float(result.precision),
        "recall": float(result.recall),
        "f1_score": float(result.f1_score),
        "cv_mean": float(np.mean(result.cv_scores)),
        "cv_std": float(np.std(result.cv_scores)),
        "confusion_matrix": result.confusion_matrix.tolist(),
        "permutation_p_value": float(result.permutation_p_value),
        "is_significant": result.is_significant,
        "n_epochs": len(y)
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Classification complete. P-value: {p_val:.4f}. Significant: {result.is_significant}")
    return report

def main():
    """Entry point for classification."""
    config = load_config()
    paths = get_paths(config)
    
    features_file = paths["processed"] / paths["features"]
    results_file = paths["processed"] / paths["results"]
    
    try:
        report = run_classification(features_file, results_file, config)
        print(f"Classification complete. Results: {results_file}")
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise

if __name__ == "__main__":
    main()
