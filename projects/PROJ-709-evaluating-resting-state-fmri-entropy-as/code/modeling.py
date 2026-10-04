import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from scipy.stats import pearsonr
from scipy.stats import ttest_rel
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/derived/modeling.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_entropy_features(path: str = "data/processed/subject_entropy_features.csv") -> pd.DataFrame:
    """Load entropy features from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Entropy features file not found: {path}")
    df = pd.read_csv(path)
    return df

def load_connectivity_features(path: str = "data/derived/connectivity_features_baseline.csv") -> pd.DataFrame:
    """Load connectivity features from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Connectivity features file not found: {path}")
    df = pd.read_csv(path)
    return df

def load_phenotype_data(path: str = "data/derived/phenotype_data.csv") -> pd.DataFrame:
    """Load phenotype data from CSV."""
    if not os.path.exists(path):
        # Fallback to OpenNeuro phenotypic file if standard path missing
        fallback_path = "data/raw/ADHD-200_Cleveland/ADHD-200_Cleveland_phenotypic.csv"
        if os.path.exists(fallback_path):
            df = pd.read_csv(fallback_path)
            # Standardize column names if necessary
            if 'ADHD' in df.columns or 'Diagnosis' in df.columns:
                return df
            else:
                raise FileNotFoundError(f"Phenotype data file not found at fallback path: {fallback_path}")
        raise FileNotFoundError(f"Phenotype data file not found: {path}")
    return pd.read_csv(path)

def align_features_and_labels(features_df: pd.DataFrame, labels_df: pd.DataFrame, 
                              subject_col: str = "subject_id", label_col: str = "Diagnosis") -> Tuple[np.ndarray, np.ndarray]:
    """Align feature matrix and labels based on subject IDs."""
    # Merge on subject_id
    merged = features_df.merge(labels_df, on=subject_col, how='inner')
    if merged.empty:
        raise ValueError("No matching subjects found between features and labels.")
    
    # Sort to ensure consistent ordering
    merged = merged.sort_values(by=subject_col)
    
    X = merged.drop(columns=[subject_col, label_col]).values
    y = merged[label_col].values
    
    logger.info(f"Aligned {len(X)} samples with {X.shape[1]} features")
    return X, y

