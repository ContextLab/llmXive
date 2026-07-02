import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
from scipy import stats
from loguru import logger
from src.utils.logging import get_logger

logger = get_logger(__name__)

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Perform Benjamini-Hochberg FDR correction on a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        List of adjusted p-values (q-values).
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BH adjusted p-values
    # q_i = p_i * n / i (where i is rank, 1-based)
    # Then enforce monotonicity (q_i <= q_{i+1})
    ranks = np.arange(1, n + 1)
    adjusted = sorted_p * n / ranks
    
    # Ensure monotonicity: q_i = min(q_i, q_{i+1}, ..., q_n)
    # We do this by iterating backwards
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
    
    # Cap at 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Restore original order
    result = np.zeros(n)
    result[sorted_indices] = adjusted
    
    return result.tolist()

def calculate_cohen_d(group1: Union[List[float], np.ndarray], group2: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
        
    Returns:
        Cohen's d value.
    """
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1 = np.mean(group1)
    mean2 = np.mean(group2)
    
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def run_kfold_cross_validation(
    features_df: pd.DataFrame,
    labels: pd.Series,
    n_splits: int = 5,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run k-fold cross-validation and return metrics.
    
    Args:
        features_df: Feature matrix DataFrame.
        labels: Target labels Series.
        n_splits: Number of CV folds.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing cross-validation metrics.
    """
    from sklearn.model_selection import KFold
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import precision_score, recall_score, roc_auc_score
    
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    auprc_scores = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(kf.split(features_df)):
        X_train = features_df.iloc[train_idx]
        y_train = labels.iloc[train_idx]
        X_val = features_df.iloc[val_idx]
        y_val = labels.iloc[val_idx]
        
        model = LogisticRegression(penalty='l2', max_iter=1000, random_state=random_state)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)[:, 1]
        
        auprc = roc_auc_score(y_val, y_proba)
        auprc_scores.append(auprc)
        
        logger.info(f"Fold {fold_idx + 1}/{n_splits}: AUPRC = {auprc:.4f}")
    
    return {
        "mean_auprc": np.mean(auprc_scores),
        "std_auprc": np.std(auprc_scores),
        "scores": auprc_scores
    }

