"""
Modeling module for User Story 2: Train and Evaluate Predictive Models.

Implements Ridge Regression and Logistic Ridge for ADHD-RS prediction and
binary diagnosis using Entropy-only, Connectivity-only, and Combined models.

Requirements:
- FR-003: Train models using Entropy-only, Connectivity-only, and Combined features.
- FR-002: Execute k-fold stratified cross-validation.
- Ensure Entropy-only features strictly exclude motion covariates.
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import make_scorer, r2_score, roc_auc_score
from scipy.stats import pearsonr

# Import existing API surface
from connectivity_engine import load_phenotypic_data, save_reduced_features
from utils import setup_logger

# Constants
TARGET_LENGTH = 120
ATLAS_N = 200
N_FOLDS = 5
RANDOM_STATE = 42

logger = setup_logger(__name__)


def load_entropy_features(csv_path: str) -> pd.DataFrame:
    """
    Load entropy features from CSV.
    
    Args:
        csv_path: Path to subject_entropy_features.csv
        
    Returns:
        DataFrame with subject_id as index and entropy features as columns.
        
    Note:
        This function strictly excludes motion covariates (e.g., scrub_fraction)
        as required by FR-003.
    """
    df = pd.read_csv(csv_path)
    if 'subject_id' in df.columns:
        df = df.set_index('subject_id')
    # Ensure no motion-related columns are included
    motion_cols = [col for col in df.columns if 'fd' in col.lower() or 'motion' in col.lower()]
    if motion_cols:
        logger.warning(f"Removing motion covariates from entropy features: {motion_cols}")
        df = df.drop(columns=motion_cols)
    return df


def load_connectivity_features(csv_path: str) -> pd.DataFrame:
    """
    Load reduced connectivity features from CSV (output of T023c).
    
    Args:
        csv_path: Path to connectivity_features_reduced.csv
        
    Returns:
        DataFrame with subject_id as index and reduced connectivity features.
    """
    df = pd.read_csv(csv_path)
    if 'subject_id' in df.columns:
        df = df.set_index('subject_id')
    return df


def align_features_and_labels(
    entropy_df: pd.DataFrame,
    conn_df: pd.DataFrame,
    phenotypic_df: pd.DataFrame,
    target_col: str = 'adhd_rs_total'
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Align subjects across all feature sets and extract labels.
    
    Args:
        entropy_df: Entropy features DataFrame
        conn_df: Connectivity features DataFrame
        phenotypic_df: Phenotypic data with labels
        target_col: Column name for ADHD-RS total score
        
    Returns:
        Tuple of (combined_features_df, adhd_rs_labels, binary_labels)
    """
    # Find common subjects
    common_subjects = set(entropy_df.index) & set(conn_df.index) & set(phenotypic_df.index)
    
    if len(common_subjects) == 0:
        raise ValueError("No common subjects found across feature sets and phenotypic data.")
    
    logger.info(f"Aligning {len(common_subjects)} subjects across all data sources.")
    
    # Filter to common subjects
    entropy_df = entropy_df.loc[list(common_subjects)]
    conn_df = conn_df.loc[list(common_subjects)]
    phenotypic_df = phenotypic_df.loc[list(common_subjects)]
    
    # Combine features
    combined_df = pd.concat([entropy_df, conn_df], axis=1)
    
    # Extract labels
    adhd_rs_labels = phenotypic_df[target_col]
    binary_labels = (phenotypic_df['diagnosis'] == 'ADHD').astype(int)
    
    return combined_df, adhd_rs_labels, binary_labels