def compute_pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Pearson correlation coefficient."""
    return pearsonr(y_true, y_pred)[0]

def train_and_evaluate_ridge(X: np.ndarray, y: np.ndarray, 
                             cv_folds: int = 5, 
                             random_state: int = 42,
                             alpha: float = 1.0) -> Dict[str, Any]:
    """Train Ridge Regression and evaluate with CV."""
    logger.info(f"Training Ridge Regression with alpha={alpha}")
    logger.info(f"Samples (N): {X.shape[0]}, Features (P): {X.shape[1]}")
    
    if X.shape[0] < X.shape[1]:
        logger.warning(f"Underpowered model detected: N ({X.shape[0]}) < P ({X.shape[1]}). Potential overfitting.")

    # Stratified K-Fold
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    # Check for minimum samples per class per fold
    for i, (train_index, test_index) in enumerate(skf.split(X, y)):
        y_train_fold = y[train_index]
        y_test_fold = y[test_index]
        
        unique_train, counts_train = np.unique(y_train_fold, return_counts=True)
        unique_test, counts_test = np.unique(y_test_fold, return_counts=True)
        
        for cls, count in zip(unique_train, counts_train):
            if count < 10:
                raise ValueError(
                    f"Stratified CV fold {i} has insufficient samples for class {cls} in training set: {count} < 10. "
                    "This violates the minimum stratification requirement."
                )
        for cls, count in zip(unique_test, counts_test):
            if count < 10:
                raise ValueError(
                    f"Stratified CV fold {i} has insufficient samples for class {cls} in test set: {count} < 10. "
                    "This violates the minimum stratification requirement."
                )
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', Ridge(alpha=alpha))
    ])
    
    scores = cross_val_score(pipeline, X, y, cv=skf, scoring='neg_mean_squared_error')
    mse_scores = -scores
    rmse_scores = np.sqrt(mse_scores)
    
    # Also compute correlation scores manually if needed, but sklearn doesn't have direct r scoring for regression
    # We'll simulate correlation scoring by fitting on each fold
    correlations = []
    for train_index, test_index in skf.split(X, y):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        corr = compute_pearson_r(y_test, y_pred)
        correlations.append(corr)
    
    return {
        "model": "Ridge",
        "mean_rmse": np.mean(rmse_scores),
        "std_rmse": np.std(rmse_scores),
        "mean_correlation": np.mean(correlations),
        "std_correlation": np.std(correlations),
        "correlations_per_fold": correlations
    }

def train_and_evaluate_logistic_ridge(X: np.ndarray, y: np.ndarray, 
                                      cv_folds: int = 5, 
                                      random_state: int = 42,
                                      alpha: float = 1.0) -> Dict[str, Any]:
    """Train Logistic Regression and evaluate with CV."""
    logger.info(f"Training Logistic Ridge with alpha={alpha}")
    logger.info(f"Samples (N): {X.shape[0]}, Features (P): {X.shape[1]}")
    
    # Stratified K-Fold
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    # Check for minimum samples per class per fold
    for i, (train_index, test_index) in enumerate(skf.split(X, y)):
        y_train_fold = y[train_index]
        y_test_fold = y[test_index]
        
        unique_train, counts_train = np.unique(y_train_fold, return_counts=True)
        unique_test, counts_test = np.unique(y_test_fold, return_counts=True)
        
        for cls, count in zip(unique_train, counts_train):
            if count < 10:
                raise ValueError(
                    f"Stratified CV fold {i} has insufficient samples for class {cls} in training set: {count} < 10. "
                    "This violates the minimum stratification requirement."
                )
        for cls, count in zip(unique_test, counts_test):
            if count < 10:
                raise ValueError(
                    f"Stratified CV fold {i} has insufficient samples for class {cls} in test set: {count} < 10. "
                    "This violates the minimum stratification requirement."
                )
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(penalty='l2', C=1.0/alpha, solver='lbfgs', max_iter=1000))
    ])
    
    # AUC scoring
    scores = cross_val_score(pipeline, X, y, cv=skf, scoring='roc_auc')
    
    return {
        "model": "LogisticRidge",
        "mean_auc": np.mean(scores),
        "std_auc": np.std(scores),
        "auc_per_fold": scores.tolist()
    }

def perform_likelihood_ratio_test(full_model_scores: Dict, reduced_model_scores: Dict) -> Dict[str, Any]:
    """Perform likelihood ratio test (simplified as difference in metrics)."""
    # Note: True LRT requires log-likelihoods. Here we approximate with metric differences.
    delta_r = full_model_scores.get("mean_correlation", 0) - reduced_model_scores.get("mean_correlation", 0)
    return {
        "delta_r": delta_r,
        "full_model_mean_r": full_model_scores.get("mean_correlation", 0),
        "reduced_model_mean_r": reduced_model_scores.get("mean_correlation", 0)
    }

def run_modeling_pipeline(entropy_path: str = "data/processed/subject_entropy_features.csv",
                          connectivity_path: str = "data/derived/connectivity_features_baseline.csv",
                          phenotype_path: str = "data/derived/phenotype_data.csv",
                          output_path: str = "data/derived/model_metrics.json") -> str:
    """Run the full modeling pipeline."""
    logger.info("Starting modeling pipeline...")
    
    # Load data
    entropy_df = load_entropy_features(entropy_path)
    conn_df = load_connectivity_features(connectivity_path)
    phen_df = load_phenotype_data(phenotype_path)
    
    # Prepare labels (binary diagnosis)
    if 'Diagnosis' not in phen_df.columns:
        # Try to map ADHD column
        for col in ['ADHD', 'diagnosis']:
            if col in phen_df.columns:
                phen_df['Diagnosis'] = phen_df[col]
                break
    
    # Align Entropy
    X_entropy, y = align_features_and_labels(entropy_df, phen_df, label_col='Diagnosis')
    
    # Align Connectivity
    X_conn, _ = align_features_and_labels(conn_df, phen_df, label_col='Diagnosis')
    
    # Combined
    X_combined = np.hstack([X_entropy, X_conn])
    
    results = {}
    
    # 1. Entropy Only
    try:
        logger.info("Evaluating Entropy-only model...")
        results['entropy'] = train_and_evaluate_ridge(X_entropy, y)
    except ValueError as e:
        logger.error(f"Entropy model failed: {e}")
        results['entropy'] = {"error": str(e)}
    
    # 2. Connectivity Only
    try:
        logger.info("Evaluating Connectivity-only model...")
        results['connectivity'] = train_and_evaluate_ridge(X_conn, y)
    except ValueError as e:
        logger.error(f"Connectivity model failed: {e}")
        results['connectivity'] = {"error": str(e)}
    
    # 3. Combined
    try:
        logger.info("Evaluating Combined model...")
        results['combined'] = train_and_evaluate_ridge(X_combined, y)
    except ValueError as e:
        logger.error(f"Combined model failed: {e}")
        results['combined'] = {"error": str(e)}
    
    # Logistic Models
    try:
        logger.info("Evaluating Logistic Entropy-only...")
        results['logistic_entropy'] = train_and_evaluate_logistic_ridge(X_entropy, y)
    except ValueError as e:
        logger.error(f"Logistic Entropy model failed: {e}")
        results['logistic_entropy'] = {"error": str(e)}
    
    try:
        logger.info("Evaluating Logistic Connectivity...")
        results['logistic_connectivity'] = train_and_evaluate_logistic_ridge(X_conn, y)
    except ValueError as e:
        logger.error(f"Logistic Connectivity model failed: {e}")
        results['logistic_connectivity'] = {"error": str(e)}
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Modeling pipeline complete. Results saved to {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Run modeling pipeline for ADHD prediction.")
    parser.add_argument('--entropy', type=str, default="data/processed/subject_entropy_features.csv",
                        help='Path to entropy features CSV')
    parser.add_argument('--connectivity', type=str, default="data/derived/connectivity_features_baseline.csv",
                        help='Path to connectivity features CSV')
    parser.add_argument('--phenotype', type=str, default="data/derived/phenotype_data.csv",
                        help='Path to phenotype data CSV')
    parser.add_argument('--output', type=str, default="data/derived/model_metrics.json",
                        help='Path to output metrics JSON')
    
    args = parser.parse_args()
    
    run_modeling_pipeline(
        entropy_path=args.entropy,
        connectivity_path=args.connectivity,
        phenotype_path=args.phenotype,
        output_path=args.output
    )

if __name__ == "__main__":
    main()