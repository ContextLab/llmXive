import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

def spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation and p-value between two columns.
    Returns (correlation, p-value).
    """
    # Drop rows where either column is NaN
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 3:
        return 0.0, 1.0
    
    corr, p_value = stats.spearmanr(valid_data[x_col], valid_data[y_col])
    return float(corr), float(p_value)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.
    Returns a dictionary mapping feature names to VIF values.
    """
    X = df[features].dropna()
    if len(X) < len(features) + 1:
        return {f: float('inf') for f in features}
    
    X = add_constant(X)
    vif_data = {}
    for i, col in enumerate(features):
        vif = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
        vif_data[col] = float(vif)
    return vif_data

def linear_regression_r2(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float]:
    """
    Perform simple linear regression and return R² and p-value for the slope.
    """
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 3:
        return 0.0, 1.0
    
    X = valid_data[x_col].values
    y = valid_data[y_col].values
    
    X_const = add_constant(pd.DataFrame(X))
    model = OLS(y, X_const).fit()
    
    r2 = model.rsquared
    p_value = model.pvalues[1]  # p-value for the slope (first non-constant)
    return float(r2), float(p_value)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.
    Returns corrected p-values and whether any are significant.
    """
    n = len(p_values)
    if n == 0:
        return {"corrected_p_values": [], "significant": False, "method": "bonferroni"}
    
    corrected_p = [min(p * n, 1.0) for p in p_values]
    significant = any(p < alpha for p in corrected_p)
    
    return {
        "corrected_p_values": corrected_p,
        "significant": significant,
        "method": "bonferroni"
    }

def power_analysis(n_samples: int, effect_size: float = 0.30, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis.
    Returns whether power is sufficient and minimum detectable effect size.
    """
    # Simplified power calculation for correlation
    # Using approximation: power depends on n and effect size
    # For r=0.30, n=30 gives roughly 0.56 power (approx)
    
    # Calculate minimum detectable effect size for given n and power=0.8
    # Using approximation formula
    if n_samples < 5:
        min_effect = 1.0
        power_warning = True
    else:
        # Approximate calculation
        # For power=0.8, alpha=0.05, the required n for effect size r is roughly:
        # n = (Z_alpha + Z_beta)^2 / r^2 + 3
        # Solving for r given n and power=0.8 (Z_beta ≈ 0.84)
        # r = sqrt((Z_alpha + Z_beta)^2 / (n - 3))
        z_alpha = 1.96  # for alpha=0.05 two-tailed
        z_beta = 0.84   # for power=0.8
        min_effect = np.sqrt((z_alpha + z_beta)**2 / (n_samples - 3))
        power_warning = n_samples < 30
    
    return {
        "min_detectable_effect_size": float(min_effect),
        "power_warning_flag": power_warning,
        "n_samples": n_samples
    }

def test_piecewise_model(df: pd.DataFrame, x_col: str, y_col: str, threshold_col: Optional[str] = None) -> Dict[str, Any]:
    """
    Test non-linear (piecewise) model if R² < 0.1.
    Attempts to find a breakpoint that improves fit.
    
    Returns:
        Dict with 'piecewise_r2_improvement' key.
        If piecewise model doesn't improve fit or isn't needed, returns 0.0.
    """
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 10:
        logger.warning("Not enough data for piecewise model test")
        return {"piecewise_r2_improvement": 0.0, "reason": "insufficient_data"}
    
    x = valid_data[x_col].values
    y = valid_data[y_col].values
    
    # First, fit a simple linear model to get baseline R²
    X_const = add_constant(pd.DataFrame(x))
    linear_model = OLS(y, X_const).fit()
    baseline_r2 = linear_model.rsquared
    
    # Only test piecewise if baseline R² < 0.1
    if baseline_r2 >= 0.1:
        logger.info(f"Baseline R² ({baseline_r2:.4f}) >= 0.1, skipping piecewise test")
        return {"piecewise_r2_improvement": 0.0, "reason": "baseline_r2_high"}
    
    # Try to find a breakpoint
    # Sort by x and try different breakpoints
    sorted_indices = np.argsort(x)
    x_sorted = x[sorted_indices]
    y_sorted = y[sorted_indices]
    
    best_piecewise_r2 = baseline_r2
    best_breakpoint = None
    
    # Try breakpoints at 25%, 50%, 75% of data range
    n = len(x_sorted)
    test_percentiles = [0.25, 0.5, 0.75]
    
    for pct in test_percentiles:
        idx = int(n * pct)
        if idx < 2 or idx > n - 2:
            continue
        
        breakpoint_val = x_sorted[idx]
        
        # Create piecewise features
        # x1 = min(x, breakpoint), x2 = max(0, x - breakpoint)
        x1 = np.minimum(x_sorted, breakpoint_val)
        x2 = np.maximum(0, x_sorted - breakpoint_val)
        
        X_piece = pd.DataFrame({
            'const': np.ones(n),
            'x1': x1,
            'x2': x2
        })
        
        try:
            piecewise_model = OLS(y_sorted, X_piece).fit()
            piecewise_r2 = piecewise_model.rsquared
            
            if piecewise_r2 > best_piecewise_r2:
                best_piecewise_r2 = piecewise_r2
                best_breakpoint = breakpoint_val
        except Exception as e:
            logger.warning(f"Piecewise model failed at breakpoint {breakpoint_val}: {e}")
            continue
    
    improvement = best_piecewise_r2 - baseline_r2
    
    if improvement > 0:
        logger.info(f"Piecewise model improved R² by {improvement:.4f} (breakpoint at {best_breakpoint})")
        return {
            "piecewise_r2_improvement": float(improvement),
            "reason": "improved_fit",
            "best_breakpoint": float(best_breakpoint) if best_breakpoint is not None else None
        }
    else:
        logger.info("No improvement found with piecewise model")
        return {"piecewise_r2_improvement": 0.0, "reason": "no_improvement"}

