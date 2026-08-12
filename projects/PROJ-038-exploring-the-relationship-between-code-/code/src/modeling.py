import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score
from sklearn.metrics import make_scorer, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from src.config import get_memory_limit_bytes

logger = logging.getLogger(__name__)

def load_features_csv(path: str) -> pd.DataFrame:
    """Load the features CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found: {path}")
    return pd.read_csv(path)

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare features (X) and target (y) from the dataframe."""
    metric_cols = ['cc', 'halstead', 'loc']
    # Ensure columns exist
    missing = [c for c in metric_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing metric columns: {missing}")
    
    X = df[metric_cols].values
    y = df['is_buggy'].values
    return X, y

def train_logistic_regression(X: np.ndarray, y: np.ndarray, seed: int = 42) -> Tuple[Pipeline, Dict[str, Any]]:
    """Train Logistic Regression with Repeated 5-Fold CV."""
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=seed)
    
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, random_state=seed))
    ])
    
    scorers = {
        'roc_auc': make_scorer(roc_auc_score, needs_threshold=True),
        'f1': make_scorer(f1_score)
    }
    
    results = {}
    for name, scorer in scorers.items():
        scores = cross_val_score(pipe, X, y, cv=cv, scoring=scorer, n_jobs=-1)
        results[name] = {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'scores': scores.tolist()
        }
    
    return pipe, results

def train_random_forest(X: np.ndarray, y: np.ndarray, seed: int = 42) -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """Train Random Forest with Repeated 5-Fold CV."""
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=seed)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=-1)
    
    scorers = {
        'roc_auc': make_scorer(roc_auc_score, needs_threshold=True),
        'f1': make_scorer(f1_score)
    }
    
    results = {}
    for name, scorer in scorers.items():
        scores = cross_val_score(clf, X, y, cv=cv, scoring=scorer, n_jobs=-1)
        results[name] = {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'scores': scores.tolist()
        }
    
    return clf, results

def run_modeling_analysis(features_path: str, output_dir: str, seed: int = 42) -> None:
    """Run the full modeling analysis and save results."""
    logger.info(f"Loading features from {features_path}")
    df = load_features_csv(features_path)
    
    # Check for class imbalance
    if df['is_buggy'].sum() == 0:
        logger.warning("No buggy files found. Skipping modeling.")
        return
    
    X, y = prepare_features(df)
    
    logger.info("Training Logistic Regression...")
    lr_model, lr_results = train_logistic_regression(X, y, seed)
    
    logger.info("Training Random Forest...")
    rf_model, rf_results = train_random_forest(X, y, seed)
    
    # Aggregate results
    results = {
        'logistic_regression': lr_results,
        'random_forest': rf_results
    }
    
    # Save results
    output_path = Path(output_dir) / 'baseline_metrics.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for modeling analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Run modeling analysis")
    parser.add_argument("--features", type=str, required=True, help="Path to features CSV")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    run_modeling_analysis(args.features, args.output, args.seed)

if __name__ == "__main__":
    main()
