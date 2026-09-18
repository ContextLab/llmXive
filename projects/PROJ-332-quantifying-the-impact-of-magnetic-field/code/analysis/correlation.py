import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from scipy import stats
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_power(n: int, r: float = 0.5, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a Pearson correlation test.
    
    Args:
        n: Sample size (number of discharges)
        r: Expected effect size (correlation coefficient), default 0.5
        alpha: Significance level, default 0.05
        
    Returns:
        Power value between 0 and 1
    """
    if n < 3:
        return 0.0
        
    # Effect size for correlation
    # Cohen's q = 0.5 (medium), 0.8 (large)
    # For r=0.5, q = 0.5
    # Power calculation using non-central t-distribution
    
    # Fisher's z transformation
    z_r = 0.5 * np.log((1 + r) / (1 - r))
    
    # Standard error of z_r
    se = 1.0 / np.sqrt(n - 3)
    
    # Critical z value for alpha (two-tailed)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    
    # Non-centrality parameter
    delta = z_r / se
    
    # Power = P(Z > z_crit - delta) + P(Z < -z_crit - delta)
    # For positive correlation, we care about the upper tail
    power = 1 - stats.norm.cdf(z_crit - delta) + stats.norm.cdf(-z_crit - delta)
    
    return float(power)

def check_power_sufficiency(power: float, threshold: float = 0.20) -> Tuple[bool, str]:
    """
    Check if statistical power is sufficient.
    
    Args:
        power: Calculated power value
        threshold: Minimum acceptable power (default 0.20 per FR-008)
        
    Returns:
        Tuple of (is_sufficient, status_message)
    """
    if power < threshold:
        return False, f"Inconclusive due to low power (power={power:.3f} < {threshold})"
    return True, f"Power sufficient (power={power:.3f})"

def calculate_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, float]:
    """
    Calculate Spearman rank correlation with bootstrap confidence intervals.
    
    Args:
        df: DataFrame containing the data
        x_col: Name of the independent variable column
        y_col: Name of the dependent variable column
        
    Returns:
        Dictionary with correlation coefficient, p-value, and CI bounds
    """
    x = df[x_col].dropna()
    y = df[y_col].dropna()
    
    # Align indices
    common_idx = x.index.intersection(y.index)
    x = x.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(x) < 3:
        logger.warning(f"Insufficient data points for correlation: n={len(x)}")
        return {
            'r': np.nan,
            'p_value': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan
        }
    
    # Calculate Spearman correlation
    r, p_value = stats.spearmanr(x, y)
    
    return {
        'r': float(r),
        'p_value': float(p_value)
    }

def bootstrap_confidence_intervals(df: pd.DataFrame, x_col: str, y_col: str, 
                                   iterations: int = 1000, random_seed: int = 42) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence intervals for correlation coefficient.
    
    Args:
        df: DataFrame containing the data
        x_col: Name of the independent variable column
        y_col: Name of the dependent variable column
        iterations: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (ci_lower, ci_upper)
    """
    np.random.seed(random_seed)
    
    x = df[x_col].dropna().values
    y = df[y_col].dropna().values
    
    n = len(x)
    if n < 3:
        return (np.nan, np.nan)
    
    bootstrap_rs = []
    for _ in range(iterations):
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        r, _ = stats.spearmanr(x_boot, y_boot)
        if not np.isnan(r):
            bootstrap_rs.append(r)
    
    if len(bootstrap_rs) == 0:
        return (np.nan, np.nan)
    
    ci_lower = float(np.percentile(bootstrap_rs, 2.5))
    ci_upper = float(np.percentile(bootstrap_rs, 97.5))
    
    return ci_lower, ci_upper

def check_multicollinearity(df: pd.DataFrame, col1: str, col2: str, threshold: float = 0.95) -> Tuple[bool, float]:
    """
    Check for multicollinearity between two variables.
    
    Args:
        df: DataFrame containing the data
        col1: Name of the first column
        col2: Name of the second column
        threshold: Correlation threshold for flagging collinearity
        
    Returns:
        Tuple of (is_collinear, correlation_value)
    """
    x = df[col1].dropna()
    y = df[col2].dropna()
    
    common_idx = x.index.intersection(y.index)
    x = x.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(x) < 3:
        return False, np.nan
    
    corr, _ = stats.pearsonr(x, y)
    is_collinear = abs(corr) > threshold
    
    return is_collinear, float(corr)

def stratify_by_mode(df: pd.DataFrame, mode_col: str = 'confinement_mode') -> Dict[str, pd.DataFrame]:
    """
    Stratify data by confinement mode.
    
    Args:
        df: DataFrame containing the data
        mode_col: Name of the confinement mode column
        
    Returns:
        Dictionary mapping mode names to filtered DataFrames
    """
    if mode_col not in df.columns:
        logger.warning(f"Mode column '{mode_col}' not found in DataFrame")
        return {}
    
    modes = df[mode_col].unique()
    stratified = {}
    
    for mode in modes:
        mask = df[mode_col] == mode
        stratified[mode] = df[mask].copy()
        logger.info(f"Mode '{mode}': n={len(stratified[mode])}")
    
    return stratified

def run_correlation_analysis(df: pd.DataFrame, x_col: str, y_col: str, 
                             bootstrap_iterations: int = 1000, random_seed: int = 42) -> Dict[str, Any]:
    """
    Run full correlation analysis with bootstrap confidence intervals.
    
    Args:
        df: DataFrame containing the data
        x_col: Name of the independent variable column
        y_col: Name of the dependent variable column
        bootstrap_iterations: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with correlation results
    """
    result = calculate_spearman_correlation(df, x_col, y_col)
    
    if not np.isnan(result['r']):
        ci_lower, ci_upper = bootstrap_confidence_intervals(
            df, x_col, y_col, bootstrap_iterations, random_seed
        )
        result['ci_lower'] = ci_lower
        result['ci_upper'] = ci_upper
    else:
        result['ci_lower'] = np.nan
        result['ci_upper'] = np.nan
    
    return result

def save_analysis_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        results: Dictionary containing analysis results
        output_path: Path to the output JSON file
    """
    import json
    
    # Convert numpy types to Python native types
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            if np.isnan(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    clean_results = convert_numpy_types(results)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """Main entry point for correlation analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run correlation analysis on plasma confinement data')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file path')
    parser.add_argument('--x-col', type=str, default='island_width', help='Independent variable column')
    parser.add_argument('--y-col', type=str, default='tau_e', help='Dependent variable column')
    parser.add_argument('--bootstrap-iterations', type=int, default=1000, help='Number of bootstrap iterations')
    parser.add_argument('--random-seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    logger.info(f"Running correlation analysis: {args.x_col} vs {args.y_col}")
    results = run_correlation_analysis(
        df, args.x_col, args.y_col,
        args.bootstrap_iterations, args.random_seed
    )
    
    save_analysis_results(results, Path(args.output))
    logger.info("Analysis complete")

if __name__ == '__main__':
    main()
