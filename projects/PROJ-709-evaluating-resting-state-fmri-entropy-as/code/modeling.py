import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, roc_auc_score

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_entropy_features(filepath: str) -> pd.DataFrame:
    """Load entropy features from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Entropy features file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def load_connectivity_features(filepath: str) -> pd.DataFrame:
    """Load connectivity features (baseline or reduced) from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Connectivity features file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def load_phenotype_data(filepath: str) -> pd.DataFrame:
    """Load phenotype data (ADHD scores/diagnosis)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Phenotype data file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def align_features_and_labels(
    feature_df: pd.DataFrame,
    label_df: pd.DataFrame,
    id_col: str = 'subject_id'
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Align feature matrix and labels by subject_id, returning X, y, and subject_ids."""
    merged = pd.merge(feature_df, label_df, on=id_col, how='inner')
    if len(merged) == 0:
        raise ValueError("No overlapping subjects between features and labels.")
    
    # Sort to ensure consistent ordering
    merged = merged.sort_values(by=id_col)
    subject_ids = merged[id_col].tolist()
    y = merged['adhd_rs_score'].values  # Regression target
    # For binary classification, we might derive y_binary later if needed
    X = merged.drop(columns=[id_col, 'adhd_rs_score', 'diagnosis']).values
    return X, y, subject_ids

def compute_pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Pearson correlation coefficient."""
    if len(y_true) < 2 or np.std(y_true) == 0 or np.std(y_pred) == 0:
        return 0.0
    corr, _ = stats.pearsonr(y_true, y_pred)
    return float(corr)

def train_and_evaluate_ridge(
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """Train Ridge Regression with CV and return metrics."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = Ridge(alpha=1.0)
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
    
    # Create dummy binary labels for StratifiedKFold if y is continuous
    # We use median split for stratification purposes only
    y_dummy = (y > np.median(y)).astype(int)
    
    r_scores = []
    mse_scores = []
    
    for train_idx, test_idx in skf.split(X_scaled, y_dummy):
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        r_scores.append(compute_pearson_r(y_test, y_pred))
        mse_scores.append(mean_squared_error(y_test, y_pred))
    
    return {
        'mean_r': float(np.mean(r_scores)),
        'std_r': float(np.std(r_scores)),
        'mean_mse': float(np.mean(mse_scores)),
        'std_mse': float(np.std(mse_scores))
    }

