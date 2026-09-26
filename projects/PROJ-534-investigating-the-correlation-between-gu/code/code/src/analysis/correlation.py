import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np
from scipy import stats
from code.src.utils.config import get_results_dir, get_logs_dir, ensure_directories

# Configure logger for this module
logger = logging.getLogger(__name__)

def calculate_skewness(series: pd.Series) -> float:
    """
    Calculate the skewness of a pandas Series.
    Returns 0.0 if the series has fewer than 3 non-null values.
    """
    valid_series = series.dropna()
    if len(valid_series) < 3:
        return 0.0
    return float(stats.skew(valid_series))

def shapiro_wilk_test(series: pd.Series) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.
    Returns (statistic, p-value).
    If the series has fewer than 3 or more than 5000 values, returns (0.0, 1.0)
    to indicate the test cannot be performed (and thus we default to Pearson if skewness is low).
    """
    valid_series = series.dropna()
    n = len(valid_series)
    if n < 3 or n > 5000:
        # scipy.stats.shapiro fails for n > 5000
        return 0.0, 1.0
    
    try:
        stat, p_value = stats.shapiro(valid_series)
        return float(stat), float(p_value)
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}. Returning default (0.0, 1.0).")
        return 0.0, 1.0

def should_switch_to_spearman(var_x: pd.Series, var_y: pd.Series, skew_threshold: float = 1.0, alpha: float = 0.05) -> bool:
    """
    Determine whether to switch from Pearson to Spearman correlation.
    
    Switch to Spearman if:
    1. Skewness of either variable > skew_threshold (default 1.0)
    2. Shapiro-Wilk p-value < alpha (default 0.05) for either variable
    
    Returns True if switch is needed, False otherwise.
    """
    skew_x = calculate_skewness(var_x)
    skew_y = calculate_skewness(var_y)
    
    if abs(skew_x) > skew_threshold or abs(skew_y) > skew_threshold:
        logger.debug(f"Switching to Spearman: Skewness threshold exceeded (X: {skew_x:.3f}, Y: {skew_y:.3f})")
        return True
    
    stat_x, p_x = shapiro_wilk_test(var_x)
    stat_y, p_y = shapiro_wilk_test(var_y)
    
    if p_x < alpha or p_y < alpha:
        logger.debug(f"Switching to Spearman: Normality assumption violated (X p={p_x:.3f}, Y p={p_y:.3f})")
        return True
    
    return False

def pearson_correlation_with_ci(x: pd.Series, y: pd.Series, confidence_level: float = 0.95) -> Dict[str, Any]:
    """
    Calculate Pearson correlation coefficient with confidence interval.
    """
    valid_pairs = pd.concat([x, y], axis=1).dropna()
    if len(valid_pairs) < 3:
        return {
            "correlation_coefficient": np.nan,
            "p_value": np.nan,
            "confidence_interval": (np.nan, np.nan),
            "n": len(valid_pairs)
        }
    
    r, p_value = stats.pearsonr(valid_pairs.iloc[:, 0], valid_pairs.iloc[:, 1])
    
    # Fisher transformation for CI
    if abs(r) >= 1.0:
        # Avoid division by zero or log of non-positive
        ci_low, ci_high = (np.nan, np.nan)
    else:
        z = 0.5 * np.log((1 + r) / (1 - r))
        se = 1.0 / np.sqrt(len(valid_pairs) - 3)
        z_crit = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        
        z_low = z - z_crit * se
        z_high = z + z_crit * se
        
        ci_low = (np.exp(2 * z_low) - 1) / (np.exp(2 * z_low) + 1)
        ci_high = (np.exp(2 * z_high) - 1) / (np.exp(2 * z_high) + 1)
    
    return {
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "confidence_interval": (float(ci_low), float(ci_high)),
        "n": len(valid_pairs),
        "method": "pearson"
    }

def spearman_correlation_with_ci(x: pd.Series, y: pd.Series, confidence_level: float = 0.95) -> Dict[str, Any]:
    """
    Calculate Spearman rank correlation coefficient with confidence interval.
    Note: CI calculation for Spearman is approximate using Fisher transformation on r_s.
    """
    valid_pairs = pd.concat([x, y], axis=1).dropna()
    if len(valid_pairs) < 3:
        return {
            "correlation_coefficient": np.nan,
            "p_value": np.nan,
            "confidence_interval": (np.nan, np.nan),
            "n": len(valid_pairs)
        }
    
    r, p_value = stats.spearmanr(valid_pairs.iloc[:, 0], valid_pairs.iloc[:, 1])
    
    # Approximate CI using Fisher transformation (same as Pearson, but less theoretically rigorous for Spearman)
    if abs(r) >= 1.0:
        ci_low, ci_high = (np.nan, np.nan)
    else:
        z = 0.5 * np.log((1 + r) / (1 - r))
        se = 1.0 / np.sqrt(len(valid_pairs) - 3)
        z_crit = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        
        z_low = z - z_crit * se
        z_high = z + z_crit * se
        
        ci_low = (np.exp(2 * z_low) - 1) / (np.exp(2 * z_low) + 1)
        ci_high = (np.exp(2 * z_high) - 1) / (np.exp(2 * z_high) + 1)
    
    return {
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "confidence_interval": (float(ci_low), float(ci_high)),
        "n": len(valid_pairs),
        "method": "spearman"
    }

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns a list of adjusted p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_pvals = [p_values[i] for i in sorted_indices]
    
    adjusted = [0.0] * n
    rank_order = [0] * n
    
    for i, idx in enumerate(sorted_indices):
        rank_order[idx] = i + 1
    
    # Calculate adjusted p-values
    # Start from the largest p-value and work backwards to ensure monotonicity
    current_min = 1.0
    for i in range(n - 1, -1, -1):
        original_idx = sorted_indices[i]
        rank = i + 1
        adj_p = (sorted_pvals[i] * n) / rank
        if adj_p > current_min:
            adj_p = current_min
        else:
            current_min = adj_p
        adjusted[original_idx] = min(adj_p, 1.0)
    
    return adjusted

def run_correlation_analysis(
    df: pd.DataFrame,
    var_x: str,
    var_y: str,
    covariates: Optional[List[str]] = None,
    skew_threshold: float = 1.0,
    alpha_normality: float = 0.05,
    confidence_level: float = 0.95,
    log_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Perform correlation analysis between var_x and var_y.
    
    Automatically switches to Spearman if:
    - Skewness > skew_threshold
    - Shapiro-Wilk p < alpha_normality
    
    Logs the switch decision.
    
    Returns a dictionary with correlation results.
    """
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.info(f"Running correlation analysis: {var_x} vs {var_y}")
    
    if var_x not in df.columns or var_y not in df.columns:
        raise ValueError(f"Columns {var_x} or {var_y} not found in dataframe")
    
    series_x = df[var_x]
    series_y = df[var_y]
    
    # Check for skewness
    skew_x = calculate_skewness(series_x)
    skew_y = calculate_skewness(series_y)
    
    # Check for normality
    stat_x, p_x = shapiro_wilk_test(series_x)
    stat_y, p_y = shapiro_wilk_test(series_y)
    
    use_spearman = should_switch_to_spearman(series_x, series_y, skew_threshold, alpha_normality)
    
    if use_spearman:
        logger.info(f"Switching to Spearman correlation for {var_x} vs {var_y}. "
                    f"Reason: Skewness (X={skew_x:.3f}, Y={skew_y:.3f}) > {skew_threshold} "
                    f"or Normality violated (X p={p_x:.3f}, Y p={p_y:.3f} < {alpha_normality})")
        result = spearman_correlation_with_ci(series_x, series_y, confidence_level)
    else:
        logger.info(f"Using Pearson correlation for {var_x} vs {var_y}. "
                    f"Reason: Skewness (X={skew_x:.3f}, Y={skew_y:.3f}) <= {skew_threshold} "
                    f"and Normality holds (X p={p_x:.3f}, Y p={p_y:.3f} >= {alpha_normality})")
        result = pearson_correlation_with_ci(series_x, series_y, confidence_level)
    
    result["variable_x"] = var_x
    result["variable_y"] = var_y
    result["used_spearman"] = use_spearman
    result["skewness_x"] = skew_x
    result["skewness_y"] = skew_y
    result["shapiro_p_x"] = p_x
    result["shapiro_p_y"] = p_y
    
    if covariates:
        # Note: Simple correlation doesn't handle covariates. 
        # This is handled in regression (T021).
        # For now, just log that covariates were provided but not used in this specific function.
        logger.warning(f"Covariates {covariates} provided but not used in simple correlation. Use run_regression for adjusted analysis.")
    
    if log_file:
        # Remove file handler to avoid duplicates in subsequent calls
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
    
    return result