def compute_pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Pearson correlation coefficient."""
    if len(np.unique(y_true)) < 2 or len(np.unique(y_pred)) < 2:
        return 0.0
    r, _ = pearsonr(y_true, y_pred)
    return r if not np.isnan(r) else 0.0


def train_and_evaluate_ridge(
    X: pd.DataFrame,
    y: pd.Series,
    n_folds: int = N_FOLDS,
    random_state: int = RANDOM_STATE
) -> Dict[str, Any]:
    """
    Train Ridge Regression model with k-fold cross-validation.
    
    Args:
        X: Feature DataFrame
        y: Target Series (ADHD-RS total score)
        n_folds: Number of CV folds
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with metrics: mean_r, std_r, fold_r_values
    """
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Define model
    model = Ridge(alpha=1.0, random_state=random_state)
    
    # Custom scorer for Pearson r
    pearson_scorer = make_scorer(compute_pearson_r)
    
    # Stratified K-Fold
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    # Compute cross-validation scores
    cv_scores = cross_val_score(model, X_scaled, y, cv=skf, scoring=pearson_scorer)
    
    # Get predictions for all folds
    y_pred = cross_val_predict(model, X_scaled, y, cv=skf)
    
    # Compute overall metrics
    mean_r = np.mean(cv_scores)
    std_r = np.std(cv_scores)
    
    return {
        'mean_r': float(mean_r),
        'std_r': float(std_r),
        'fold_r_values': [float(r) for r in cv_scores],
        'overall_pearson_r': float(compute_pearson_r(y.values, y_pred))
    }


def train_and_evaluate_logistic_ridge(
    X: pd.DataFrame,
    y: pd.Series,
    n_folds: int = N_FOLDS,
    random_state: int = RANDOM_STATE
) -> Dict[str, Any]:
    """
    Train Logistic Ridge model with k-fold cross-validation.
    
    Args:
        X: Feature DataFrame
        y: Binary target Series (ADHD diagnosis)
        n_folds: Number of CV folds
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with metrics: mean_auc, std_auc, fold_auc_values
    """
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Define model
    model = LogisticRegression(
        penalty='l2',
        C=1.0,
        solver='lbfgs',
        max_iter=1000,
        random_state=random_state
    )
    
    # Stratified K-Fold
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    # Compute cross-validation scores (AUC)
    cv_scores = cross_val_score(model, X_scaled, y, cv=skf, scoring='roc_auc')
    
    # Get predictions for all folds
    y_pred_proba = cross_val_predict(model, X_scaled, y, cv=skf, method='predict_proba')[:, 1]
    
    # Compute overall metrics
    mean_auc = np.mean(cv_scores)
    std_auc = np.std(cv_scores)
    
    return {
        'mean_auc': float(mean_auc),
        'std_auc': float(std_auc),
        'fold_auc_values': [float(auc) for auc in cv_scores],
        'overall_auc': float(roc_auc_score(y.values, y_pred_proba))
    }


def run_modeling_pipeline(
    entropy_csv: str,
    conn_csv: str,
    phenotypic_csv: str,
    output_dir: str,
    use_entropy: bool = True,
    use_connectivity: bool = True
) -> Dict[str, Any]:
    """
    Run the full modeling pipeline for specified model types.
    
    Args:
        entropy_csv: Path to entropy features CSV
        conn_csv: Path to reduced connectivity features CSV
        phenotypic_csv: Path to phenotypic data CSV
        output_dir: Directory to save results
        use_entropy: Include entropy features
        use_connectivity: Include connectivity features
        
    Returns:
        Dictionary with all model metrics
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    logger.info("Loading entropy features...")
    entropy_df = load_entropy_features(entropy_csv)
    
    logger.info("Loading connectivity features...")
    conn_df = load_connectivity_features(conn_csv)
    
    logger.info("Loading phenotypic data...")
    phenotypic_df = load_phenotypic_data(phenotypic_csv)
    
    # Align data
    combined_df, adhd_rs_labels, binary_labels = align_features_and_labels(
        entropy_df, conn_df, phenotypic_df
    )
    
    # Determine feature subsets
    results = {}
    
    # Entropy-only model
    if use_entropy:
        logger.info("Training Entropy-only Ridge model...")
        entropy_features = entropy_df.loc[combined_df.index]
        results['entropy_ridge'] = train_and_evaluate_ridge(
            entropy_features, adhd_rs_labels
        )
        
        logger.info("Training Entropy-only Logistic Ridge model...")
        results['entropy_logistic'] = train_and_evaluate_logistic_ridge(
            entropy_features, binary_labels
        )
    
    # Connectivity-only model
    if use_connectivity:
        logger.info("Training Connectivity-only Ridge model...")
        conn_features = conn_df.loc[combined_df.index]
        results['connectivity_ridge'] = train_and_evaluate_ridge(
            conn_features, adhd_rs_labels
        )
        
        logger.info("Training Connectivity-only Logistic Ridge model...")
        results['connectivity_logistic'] = train_and_evaluate_logistic_ridge(
            conn_features, binary_labels
        )
    
    # Combined model
    if use_entropy and use_connectivity:
        logger.info("Training Combined Ridge model...")
        results['combined_ridge'] = train_and_evaluate_ridge(
            combined_df, adhd_rs_labels
        )
        
        logger.info("Training Combined Logistic Ridge model...")
        results['combined_logistic'] = train_and_evaluate_logistic_ridge(
            combined_df, binary_labels
        )
    
    # Save results
    results_path = Path(output_dir) / 'model_metrics.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    
    return results


def main():
    """Main entry point for modeling pipeline."""
    parser = argparse.ArgumentParser(description='Train and evaluate predictive models for ADHD traits.')
    parser.add_argument('--entropy-csv', type=str, required=True, 
                      help='Path to entropy features CSV')
    parser.add_argument('--conn-csv', type=str, required=True,
                      help='Path to reduced connectivity features CSV')
    parser.add_argument('--phenotypic-csv', type=str, required=True,
                      help='Path to phenotypic data CSV')
    parser.add_argument('--output-dir', type=str, default='data/derived',
                      help='Output directory for results')
    parser.add_argument('--no-entropy', action='store_true',
                      help='Skip entropy-only models')
    parser.add_argument('--no-connectivity', action='store_true',
                      help='Skip connectivity-only models')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger(__name__, level=logging.INFO)
    
    try:
        results = run_modeling_pipeline(
            entropy_csv=args.entropy_csv,
            conn_csv=args.conn_csv,
            phenotypic_csv=args.phenotypic_csv,
            output_dir=args.output_dir,
            use_entropy=not args.no_entropy,
            use_connectivity=not args.no_connectivity
        )
        
        # Print summary
        print("\n=== Model Performance Summary ===")
        for model_name, metrics in results.items():
            if 'mean_r' in metrics:
                print(f"{model_name}: Pearson r = {metrics['mean_r']:.4f} (+/- {metrics['std_r']:.4f})")
            if 'mean_auc' in metrics:
                print(f"{model_name}: AUC = {metrics['mean_auc']:.4f} (+/- {metrics['std_auc']:.4f})")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == '__main__':
    main()