def train_and_evaluate_logistic_ridge(
    X: np.ndarray,
    y_binary: np.ndarray,
    cv: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """Train Logistic Regression with CV and return AUC metrics."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(max_iter=1000, random_state=random_state)
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
    
    auc_scores = []
    
    for train_idx, test_idx in skf.split(X_scaled, y_binary):
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y_binary[train_idx], y_binary[test_idx]
        
        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        if len(np.unique(y_test)) > 1:
            auc_scores.append(roc_auc_score(y_test, y_prob))
        else:
            auc_scores.append(0.5) # Fallback if only one class in fold
    
    return {
        'mean_auc': float(np.mean(auc_scores)),
        'std_auc': float(np.std(auc_scores))
    }

def perform_likelihood_ratio_test(
    X_reduced: np.ndarray,
    y: np.ndarray,
    X_full: np.ndarray,
    cv: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform Nested Model Comparison (Likelihood Ratio Test) to verify unique value of entropy.
    
    Compares a reduced model (Connectivity only) against a full model (Connectivity + Entropy).
    Since Ridge regression does not have a direct log-likelihood in the standard sense 
    without assuming Gaussian errors, we approximate the LRT using the difference in 
    residual sum of squares (RSS) scaled by degrees of freedom, or use an F-test 
    equivalent for nested linear models.
    
    However, to strictly follow "Likelihood Ratio Test" in a regularized context, 
    we will use the difference in log-likelihoods derived from the Gaussian assumption:
    LL = -N/2 * log(2*pi*sigma^2) - RSS / (2*sigma^2)
    
    We estimate sigma^2 from the full model's residuals.
    """
    scaler_reduced = StandardScaler()
    X_red_scaled = scaler_reduced.fit_transform(X_reduced)
    
    scaler_full = StandardScaler()
    X_full_scaled = scaler_full.fit_transform(X_full)
    
    # Use a fixed alpha for comparison consistency
    alpha = 1.0
    
    # Fit models on full data for LRT statistic calculation
    # Note: In a strict nested test, we often compare on the same hold-out or use CV-averaged likelihoods.
    # Here we implement a standard LRT on the aggregated predictions or a pooled fit.
    # Given the cross-validation context of the pipeline, we will perform the test 
    # on the aggregated predicted values from CV (pseudo-likelihood) or simply 
    # compare the RSS on the full dataset if the goal is feature contribution.
    
    # Approach: Fit on full data to estimate RSS for LRT statistic (common in exploratory biomarker analysis)
    # This tests if adding features significantly reduces RSS.
    
    model_red = Ridge(alpha=alpha)
    model_red.fit(X_red_scaled, y)
    y_pred_red = model_red.predict(X_red_scaled)
    rss_red = np.sum((y - y_pred_red) ** 2)
    
    model_full = Ridge(alpha=alpha)
    model_full.fit(X_full_scaled, y)
    y_pred_full = model_full.predict(X_full_scaled)
    rss_full = np.sum((y - y_pred_full) ** 2)
    
    n = len(y)
    p_red = X_reduced.shape[1]
    p_full = X_full.shape[1]
    k = p_full - p_red  # number of added parameters (entropy features)
    
    # Estimate sigma^2 from full model residuals
    sigma2_hat = rss_full / (n - p_full)
    
    if sigma2_hat <= 0:
        logger.warning("Sigma squared estimate is non-positive. LRT may be invalid.")
        return {'statistic': 0.0, 'p_value': 1.0, 'conclusion': 'Invalid sigma2'}
    
    # LRT Statistic: Lambda = (RSS_red - RSS_full) / sigma^2
    # Under H0, this follows Chi-squared distribution with k degrees of freedom
    # Note: In OLS, (RSS_red - RSS_full)/sigma^2 ~ Chi2(k)
    # With Ridge, this is an approximation.
    lrt_stat = (rss_red - rss_full) / sigma2_hat
    
    # Calculate p-value
    p_value = 1.0 - stats.chi2.cdf(lrt_stat, k)
    
    return {
        'rss_reduced': float(rss_red),
        'rss_full': float(rss_full),
        'sigma2_hat': float(sigma2_hat),
        'lrt_statistic': float(lrt_stat),
        'degrees_of_freedom': int(k),
        'p_value': float(p_value),
        'entropy_significant': p_value < 0.05
    }

def run_modeling_pipeline(
    entropy_path: str,
    connectivity_path: str,
    phenotype_path: str,
    output_path: str
) -> str:
    """
    Run the full modeling pipeline including Nested Model Comparison.
    
    1. Load Entropy, Connectivity, and Phenotype data.
    2. Align features.
    3. Train models (Entropy-only, Connectivity-only, Combined).
    4. Perform Nested Model Comparison (LRT) to verify unique value of Entropy.
    5. Save results to JSON.
    """
    logger.info(f"Loading entropy features from {entropy_path}")
    df_entropy = load_entropy_features(entropy_path)
    
    logger.info(f"Loading connectivity features from {connectivity_path}")
    df_conn = load_connectivity_features(connectivity_path)
    
    logger.info(f"Loading phenotype data from {phenotype_path}")
    df_pheno = load_phenotype_data(phenotype_path)
    
    # Align Entropy + Phenotype
    X_entropy, y, subjects = align_features_and_labels(df_entropy, df_pheno)
    logger.info(f"Aligned {len(subjects)} subjects for Entropy model.")
    
    # Align Connectivity + Phenotype (must use same subjects)
    # Filter connectivity to only subjects in the entropy set
    df_conn_filtered = df_conn[df_conn['subject_id'].isin(subjects)].sort_values('subject_id')
    df_pheno_filtered = df_pheno[df_pheno['subject_id'].isin(subjects)].sort_values('subject_id')
    
    X_conn, _, _ = align_features_and_labels(df_conn_filtered, df_pheno_filtered)
    logger.info(f"Aligned {len(X_conn)} subjects for Connectivity model.")
    
    # Combined features
    X_combined = np.hstack([X_entropy, X_conn])
    
    # 1. Train and Evaluate Models
    logger.info("Training Entropy-only model...")
    metrics_entropy = train_and_evaluate_ridge(X_entropy, y)
    
    logger.info("Training Connectivity-only model...")
    metrics_conn = train_and_evaluate_ridge(X_conn, y)
    
    logger.info("Training Combined model...")
    metrics_combined = train_and_evaluate_ridge(X_combined, y)
    
    # 2. Nested Model Comparison (Likelihood Ratio Test)
    # Reduced: Connectivity only
    # Full: Connectivity + Entropy
    logger.info("Performing Nested Model Comparison (LRT)...")
    lrt_results = perform_likelihood_ratio_test(
        X_reduced=X_conn,
        y=y,
        X_full=X_combined,
        cv=5
    )
    
    # Compile results
    results = {
        'entropy_model': metrics_entropy,
        'connectivity_model': metrics_conn,
        'combined_model': metrics_combined,
        'nested_model_comparison': lrt_results
    }
    
    # Save results
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Modeling pipeline complete. Results saved to {output_path}")
    
    # Log summary
    logger.info(f"Entropy-only R: {metrics_entropy['mean_r']:.4f} (+/- {metrics_entropy['std_r']:.4f})")
    logger.info(f"Connectivity-only R: {metrics_conn['mean_r']:.4f} (+/- {metrics_conn['std_r']:.4f})")
    logger.info(f"Combined R: {metrics_combined['mean_r']:.4f} (+/- {metrics_combined['std_r']:.4f})")
    logger.info(f"LRT p-value: {lrt_results['p_value']:.4f} (Entropy unique value: {lrt_results['entropy_significant']})")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Run Modeling Pipeline with LRT")
    parser.add_argument("--entropy", type=str, required=True, help="Path to entropy features CSV")
    parser.add_argument("--connectivity", type=str, required=True, help="Path to connectivity features CSV")
    parser.add_argument("--phenotype", type=str, required=True, help="Path to phenotype CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    
    args = parser.parse_args()
    
    run_modeling_pipeline(
        entropy_path=args.entropy,
        connectivity_path=args.connectivity,
        phenotype_path=args.phenotype,
        output_path=args.output
    )

if __name__ == "__main__":
    main()