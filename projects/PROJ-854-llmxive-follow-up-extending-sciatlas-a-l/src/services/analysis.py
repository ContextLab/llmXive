import logging
import json
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

def calculate_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, float]:
    """Calculate Spearman rank correlation between two columns."""
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in dataframe")
    
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 2:
        return {"correlation": np.nan, "p_value": np.nan}
    
    corr, p_value = stats.spearmanr(valid_data[x_col], valid_data[y_col])
    return {"correlation": float(corr), "p_value": float(p_value)}

def perform_linear_regression(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, float]:
    """Perform linear regression between two columns."""
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in dataframe")
    
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 2:
        return {"slope": np.nan, "intercept": np.nan, "r_squared": np.nan, "p_value": np.nan}
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid_data[x_col], valid_data[y_col])
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value)
    }

def apply_multiple_comparison_correction(p_values: List[float], method: str = "bonferroni") -> List[float]:
    """Apply multiple comparison correction to p-values."""
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array([p_values[i] for i in sorted_indices])
    
    if method == "bonferroni":
        corrected = np.minimum(sorted_pvals * n, 1.0)
    elif method == "benjamini_hochberg":
        ranks = np.arange(1, n + 1)
        corrected = np.minimum((sorted_pvals * n) / ranks, 1.0)
        # Ensure monotonicity
        for i in range(n - 2, -1, -1):
            corrected[i] = min(corrected[i], corrected[i + 1])
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    # Restore original order
    result = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        result[idx] = float(corrected[i])
    
    return result

