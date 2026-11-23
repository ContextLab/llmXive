import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
import warnings

import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.inspection import permutation_importance
from scipy import stats

from config import get_config, get_paths, set_random_seed
from logger import get_logger

# Ensure logger is available
logger = get_logger(__name__)

def load_features(path: str) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Load the feature matrix and labels from the CSV file produced by feature extraction.
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Labels (n_samples,)
        df: The original dataframe for metadata access
    """
    df = pd.read_csv(path)
    
    # Identify feature columns (exclude 'epoch_id' and 'condition')
    feature_cols = [c for c in df.columns if c not in ['epoch_id', 'condition']]
    
    X = df[feature_cols].values
    y = (df['condition'] == 'active').astype(int).values # 1 for active, 0 for passive
    
    return X, y, df

def train_and_validate(X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> Dict[str, Any]:
    """
    Train LDA with k-fold cross-validation.
    """
    set_random_seed()
    cfg = get_config()
    
    lda = LinearDiscriminantAnalysis()
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=cfg['SEED'])
    
    # Cross-validation scores
    cv_scores = cross_val_score(lda, X, y, cv=cv, scoring='accuracy')
    
    # Train on full data to get predictions for precision/recall (approximate)
    lda_full = LinearDiscriminantAnalysis()
    lda_full.fit(X, y)
    y_pred = lda_full.predict(X)
    
    return {
        'accuracy_mean': float(np.mean(cv_scores)),
        'accuracy_std': float(np.std(cv_scores)),
        'precision': float(precision_score(y, y_pred)),
        'recall': float(recall_score(y, y_pred)),
        'cv_scores': cv_scores.tolist()
    }

def permutation_test(X: np.ndarray, y: np.ndarray, n_permutations: int = 1000) -> float:
    """
    Perform permutation testing to establish statistical significance.
    Returns the p-value.
    """
    set_random_seed()
    lda = LinearDiscriminantAnalysis()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Actual score
    actual_score = cross_val_score(lda, X, y, cv=cv, scoring='accuracy').mean()
    
    # Permutation scores
    perm_scores = []
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y)
        perm_score = cross_val_score(lda, X, y_perm, cv=cv, scoring='accuracy').mean()
        perm_scores.append(perm_score)
    
    perm_scores = np.array(perm_scores)
    
    # Calculate p-value (one-tailed: probability of getting >= actual score by chance)
    p_value = float((np.sum(perm_scores >= actual_score) + 1) / (n_permutations + 1))
    
    return p_value

def run_sensitivity_analysis(X: np.ndarray, y: np.ndarray) -> List[Dict[str, float]]:
    """
    Sweep classification threshold and report FP/FN variation.
    """
    set_random_seed()
    lda = LinearDiscriminantAnalysis()
    lda.fit(X, y)
    
    # Get decision function scores (distance from hyperplane)
    scores = lda.decision_function(X)
    
    thresholds = np.linspace(scores.min(), scores.max(), 20)
    results = []
    
    for thresh in thresholds:
        y_pred = (scores > thresh).astype(int)
        
        # True Positives, False Positives, etc.
        tp = np.sum((y_pred == 1) & (y == 1))
        fp = np.sum((y_pred == 1) & (y == 0))
        tn = np.sum((y_pred == 0) & (y == 0))
        fn = np.sum((y_pred == 0) & (y == 1))
        
        fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            'threshold': float(thresh),
            'fp_rate': float(fp_rate),
            'fn_rate': float(fn_rate)
        })
    
    return results

def run_classification() -> Dict[str, Any]:
    """
    Main orchestration function for classification tasks.
    """
    paths = get_paths()
    config = get_config()
    
    feature_path = paths['processed'] / 'features_matrix.csv'
    output_path = paths['processed'] / 'results.json'
    
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {feature_path}. Run feature extraction first.")
    
    logger.info(f"Loading features from {feature_path}")
    X, y, df = load_features(str(feature_path))
    
    logger.info(f"Training and validating classifier...")
    cv_results = train_and_validate(X, y)
    
    logger.info("Running permutation test...")
    p_value = permutation_test(X, y)
    
    logger.info("Running sensitivity analysis...")
    sensitivity_data = run_sensitivity_analysis(X, y)
    
    # Save sensitivity data
    sens_path = paths['processed'] / 'sensitivity_analysis.csv'
    pd.DataFrame(sensitivity_data).to_csv(sens_path, index=False)
    
    # Determine benchmark status (Task T032)
    benchmark_acc = config.get('BENCHMARK_ACCURACY')
    status = "deferred"
    
    if benchmark_acc is not None and benchmark_acc != 'targetThreshold':
        try:
            target = float(benchmark_acc)
            if cv_results['accuracy_mean'] >= target:
                status = "pass"
            else:
                status = "fail"
        except (ValueError, TypeError):
            status = "deferred"
    elif benchmark_acc == 'targetThreshold':
        # Explicitly check for the placeholder string defined in config.py
        status = "deferred"
    
    results = {
        'participant_count': len(df['epoch_id'].unique()) if 'epoch_id' in df.columns else len(df),
        'epoch_count': len(df),
        'classification_results': cv_results,
        'statistical_corrections': {
            'permutation_p_value': p_value,
            'hypothesis_rejected': p_value < 0.05
        },
        'sensitivity_analysis': {
            'points_count': len(sensitivity_data),
            'file': 'sensitivity_analysis.csv'
        },
        'benchmark_status': status
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return results

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Classification and Statistical Validation")
    parser.add_argument('--input', type=str, default=None, help="Path to features CSV")
    args = parser.parse_args()
    
    try:
        run_classification()
        print("Classification completed successfully.")
    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()