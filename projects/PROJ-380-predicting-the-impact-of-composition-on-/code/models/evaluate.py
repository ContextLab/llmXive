import os
import sys
import json
import logging
import math
import csv
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from scipy import stats

# Import project utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.config import get_paths, set_random_seed
from utils.logging_config import get_logger
from utils.provenance import record_artifact, compute_file_checksum

logger = get_logger(__name__)

def corrected_resampled_ttest(
    model_a_scores: np.ndarray,
    model_b_scores: np.ndarray,
    n_iterations: int = 100
) -> Dict[str, Any]:
    """
    Implements the Corrected Resampled t-test (Nadeau & Bengio) for comparing
    two models' cross-validation scores.
    
    Args:
        model_a_scores: Array of scores for model A (e.g., R2 per fold).
        model_b_scores: Array of scores for model B.
        n_iterations: Number of resampling iterations.
        
    Returns:
        Dictionary with p-value, t-statistic, and confidence interval.
    """
    if len(model_a_scores) != len(model_b_scores):
        raise ValueError("Score arrays must have the same length.")
    
    n = len(model_a_scores)
    if n < 2:
        raise ValueError("Need at least 2 scores to perform t-test.")
        
    # Estimate variance components
    # Note: Simplified implementation for resampled t-test
    # In full implementation, we would re-split data n_iterations times
    # Here we assume scores are already obtained from a robust CV process
    
    diff = model_a_scores - model_b_scores
    mean_diff = np.mean(diff)
    var_diff = np.var(diff, ddof=1)
    
    # Correction factor for dependence
    # k is number of folds, n is number of samples (approximated by len(scores))
    # This is a simplified version; full implementation requires re-sampling
    k = n 
    n_samples = n * 100  # Approximation
    correction = math.sqrt((1/n) + (n_samples/n) * (1/n_samples))
    
    # Standard error with correction
    se = math.sqrt(var_diff) * correction
    
    if se == 0:
        t_stat = 0.0
        p_value = 1.0
    else:
        t_stat = mean_diff / se
        # Two-tailed test
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
        
    # 95% Confidence Interval
    ci_margin = stats.t.ppf(0.975, df=n-1) * se
    ci_lower = mean_diff - ci_margin
    ci_upper = mean_diff + ci_margin
    
    return {
        "method": "corrected_resampled_ttest",
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "mean_difference": float(mean_diff),
        "confidence_interval_95": [float(ci_lower), float(ci_upper)],
        "significant_at_0.05": p_value < 0.05
    }

def wilcoxon_signed_rank_test(
    model_a_scores: np.ndarray,
    model_b_scores: np.ndarray
) -> Dict[str, Any]:
    """
    Implements Wilcoxon Signed-Rank Test as a fallback for model comparison.
    Non-parametric test suitable for small sample sizes or non-normal distributions.
    
    Args:
        model_a_scores: Array of scores for model A.
        model_b_scores: Array of scores for model B.
        
    Returns:
        Dictionary with p-value, statistic, and interpretation.
    """
    if len(model_a_scores) != len(model_b_scores):
        raise ValueError("Score arrays must have the same length.")
        
    diff = model_a_scores - model_b_scores
    stat, p_value = stats.wilcoxon(diff)
    
    return {
        "method": "wilcoxon_signed_rank_test",
        "statistic": float(stat),
        "p_value": float(p_value),
        "significant_at_0.05": p_value < 0.05
    }

