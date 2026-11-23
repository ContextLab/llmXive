import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, f1_score, make_scorer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from src.config import get_memory_limit_bytes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_features_csv(path: str) -> pd.DataFrame:
    """
    Load the features CSV file.
    
    Args:
        path: Path to the features CSV file.
        
    Returns:
        DataFrame containing features and labels.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded features from {path}: {df.shape}")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features and target for modeling.
    
    Args:
        df: DataFrame with features and 'is_buggy' label.
        
    Returns:
        Tuple of (X, y) where X is feature matrix and y is target.
    """
    feature_cols = ['cc', 'halstead', 'loc']
    if not all(col in df.columns for col in feature_cols):
        missing = [col for col in feature_cols if col not in df.columns]
        raise ValueError(f"Missing required feature columns: {missing}")
    
    if 'is_buggy' not in df.columns:
        raise ValueError("Missing 'is_buggy' target column")
    
    # Check for class imbalance
    buggy_count = df['is_buggy'].sum()
    if buggy_count == 0:
        logger.warning("No buggy files found in dataset. Skipping modeling.")
        return None, None
    
    X = df[feature_cols].values
    y = df['is_buggy'].values
    
    # Check for NaN values
    if np.isnan(X).any():
        raise ValueError("NaN values found in feature matrix")
    
    logger.info(f"Prepared features: {X.shape[0]} samples, {X.shape[1]} features")
    return X, y

def train_logistic_regression(X: np.ndarray, y: np.ndarray, 
                               n_splits: int = 5, 
                               n_repeats: int = 10, 
                               seed: int = 42) -> Dict[str, Any]:
    """
    Train Logistic Regression with Repeated 5-Fold CV.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        n_splits: Number of folds (default 5).
        n_repeats: Number of repeats (default 10).
        seed: Random seed.
        
    Returns:
        Dictionary with ROC-AUC and F1-score results.
    """
    logger.info("Starting Logistic Regression training with Repeated 5-Fold CV")
    
    # Create pipeline with scaling and model
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(
            max_iter=1000, 
            random_state=seed,
            solver='lbfgs'
        ))
    ])
    
    # Define cross-validation strategy
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    
    # Define scorers
    roc_auc_scorer = make_scorer(roc_auc_score, needs_proba=True)
    f1_scorer = make_scorer(f1_score)
    
    # Calculate ROC-AUC scores
    logger.info("Calculating ROC-AUC scores...")
    roc_auc_scores = cross_val_score(model, X, y, cv=cv, scoring=roc_auc_scorer)
    
    # Calculate F1 scores
    logger.info("Calculating F1 scores...")
    f1_scores = cross_val_score(model, X, y, cv=cv, scoring=f1_scorer)
    
    # Calculate statistics per repeat (groups of n_splits scores)
    roc_auc_per_repeat = [
        np.mean(roc_auc_scores[i*n_splits:(i+1)*n_splits]) 
        for i in range(n_repeats)
    ]
    f1_per_repeat = [
        np.mean(f1_scores[i*n_splits:(i+1)*n_splits]) 
        for i in range(n_repeats)
    ]
    
    # Grand mean and std of repeat means
    mean_roc_auc = np.mean(roc_auc_per_repeat)
    std_roc_auc = np.std(roc_auc_per_repeat)
    mean_f1 = np.mean(f1_per_repeat)
    std_f1 = np.std(f1_per_repeat)
    
    results = {
        'model_type': 'LogisticRegression',
        'cv_strategy': f'Repeated {n_splits}-Fold CV ({n_repeats} repeats)',
        'seed': seed,
        'metrics': {
            'roc_auc': {
                'mean': float(mean_roc_auc),
                'std': float(std_roc_auc),
                'all_scores': roc_auc_scores.tolist()
            },
            'f1_score': {
                'mean': float(mean_f1),
                'std': float(std_f1),
                'all_scores': f1_scores.tolist()
            }
        },
        'n_samples': int(X.shape[0]),
        'n_features': int(X.shape[1])
    }
    
    logger.info(f"Logistic Regression Results - ROC-AUC: {mean_roc_auc:.4f} (+/- {std_roc_auc:.4f}), F1: {mean_f1:.4f} (+/- {std_f1:.4f})")
    return results

