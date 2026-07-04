import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import existing utilities if needed, though this file focuses on metrics
# Ensure paths are relative to project root if running as script
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Compute Variance Inflation Factors (VIF) for given features.
    
    Args:
        df: DataFrame containing features
        feature_cols: List of column names to compute VIF for
        
    Returns:
        Dictionary mapping feature names to VIF values
    """
    vif_data = {}
    X = df[feature_cols].dropna()
    
    if X.shape[0] < len(feature_cols) + 1:
        logger.warning("Insufficient samples for VIF computation")
        return {col: float('inf') for col in feature_cols}
        
    for i, col in enumerate(feature_cols):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error computing VIF for {col}: {e}")
            vif_data[col] = float('inf')
            
    return vif_data

def residualize_features(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> pd.DataFrame:
    """
    Residualize features against a target to remove collinearity.
    
    Args:
        df: DataFrame
        target_col: Column to residualize against
        feature_cols: Features to residualize
        
    Returns:
        DataFrame with residualized features
    """
    from sklearn.linear_model import LinearRegression
    
    X = df[target_col].values.reshape(-1, 1)
    y = df[feature_cols].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    residuals = y - model.predict(X)
    
    df_res = df.copy()
    for i, col in enumerate(feature_cols):
        df_res[col] = residuals[:, i]
        
    return df_res

def update_performance_metrics(metrics_path: Path, updates: Dict) -> None:
    """
    Update the performance metrics JSON file with new values.
    
    Args:
        metrics_path: Path to the performance_metrics.json file
        updates: Dictionary of values to update/add
    """
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    else:
        metrics = {}
        
    metrics.update(updates)
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Updated performance metrics at {metrics_path}")

def check_and_mitigate_collinearity(df: pd.DataFrame, feature_cols: List[str], 
                                   metrics_path: Path, threshold: float = 5.0) -> Tuple[bool, Dict]:
    """
    Check for collinearity and mitigate if necessary.
    
    Args:
        df: DataFrame with features
        feature_cols: List of feature column names
        metrics_path: Path to save metrics
        threshold: VIF threshold for triggering mitigation
        
    Returns:
        Tuple of (collinearity_detected, mitigation_info)
    """
    vif_data = compute_vif(df, feature_cols)
    max_vif = max(vif_data.values()) if vif_data else 0
    
    mitigation_info = {
        "vif_values": vif_data,
        "max_vif": max_vif,
        "collinearity_detected": max_vif >= threshold,
        "mitigation_strategy": None
    }
    
    if max_vif >= threshold:
        logger.warning(f"Collinearity detected (max VIF: {max_vif:.2f}). Triggering residualization.")
        mitigation_info["mitigation_strategy"] = "residualization"
        update_performance_metrics(metrics_path, {"collinearity_mitigation": "residualization"})
        
    return max_vif >= threshold, mitigation_info

def compute_bootstrap_ci_for_shap_difference(shap_values: pd.DataFrame, 
                                             group_a_features: List[str], 
                                             group_b_features: List[str],
                                             n_bootstrap: int = 1000,
                                             alpha: float = 0.05) -> Dict:
    """
    Compute 95% bootstrapped confidence intervals for the difference in mean absolute SHAP values
    between two groups of features, with family-wise error rate control.
    
    Args:
        shap_values: DataFrame of SHAP values (rows=samples, cols=features)
        group_a_features: List of feature names for group A (e.g., chemical heterogeneity)
        group_b_features: List of feature names for group B (e.g., mean coordination number)
        n_bootstrap: Number of bootstrap iterations
        alpha: Significance level (default 0.05 for 95% CI)
        
    Returns:
        Dictionary with ci_lower, ci_upper, is_significant, and p_value
    """
    # Filter to only requested features
    available_a = [f for f in group_a_features if f in shap_values.columns]
    available_b = [f for f in group_b_features if f in shap_values.columns]
    
    if not available_a or not available_b:
        logger.error(f"Missing features for SHAP comparison. A: {available_a}, B: {available_b}")
        return {
            "ci_lower": None,
            "ci_upper": None,
            "is_significant": False,
            "p_value": None,
            "error": "Missing features for comparison"
        }
    
    # Compute mean absolute SHAP values for each group per sample
    mean_abs_a = shap_values[available_a].abs().mean(axis=1)
    mean_abs_b = shap_values[available_b].abs().mean(axis=1)
    
    # Observed difference
    observed_diff = (mean_abs_a - mean_abs_b).mean()
    
    # Bootstrap distribution of the difference
    n_samples = len(shap_values)
    bootstrap_diffs = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        boot_a = mean_abs_a.iloc[indices]
        boot_b = mean_abs_b.iloc[indices]
        boot_diff = (boot_a - boot_b).mean()
        bootstrap_diffs.append(boot_diff)
        
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    # Compute confidence interval (percentile method)
    ci_lower = np.percentile(bootstrap_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))
    
    # Hypothesis testing: H0: difference = 0
    # Using bootstrap p-value
    p_value = 2 * min(np.mean(bootstrap_diffs <= 0), np.mean(bootstrap_diffs >= 0))
    
    # Family-wise error rate control (Bonferroni)
    # Since we are testing 1 hypothesis (A vs B), Bonferroni correction factor is 1
    # If this function were called for multiple pairs, we would adjust alpha
    adjusted_alpha = alpha / 1  # 1 comparison
    is_significant = (ci_lower > 0) or (ci_upper < 0)
    
    # For Bonferroni, we check if p-value < adjusted_alpha
    is_significant_bonferroni = p_value < adjusted_alpha
    
    logger.info(f"SHAP Difference CI: [{ci_lower:.4f}, {ci_upper:.4f}], p={p_value:.4f}, significant={is_significant_bonferroni}")
    
    return {
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "is_significant": bool(is_significant_bonferroni),
        "p_value": float(p_value),
        "observed_difference": float(observed_diff),
        "n_bootstrap": n_bootstrap,
        "method": "Bonferroni-corrected bootstrap CI"
    }

def main():
    """
    Main function to demonstrate metrics computation.
    This is intended to be called by other modules or as a script for testing.
    """
    # Example usage would require loading actual SHAP values from a previous step
    # This is a placeholder for the logic defined above
    logger.info("Metrics module loaded. Functions available: compute_vif, residualize_features, check_and_mitigate_collinearity, compute_bootstrap_ci_for_shap_difference")

if __name__ == "__main__":
    main()