def run_multiple_correlations(
    df: pd.DataFrame,
    var_x_list: List[str],
    var_y: str,
    skew_threshold: float = 1.0,
    alpha_normality: float = 0.05,
    confidence_level: float = 0.95,
    log_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run correlation analysis for multiple X variables against one Y variable.
    Applies Benjamini-Hochberg correction to p-values.
    
    Returns a dictionary with individual results and adjusted p-values.
    """
    results = []
    p_values = []
    
    for var_x in var_x_list:
        res = run_correlation_analysis(
            df=df,
            var_x=var_x,
            var_y=var_y,
            skew_threshold=skew_threshold,
            alpha_normality=alpha_normality,
            confidence_level=confidence_level,
            log_file=log_file
        )
        results.append(res)
        p_values.append(res["p_value"])
    
    adjusted_p_values = apply_benjamini_hochberg(p_values)
    
    for i, res in enumerate(results):
        res["adjusted_p_value"] = adjusted_p_values[i]
    
    return {
        "results": results,
        "n_tests": len(results),
        "alpha_normality": alpha_normality,
        "skew_threshold": skew_threshold
    }

def main():
    """
    Main entry point for correlation analysis.
    Loads filtered cohort, runs correlation analysis on alpha diversity vs cognitive scores,
    and saves results.
    """
    # Setup paths
    results_dir = get_results_dir()
    logs_dir = get_logs_dir()
    ensure_directories(results_dir, logs_dir)
    
    log_file = logs_dir / "correlation_analysis.log"
    input_file = results_dir.parent / "processed" / "filtered_cohort.csv"
    output_file = results_dir / "correlation_results.json"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Load data
    df = pd.read_csv(input_file)
    
    # Define variables of interest
    # Assuming diversity metrics are in columns like 'shannon', 'simpson', 'chao1'
    # and cognitive score is in 'cognitive_score' or similar
    diversity_metrics = [col for col in df.columns if col.lower() in ['shannon', 'simpson', 'chao1']]
    cognitive_col = None
    
    # Find cognitive score column
    for col in df.columns:
        if 'cognitive' in col.lower() and 'score' in col.lower():
            cognitive_col = col
            break
    
    if not cognitive_col:
        # Try common alternatives
        if 'cognitive_flexibility' in df.columns:
            cognitive_col = 'cognitive_flexibility'
        elif 'cognitive' in df.columns:
            cognitive_col = 'cognitive'
        else:
            logger.error("Could not find cognitive score column in dataset.")
            sys.exit(1)
    
    if not diversity_metrics:
        logger.error("No diversity metrics found in dataset.")
        sys.exit(1)
    
    logger.info(f"Running correlation analysis for {len(diversity_metrics)} metrics vs {cognitive_col}")
    
    # Run analysis
    analysis_results = run_multiple_correlations(
        df=df,
        var_x_list=diversity_metrics,
        var_y=cognitive_col,
        log_file=log_file
    )
    
    # Save results
    import json
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_file}")
    print(f"Correlation analysis complete. Results saved to {output_file}")
    return analysis_results

if __name__ == "__main__":
    main()