def train_random_forest(X: np.ndarray, y: np.ndarray,
                        n_splits: int = 5,
                        n_repeats: int = 10,
                        seed: int = 42) -> Dict[str, Any]:
    """
    Train Random Forest with Repeated 5-Fold CV.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        n_splits: Number of folds (default 5).
        n_repeats: Number of repeats (default 10).
        seed: Random seed.
        
    Returns:
        Dictionary with ROC-AUC and F1-score results.
    """
    from sklearn.ensemble import RandomForestClassifier
    
    logger.info("Starting Random Forest training with Repeated 5-Fold CV")
    
    # Create pipeline with scaling and model
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            random_state=seed,
            n_jobs=-1
        ))
    ])
    
    # Define cross-validation strategy
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    
    # Define scorers
    roc_auc_scorer = make_scorer(roc_auc_score, needs_proba=True)
    f1_scorer = make_scorer(f1_score)
    
    # Calculate ROC-AUC scores
    logger.info("Calculating ROC-AUC scores...")
    roc_auc_scores = cross_val_score(model, X, y, cv=cv, scoring=roc_auc_scorer)
    
    # Calculate F1 scores
    logger.info("Calculating F1 scores...")
    f1_scores = cross_val_score(model, X, y, cv=cv, scoring=f1_scorer)
    
    # Calculate statistics per repeat
    roc_auc_per_repeat = [
        np.mean(roc_auc_scores[i*n_splits:(i+1)*n_splits]) 
        for i in range(n_repeats)
    ]
    f1_per_repeat = [
        np.mean(f1_scores[i*n_splits:(i+1)*n_splits]) 
        for i in range(n_repeats)
    ]
    
    # Grand mean and std of repeat means
    mean_roc_auc = np.mean(roc_auc_per_repeat)
    std_roc_auc = np.std(roc_auc_per_repeat)
    mean_f1 = np.mean(f1_per_repeat)
    std_f1 = np.std(f1_per_repeat)
    
    results = {
        'model_type': 'RandomForest',
        'cv_strategy': f'Repeated {n_splits}-Fold CV ({n_repeats} repeats)',
        'seed': seed,
        'metrics': {
            'roc_auc': {
                'mean': float(mean_roc_auc),
                'std': float(std_roc_auc),
                'all_scores': roc_auc_scores.tolist()
            },
            'f1_score': {
                'mean': float(mean_f1),
                'std': float(std_f1),
                'all_scores': f1_scores.tolist()
            }
        },
        'n_samples': int(X.shape[0]),
        'n_features': int(X.shape[1])
    }
    
    logger.info(f"Random Forest Results - ROC-AUC: {mean_roc_auc:.4f} (+/- {std_roc_auc:.4f}), F1: {mean_f1:.4f} (+/- {std_f1:.4f})")
    return results

def run_modeling_analysis(features_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run full modeling analysis: Logistic Regression and Random Forest.
    
    Args:
        features_path: Path to features CSV.
        output_path: Path to save results JSON.
        
    Returns:
        Dictionary with all modeling results.
    """
    logger.info("Starting modeling analysis")
    
    # Load data
    df = load_features_csv(features_path)
    X, y = prepare_features(df)
    
    if X is None or y is None:
        logger.warning("Skipping modeling due to class imbalance")
        return {'status': 'skipped', 'reason': 'no_buggy_samples'}
    
    # Train models
    lr_results = train_logistic_regression(X, y)
    rf_results = train_random_forest(X, y)
    
    # Compile results
    results = {
        'logistic_regression': lr_results,
        'random_forest': rf_results
    }
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return results

def main():
    """Main entry point for modeling analysis."""
    # Default paths
    features_path = "code/data/processed/features.csv"
    output_path = "code/data/results/baseline_metrics.json"
    
    # Allow override via command line
    import sys
    if len(sys.argv) > 1:
        features_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    try:
        results = run_modeling_analysis(features_path, output_path)
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Modeling analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()