def perform_binned_analysis(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    n_bins: int = 10,
    min_samples_per_bin: int = 5
) -> Dict[str, Any]:
    """
    Perform binned non-linear analysis to detect inverted-U effects.
    
    Splits data into bins based on x_col, calculates mean y for each bin,
    and fits a quadratic model to detect non-linear (inverted-U) patterns.
    
    Args:
        df: Input dataframe
        x_col: Name of the independent variable column (e.g., bridging_coefficient)
        y_col: Name of the dependent variable column (e.g., citation_count)
        n_bins: Number of bins to create
        min_samples_per_bin: Minimum samples required per bin to be included
    
    Returns:
        Dictionary containing:
            - bin_edges: boundaries of each bin
            - bin_means_x: mean x value in each bin
            - bin_means_y: mean y value in each bin
            - bin_counts: number of samples in each bin
            - quadratic_fit: dict with coefficients for y = a*x^2 + b*x + c
            - quadratic_r_squared: goodness of fit for quadratic model
            - has_inverted_u: boolean indicating if quadratic coefficient is significantly negative
    """
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in dataframe")
    
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < n_bins * min_samples_per_bin:
        logger.warning(f"Dataset too small for {n_bins} bins with min {min_samples_per_bin} samples. "
                     f"Got {len(valid_data)} samples.")
        return {
            "bin_edges": [],
            "bin_means_x": [],
            "bin_means_y": [],
            "bin_counts": [],
            "quadratic_fit": {"a": np.nan, "b": np.nan, "c": np.nan},
            "quadratic_r_squared": np.nan,
            "has_inverted_u": False,
            "warning": "Insufficient data for binning"
        }
    
    # Create bins
    x_values = valid_data[x_col].values
    y_values = valid_data[y_col].values
    bin_edges = np.linspace(x_values.min(), x_values.max(), n_bins + 1)
    
    bin_means_x = []
    bin_means_y = []
    bin_counts = []
    valid_bin_indices = []
    
    for i in range(n_bins):
        mask = (x_values >= bin_edges[i]) & (x_values < bin_edges[i + 1])
        # Include last edge
        if i == n_bins - 1:
            mask = (x_values >= bin_edges[i]) & (x_values <= bin_edges[i + 1])
        
        bin_x = x_values[mask]
        bin_y = y_values[mask]
        
        if len(bin_x) >= min_samples_per_bin:
            bin_means_x.append(np.mean(bin_x))
            bin_means_y.append(np.mean(bin_y))
            bin_counts.append(len(bin_x))
            valid_bin_indices.append(i)
    
    if len(bin_means_x) < 3:
        logger.warning("Too few valid bins for quadratic fitting")
        return {
            "bin_edges": [float(e) for e in bin_edges],
            "bin_means_x": [],
            "bin_means_y": [],
            "bin_counts": [],
            "quadratic_fit": {"a": np.nan, "b": np.nan, "c": np.nan},
            "quadratic_r_squared": np.nan,
            "has_inverted_u": False,
            "warning": "Too few valid bins"
        }
    
    bin_means_x = np.array(bin_means_x)
    bin_means_y = np.array(bin_means_y)
    
    # Fit quadratic model: y = a*x^2 + b*x + c
    X = np.vstack([bin_means_x**2, bin_means_x, np.ones_like(bin_means_x)]).T
    try:
        coeffs, residuals, rank, s = np.linalg.lstsq(X, bin_means_y, rcond=None)
        a, b, c = coeffs
        
        # Calculate R-squared
        y_pred = a * bin_means_x**2 + b * bin_means_x + c
        ss_res = np.sum((bin_means_y - y_pred) ** 2)
        ss_tot = np.sum((bin_means_y - np.mean(bin_means_y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Check for inverted-U (concave down): a < 0
        # We'll consider it "significant" if a is negative and the fit is reasonable
        has_inverted_u = a < 0 and r_squared > 0.5
        
        return {
            "bin_edges": [float(e) for e in bin_edges],
            "bin_means_x": [float(x) for x in bin_means_x],
            "bin_means_y": [float(y) for y in bin_means_y],
            "bin_counts": [int(c) for c in bin_counts],
            "quadratic_fit": {
                "a": float(a),
                "b": float(b),
                "c": float(c)
            },
            "quadratic_r_squared": float(r_squared),
            "has_inverted_u": bool(has_inverted_u)
        }
    except Exception as e:
        logger.error(f"Quadratic fitting failed: {e}")
        return {
            "bin_edges": [float(e) for e in bin_edges],
            "bin_means_x": [float(x) for x in bin_means_x],
            "bin_means_y": [float(y) for y in bin_means_y],
            "bin_counts": [int(c) for c in bin_counts],
            "quadratic_fit": {"a": np.nan, "b": np.nan, "c": np.nan},
            "quadratic_r_squared": np.nan,
            "has_inverted_u": False,
            "error": str(e)
        }

def run_full_analysis(df: pd.DataFrame, correction_method: str = "bonferroni") -> Dict[str, Any]:
    """Run the full statistical analysis pipeline."""
    results = {}
    
    # Spearman correlations
    spearman_results = {}
    for target in ["citation_count", "novelty_score"]:
        spearman_results[f"bridging_vs_{target}"] = calculate_spearman_correlation(
            df, "bridging_coefficient", target
        )
    results["spearman_correlations"] = spearman_results
    
    # Linear regressions
    linear_results = {}
    for target in ["citation_count", "novelty_score"]:
        linear_results[f"bridging_vs_{target}"] = perform_linear_regression(
            df, "bridging_coefficient", target
        )
    results["linear_regressions"] = linear_results
    
    # Binned analysis (inverted-U detection)
    binned_results = {}
    for target in ["citation_count", "novelty_score"]:
        binned_results[f"bridging_vs_{target}"] = perform_binned_analysis(
            df, "bridging_coefficient", target
        )
    results["binned_analysis"] = binned_results
    
    # Collect all p-values for correction
    all_p_values = []
    p_value_labels = []
    
    for label, res in spearman_results.items():
        all_p_values.append(res["p_value"])
        p_value_labels.append(f"spearman_{label}")
    
    for label, res in linear_results.items():
        all_p_values.append(res["p_value"])
        p_value_labels.append(f"linear_{label}")
    
    corrected_p_values = apply_multiple_comparison_correction(all_p_values, correction_method)
    results["corrected_p_values"] = dict(zip(p_value_labels, corrected_p_values))
    
    return results

def save_analysis_report(results: Dict[str, Any], output_path: str) -> None:
    """Save analysis results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Analysis report saved to {output_path}")