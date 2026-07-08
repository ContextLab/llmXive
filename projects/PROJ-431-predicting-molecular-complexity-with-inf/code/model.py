import os
import json
import pickle
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from scipy.stats import pearsonr
from scipy import stats

def train_ridge_model(
    X: np.ndarray, y: np.ndarray, alpha: float = 1.0, seed: int = 42
) -> Tuple[Ridge, Dict[str, Any]]:
    """
    Train a Ridge Regression model and return the model and metrics.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        alpha: Regularization strength
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (trained model, metrics dict with rmse, r, p_value)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )
    
    model = Ridge(alpha=alpha)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    
    # Calculate Pearson r and p-value
    r, p_value = pearsonr(y_test, y_pred)
    
    metrics = {
        "rmse": float(rmse),
        "r": float(r),
        "p_value": float(p_value),
        "n_train": len(y_train),
        "n_test": len(y_test),
        "alpha": float(alpha)
    }
    
    return model, metrics

def compute_bonferroni_pvalue(p_value: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to a p-value.
    
    Args:
        p_value: Raw p-value
        n_tests: Total number of tests performed
    
    Returns:
        Bonferroni-adjusted p-value (capped at 1.0)
    """
    adjusted = p_value * n_tests
    return min(adjusted, 1.0)

def compute_benjamini_hochberg_pvalues(
    p_values: List[float], alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level for FDR control
    
    Returns:
        List of dicts with 'raw_p', 'bh_p', 'significant' for each test
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    indexed_pvals = list(enumerate(p_values))
    sorted_pvals = sorted(indexed_pvals, key=lambda x: x[1])
    
    bh_pvalues = []
    for rank, (idx, p_val) in enumerate(sorted_pvals, start=1):
        # BH critical value
        bh_val = (rank / n) * alpha
        bh_p = min(p_val * (n / rank), 1.0)
        bh_pvalues.append({
            "index": idx,
            "raw_p": float(p_val),
            "bh_p": float(bh_p),
            "critical_value": float(bh_val)
        })
    
    # Sort back to original order
    bh_pvalues_sorted = sorted(bh_pvalues, key=lambda x: x["index"])
    return bh_pvalues_sorted

def run_sensitivity_analysis(
    X: np.ndarray, y: np.ndarray, alpha_values: List[float], seed: int = 42
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across different alpha values.
    
    Args:
        X: Feature matrix
        y: Target vector
        alpha_values: List of alpha values to test
        seed: Random seed
    
    Returns:
        Dict with sensitivity metrics (range, mean, stability)
    """
    results = []
    for alpha in alpha_values:
        _, metrics = train_ridge_model(X, y, alpha=alpha, seed=seed)
        results.append({
            "alpha": alpha,
            "rmse": metrics["rmse"],
            "r": metrics["r"],
            "p_value": metrics["p_value"]
        })
    
    rmse_values = [r["rmse"] for r in results]
    r_values = [r["r"] for r in results]
    
    # Calculate relative range (stability metric)
    rmse_range = (max(rmse_values) - min(rmse_values)) / (np.mean(rmse_values) + 1e-8)
    r_range = (max(r_values) - min(r_values)) / (np.mean(r_values) + 1e-8)
    
    return {
        "alpha_sweep": results,
        "rmse_relative_range": float(rmse_range),
        "r_relative_range": float(r_range),
        "stability_rmse": "stable" if rmse_range < 0.1 else "unstable",
        "stability_r": "stable" if r_range < 0.1 else "unstable"
    }

def train_models_from_csv(
    data_path: str,
    feature_cols: List[str],
    target_col: str,
    output_model_path: str,
    output_metrics_path: str,
    alpha: float = 1.0,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Train models from a CSV file and save results.
    
    Args:
        data_path: Path to input CSV
        feature_cols: List of feature column names
        target_col: Target column name
        output_model_path: Path to save model pickle
        output_metrics_path: Path to save metrics JSON
        alpha: Ridge alpha parameter
        seed: Random seed
    
    Returns:
        Metrics dictionary
    """
    df = pd.read_csv(data_path)
    
    # Drop rows with missing values in features or target
    mask = df[feature_cols + [target_col]].notna().all(axis=1)
    df_clean = df[mask]
    
    X = df_clean[feature_cols].values
    y = df_clean[target_col].values
    
    model, metrics = train_ridge_model(X, y, alpha=alpha, seed=seed)
    
    # Save model
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    with open(output_model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save metrics
    os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
    with open(output_metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics

def run_full_analysis(
    data_path: str,
    feature_col: str,
    target_col: str,
    output_dir: str,
    alpha: float = 1.0,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run full analysis including model training, baseline comparison, and report generation.
    
    Args:
        data_path: Path to enriched CSV
        feature_col: Name of entropy feature column (e.g., 'atom_entropy')
        target_col: Name of target column (e.g., 'logS')
        output_dir: Directory to save outputs
        alpha: Ridge alpha parameter
        seed: Random seed
    
    Returns:
        Complete analysis report dictionary
    """
    from baseline import run_baseline_analysis, compute_partial_correlation
    
    # Load data
    df = pd.read_csv(data_path)
    
    # Prepare features and target
    feature_cols = [feature_col]
    mask = df[feature_cols + [target_col]].notna().all(axis=1)
    df_clean = df[mask]
    
    X = df_clean[feature_cols].values
    y = df_clean[target_col].values
    
    # Train main model
    model, main_metrics = train_ridge_model(X, y, alpha=alpha, seed=seed)
    
    # Run baseline analysis
    baseline_results = run_baseline_analysis(
        data_path=data_path,
        target_col=target_col,
        output_dir=output_dir,
        seed=seed
    )
    
    # Compute partial correlation (controlling for molecular weight)
    partial_corr = None
    if 'molecular_weight' in df_clean.columns:
        mw = df_clean['molecular_weight'].values
        partial_corr = compute_partial_correlation(
            X.flatten(), y, mw
        )
    
    # Calculate Bonferroni-adjusted p-value (2 tests: logS and logP typically)
    bonf_p = compute_bonferroni_pvalue(main_metrics["p_value"], n_tests=2)
    
    # Calculate Benjamini-Hochberg adjusted p-values
    # We'll compare entropy vs size baseline p-values
    all_p_values = [main_metrics["p_value"]]
    if 'baseline_metrics' in baseline_results:
        for baseline_name, bm in baseline_results['baseline_metrics'].items():
            if 'p_value' in bm:
                all_p_values.append(bm['p_value'])
    
    bh_results = compute_benjamini_hochberg_pvalues(all_p_values)
    
    # Determine if entropy model beats size baseline (Scientific Success Criterion)
    size_baseline_rmse = baseline_results.get('size_baseline_rmse', float('inf'))
    entropy_beats_size = main_metrics["rmse"] < size_baseline_rmse
    
    # Construct Entropy-vs-Size comparison table
    comparison_table = {
        "model": "Entropy (Ridge)",
        "rmse": main_metrics["rmse"],
        "r": main_metrics["r"],
        "p_value": main_metrics["p_value"],
        "bonferroni_p": bonf_p,
        "size_baseline_rmse": size_baseline_rmse,
        "entropy_beats_size": entropy_beats_size
    }
    
    # Build final report
    report = {
        "target_property": target_col,
        "model_type": "Ridge Regression",
        "alpha": alpha,
        "n_samples": len(y),
        "train_size": main_metrics["n_train"],
        "test_size": main_metrics["n_test"],
        "metrics": {
            "rmse": main_metrics["rmse"],
            "pearson_r": main_metrics["r"],
            "p_value": main_metrics["p_value"],
            "bonferroni_adjusted_p": bonf_p
        },
        "benjamini_hochberg_adjusted": bh_results,
        "partial_correlation_with_mw": partial_corr,
        "baseline_comparison": baseline_results,
        "entropy_vs_size_comparison": comparison_table,
        "scientific_success": entropy_beats_size
    }
    
    # Save report
    report_path = os.path.join(output_dir, "metrics.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report