def run_correlation_analysis(df: pd.DataFrame, metrics_path: str = "results/metrics.json") -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline including piecewise model test.
    """
    # Ensure results directory exists
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    
    results = {}
    
    # Spearman correlations
    flare_corr, flare_p = spearman_correlation(df, 'log_flare_flux', 'Dst')
    cme_corr, cme_p = spearman_correlation(df, 'cme_speed', 'Dst')
    
    results['spearman'] = {
        'flare_dst': {'correlation': flare_corr, 'p_value': flare_p},
        'cme_dst': {'correlation': cme_corr, 'p_value': cme_p}
    }
    
    # Linear regression R²
    flare_r2, flare_r2_p = linear_regression_r2(df, 'log_flare_flux', 'Dst')
    cme_r2, cme_r2_p = linear_regression_r2(df, 'cme_speed', 'Dst')
    
    results['linear_r2'] = {
        'flare': {'r2': flare_r2, 'p_value': flare_r2_p},
        'cme': {'r2': cme_r2, 'p_value': cme_r2_p}
    }
    
    # VIF calculation
    features = ['log_flare_flux', 'cme_speed']
    valid_features = [f for f in features if f in df.columns]
    
    if len(valid_features) == 2:
        vif_values = calculate_vif(df, valid_features)
        results['vif'] = vif_values
        
        # Check for multicollinearity
        max_vif = max(vif_values.values())
        if max_vif > 5:
            logger.warning(f"High multicollinearity detected (max VIF={max_vif:.2f})")
            # Select model with higher absolute correlation
            if abs(flare_corr) > abs(cme_corr):
                results['selected_model'] = 'univariate_flare'
                results['selected_model_r2'] = flare_r2
            else:
                results['selected_model'] = 'univariate_cme'
                results['selected_model_r2'] = cme_r2
        else:
            results['selected_model'] = 'joint'
            # For joint model, we'd need to calculate multiple R²
            # Using the better of the two as approximation for now
            results['selected_model_r2'] = max(flare_r2, cme_r2)
    else:
        results['selected_model'] = 'univariate_flare' if 'log_flare_flux' in df.columns else 'univariate_cme'
        results['selected_model_r2'] = flare_r2 if 'log_flare_flux' in df.columns else cme_r2
    
    # Bonferroni correction
    p_values = [flare_p, cme_p]
    bonf_result = bonferroni_correction(p_values)
    results['correction'] = bonf_result
    
    # Power analysis
    n_samples = len(df.dropna(subset=['Dst']))
    power_result = power_analysis(n_samples)
    results['power_analysis'] = power_result
    
    # Piecewise model test
    piecewise_result = test_piecewise_model(df, 'log_flare_flux', 'Dst')
    results['piecewise'] = piecewise_result
    
    # Write results
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Correlation analysis results written to {metrics_path}")
    return results

def main():
    """Main entry point for analysis script."""
    logging.basicConfig(level=logging.INFO)
    
    # Load aligned events
    aligned_path = "data/processed/aligned_events.csv"
    if not os.path.exists(aligned_path):
        logger.error(f"Aligned events file not found: {aligned_path}")
        return
    
    df = pd.read_csv(aligned_path)
    
    # Run analysis
    results = run_correlation_analysis(df)
    
    # Print summary
    print("\n=== Correlation Analysis Summary ===")
    print(f"Spearman (Flare-Dst): {results['spearman']['flare_dst']['correlation']:.4f} (p={results['spearman']['flare_dst']['p_value']:.4f})")
    print(f"Spearman (CME-Dst): {results['spearman']['cme_dst']['correlation']:.4f} (p={results['spearman']['cme_dst']['p_value']:.4f})")
    print(f"Selected Model: {results['selected_model']}")
    print(f"Selected Model R²: {results['selected_model_r2']:.4f}")
    print(f"Piecewise Improvement: {results['piecewise']['piecewise_r2_improvement']:.4f}")
    print(f"Power Warning: {results['power_analysis']['power_warning_flag']}")

if __name__ == "__main__":
    main()