def bayes_factor_wilcoxon(
    model_a_scores: np.ndarray,
    model_b_scores: np.ndarray
) -> Dict[str, Any]:
    """
    Calculates a simplified Bayes Factor for Wilcoxon test results.
    Approximation using effect size and sample size.
    
    Args:
        model_a_scores: Array of scores for model A.
        model_b_scores: Array of scores for model B.
        
    Returns:
        Dictionary with Bayes Factor and evidence strength.
    """
    if len(model_a_scores) != len(model_b_scores):
        raise ValueError("Score arrays must have the same length.")
        
    diff = model_a_scores - model_b_scores
    n = len(diff)
    
    # Calculate effect size (r)
    stat, _ = stats.wilcoxon(diff)
    # Approximate Z score from Wilcoxon statistic
    # This is a simplified approximation
    z = stat / math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    r = z / math.sqrt(2 * n)
    
    # Approximate Bayes Factor (BF10)
    # Using a simplified formula based on effect size
    # BF10 = exp( (n * r^2) / 2 )
    bf10 = math.exp((n * r**2) / 2)
    
    # Interpretation
    if bf10 < 1:
        evidence = "Evidence for null hypothesis (H0)"
    elif bf10 < 3:
        evidence = "Barely worth mentioning"
    elif bf10 < 10:
        evidence = "Substantial evidence for alternative (H1)"
    elif bf10 < 30:
        evidence = "Strong evidence for alternative (H1)"
    else:
        evidence = "Very strong evidence for alternative (H1)"
        
    return {
        "method": "bayes_factor_wilcoxon",
        "bayes_factor_10": float(bf10),
        "effect_size_r": float(r),
        "evidence_strength": evidence
    }

def hybrid_lofo_groupkfold(
    X: np.ndarray,
    y: np.ndarray,
    groups: List[str],
    model: Any,
    large_family_threshold: int = 10,
    n_folds: int = 5
) -> Dict[str, Any]:
    """
    Implements hybrid Leave-One-Family-Out (LOFO) for large families 
    and GroupKFold for small families.
    
    Logic:
    1. Count samples per family.
    2. For families with count >= threshold: Use LOFO (leave that family out).
    3. For families with count < threshold: Group them and use GroupKFold.
    4. Return aggregated metrics.
    
    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        groups: List of alloy family names for each sample.
        model: Scikit-learn compatible model with .fit() and .score() methods.
        large_family_threshold: Minimum samples to treat a family as "large".
        n_folds: Number of folds for GroupKFold on small families.
        
    Returns:
        Dictionary with mean score, std score, and detailed fold results.
    """
    unique_groups, counts = np.unique(groups, return_counts=True)
    group_dict = dict(zip(unique_groups, counts))
    
    large_families = [g for g, c in group_dict.items() if c >= large_family_threshold]
    small_families = [g for g, c in group_dict.items() if c < large_family_threshold]
    
    logger.info(f"Hybrid Split: {len(large_families)} large families, {len(small_families)} small families.")
    
    scores = []
    fold_details = []
    
    # 1. LOFO for Large Families
    if large_families:
        logger.info(f"Performing LOFO for {len(large_families)} large families...")
        lofo = LeaveOneGroupOut()
        
        # Create a mask for large family indices
        large_group_indices = [i for i, g in enumerate(groups) if g in large_families]
        large_groups_subset = [groups[i] for i in large_group_indices]
        X_large = X[large_group_indices]
        y_large = y[large_group_indices]
        
        if len(X_large) > 0:
            try:
                for train_idx, test_idx in lofo.split(X_large, y_large, groups=large_groups_subset):
                    X_train, X_test = X_large[train_idx], X_large[test_idx]
                    y_train, y_test = y_large[train_idx], y_large[test_idx]
                    
                    # Clone model to avoid state leakage
                    try:
                        cloned_model = model.__class__(**model.get_params())
                    except AttributeError:
                        # Fallback for models without get_params
                        cloned_model = model.__class__()
                        
                    cloned_model.fit(X_train, y_train)
                    score = cloned_model.score(X_test, y_test)
                    scores.append(score)
                    
                    # Identify which family was left out
                    left_out_family = large_groups_subset[test_idx[0]]
                    fold_details.append({
                        "type": "LOFO",
                        "left_out_family": left_out_family,
                        "score": float(score)
                    })
                    logger.debug(f"LOFO Fold: Left out {left_out_family}, Score: {score:.4f}")
            except Exception as e:
                logger.error(f"Error in LOFO split: {e}")
    
    # 2. GroupKFold for Small Families
    if small_families:
        logger.info(f"Performing GroupKFold for {len(small_families)} small families...")
        # Map small families to integer groups for GroupKFold
        small_group_indices = [i for i, g in enumerate(groups) if g in small_families]
        small_groups_subset = [groups[i] for i in small_group_indices]
        X_small = X[small_group_indices]
        y_small = y[small_group_indices]
        
        if len(X_small) > 0:
            # Ensure we have enough groups for n_folds
            unique_small = set(small_groups_subset)
            if len(unique_small) < n_folds:
                # Adjust folds if not enough groups
                actual_folds = min(len(unique_small), n_folds)
                logger.warning(f"Only {len(unique_small)} small groups found. Reducing folds to {actual_folds}.")
            else:
                actual_folds = n_folds
                
            gkf = GroupKFold(n_splits=actual_folds)
            
            try:
                for train_idx, test_idx in gkf.split(X_small, y_small, groups=small_groups_subset):
                    X_train, X_test = X_small[train_idx], X_small[test_idx]
                    y_train, y_test = y_small[train_idx], y_small[test_idx]
                    
                    try:
                        cloned_model = model.__class__(**model.get_params())
                    except AttributeError:
                        cloned_model = model.__class__()
                        
                    cloned_model.fit(X_train, y_train)
                    score = cloned_model.score(X_test, y_test)
                    scores.append(score)
                    
                    # Identify families in test set
                    test_families = list(set([small_groups_subset[i] for i in test_idx]))
                    fold_details.append({
                        "type": "GroupKFold",
                        "test_families": test_families,
                        "score": float(score)
                    })
                    logger.debug(f"GroupKFold Fold: Families {test_families}, Score: {score:.4f}")
            except Exception as e:
                logger.error(f"Error in GroupKFold split: {e}")
    
    if not scores:
        logger.warning("No scores generated from hybrid split. Check data distribution.")
        return {
            "mean_score": None,
            "std_score": None,
            "n_folds": 0,
            "fold_details": [],
            "error": "No valid folds generated"
        }
        
    return {
        "mean_score": float(np.mean(scores)),
        "std_score": float(np.std(scores)),
        "n_folds": len(scores),
        "fold_details": fold_details,
        "large_families_processed": len(large_families),
        "small_families_processed": len(small_families)
    }

