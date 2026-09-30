import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import warnings

# Import local config
from code.src.utils.config import get_results_dir, get_processed_data_dir, get_logs_dir, set_global_seed

logger = logging.getLogger(__name__)

def calculate_skewness(series: pd.Series) -> float:
    """Calculate skewness for a given series."""
    return series.skew()

def shapiro_wilk_test(series: pd.Series) -> Tuple[float, float]:
    """Perform Shapiro-Wilk test for normality."""
    if len(series.dropna()) < 3:
        return 0.0, 1.0
    stat, p_value = stats.shapiro(series.dropna())
    return float(stat), float(p_value)

def should_switch_to_spearman(series_x: pd.Series, series_y: pd.Series) -> bool:
    """
    Determine if Spearman correlation should be used instead of Pearson.
    Switch if skewness > 1.0 or Shapiro-Wilk p < 0.05 for either variable.
    """
    skew_x = calculate_skewness(series_x)
    skew_y = calculate_skewness(series_y)
    if abs(skew_x) > 1.0 or abs(skew_y) > 1.0:
        return True

    _, p_x = shapiro_wilk_test(series_x)
    _, p_y = shapiro_wilk_test(series_y)

    if p_x < 0.05 or p_y < 0.05:
        return True

    return False

def pearson_correlation_with_ci(x: pd.Series, y: pd.Series, confidence: float = 0.95) -> Dict[str, Any]:
    """Calculate Pearson correlation with confidence interval."""
    x_clean = x.dropna()
    y_clean = y.dropna()
    min_len = min(len(x_clean), len(y_clean))
    x_clean = x_clean.iloc[:min_len]
    y_clean = y_clean.iloc[:min_len]

    corr, p_value = stats.pearsonr(x_clean, y_clean)
    n = len(x_clean)
    if n < 3:
        return {"correlation": 0.0, "p_value": 1.0, "ci_lower": 0.0, "ci_upper": 0.0}

    # Fisher transformation for CI
    z = 0.5 * np.log((1 + corr) / (1 - corr))
    se_z = 1.0 / np.sqrt(n - 3)
    z_lower = z - stats.norm().inverse_cdf((1 + confidence) / 2) * se_z
    z_upper = z + stats.norm().inverse_cdf((1 + confidence) / 2) * se_z

    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "n": n
    }

def spearman_correlation_with_ci(x: pd.Series, y: pd.Series, confidence: float = 0.95) -> Dict[str, Any]:
    """Calculate Spearman correlation with confidence interval."""
    x_clean = x.dropna()
    y_clean = y.dropna()
    min_len = min(len(x_clean), len(y_clean))
    x_clean = x_clean.iloc[:min_len]
    y_clean = y_clean.iloc[:min_len]

    corr, p_value = stats.spearmanr(x_clean, y_clean)
    n = len(x_clean)
    if n < 3:
        return {"correlation": 0.0, "p_value": 1.0, "ci_lower": 0.0, "ci_upper": 0.0}

    # Fisher transformation for CI (approximate for Spearman)
    z = 0.5 * np.log((1 + corr) / (1 - corr))
    se_z = 1.0 / np.sqrt(n - 3)
    z_lower = z - stats.norm().inverse_cdf((1 + confidence) / 2) * se_z
    z_upper = z + stats.norm().inverse_cdf((1 + confidence) / 2) * se_z

    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "n": n
    }

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    if not p_values:
        return []

    n = len(p_values)
    sorted_indices = sorted(range(len(p_values)), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]

    adjusted_p_values = [0.0] * n
    min_val = 1.0
    for i in range(n - 1, -1, -1):
        adjusted = sorted_p_values[i] * n / (i + 1)
        min_val = min(min_val, adjusted)
        adjusted_p_values[sorted_indices[i]] = min(1.0, min_val)

    return adjusted_p_values

