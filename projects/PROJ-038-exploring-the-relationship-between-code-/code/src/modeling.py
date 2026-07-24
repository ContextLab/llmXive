import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score, cross_validate
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score, make_scorer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_features_csv(path: str) -> pd.DataFrame:
    """
    Load the features CSV file.
    
    Args:
        path: Path to the features CSV file.
        
    Returns:
        DataFrame with features and target.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded features CSV: {df.shape}")
    return df

def prepare_features(df: pd.DataFrame, feature_cols: List[str], target_col: str = 'is_buggy') -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare features and target for modeling.
    
    Args:
        df: DataFrame with features and target.
        feature_cols: List of feature column names.
        target_col: Name of the target column.
        
    Returns:
        Tuple of (X, y, feature_names)
    """
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def train_logistic_regression(X: np.ndarray, y: np.ndarray, feature_names: List[str], n_splits: int = 5, n_repeats: int = 10, random_state: int = 42) -> Dict[str, Any]:
    """
    Train Logistic Regression with Repeated Stratified K-Fold CV.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        feature_names: List of feature names.
        n_splits: Number of folds.
        n_repeats: Number of repeats.
        random_state: Random seed.
        
    Returns:
        Dictionary with results.
    """
    from sklearn.linear_model import LogisticRegression
    
    rskf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=random_state)
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, random_state=random_state))
    ])
    
    # Calculate ROC-AUC and F1 scores
    auc_scores = cross_val_score(pipeline, X, y, cv=rskf, scoring='roc_auc')
    f1_scores = cross_val_score(pipeline, X, y, cv=rskf, scoring='f1')
    
    results = {
        'model_type': 'LogisticRegression',
        'roc_auc': {
            'mean': float(np.mean(auc_scores)),
            'std': float(np.std(auc_scores))
        },
        'f1': {
            'mean': float(np.mean(f1_scores)),
            'std': float(np.std(f1_scores))
        },
        'n_folds': n_splits,
        'n_repeats': n_repeats
    }
    
    logger.info(f"Logistic Regression - ROC-AUC: {results['roc_auc']['mean']:.4f} (+/- {results['roc_auc']['std']:.4f})")
    logger.info(f"Logistic Regression - F1: {results['f1']['mean']:.4f} (+/- {results['f1']['std']:.4f})")
    
    return results

def train_random_forest(X: np.ndarray, y: np.ndarray, feature_names: List[str], n_splits: int = 5, n_repeats: int = 10, random_state: int = 42, n_estimators: int = 100) -> Dict[str, Any]:
    """
    Train Random Forest with Repeated Stratified K-Fold CV.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        feature_names: List of feature names.
        n_splits: Number of folds.
        n_repeats: Number of repeats.
        random_state: Random seed.
        n_estimators: Number of trees in the forest.
        
    Returns:
        Dictionary with results.
    """
    rskf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=random_state)
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(n_estimators=n_estimators, random_state=random_state, n_jobs=-1))
    ])
    
    # Calculate ROC-AUC and F1 scores
    auc_scores = cross_val_score(pipeline, X, y, cv=rskf, scoring='roc_auc')
    f1_scores = cross_val_score(pipeline, X, y, cv=rskf, scoring='f1')
    
    results = {
        'model_type': 'RandomForest',
        'roc_auc': {
            'mean': float(np.mean(auc_scores)),
            'std': float(np.std(auc_scores))
        },
        'f1': {
            'mean': float(np.mean(f1_scores)),
            'std': float(np.std(f1_scores))
        },
        'n_folds': n_splits,
        'n_repeats': n_repeats,
        'n_estimators': n_estimators
    }
    
    logger.info(f"Random Forest - ROC-AUC: {results['roc_auc']['mean']:.4f} (+/- {results['roc_auc']['std']:.4f})")
    logger.info(f"Random Forest - F1: {results['f1']['mean']:.4f} (+/- {results['f1']['std']:.4f})")
    
    return results

def run_modeling_analysis(features_path: str, results_dir: str) -> Dict[str, Any]:
    """
    Run the full modeling analysis including Logistic Regression and Random Forest.
    
    Args:
        features_path: Path to the features CSV file.
        results_dir: Directory to save results.
        
    Returns:
        Dictionary with all results.
    """
    # Load data
    df = load_features_csv(features_path)
    
    # Identify feature columns (exclude non-metric columns)
    exclude_cols = ['file_path', 'is_buggy']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset")
    
    logger.info(f"Using feature columns: {feature_cols}")
    
    # Prepare data
    X, y, feature_names = prepare_features(df, feature_cols)
    
    # Check for class imbalance
    unique, counts = np.unique(y, return_counts=True)
    logger.info(f"Class distribution: {dict(zip(unique, counts))}")
    
    if len(unique) < 2:
        logger.warning("Only one class present in the target. Skipping modeling.")
        return {'error': 'Only one class present in target'}
    
    # Train models
    lr_results = train_logistic_regression(X, y, feature_names)
    rf_results = train_random_forest(X, y, feature_names)
    
    # Compile results
    all_results = {
        'logistic_regression': lr_results,
        'random_forest': rf_results
    }
    
    # Ensure results directory exists
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    # Save results
    output_path = os.path.join(results_dir, 'baseline_metrics.json')
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    return all_results

def main():
    """Main entry point for the modeling script."""
    # Default paths
    features_path = 'code/data/processed/features.csv'
    results_dir = 'code/data/results'
    
    # Allow override via environment variables
    features_path = os.environ.get('FEATURES_PATH', features_path)
    results_dir = os.environ.get('RESULTS_DIR', results_dir)
    
    logger.info(f"Starting modeling analysis with features from {features_path}")
    
    try:
        results = run_modeling_analysis(features_path, results_dir)
        logger.info("Modeling analysis completed successfully")
    except Exception as e:
        logger.error(f"Modeling analysis failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()