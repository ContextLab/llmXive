import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy.stats import pearsonr, ttest_ind
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Import existing utilities if available (fallback to local definition if not)
try:
    from utils import set_global_seed
except ImportError:
    def set_global_seed(seed: int = 42):
        np.random.seed(seed)
        import random
        random.seed(seed)

logger = logging.getLogger(__name__)

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        feature_names: List of feature names corresponding to columns in X
        
    Returns:
        DataFrame with feature names and VIF values
    """
    if X.shape[0] <= X.shape[1]:
        logger.warning("VIF calculation requires more samples than features. Returning NaNs.")
        return pd.DataFrame({"feature": feature_names, "VIF": [np.nan] * len(feature_names)})
    
    # Add intercept for statsmodels
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    vif_data = []
    
    for i in range(X.shape[1]):
        try:
            vif = variance_inflation_factor(X_with_intercept, i + 1)
            vif_data.append({"feature": feature_names[i], "VIF": vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature_names[i]}: {e}")
            vif_data.append({"feature": feature_names[i], "VIF": np.nan})
    
    return pd.DataFrame(vif_data)

def calculate_permutation_importance(
    X: np.ndarray, 
    y: np.ndarray, 
    model, 
    n_repeats: int = 10,
    scoring_metric: str = 'r2'
) -> Dict[str, float]:
    """
    Calculate permutation importance for features.
    
    Args:
        X: Feature matrix
        y: Target vector
        model: Trained model
        n_repeats: Number of times to shuffle each feature
        scoring_metric: Metric to use for evaluation ('r2' or 'neg_mean_squared_error')
        
    Returns:
        Dictionary mapping feature indices to importance scores
    """
    # Calculate baseline score
    baseline_score = model.score(X, y)
    
    importance_scores = {}
    
    for i in range(X.shape[1]):
        scores = []
        for _ in range(n_repeats):
            X_perm = X.copy()
            np.random.shuffle(X_perm[:, i])
            perm_score = model.score(X_perm, y)
            scores.append(baseline_score - perm_score)
        
        importance_scores[i] = np.mean(scores)
    
    return importance_scores

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of adjusted p-values
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []
    
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        adjusted_p_values[sorted_indices[i]] = min(
            (n / (i + 1)) * sorted_p_values[i],
            1.0
        )
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted_p_values[sorted_indices[i]] = min(
            adjusted_p_values[sorted_indices[i]],
            adjusted_p_values[sorted_indices[i + 1]]
        )
    
    return adjusted_p_values.tolist()

def run_median_split_sensitivity(
    X: np.ndarray, 
    y: np.ndarray, 
    feature_names: List[str],
    thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform median-split sensitivity analysis.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        thresholds: List of thresholds to use for splitting
        
    Returns:
        Dictionary with sensitivity analysis results
    """
    median = np.median(y)
    if thresholds is None:
        thresholds = [median - 0.1, median - 0.05, median, median + 0.05, median + 0.1]
    
    results = {
        "thresholds": [],
        "effect_sizes": [],
        "p_values": [],
        "high_pain_mean": [],
        "low_pain_mean": []
    }
    
    # Select top 5 features based on correlation with y for detailed analysis
    correlations = [np.corrcoef(X[:, i], y)[0, 1] for i in range(X.shape[1])]
    top_feature_indices = np.argsort(correlations)[-5:][::-1]
    top_features = [feature_names[i] for i in top_feature_indices]
    
    for threshold in thresholds:
        high_pain_mask = y < threshold
        low_pain_mask = y >= threshold
        
        if np.sum(high_pain_mask) < 5 or np.sum(low_pain_mask) < 5:
            logger.warning(f"Not enough samples for threshold {threshold}")
            continue
        
        results["thresholds"].append(threshold)
        
        # Analyze top features
        feature_results = {}
        for i, idx in enumerate(top_feature_indices):
            high_pain_vals = X[high_pain_mask, idx]
            low_pain_vals = X[low_pain_mask, idx]
            
            effect_size = (np.mean(high_pain_vals) - np.mean(low_pain_vals)) / np.std(np.concatenate([high_pain_vals, low_pain_vals]))
            _, p_val = ttest_ind(high_pain_vals, low_pain_vals)
            
            feature_results[feature_names[idx]] = {
                "effect_size": effect_size,
                "p_value": p_val,
                "high_pain_mean": np.mean(high_pain_vals),
                "low_pain_mean": np.mean(low_pain_vals)
            }
        
        results["effect_sizes"].append(feature_results)
    
    return results

