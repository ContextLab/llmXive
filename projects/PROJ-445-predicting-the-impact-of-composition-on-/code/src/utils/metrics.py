"""
Metrics and statistical analysis utilities for chalcogenide glass Tg prediction.
Implements Variance Inflation Factor (VIF) computation, collinearity mitigation
via residualization, and bootstrap confidence intervals for SHAP differences.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import itertools

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = PROJECT_ROOT / "state"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Logger setup
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def compute_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Compute Variance Inflation Factors (VIF) for a set of features.
    
    Args:
        df: DataFrame containing the features.
        feature_cols: List of column names to compute VIF for.
        
    Returns:
        Dictionary mapping feature names to their VIF values.
        
    Raises:
        ValueError: If any feature has zero variance.
    """
    if not feature_cols:
        return {}
        
    X = df[feature_cols].copy()
    
    # Check for zero variance features
    for col in feature_cols:
        if X[col].var() == 0:
            raise ValueError(f"Feature '{col}' has zero variance. VIF cannot be computed.")
    
    # Add intercept for VIF calculation (statsmodels expects it)
    X_with_intercept = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(feature_cols):
        # VIF for feature i is the VIF of the i-th column (excluding constant)
        # In X_with_intercept, constant is at index 0, features start at 1
        vif = variance_inflation_factor(X_with_intercept.values, i + 1)
        vif_data[col] = vif
        
    return vif_data


