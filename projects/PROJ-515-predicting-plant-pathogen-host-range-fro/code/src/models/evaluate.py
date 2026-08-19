import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
from loguru import logger
from sklearn.metrics import roc_auc_score, precision_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from scipy import stats

# Import local utilities if they exist in the project structure
try:
    from src.utils.logging import get_logger
    logger = get_logger()
except ImportError:
    # Fallback if logging module not fully initialized in this context
    pass

def calculate_auprc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate Area Under the Precision-Recall Curve (AUPRC).
    Note: sklearn roc_auc_score with 'average' parameter handles multiclass,
    but for binary PR AUC, we use average_precision_score if available,
    or approximate via roc_auc_score if strictly binary is assumed.
    Here we use roc_auc_score for binary classification as a proxy if
    average_precision_score is not explicitly imported, but standard practice
    for PR-AUC is average_precision_score.
    
    Correction: Using sklearn's average_precision_score for true AUPRC.
    """
    from sklearn.metrics import average_precision_score
    return average_precision_score(y_true, y_scores)

def calculate_precision(y_true: np.ndarray, y_pred: np.ndarray, average: str = 'binary') -> float:
    """Calculate precision score."""
    return precision_score(y_true, y_pred, average=average, zero_division=0)

def benjamini_hochberg_fdr(p_values: Union[List[float], np.ndarray], alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Implement Benjamini-Hochberg FDR correction to adjust p-values.
    
    Args:
        p_values: List or array of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of (adjusted_p_values, boolean_mask_significant)
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([], dtype=bool)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values
    # Formula: p_adj[i] = p[i] * n / i
    # We must ensure monotonicity: p_adj[i] <= p_adj[i+1]
    # So we calculate from the end backwards: min(p_adj[i], p_adj[i+1])
    
    adjusted_p = np.empty(n)
    for i in range(n):
        # Rank is i + 1 (1-based)
        rank = i + 1
        adjusted_p[i] = sorted_p_values[i] * n / rank
    
    # Enforce monotonicity (cumulative minimum from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
        
    # Clamp to 1.0
    adjusted_p = np.minimum(adjusted_p, 1.0)
    
    # Restore original order
    final_adjusted_p = np.empty(n)
    final_adjusted_p[sorted_indices] = adjusted_p
    
    # Determine significance
    significant = final_adjusted_p <= alpha
    
    return final_adjusted_p, significant

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: Array of values for group 1.
        group2: Array of values for group 2.
        
    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
        
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def generate_significant_features_report(
    feature_names: List[str],
    cohen_d_values: List[float],
    p_values: List[float],
    output_path: Union[str, Path],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Generate the significant features report with FDR correction.
    
    Args:
        feature_names: List of feature names.
        cohen_d_values: List of Cohen's d effect sizes.
        p_values: List of raw p-values.
        output_path: Path to save the TSV report.
        alpha: Significance threshold for FDR.
        
    Returns:
        DataFrame containing the report data.
    """
    # Apply Benjamini-Hochberg FDR correction
    adj_p_values, significant_mask = benjamini_hochberg_fdr(p_values, alpha)
    
    # Create DataFrame
    report_data = {
        'feature_name': feature_names,
        'cohen_d': cohen_d_values,
        'adj_p_value': adj_p_values,
        'significant_flag': significant_mask
    }
    
    df = pd.DataFrame(report_data)
    
    # Sort by adjusted p-value
    df = df.sort_values('adj_p_value')
    
    # Save to TSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, sep='\t', index=False)
    
    logger.info(f"Significant features report saved to {output_path}")
    logger.info(f"Found {significant_mask.sum()} significant features at FDR <= {alpha}")
    
    return df