def run_regularization_sensitivity(
    X: np.ndarray, 
    y: np.ndarray, 
    alpha_range: Tuple[float, float] = (0.0, 1.0), 
    step: float = 0.05,
    cv_folds: int = 5
) -> Dict[str, Any]:
    """
    Perform regularization sensitivity analysis by sweeping alpha values.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        alpha_range: Tuple of (min_alpha, max_alpha) for the sweep
        step: Step size for alpha values
        cv_folds: Number of folds for cross-validation
        
    Returns:
        Dictionary containing alpha values and corresponding R-squared stability metrics
    """
    logger.info("Starting regularization sensitivity analysis...")
    
    alphas = []
    r2_scores = []
    std_scores = []
    
    # Create alpha values
    current_alpha = alpha_range[0]
    while current_alpha <= alpha_range[1] + 1e-9:  # Small epsilon for float comparison
        if current_alpha == 0.0:  # Avoid exact 0 for ElasticNet
            current_alpha = 0.01
        alphas.append(current_alpha)
        current_alpha += step
    
    logger.info(f"Testing {len(alphas)} alpha values: {alphas}")
    
    # Prepare data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Cross-validation setup
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    for alpha in alphas:
        fold_scores = []
        for train_idx, test_idx in kf.split(X_scaled):
            X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            model = ElasticNet(alpha=alpha, l1_ratio=0.5, max_iter=5000, random_state=42)
            model.fit(X_train, y_train)
            
            r2 = model.score(X_test, y_test)
            fold_scores.append(r2)
        
        mean_r2 = np.mean(fold_scores)
        std_r2 = np.std(fold_scores)
        
        r2_scores.append(mean_r2)
        std_scores.append(std_r2)
        
        logger.info(f"Alpha={alpha:.2f}, Mean R²={mean_r2:.4f}, Std R²={std_r2:.4f}")
    
    results = {
        "alphas": alphas,
        "mean_r2_scores": r2_scores,
        "std_r2_scores": std_scores,
        "optimal_alpha": alphas[np.argmax(r2_scores)],
        "max_r2": max(r2_scores),
        "stability_range": max(r2_scores) - min(r2_scores)
    }
    
    logger.info(f"Regularization sensitivity analysis complete. Optimal alpha: {results['optimal_alpha']:.2f}")
    return results

def run_diagnostics_pipeline(
    X: np.ndarray, 
    y: np.ndarray, 
    feature_names: List[str],
    model=None,
    output_dir: str = "artifacts"
) -> Dict[str, Any]:
    """
    Run complete diagnostics pipeline including VIF, permutation importance, and sensitivity analyses.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        model: Optional pre-trained model
        output_dir: Directory to save results
        
    Returns:
        Dictionary with all diagnostic results
    """
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # VIF Analysis
    logger.info("Calculating VIF...")
    vif_results = calculate_vif(X, feature_names)
    high_vif = vif_results[vif_results['VIF'] > 10]
    results['vif'] = {
        'full': vif_results.to_dict('records'),
        'high_vif_features': high_vif['feature'].tolist(),
        'high_vif_values': high_vif.set_index('feature')['VIF'].to_dict()
    }
    logger.info(f"Found {len(high_vif)} features with VIF > 10")
    
    # Permutation Importance
    logger.info("Calculating permutation importance...")
    if model is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = ElasticNet(alpha=0.5, l1_ratio=0.5, max_iter=5000, random_state=42)
        model.fit(X_scaled, y)
    
    perm_importance = calculate_permutation_importance(X, y, model)
    results['permutation_importance'] = {
        'scores': perm_importance,
        'top_features': sorted(perm_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    }
    
    # Median Split Sensitivity
    logger.info("Running median split sensitivity analysis...")
    median_results = run_median_split_sensitivity(X, y, feature_names)
    results['median_split_sensitivity'] = median_results
    
    # Regularization Sensitivity
    logger.info("Running regularization sensitivity analysis...")
    reg_results = run_regularization_sensitivity(X, y)
    results['regularization_sensitivity'] = reg_results
    
    # Save results
    output_file = Path(output_dir) / "diagnostics_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Diagnostics results saved to {output_file}")
    
    return results

def main():
    """Main entry point for diagnostics module."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Diagnostics module loaded successfully.")
    
    # Example usage if run directly
    if __name__ == "__main__":
        logger.info("This module is intended to be imported and used by the main pipeline.")
        logger.info("Example: from diagnostics import run_diagnostics_pipeline")

if __name__ == "__main__":
    main()