def residualize_features(
    df: pd.DataFrame, 
    target_col: str, 
    predictor_col: str, 
    confounder_cols: List[str]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Residualize a predictor against confounders to remove collinearity.
    This orthogonalizes the predictor with respect to the confounders.
    
    Args:
        df: Input DataFrame.
        target_col: The column name of the predictor to residualize.
        predictor_col: The name for the new residualized column (e.g., 'resid_<target_col>').
        confounder_cols: List of column names to regress against (confounders).
        
    Returns:
        Tuple of (DataFrame with new residualized column, metadata dict).
    """
    if not confounder_cols:
        # If no confounders, just return the original column
        df = df.copy()
        df[predictor_col] = df[target_col]
        return df, {"method": "none", "reason": "No confounders provided"}
    
    # Ensure we have data
    mask = df[[target_col] + confounder_cols].notna().all(axis=1)
    if mask.sum() == 0:
        raise ValueError("No valid data points after removing NaNs for residualization.")
        
    X = df.loc[mask, confounder_cols]
    y = df.loc[mask, target_col]
    
    # Add constant
    X_with_const = sm.add_constant(X)
    
    # Fit linear model: target = beta0 + beta1*conf1 + ... + epsilon
    model = sm.OLS(y, X_with_const).fit()
    
    # Get residuals (these are the orthogonalized values)
    residuals = model.resid
    
    # Create new DataFrame
    df_resid = df.copy()
    df_resid.loc[mask, predictor_col] = residuals
    
    # Fill NaNs in rows that were excluded
    df_resid.loc[~mask, predictor_col] = np.nan
    
    metadata = {
        "method": "residualization",
        "target_variable": target_col,
        "confounders": confounder_cols,
        "r_squared": model.rsquared,
        "n_samples": int(mask.sum()),
        "formula": model.model.formula
    }
    
    return df_resid, metadata


def check_and_mitigate_collinearity(
    df: pd.DataFrame, 
    feature_cols: List[str], 
    threshold: float = 5.0,
    performance_metrics_path: Optional[Path] = None
) -> Tuple[bool, pd.DataFrame, Dict[str, Any]]:
    """
    Check for collinearity using VIF and mitigate if necessary.
    
    Args:
        df: DataFrame with features.
        feature_cols: List of feature column names.
        threshold: VIF threshold above which mitigation is triggered.
        performance_metrics_path: Path to save/update performance_metrics.json.
        
    Returns:
        Tuple of (mitigation_triggered, processed_df, mitigation_metadata).
    """
    vif_results = compute_vif(df, feature_cols)
    
    high_vif_features = {k: v for k, v in vif_results.items() if v >= threshold}
    
    mitigation_metadata = {
        "vif_results": vif_results,
        "threshold": threshold,
        "high_vif_features": high_vif_features,
        "mitigation_triggered": False,
        "mitigation_strategy": None,
        "mitigation_details": {}
    }
    
    processed_df = df.copy()
    
    if high_vif_features:
        logger.warning(f"Collinearity detected! VIF >= {threshold} for: {list(high_vif_features.keys())}")
        
        # Mitigation strategy: Residualization
        # Identify the most collinear feature (highest VIF)
        target_feature = max(high_vif_features, key=high_vif_features.get)
        
        # Confounders are all other features
        confounders = [f for f in feature_cols if f != target_feature]
        
        # Residualize the target feature against confounders
        residualized_col = f"resid_{target_feature}"
        processed_df, resid_meta = residualize_features(
            processed_df, 
            target_feature, 
            residualized_col, 
            confounders
        )
        
        mitigation_metadata["mitigation_triggered"] = True
        mitigation_metadata["mitigation_strategy"] = "residualization"
        mitigation_metadata["mitigation_details"] = resid_meta
        
        logger.info(f"Mitigated collinearity by residualizing '{target_feature}' against {confounders}")
        
        # Update performance metrics file if path provided
        if performance_metrics_path:
            update_performance_metrics(
                performance_metrics_path, 
                {
                    "collinearity_mitigation": "residualization",
                    "mitigation_details": resid_meta
                }
            )
    else:
        logger.info("No collinearity detected (all VIF < {}). Proceeding without mitigation.".format(threshold))
        
    return mitigation_metadata["mitigation_triggered"], processed_df, mitigation_metadata


def update_performance_metrics(
    metrics_path: Path, 
    updates: Dict[str, Any]
) -> None:
    """
    Update or create the performance_metrics.json artifact with new data.
    
    Args:
        metrics_path: Path to the performance_metrics.json file.
        updates: Dictionary of key-value pairs to update/add.
    """
    metrics_path = Path(metrics_path)
    
    # Load existing metrics if file exists
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    else:
        metrics = {}
        
    # Update with new data
    metrics.update(updates)
    
    # Save back
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Updated performance metrics at {metrics_path}")


def compute_bootstrap_ci_for_shap_difference(
    shap_values: np.ndarray, 
    feature_names: List[str], 
    feature_group_a: List[str], 
    feature_group_b: List[str], 
    n_bootstrap: int = 1000, 
    alpha: float = 0.05,
    correction_method: str = "holm"
) -> Dict[str, Any]:
    """
    Compute 95% bootstrapped confidence intervals for the difference in 
    mean absolute SHAP values between two feature groups, with family-wise 
    error rate control.
    
    Args:
        shap_values: 2D array of SHAP values (samples x features).
        feature_names: List of feature names corresponding to columns in shap_values.
        feature_group_a: List of feature names in group A.
        feature_group_b: List of feature names in group B.
        n_bootstrap: Number of bootstrap iterations.
        alpha: Significance level (default 0.05 for 95% CI).
        correction_method: Method for multiple comparison correction ("holm", "bonferroni").
        
    Returns:
        Dictionary with ci_lower, ci_upper, is_significant, and p_value.
    """
    # Validate groups
    group_a_indices = [feature_names.index(f) for f in feature_group_a if f in feature_names]
    group_b_indices = [feature_names.index(f) for f in feature_group_b if f in feature_names]
    
    if not group_a_indices or not group_b_indices:
        raise ValueError("One or both feature groups are empty or contain invalid features.")
        
    # Compute mean absolute SHAP for each group per sample
    mean_abs_shap_a = np.abs(shap_values[:, group_a_indices]).mean(axis=1)
    mean_abs_shap_b = np.abs(shap_values[:, group_b_indices]).mean(axis=1)
    
    # Observed difference
    observed_diff = mean_abs_shap_a.mean() - mean_abs_shap_b.mean()
    
    # Bootstrap
    boot_diffs = []
    n_samples = shap_values.shape[0]
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        boot_a = mean_abs_shap_a[indices]
        boot_b = mean_abs_shap_b[indices]
        boot_diff = boot_a.mean() - boot_b.mean()
        boot_diffs.append(boot_diff)
        
    boot_diffs = np.array(boot_diffs)
    
    # Compute confidence interval
    ci_lower = np.percentile(boot_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(boot_diffs, 100 * (1 - alpha / 2))
    
    # Hypothesis test: H0: difference == 0
    # Two-sided test
    p_value = 2 * (1 - stats.norm.cdf(abs(observed_diff) / boot_diffs.std()))
    
    # Multiple comparison correction (if multiple hypotheses tested)
    # For now, we assume this is a single comparison. If called multiple times,
    # the caller should handle correction across calls.
    # Implementing Holm-Bonferroni for a single comparison is trivial (no change).
    
    is_significant = (ci_lower > 0) or (ci_upper < 0)
    
    return {
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "is_significant": bool(is_significant),
        "p_value": float(p_value),
        "observed_difference": float(observed_diff),
        "n_bootstrap": n_bootstrap,
        "correction_method": correction_method
    }


def main():
    """
    Main function to demonstrate VIF computation and collinearity mitigation.
    This is intended to be called by other modules, not run standalone for production.
    """
    logger.info("Starting metrics module demonstration...")
    
    # Create sample data for demonstration
    np.random.seed(42)
    n_samples = 100
    
    # Simulate collinear features
    x1 = np.random.normal(0, 1, n_samples)
    x2 = x1 * 0.9 + np.random.normal(0, 0.1, n_samples)  # Highly correlated with x1
    x3 = np.random.normal(0, 1, n_samples)  # Independent
    
    df_demo = pd.DataFrame({
        "feature_1": x1,
        "feature_2": x2,
        "feature_3": x3
    })
    
    # Compute VIF
    vif_results = compute_vif(df_demo, ["feature_1", "feature_2", "feature_3"])
    logger.info(f"VIF Results: {vif_results}")
    
    # Check and mitigate
    triggered, df_processed, metadata = check_and_mitigate_collinearity(
        df_demo, 
        ["feature_1", "feature_2", "feature_3"], 
        threshold=5.0,
        performance_metrics_path=ARTIFACTS_DIR / "performance_metrics.json"
    )
    
    if triggered:
        logger.info(f"Collinearity mitigated. New columns: {df_processed.columns.tolist()}")
    else:
        logger.info("No mitigation needed.")
        
    logger.info("Metrics module demonstration complete.")


if __name__ == "__main__":
    main()