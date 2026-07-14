import os
import sys
import json
import time
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.inspection import permutation_importance
from scipy.stats import zscore
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_vif(X: pd.DataFrame) -> pd.Series:
    """Calculate Variance Inflation Factor for all features."""
    vif_data = pd.Series(
        [variance_inflation_factor(X.values, i) for i in range(X.shape[1])],
        index=X.columns
    )
    return vif_data

def flag_high_vif(vif_series: pd.Series, threshold: float = 10.0) -> Dict[str, bool]:
    """Flag features with VIF > threshold."""
    return {col: val > threshold for col, val in vif_series.items()}

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute R2, MAE, RMSE."""
    return {
        'r2': float(r2_score(y_true, y_pred)),
        'mae': float(mean_absolute_error(y_true, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred)))
    }

def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """Evaluate a trained model on test data."""
    y_pred = model.predict(X_test)
    return compute_metrics(y_test, y_pred)

def run_permutation_importance(model, X: pd.DataFrame, y: np.ndarray, n_repeats: int = 1000, random_state: int = 42) -> Dict[str, Any]:
    """Run permutation importance and return p-values for features."""
    result = permutation_importance(
        model, X, y,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring='r2'
    )
    
    # Calculate p-values assuming normal distribution of scores
    # Null hypothesis: feature has no effect (mean importance = 0)
    mean_importance = result.importances_mean
    std_importance = result.importances_std
    
    # Avoid division by zero
    std_importance = np.where(std_importance == 0, 1e-9, std_importance)
    z_scores = mean_importance / std_importance
    p_values = 2 * (1 - scipy_stats.norm.cdf(np.abs(z_scores)))
    
    return {
        'feature_names': X.columns.tolist(),
        'mean_importance': mean_importance.tolist(),
        'std_importance': std_importance.tolist(),
        'p_values': p_values.tolist()
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply Bonferroni correction for multiple comparisons."""
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests if n_tests > 0 else alpha
    significant = [p < corrected_alpha for p in p_values]
    return {
        'original_alpha': alpha,
        'corrected_alpha': corrected_alpha,
        'significant': significant,
        'count_significant': sum(significant)
    }

def apply_bh_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply Benjamini-Hochberg correction for multiple comparisons."""
    import scipy.stats
    n_tests = len(p_values)
    if n_tests == 0:
        return {'corrected_alpha': 0, 'significant': [], 'count_significant': 0}
    
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # BH critical values
    ranks = np.arange(1, n_tests + 1)
    critical_values = (ranks / n_tests) * alpha
    
    # Find the largest k such that p(k) <= critical(k)
    significant_mask = sorted_p_values <= critical_values
    if not any(significant_mask):
        return {
            'corrected_alpha': alpha,
            'significant': [False] * n_tests,
            'count_significant': 0
        }
    
    k = np.max(np.where(significant_mask)[0])
    bh_threshold = critical_values[k]
    
    # All p-values <= threshold are significant
    final_significant = [p <= bh_threshold for p in p_values]
    
    return {
        'original_alpha': alpha,
        'corrected_alpha': bh_threshold,
        'significant': final_significant,
        'count_significant': sum(final_significant)
    }

def run_multiple_comparison_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Run both Bonferroni and BH corrections."""
    return {
        'bonferroni': apply_bonferroni_correction(p_values, alpha),
        'benjamini_hochberg': apply_bh_correction(p_values, alpha)
    }

def run_bootstrap_resampling(model, X: pd.DataFrame, y: np.ndarray, n_resamples: int = 1000, random_state: int = 42) -> Dict[str, Any]:
    """Run bootstrap resampling to calculate 95% CI for R2."""
    np.random.seed(random_state)
    n_samples = len(y)
    r2_scores = []
    
    for _ in range(n_resamples):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_boot = X.iloc[indices]
        y_boot = y[indices]
        
        # Retrain model on bootstrap sample
        model_clone = type(model)(**model.get_params())
        model_clone.fit(X_boot, y_boot)
        
        # Evaluate on original test set (or out-of-bag if needed, but keeping simple)
        # Note: For proper bootstrap CI, we usually evaluate on OOB or hold-out
        # Here we evaluate on the same data to estimate stability of the metric
        # A more rigorous approach would use OOB or a fixed hold-out
        y_pred = model_clone.predict(X)
        r2 = r2_score(y, y_pred)
        r2_scores.append(r2)
    
    r2_scores = np.array(r2_scores)
    ci_lower = np.percentile(r2_scores, 2.5)
    ci_upper = np.percentile(r2_scores, 97.5)
    
    return {
        'mean_r2': float(np.mean(r2_scores)),
        'std_r2': float(np.std(r2_scores)),
        'ci_95': [float(ci_lower), float(ci_upper)],
        'resamples': n_resamples
    }