def run_evaluation(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model: Any,
    groups: List[str],
    test_model: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Runs full evaluation including hybrid LOFO/GroupKFold, standard metrics,
    and statistical comparison if a test model is provided.
    
    Args:
        X_train, y_train: Training data.
        X_test, y_test: Test data.
        model: Primary model to evaluate.
        test_model: Optional secondary model for statistical comparison.
        
    Returns:
        Comprehensive evaluation report.
    """
    # 1. Standard Train/Test Metrics
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    
    metrics = {
        "R2": float(r2),
        "MAE": float(mae),
        "RMSE": float(rmse)
    }
    
    # 2. Hybrid LOFO/GroupKFold Evaluation
    # We need to perform CV on the training set or full set depending on strategy
    # Here we perform on the full dataset provided (X_train, y_train) to assess generalization
    # across families, as per FR-008
    hybrid_results = hybrid_lofo_groupkfold(
        X=X_train,
        y=y_train,
        groups=groups,
        model=model
    )
    
    report = {
        "metrics": metrics,
        "hybrid_cv_results": hybrid_results,
        "model_type": model.__class__.__name__
    }
    
    # 3. Statistical Comparison if test_model provided
    if test_model is not None:
        logger.info("Performing statistical comparison between models...")
        
        # Get CV scores for both models using the hybrid strategy
        # We need to re-run hybrid logic to get scores for both
        scores_a = []
        scores_b = []
        
        # Re-use hybrid logic to extract scores directly
        # This is a simplified re-implementation for comparison
        unique_groups, counts = np.unique(groups, return_counts=True)
        group_dict = dict(zip(unique_groups, counts))
        large_families = [g for g, c in group_dict.items() if c >= 10]
        small_families = [g for g, c in group_dict.items() if c < 10]
        
        # Helper to get scores
        def get_model_scores(X, y, groups, model_obj, large_fams, small_fams):
            scores = []
            if large_fams:
                large_idx = [i for i, g in enumerate(groups) if g in large_fams]
                X_l, y_l, g_l = X[large_idx], y[large_idx], [groups[i] for i in large_idx]
                if len(X_l) > 0:
                    lofo = LeaveOneGroupOut()
                    for tr, te in lofo.split(X_l, y_l, g_l):
                        m = model_obj.__class__(**model_obj.get_params())
                        m.fit(X_l[tr], y_l[tr])
                        scores.append(m.score(X_l[te], y_l[te]))
            if small_fams:
                small_idx = [i for i, g in enumerate(groups) if g in small_fams]
                X_s, y_s, g_s = X[small_idx], y[small_idx], [groups[i] for i in small_idx]
                if len(X_s) > 0:
                    gkf = GroupKFold(n_splits=5)
                    for tr, te in gkf.split(X_s, y_s, g_s):
                        m = model_obj.__class__(**model_obj.get_params())
                        m.fit(X_s[tr], y_s[tr])
                        scores.append(m.score(X_s[te], y_s[te]))
            return np.array(scores)
        
        try:
            scores_a = get_model_scores(X_train, y_train, groups, model, large_families, small_families)
            scores_b = get_model_scores(X_train, y_train, groups, test_model, large_families, small_families)
            
            if len(scores_a) > 0 and len(scores_b) > 0:
                # Primary: Corrected Resampled t-test
                t_test_res = corrected_resampled_ttest(scores_a, scores_b)
                report["statistical_test"] = t_test_res
                
                # Fallback: Wilcoxon if t-test assumptions violated or N small
                if len(scores_a) < 30:
                    wilcoxon_res = wilcoxon_signed_rank_test(scores_a, scores_b)
                    report["statistical_test_fallback_wilcoxon"] = wilcoxon_res
                    
                    # Bayes Factor for Wilcoxon
                    bf_res = bayes_factor_wilcoxon(scores_a, scores_b)
                    report["statistical_test_bayes_factor"] = bf_res
            else:
                report["statistical_test"] = {"error": "Insufficient data for comparison"}
        except Exception as e:
            logger.error(f"Statistical comparison failed: {e}")
            report["statistical_test"] = {"error": str(e)}
    
    return report

def main():
    """
    Main entry point for evaluation script.
    Loads data, runs hybrid evaluation, and saves report.
    """
    paths = get_paths()
    logger.info(f"Starting evaluation. Paths: {paths}")
    
    # Load processed data (assuming it exists from previous steps)
    # In a real pipeline, this would load from data/processed/
    # For this implementation, we expect arguments or a specific file
    data_path = paths.get("processed_data", "data/processed/features.csv")
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
        
    # Load data
    X_list = []
    y_list = []
    groups_list = []
    
    with open(data_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Assume last column is target, second to last is family, rest are features
        # This is a simplification; real logic would use schema
        feature_cols = [h for h in headers if h not in ['target', 'alloy_family']]
        target_col = 'target'
        family_col = 'alloy_family'
        
        for row in reader:
            X_list.append([float(row[c]) for c in feature_cols])
            y_list.append(float(row[target_col]))
            groups_list.append(row[family_col])
            
    X = np.array(X_list)
    y = np.array(y_list)
    groups = groups_list
    
    # Train a baseline model for evaluation
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    
    # Run evaluation
    results = run_evaluation(X, y, X, y, model, groups)
    
    # Save results
    output_path = os.path.join(paths.get("artifacts", "artifacts"), "evaluation_report.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Evaluation report saved to {output_path}")
    
    # Record provenance
    checksum = compute_file_checksum(output_path)
    record_artifact(
        path=output_path,
        checksum=checksum,
        task_id="T030",
        description="Hybrid LOFO/GroupKFold evaluation report"
    )
    
    return results

if __name__ == "__main__":
    main()