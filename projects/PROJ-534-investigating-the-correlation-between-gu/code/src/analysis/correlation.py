"""
Correlation analysis module for gut microbiome and cognitive flexibility data.

Implements Pearson/Spearman correlation with auto-switch logic based on data
distribution characteristics, and applies Benjamini-Hochberg FDR correction.
"""
import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

def calculate_skewness(data: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate the skewness of a dataset.
    
    Args:
        data: Input data series or array.
        
    Returns:
        Skewness value.
    """
    if isinstance(data, pd.Series):
        data = data.dropna()
    return float(stats.skew(data))

def shapiro_wilk_test(data: Union[pd.Series, np.ndarray]) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: Input data series or array.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    if isinstance(data, pd.Series):
        data = data.dropna()
    statistic, p_value = stats.shapiro(data)
    return float(statistic), float(p_value)

def should_switch_to_spearman(data_x: Union[pd.Series, np.ndarray], 
                              data_y: Union[pd.Series, np.ndarray],
                            skewness_threshold: float = 1.0,
                            shapiro_p_threshold: float = 0.05) -> bool:
    """
    Determine if Spearman correlation should be used instead of Pearson.
    
    Logic: Switch to Spearman if:
    - Skewness of either variable > threshold, OR
    - Shapiro-Wilk p-value < threshold (non-normal)
    
    Args:
        data_x: First variable.
        data_y: Second variable.
        skewness_threshold: Skewness threshold for switch.
        shapiro_p_threshold: P-value threshold for normality test.
        
    Returns:
        True if Spearman should be used, False otherwise.
    """
    x_clean = pd.Series(data_x).dropna()
    y_clean = pd.Series(data_y).dropna()
    
    # Check skewness
    skew_x = calculate_skewness(x_clean)
    skew_y = calculate_skewness(y_clean)
    
    if abs(skew_x) > skewness_threshold or abs(skew_y) > skewness_threshold:
        logger.info(f"Skewness threshold exceeded: X={skew_x:.3f}, Y={skew_y:.3f}")
        return True
    
    # Check normality via Shapiro-Wilk
    # Note: Shapiro-Wilk has a sample size limit (typically < 5000)
    # For larger datasets, we'll use a subset or rely on skewness
    sample_size = min(len(x_clean), len(y_clean), 5000)
    if sample_size > 3:  # Minimum requirement for Shapiro-Wilk
        x_sample = x_clean.iloc[:sample_size]
        y_sample = y_clean.iloc[:sample_size]
        
        _, p_x = shapiro_wilk_test(x_sample)
        _, p_y = shapiro_wilk_test(y_sample)
        
        if p_x < shapiro_p_threshold or p_y < shapiro_p_threshold:
            logger.info(f"Normality test failed (p < {shapiro_p_threshold}): X p={p_x:.4f}, Y p={p_y:.4f}")
            return True
    
    return False

def pearson_correlation_with_ci(data_x: Union[pd.Series, np.ndarray],
                                data_y: Union[pd.Series, np.ndarray],
                                confidence_level: float = 0.95) -> Dict[str, Any]:
    """
    Calculate Pearson correlation coefficient with confidence interval.
    
    Args:
        data_x: First variable.
        data_y: Second variable.
        confidence_level: Confidence level for CI (default 0.95).
        
    Returns:
        Dictionary with correlation, p-value, and confidence interval.
    """
    x_clean = pd.Series(data_x).dropna()
    y_clean = pd.Series(data_y).dropna()
    
    # Align indices
    common_idx = x_clean.index.intersection(y_clean.index)
    x_aligned = x_clean.loc[common_idx]
    y_aligned = y_clean.loc[common_idx]
    
    if len(x_aligned) < 3:
        raise ValueError("Insufficient data points for correlation calculation")
    
    # Calculate Pearson correlation
    r, p_value = stats.pearsonr(x_aligned, y_aligned)
    
    # Calculate confidence interval using Fisher's z-transformation
    n = len(x_aligned)
    z = np.arctanh(r)  # Fisher transformation
    se_z = 1.0 / np.sqrt(n - 3)
    
    z_lower = z - stats.norm.inv(confidence_level / 2 + 0.5) * se_z
    z_upper = z + stats.norm.inv(confidence_level / 2 + 0.5) * se_z
    
    ci_lower = np.tanh(z_lower)
    ci_upper = np.tanh(z_upper)
    
    return {
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "confidence_interval": [float(ci_lower), float(ci_upper)],
        "method": "pearson"
    }

def spearman_correlation_with_ci(data_x: Union[pd.Series, np.ndarray],
                                 data_y: Union[pd.Series, np.ndarray],
                                 confidence_level: float = 0.95) -> Dict[str, Any]:
    """
    Calculate Spearman rank correlation coefficient with confidence interval.
    
    Note: CI calculation for Spearman is approximate (using bootstrap or
    Fisher transformation on ranks). Here we use Fisher transformation
    on the rank-transformed data as an approximation.
    
    Args:
        data_x: First variable.
        data_y: Second variable.
        confidence_level: Confidence level for CI (default 0.95).
        
    Returns:
        Dictionary with correlation, p-value, and confidence interval.
    """
    x_clean = pd.Series(data_x).dropna()
    y_clean = pd.Series(data_y).dropna()
    
    # Align indices
    common_idx = x_clean.index.intersection(y_clean.index)
    x_aligned = x_clean.loc[common_idx]
    y_aligned = y_clean.loc[common_idx]
    
    if len(x_aligned) < 3:
        raise ValueError("Insufficient data points for correlation calculation")
    
    # Calculate Spearman correlation
    r, p_value = stats.spearmanr(x_aligned, y_aligned)
    
    # Calculate confidence interval using Fisher's z-transformation
    # (approximation for Spearman)
    n = len(x_aligned)
    z = np.arctanh(r)  # Fisher transformation
    se_z = 1.0 / np.sqrt(n - 3)
    
    z_lower = z - stats.norm.inv(confidence_level / 2 + 0.5) * se_z
    z_upper = z + stats.norm.inv(confidence_level / 2 + 0.5) * se_z
    
    ci_lower = np.tanh(z_lower)
    ci_upper = np.tanh(z_upper)
    
    return {
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "confidence_interval": [float(ci_lower), float(ci_upper)],
        "method": "spearman"
    }

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg procedure for FDR correction.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        # BH adjusted p-value calculation
        rank = i + 1
        adjusted_p[i] = min(1.0, (n / rank) * sorted_p[i])
    
    # Ensure monotonicity (adjusted p-values should not decrease with rank)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
    
    # Restore original order
    final_adjusted_p = np.zeros(n)
    final_adjusted_p[sorted_indices] = adjusted_p
    
    return [float(p) for p in final_adjusted_p]

def run_correlation_analysis(data_x: Union[pd.Series, np.ndarray],
                             data_y: Union[pd.Series, np.ndarray],
                             alpha: float = 0.05,
                             skewness_threshold: float = 1.0,
                             shapiro_p_threshold: float = 0.05,
                             confidence_level: float = 0.95) -> Dict[str, Any]:
    """
    Run correlation analysis with auto-switch logic and FDR correction.
    
    Args:
        data_x: First variable.
        data_y: Second variable.
        alpha: Significance level for FDR.
        skewness_threshold: Skewness threshold for method selection.
        shapiro_p_threshold: P-value threshold for normality test.
        confidence_level: Confidence level for CI.
        
    Returns:
        Dictionary with correlation results and method used.
    """
    # Determine method
    use_spearman = should_switch_to_spearman(
        data_x, data_y, skewness_threshold, shapiro_p_threshold
    )
    
    if use_spearman:
        logger.info("Switching to Spearman correlation due to distribution characteristics")
        result = spearman_correlation_with_ci(data_x, data_y, confidence_level)
    else:
        logger.info("Using Pearson correlation (data appears normally distributed)")
        result = pearson_correlation_with_ci(data_x, data_y, confidence_level)
    
    # Apply FDR correction (single p-value, but included for consistency)
    adjusted_p = apply_benjamini_hochberg([result["p_value"]], alpha)[0]
    
    result["adjusted_p_value"] = float(adjusted_p)
    result["method_used"] = "spearman" if use_spearman else "pearson"
    
    return result

def run_multiple_correlations(df: pd.DataFrame,
                              x_columns: List[str],
                              y_column: str,
                              alpha: float = 0.05,
                              skewness_threshold: float = 1.0,
                              shapiro_p_threshold: float = 0.05,
                              confidence_level: float = 0.95) -> List[Dict[str, Any]]:
    """
    Run correlation analysis for multiple X variables against one Y variable.
    
    Args:
        df: DataFrame containing all variables.
        x_columns: List of column names for X variables.
        y_column: Column name for Y variable.
        alpha: Significance level for FDR.
        skewness_threshold: Skewness threshold for method selection.
        shapiro_p_threshold: P-value threshold for normality test.
        confidence_level: Confidence level for CI.
        
    Returns:
        List of correlation result dictionaries.
    """
    results = []
    p_values = []
    
    # First pass: collect all raw p-values
    for col in x_columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in DataFrame, skipping")
            continue
        
        if y_column not in df.columns:
            logger.error(f"Y column {y_column} not found in DataFrame")
            continue
        
        result = run_correlation_analysis(
            df[col], df[y_column], alpha, skewness_threshold, 
            shapiro_p_threshold, confidence_level
        )
        results.append({
            "variable_x": col,
            "variable_y": y_column,
            **result
        })
        p_values.append(result["p_value"])
    
    # Second pass: apply FDR correction to all p-values
    adjusted_p_values = apply_benjamini_hochberg(p_values, alpha)
    
    # Update results with adjusted p-values
    for i, result in enumerate(results):
        result["adjusted_p_value"] = float(adjusted_p_values[i])
    
    return results

def main():
    """
    Main function to demonstrate correlation analysis on filtered cohort data.
    """
    from code.src.utils.config import get_processed_data_dir, get_results_dir, setup_logging
    
    setup_logging()
    
    processed_dir = get_processed_data_dir()
    results_dir = get_results_dir()
    
    input_file = processed_dir / "filtered_cohort.csv"
    output_file = results_dir / "correlation_results.json"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Load filtered cohort
    df = pd.read_csv(input_file)
    
    # Define alpha diversity metrics to correlate with cognitive flexibility
    alpha_metrics = ["shannon_diversity", "simpson_diversity", "chao1"]
    cognitive_col = "cognitive_flexibility_score"
    
    # Verify columns exist
    missing_cols = [col for col in alpha_metrics + [cognitive_col] if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)
    
    # Run correlation analysis
    logger.info(f"Running correlation analysis on {len(df)} participants")
    results = run_multiple_correlations(
        df, alpha_metrics, cognitive_col, alpha=0.05
    )
    
    # Save results
    import json
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Correlation results saved to {output_file}")
    
    # Print summary
    logger.info("\nCorrelation Summary:")
    logger.info("-" * 60)
    for res in results:
        sig = "***" if res["adjusted_p_value"] < 0.05 else ""
        logger.info(f"{res['variable_x']}: r={res['correlation_coefficient']:.3f}, "
                   f"p={res['p_value']:.4f}, adj_p={res['adjusted_p_value']:.4f} {sig}")
    
    return results

if __name__ == "__main__":
    main()