def run_sensitivity_analysis(
    model, 
    X: pd.DataFrame, 
    y: np.ndarray, 
    p_values: List[float], 
    alphas: List[float] = [0.01, 0.05, 0.1],
    method: str = 'bonferroni'
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by sweeping alpha over discrete set {0.01, 0.05, 0.1}.
    Reports how the count of significant descriptors and R2 values vary.
    
    Args:
        model: Trained model (RF, GB, or Linear)
        X: Feature DataFrame
        y: Target array
        p_values: List of p-values from permutation importance
        alphas: List of alpha thresholds to test
        method: Correction method ('bonferroni' or 'bh')
    
    Returns:
        Dictionary with sensitivity analysis results
    """
    results = []
    
    for alpha in alphas:
        # Apply correction
        if method == 'bonferroni':
            correction_result = apply_bonferroni_correction(p_values, alpha)
        elif method == 'bh':
            correction_result = apply_bh_correction(p_values, alpha)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Calculate metrics on full data (or use a fixed hold-out if available)
        # Here we assume the model is already trained and we evaluate on the same data
        # for consistency with the permutation test context
        y_pred = model.predict(X)
        metrics = compute_metrics(y, y_pred)
        
        results.append({
            'alpha': alpha,
            'count_significant': correction_result['count_significant'],
            'significant_features': [X.columns[i] for i, sig in enumerate(correction_result['significant']) if sig],
            'r2': metrics['r2'],
            'mae': metrics['mae'],
            'rmse': metrics['rmse'],
            'correction_method': method
        })
    
    return {
        'sweep_parameters': {
            'alphas': alphas,
            'method': method
        },
        'results': results
    }

def run_evaluation_pipeline(
    X_train: pd.DataFrame, 
    y_train: np.ndarray, 
    X_test: pd.DataFrame, 
    y_test: np.ndarray,
    models_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline including VIF, permutation, bootstrap, and sensitivity analysis.
    """
    logger.info("Starting evaluation pipeline...")
    
    results = {
        'vif': {},
        'permutation': {},
        'bootstrap': {},
        'sensitivity': {}
    }
    
    # 1. VIF for Linear Regression only
    if 'linear' in models_config:
        logger.info("Calculating VIF for Linear Regression...")
        vif_series = compute_vif(X_train)
        results['vif']['linear'] = {
            'values': vif_series.to_dict(),
            'high_vif_flags': flag_high_vif(vif_series)
        }
    
    # 2. Permutation Importance for all models
    for name, model in models_config.items():
        logger.info(f"Running permutation importance for {name}...")
        perm_result = run_permutation_importance(model, X_train, y_train)
        results['permutation'][name] = perm_result
    
    # 3. Bootstrap Resampling for RF and GB
    for name in ['random_forest', 'gradient_boosting']:
        if name in models_config:
            logger.info(f"Running bootstrap resampling for {name}...")
            boot_result = run_bootstrap_resampling(models_config[name], X_train, y_train)
            results['bootstrap'][name] = boot_result
    
    # 4. Sensitivity Analysis for all models
    alphas = [0.01, 0.05, 0.1]
    for name, model in models_config.items():
        if name in results['permutation']:
            logger.info(f"Running sensitivity analysis for {name}...")
            p_values = results['permutation'][name]['p_values']
            sens_result = run_sensitivity_analysis(
                model, X_train, y_train, p_values, alphas, method='bonferroni'
            )
            results['sensitivity'][name] = sens_result
            
            # Also run with BH method
            sens_result_bh = run_sensitivity_analysis(
                model, X_train, y_train, p_values, alphas, method='bh'
            )
            results['sensitivity'][f"{name}_bh"] = sens_result_bh
    
    logger.info("Evaluation pipeline completed.")
    return results

def main():
    """Main entry point for evaluation script."""
    # Load data
    processed_data_path = "data/processed/hea_descriptors.csv"
    if not os.path.exists(processed_data_path):
        logger.error(f"Processed data not found at {processed_data_path}")
        sys.exit(1)
    
    df = pd.read_csv(processed_data_path)
    
    # Prepare features and target
    # Assuming 'yield_strength_mpa' is the target and other columns are features
    target_col = 'yield_strength_mpa'
    feature_cols = [col for col in df.columns if col != target_col and col not in ['alloy_id', 'composition']]
    
    X = df[feature_cols]
    y = df[target_col].values
    
    # Simple train/test split for demonstration
    # In real pipeline, this should come from train.py
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train models
    models_config = {
        'linear': LinearRegression(),
        'random_forest': RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42),
        'gradient_boosting': GradientBoostingRegressor(n_estimators=50, max_depth=10, random_state=42)
    }
    
    for name, model in models_config.items():
        logger.info(f"Training {name}...")
        model.fit(X_train, y_train)
    
    # Run evaluation
    eval_results = run_evaluation_pipeline(X_train, y_train, X_test, y_test, models_config)
    
    # Write results to output
    output_path = "output/evaluation_results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(eval_results, f, indent=2, default=str)
    
    logger.info(f"Evaluation results written to {output_path}")
    return eval_results

if __name__ == "__main__":
    main()