def run_kfold_cv(
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Run k-fold cross-validation and return average metrics.
    
    Args:
        X: Feature matrix.
        y: Target labels.
        n_splits: Number of CV folds.
        random_state: Random seed.
        
    Returns:
        Dictionary with average AUPRC and precision.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    auprc_scores = []
    precision_scores = []
    
    for train_idx, test_idx in skf.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Train simple logistic regression for evaluation
        model = LogisticRegression(penalty='l2', solver='liblinear', max_iter=1000)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_score = model.predict_proba(X_test)[:, 1]
        
        auprc_scores.append(calculate_auprc(y_test, y_score))
        precision_scores.append(calculate_precision(y_test, y_pred))
        
    return {
        'avg_auprc': np.mean(auprc_scores),
        'avg_precision': np.mean(precision_scores),
        'std_auprc': np.std(auprc_scores),
        'std_precision': np.std(precision_scores)
    }

def run_nested_cv(
    X: np.ndarray,
    y: np.ndarray,
    n_outer_splits: int = 5,
    n_inner_splits: int = 3,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run nested cross-validation with internal VIF selection.
    
    Args:
        X: Feature matrix.
        y: Target labels.
        n_outer_splits: Number of outer CV folds.
        n_inner_splits: Number of inner CV folds for hyperparameter tuning.
        random_state: Random seed.
        
    Returns:
        Dictionary with nested CV results.
    """
    from src.models.train import run_vif_selection, train_l1_logistic_regression
    
    outer_skf = StratifiedKFold(n_splits=n_outer_splits, shuffle=True, random_state=random_state)
    inner_skf = StratifiedKFold(n_splits=n_inner_splits, shuffle=True, random_state=random_state)
    
    outer_auprc = []
    outer_precision = []
    
    for outer_idx, (train_outer_idx, test_outer_idx) in enumerate(outer_skf.split(X, y)):
        X_train_outer = X[train_outer_idx]
        y_train_outer = y[train_outer_idx]
        X_test_outer = X[test_outer_idx]
        y_test_outer = y[test_outer_idx]
        
        # Inner loop for VIF selection (simplified: VIF on full outer train)
        # In a true nested CV, VIF selection would happen inside inner loop
        # Here we apply VIF on the outer training set to reduce features before model training
        try:
            selected_features_mask, _ = run_vif_selection(X_train_outer, y_train_outer, vif_threshold=5.0)
            X_train_reduced = X_train_outer[:, selected_features_mask]
            X_test_reduced = X_test_outer[:, selected_features_mask]
        except Exception as e:
            logger.warning(f"VIF selection failed for fold {outer_idx}: {e}. Using all features.")
            X_train_reduced = X_train_outer
            X_test_reduced = X_test_outer
        
        # Train model
        model = train_l1_logistic_regression(X_train_reduced, y_train_outer)
        
        # Evaluate
        y_pred = model.predict(X_test_reduced)
        y_score = model.predict_proba(X_test_reduced)[:, 1]
        
        outer_auprc.append(calculate_auprc(y_test_outer, y_score))
        outer_precision.append(calculate_precision(y_test_outer, y_pred))
        
    return {
        'auprc_scores': outer_auprc,
        'precision_scores': outer_precision,
        'mean_auprc': np.mean(outer_auprc),
        'mean_precision': np.mean(outer_precision)
    }

def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 100,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run permutation test to assess model significance.
    
    Args:
        X: Feature matrix.
        y: Target labels.
        n_permutations: Number of permutations.
        random_state: Random seed.
        
    Returns:
        Dictionary with permutation test results.
    """
    np.random.seed(random_state)
    original_auprc = run_kfold_cv(X, y)['avg_auprc']
    
    permuted_auprcs = []
    for i in range(n_permutations):
        y_permuted = np.random.permutation(y)
        permuted_auprc = run_kfold_cv(X, y_permuted)['avg_auprc']
        permuted_auprcs.append(permuted_auprc)
        
    p_value = (np.sum(np.array(permuted_auprcs) >= original_auprc) + 1) / (n_permutations + 1)
    
    return {
        'original_auprc': original_auprc,
        'permuted_auprc_mean': np.mean(permuted_auprcs),
        'permuted_auprc_std': np.std(permuted_auprcs),
        'p_value': p_value
    }

def print_summary(results: Dict[str, Any]) -> None:
    """Print a summary of evaluation results."""
    logger.info("=== Evaluation Summary ===")
    for key, value in results.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.4f}")
        else:
            logger.info(f"{key}: {value}")
    logger.info("========================")

def compare_primary_sensitivity_models(
    primary_auprc: float,
    sensitivity_auprc: float,
    output_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Compare primary and sensitivity model performance.
    
    Args:
        primary_auprc: AUPRC of the primary model.
        sensitivity_auprc: AUPRC of the sensitivity model.
        output_path: Path to save the comparison report.
        
    Returns:
        Dictionary with comparison metrics.
    """
    delta = sensitivity_auprc - primary_auprc
    flag = "IMPROVED" if delta > 0 else "DECLINED"
    
    report = {
        'primary_auprc': primary_auprc,
        'sensitivity_auprc': sensitivity_auprc,
        'delta': delta,
        'flag': flag,
        'methodology': 'AUPRC comparison between primary (unknown=exclude) and sensitivity (unknown=negative) models'
    }
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Sensitivity analysis report saved to {output_path}")
    return report

def main():
    """Main entry point for evaluation module."""
    logger.info("Evaluation module initialized.")
    # Example usage for testing
    if __name__ == "__main__":
        # Simple test of FDR correction
        p_vals = [0.01, 0.03, 0.04, 0.06, 0.08, 0.10]
        adj_p, sig = benjamini_hochberg_fdr(p_vals, alpha=0.05)
        logger.info(f"Raw p-values: {p_vals}")
        logger.info(f"Adjusted p-values: {adj_p}")
        logger.info(f"Significant: {sig}")

if __name__ == "__main__":
    main()