def run_nested_cv(
    features_df: pd.DataFrame,
    labels: pd.Series,
    n_outer_splits: int = 5,
    n_inner_splits: int = 3,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run nested cross-validation for unbiased performance estimation.
    
    Args:
        features_df: Feature matrix DataFrame.
        labels: Target labels Series.
        n_outer_splits: Number of outer CV folds.
        n_inner_splits: Number of inner CV folds.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing nested CV metrics.
    """
    from sklearn.model_selection import KFold
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    
    outer_kf = KFold(n_splits=n_outer_splits, shuffle=True, random_state=random_state)
    inner_kf = KFold(n_splits=n_inner_splits, shuffle=True, random_state=random_state)
    
    outer_auprc_scores = []
    
    for outer_fold_idx, (outer_train_idx, outer_val_idx) in enumerate(outer_kf.split(features_df)):
        X_outer_train = features_df.iloc[outer_train_idx]
        y_outer_train = labels.iloc[outer_train_idx]
        X_outer_val = features_df.iloc[outer_val_idx]
        y_outer_val = labels.iloc[outer_val_idx]
        
        # Inner CV for hyperparameter tuning
        best_score = -np.inf
        best_params = {'penalty': 'l2', 'C': 1.0}
        
        for C in [0.01, 0.1, 1.0, 10.0]:
            inner_scores = []
            for inner_train_idx, inner_val_idx in inner_kf.split(X_outer_train):
                X_inner_train = X_outer_train.iloc[inner_train_idx]
                y_inner_train = y_outer_train.iloc[inner_train_idx]
                X_inner_val = X_outer_train.iloc[inner_val_idx]
                y_inner_val = y_outer_train.iloc[inner_val_idx]
                
                model = LogisticRegression(penalty='l2', C=C, max_iter=1000, random_state=random_state)
                model.fit(X_inner_train, y_inner_train)
                y_proba = model.predict_proba(X_inner_val)[:, 1]
                score = roc_auc_score(y_inner_val, y_proba)
                inner_scores.append(score)
            
            mean_inner_score = np.mean(inner_scores)
            if mean_inner_score > best_score:
                best_score = mean_inner_score
                best_params['C'] = C
        
        # Train final model on outer train with best params
        final_model = LogisticRegression(
            penalty='l2', 
            C=best_params['C'], 
            max_iter=1000, 
            random_state=random_state
        )
        final_model.fit(X_outer_train, y_outer_train)
        
        # Evaluate on outer validation set
        y_proba_outer = final_model.predict_proba(X_outer_val)[:, 1]
        outer_auprc = roc_auc_score(y_outer_val, y_proba_outer)
        outer_auprc_scores.append(outer_auprc)
        
        logger.info(f"Outer Fold {outer_fold_idx + 1}/{n_outer_splits}: AUPRC = {outer_auprc:.4f}")
    
    return {
        "mean_auprc": np.mean(outer_auprc_scores),
        "std_auprc": np.std(outer_auprc_scores),
        "outer_scores": outer_auprc_scores,
        "best_inner_C": best_params['C']
    }

def run_permutation_test(
    features_df: pd.DataFrame,
    labels: pd.Series,
    n_permutations: int = 100,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run permutation test to assess model significance.
    
    Args:
        features_df: Feature matrix DataFrame.
        labels: Target labels Series.
        n_permutations: Number of permutations.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing permutation test results.
    """
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    
    rng = np.random.RandomState(random_state)
    perm_scores = []
    
    for i in range(n_permutations):
        # Shuffle labels
        y_perm = labels.sample(frac=1, random_state=rng.randint(0, 2**32)).reset_index(drop=True)
        
        X_train, X_test, y_train, y_test = train_test_split(
            features_df, y_perm, test_size=0.2, random_state=random_state, stratify=y_perm
        )
        
        model = LogisticRegression(penalty='l2', max_iter=1000, random_state=random_state)
        model.fit(X_train, y_train)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        score = roc_auc_score(y_test, y_proba)
        perm_scores.append(score)
    
    return {
        "perm_scores": perm_scores,
        "mean_perm_score": np.mean(perm_scores),
        "std_perm_score": np.std(perm_scores)
    }

def generate_significant_features_report(
    features_df: pd.DataFrame,
    labels: pd.Series,
    output_path: Union[str, Path],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Generate a report of significant features based on Cohen's d and FDR-corrected p-values.
    
    Args:
        features_df: Feature matrix DataFrame (rows=pathogens, cols=features).
        labels: Target labels Series (binary: 0=narrow, 1=broad host range).
        output_path: Path to save the TSV report.
        alpha: Significance threshold for FDR correction.
        
    Returns:
        DataFrame containing the significant features report.
    """
    logger.info(f"Generating significant features report for {features_df.shape[1]} features...")
    
    # Separate groups
    group_broad = features_df[labels == 1]
    group_narrow = features_df[labels == 0]
    
    results = []
    p_values = []
    
    for feature_name in features_df.columns:
        # Calculate Cohen's d
        d = calculate_cohen_d(group_broad[feature_name], group_narrow[feature_name])
        
        # Perform t-test for p-value
        t_stat, p_val = stats.ttest_ind(
            group_broad[feature_name], 
            group_narrow[feature_name], 
            equal_var=False
        )
        
        results.append({
            'feature_name': feature_name,
            'cohen_d': d,
            'p_value': p_val
        })
        p_values.append(p_val)
    
    # Apply FDR correction
    adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha)
    
    # Add adjusted p-values and significance flag
    for i, row in enumerate(results):
        row['adj_p_value'] = adjusted_p_values[i]
        row['significant_flag'] = 'Yes' if adjusted_p_values[i] <= alpha else 'No'
    
    # Create DataFrame and sort by absolute Cohen's d
    report_df = pd.DataFrame(results)
    report_df = report_df.sort_values(by='cohen_d', key=abs, ascending=False)
    
    # Ensure correct column order
    report_df = report_df[['feature_name', 'cohen_d', 'adj_p_value', 'significant_flag']]
    
    # Save to TSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, sep='\t', index=False)
    
    logger.info(f"Significant features report saved to {output_path}")
    logger.info(f"Features with adj_p_value <= {alpha}: {report_df['significant_flag'].sum()}")
    
    return report_df

def print_summary(metrics: Dict[str, Any]) -> None:
    """
    Print a summary of evaluation metrics.
    
    Args:
        metrics: Dictionary containing evaluation metrics.
    """
    logger.info("=== Evaluation Summary ===")
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            logger.info(f"{key}: {value:.4f}")
        else:
            logger.info(f"{key}: {value}")
    logger.info("=========================")

def main():
    """
    Main function to demonstrate the evaluation pipeline.
    """
    # This is a placeholder for CLI execution
    logger.info("Evaluation module ready. Use generate_significant_features_report() to create reports.")

if __name__ == "__main__":
    main()
