import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix
from scipy.stats import ttest_ind
import json

# Import project config and logging
from config import get_paths, get_seed
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end
from ci_limits import enforce_limits, get_cpu_count

# Setup logger
logger = get_pipeline_logger(__name__)

def load_features(filepath: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load features from the processed CSV file.
    Returns: (X, y, feature_names)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature matrix not found at {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Assume the last column is the label 'condition' and others are features
    # Adjust if column names differ based on T023/T024 implementation
    if 'condition' not in df.columns:
        raise ValueError("CSV must contain a 'condition' column for classification labels")
    
    feature_cols = [c for c in df.columns if c != 'condition']
    X = df[feature_cols].values
    y = df['condition'].values
    
    logger.info(f"Loaded features: {X.shape[0]} epochs, {X.shape[1]} features")
    return X, y, feature_cols

def train_and_validate(X: np.ndarray, y: np.ndarray, n_folds: int = 5) -> Dict[str, Any]:
    """
    Train LDA classifier with k-fold cross-validation.
    Reports accuracy, precision, recall with standard deviation.
    """
    logger.info("Starting cross-validation for LDA classifier")
    
    # Enforce CPU limits
    cpu_limit = get_cpu_count()
    enforce_limits(cpu_limit=cpu_limit)
    
    # Create pipeline: Scaler -> LDA
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('lda', LDA())
    ])
    
    # Stratified K-Fold to maintain class balance
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=get_seed())
    
    # Lists to store metrics for each fold
    fold_accuracies = []
    fold_precisions = []
    fold_recalls = []
    fold_scores = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Train
        pipeline.fit(X_train, y_train)
        
        # Predict
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        
        fold_accuracies.append(acc)
        fold_precisions.append(prec)
        fold_recalls.append(rec)
        fold_scores.append(acc)
        
        logger.debug(f"Fold {fold_idx + 1}: Acc={acc:.4f}, Prec={prec:.4f}, Rec={rec:.4f}")
    
    # Calculate statistics
    results = {
        "accuracy": {
            "mean": float(np.mean(fold_accuracies)),
            "std": float(np.std(fold_accuracies)),
            "values": [float(v) for v in fold_accuracies]
        },
        "precision": {
            "mean": float(np.mean(fold_precisions)),
            "std": float(np.std(fold_precisions)),
            "values": [float(v) for v in fold_precisions]
        },
        "recall": {
            "mean": float(np.mean(fold_recalls)),
            "std": float(np.std(fold_recalls)),
            "values": [float(v) for v in fold_recalls]
        },
        "n_folds": n_folds,
        "n_samples": len(y),
        "class_distribution": {
            str(k): int(v) for k, v in zip(*np.unique(y, return_counts=True))
        }
    }
    
    logger.info(f"Cross-validation complete. Accuracy: {results['accuracy']['mean']:.4f} (+/- {results['accuracy']['std']:.4f})")
    
    return results

def permutation_test(X: np.ndarray, y: np.ndarray, n_permutations: int = 1000, n_folds: int = 5) -> Dict[str, Any]:
    """
    Perform permutation testing to establish statistical significance.
    Returns p-value and null distribution stats.
    """
    logger.info(f"Starting permutation test with {n_permutations} iterations")
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('lda', LDA())
    ])
    
    # Observed score
    observed_scores = cross_val_score(pipeline, X, y, cv=StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=get_seed()))
    observed_mean = np.mean(observed_scores)
    
    perm_scores = []
    rng = np.random.RandomState(get_seed())
    
    for i in range(n_permutations):
        # Shuffle labels
        y_perm = rng.permutation(y)
        scores = cross_val_score(pipeline, X, y_perm, cv=StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=get_seed()))
        perm_scores.append(np.mean(scores))
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation {i+1}/{n_permutations}")
    
    perm_scores = np.array(perm_scores)
    
    # Calculate p-value (one-sided: prob of perm score >= observed score)
    # Note: If observed is better than random, we count how many perms were as good or better
    p_value = (np.sum(perm_scores >= observed_mean) + 1) / (n_permutations + 1)
    
    return {
        "observed_mean": float(observed_mean),
        "perm_mean": float(np.mean(perm_scores)),
        "perm_std": float(np.std(perm_scores)),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "significant": p_value < 0.05
    }

def run_classification(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main execution function for User Story 3 classification tasks.
    1. Loads features.
    2. Runs cross-validation (T025, T026).
    3. Runs permutation test (T027).
    4. Saves comprehensive results.
    """
    log_stage_start("Classification Pipeline")
    
    try:
        # Load data
        X, y, feature_names = load_features(input_path)
        
        # 1. Cross-Validation & Metrics (T025, T026)
        cv_results = train_and_validate(X, y)
        
        # 2. Permutation Testing (T027)
        perm_results = permutation_test(X, y)
        
        # Compile final report
        report = {
            "status": "success",
            "input_file": input_path,
            "classification_metrics": cv_results,
            "permutation_test": perm_results,
            "feature_count": len(feature_names),
            "timestamp": None # Will be set by runner if needed
        }
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save results to JSON
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Classification results saved to {output_path}")
        return report
        
    except Exception as e:
        logger.error(f"Classification pipeline failed: {str(e)}")
        raise
    finally:
        log_stage_end("Classification Pipeline")

def main():
    """Entry point for script execution."""
    paths = get_paths()
    input_file = paths.get('processed_features', 'data/processed/features_matrix.csv')
    output_file = paths.get('classification_results', 'data/processed/classification_results.json')
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}. Please ensure T023 has run.")
        return 1
    
    try:
        run_classification(input_file, output_file)
        return 0
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