def run_regression_analysis(data: pd.DataFrame, diversity_col: str, target_col: str, covariates: List[str]) -> Dict[str, Any]:
    """
    Run Linear Regression: Target ~ Diversity + Covariates.
    Returns coefficients, p-values, R-squared, and baseline comparison.
    """
    if diversity_col not in data.columns or target_col not in data.columns:
        raise ValueError(f"Columns {diversity_col} or {target_col} not found in data")

    # Prepare formula
    # Ensure covariates are in the data
    missing_covs = [c for c in covariates if c not in data.columns]
    if missing_covs:
        raise ValueError(f"Missing covariates in data: {missing_covs}")

    # Handle categorical covariates (e.g., sex)
    formula_parts = [f"{target_col} ~ {diversity_col}"]
    for cov in covariates:
        if data[cov].dtype == 'object':
            formula_parts.append(f"C({cov})")
        else:
            formula_parts.append(cov)

    full_formula = " ~ ".join(formula_parts)
    baseline_formula = f"{target_col} ~ {' + '.join(covariates)}"

    # Fit full model
    try:
        model_full = ols(formula=full_formula, data=data).fit()
        r_squared_full = model_full.rsquared
        p_values_full = model_full.pvalues
        coefficients_full = model_full.params
    except Exception as e:
        logger.error(f"Failed to fit full model: {e}")
        return {
            "r_squared": float(np.nan),
            "coefficients": {},
            "p_values": {},
            "baseline_r_squared": float(np.nan),
            "delta_r_squared": float(np.nan),
            "error": str(e)
        }

    # Fit baseline model (covariates only)
    try:
        model_baseline = ols(formula=baseline_formula, data=data).fit()
        r_squared_baseline = model_baseline.rsquared
    except Exception as e:
        logger.warning(f"Failed to fit baseline model: {e}. Using 0 as baseline.")
        r_squared_baseline = 0.0

    delta_r_squared = r_squared_full - r_squared_baseline

    # Extract specific p-value for the diversity term
    diversity_p_value = p_values_full.get(diversity_col, float(np.nan))

    return {
        "r_squared": float(r_squared_full),
        "baseline_r_squared": float(r_squared_baseline),
        "delta_r_squared": float(delta_r_squared),
        "coefficients": {k: float(v) for k, v in coefficients_full.items()},
        "p_values": {k: float(v) for k, v in p_values_full.items()},
        "diversity_p_value": float(diversity_p_value),
        "diversity_coefficient": float(coefficients_full.get(diversity_col, np.nan))
    }

def run_multiple_regressions(data: pd.DataFrame, diversity_metrics: List[str], target_col: str, covariates: List[str]) -> List[Dict[str, Any]]:
    """
    Run regression for each diversity metric and apply BH correction to p-values.
    """
    results = []
    p_values = []
    diversity_names = []

    for metric in diversity_metrics:
        if metric not in data.columns:
            logger.warning(f"Skipping {metric} - not found in data")
            continue

        result = run_regression_analysis(data, metric, target_col, covariates)
        results.append({
            "metric": metric,
            "r_squared": result["r_squared"],
            "baseline_r_squared": result["baseline_r_squared"],
            "delta_r_squared": result["delta_r_squared"],
            "coefficient": result["diversity_coefficient"],
            "p_value": result["diversity_p_value"],
            "adjusted_p_value": float(np.nan), # To be filled later
            "covariate_coefficients": {k: v for k, v in result["coefficients"].items() if k != metric and k != target_col}
        })
        p_values.append(result["diversity_p_value"])
        diversity_names.append(metric)

    # Apply Benjamini-Hochberg correction to regression p-values
    if p_values:
        adjusted_p_values = apply_benjamini_hochberg(p_values)
        for i, adj_p in enumerate(adjusted_p_values):
            results[i]["adjusted_p_value"] = float(adj_p)

    return results

def main():
    """
    Main entry point for running correlation and regression analysis.
    Reads filtered cohort, runs analysis, and saves results.
    """
    set_global_seed()
    processed_dir = get_processed_data_dir()
    results_dir = get_results_dir()
    logs_dir = get_logs_dir()

    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    input_file = processed_dir / "filtered_cohort.csv"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    data = pd.read_csv(input_file)

    # Define metrics and target
    diversity_metrics = ["shannon_diversity", "simpson_diversity", "chao1"]
    target_col = "cognitive_flexibility_score"
    covariates = ["age", "sex", "bmi", "dietary_fiber", "antibiotic_use"]

    logger.info(f"Running regression analysis on {len(data)} samples")
    logger.info(f"Target: {target_col}, Metrics: {diversity_metrics}")
    logger.info(f"Covariates: {covariates}")

    # Run analysis
    results = run_multiple_regressions(data, diversity_metrics, target_col, covariates)

    # Save results
    output_file = results_dir / "correlation_results.json"
    import json
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_file}")
    return results

if __name__ == "__main__":
    main()
