"""
Statistical analysis module for exoplanetary atmospheric characterization.
Implements censored data correlation, bootstrap resampling, and regression analysis.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Try to import survival analysis libraries; if missing, log warning but allow partial runs
try:
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logging.warning("statsmodels not available. Regression features will be limited.")

try:
    from lifelines import TobitFitter
    HAS_LIFELINES = True
except ImportError:
    HAS_LIFELINES = False
    logging.warning("lifelines not available. Tobit regression features will be limited.")

try:
    from sksurv.nonparametric import kendalltau
    HAS_SKSURV = True
except ImportError:
    HAS_SKSURV = False
    logging.warning("scikit-survival not available. Censored correlation features will be limited.")

from config import get_config
from utils import setup_logging, is_censored_value, create_censored_series

# Configure logging
logger = setup_logging("analysis", level=logging.INFO)


def verify_imports() -> bool:
    """Verify that required libraries are available."""
    missing = []
    if not HAS_STATSMODELS:
        missing.append("statsmodels")
    if not HAS_LIFELINES:
        missing.append("lifelines")
    if not HAS_SKSURV:
        missing.append("scikit-survival")
    
    if missing:
        logger.error(f"Missing required libraries: {', '.join(missing)}")
        return False
    logger.info("All required libraries are available.")
    return True


def load_analysis_data(input_path: str) -> pd.DataFrame:
    """
    Load the analysis dataset containing metadata and retrieval results.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        DataFrame with analysis data.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df


def quality_control_filter(df: pd.DataFrame, snr_threshold: float = 5.0) -> pd.DataFrame:
    """
    Flag low SNR spectra and prepare censored data indicators.
    
    Args:
        df: Input DataFrame with SNR and retrieval results.
        snr_threshold: Minimum SNR for resolved measurements.
        
    Returns:
        DataFrame with additional 'is_censored' column.
    """
    df = df.copy()
    
    # Determine censored status based on SNR or explicit flag
    if 'is_upper_limit' in df.columns:
        df['is_censored'] = df['is_upper_limit']
    elif 'snr' in df.columns:
        df['is_censored'] = df['snr'] < snr_threshold
    else:
        df['is_censored'] = False
        
    n_censored = df['is_censored'].sum()
    logger.info(f"Quality control: {n_censored} censored values (SNR < {snr_threshold})")
    return df


def calculate_effect_size(df: pd.DataFrame, group_col: str = 'planet_category', value_col: str = 'water_mixing_ratio') -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        df: Input DataFrame.
        group_col: Column name for grouping.
        value_col: Column name for values.
        
    Returns:
        Cohen's d effect size.
    """
    if group_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Columns {group_col} or {value_col} not found in DataFrame")
        
    groups = df[group_col].unique()
    if len(groups) < 2:
        return 0.0
        
    g1 = df[df[group_col] == groups[0]][value_col].dropna()
    g2 = df[df[group_col] == groups[1]][value_col].dropna()
    
    if len(g1) == 0 or len(g2) == 0:
        return 0.0
        
    mean1, mean2 = g1.mean(), g2.mean()
    std1, std2 = g1.std(), g2.std()
    n1, n2 = len(g1), len(g2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std


def compute_censored_kendall_tau(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float]:
    """
    Compute Kendall's tau correlation for censored data using scikit-survival.
    
    Args:
        df: Input DataFrame.
        x_col: Column name for independent variable.
        y_col: Column name for dependent variable.
        
    Returns:
        Tuple of (tau, p-value).
    """
    if not HAS_SKSURV:
        logger.warning("scikit-survival not available. Using standard Kendall's tau.")
        valid = df[[x_col, y_col]].dropna()
        if len(valid) < 2:
            return 0.0, 1.0
        tau, p_val = scipy.stats.kendalltau(valid[x_col], valid[y_col])
        return tau, p_val
        
    # Prepare censored data
    x = df[x_col].values
    y = df[y_col].values
    is_censored = df['is_censored'].values if 'is_censored' in df.columns else np.zeros(len(df), dtype=bool)
    
    # scikit-survival expects event=False for censored (upper limit)
    # Here, is_censored=True means we have an upper limit (event=False)
    event = ~is_censored
    
    # Create structured array for survival data (y, event)
    # We are correlating x with y, so we treat y as the survival time
    try:
        tau, p_val = kendalltau((y, event), x)
        logger.info(f"Censored Kendall's tau: {tau:.4f}, p-value: {p_val:.4f}")
        return tau, p_val
    except Exception as e:
        logger.warning(f"Failed to compute censored Kendall's tau: {e}. Falling back to standard.")
        valid = df[[x_col, y_col]].dropna()
        if len(valid) < 2:
            return 0.0, 1.0
        tau, p_val = scipy.stats.kendalltau(valid[x_col], valid[y_col])
        return tau, p_val


def bootstrap_kendall_tau(df: pd.DataFrame, x_col: str, y_col: str, n_iterations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to estimate confidence interval for Kendall's tau.
    
    Args:
        df: Input DataFrame.
        x_col: Column name for independent variable.
        y_col: Column name for dependent variable.
        n_iterations: Number of bootstrap iterations.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with bootstrap results.
    """
    import scipy.stats
    np.random.seed(seed)
    
    taus = []
    mixing_ratio_samples = []
    
    logger.info(f"Starting bootstrap resampling ({n_iterations} iterations)...")
    
    for i in range(n_iterations):
        # Resample with replacement
        sample_idx = np.random.choice(len(df), size=len(df), replace=True)
        sample_df = df.iloc[sample_idx]
        
        # Compute tau for this sample
        if 'is_censored' in sample_df.columns:
            # Use censored method if available
            tau, _ = compute_censored_kendall_tau(sample_df, x_col, y_col)
        else:
            valid = sample_df[[x_col, y_col]].dropna()
            if len(valid) < 2:
                tau = 0.0
            else:
                tau, _ = scipy.stats.kendalltau(valid[x_col], valid[y_col])
        
        taus.append(tau)
        
        # Collect mixing ratio samples for variable CI calculation
        if y_col in sample_df.columns:
            sample_vals = sample_df[y_col].dropna().values
            mixing_ratio_samples.extend(sample_vals)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Bootstrap iteration {i + 1}/{n_iterations}")
    
    taus = np.array(taus)
    mixing_ratio_samples = np.array(mixing_ratio_samples)
    
    tau_mean = np.mean(taus)
    ci_lower = np.percentile(taus, 2.5)
    ci_upper = np.percentile(taus, 97.5)
    
    result = {
        "iterations": n_iterations,
        "tau_mean": float(tau_mean),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "ci_width": float(ci_upper - ci_lower)
    }
    
    logger.info(f"Bootstrap complete. Tau mean: {tau_mean:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return result, mixing_ratio_samples


def calculate_statistical_power(df: pd.DataFrame, x_col: str, y_col: str, target_tau: float = 0.3, alpha: float = 0.05, n_sim: int = 1000, seed: int = 42) -> float:
    """
    Estimate statistical power to detect a given Kendall's tau.
    
    Args:
        df: Input DataFrame.
        x_col: Column name for independent variable.
        y_col: Column name for dependent variable.
        target_tau: Target tau value to detect.
        alpha: Significance level.
        n_sim: Number of simulation iterations.
        seed: Random seed.
        
    Returns:
        Estimated power.
    """
    import scipy.stats
    np.random.seed(seed)
    
    # Simplified power estimation via bootstrap
    # Generate bootstrap samples and check how often we reject null
    significant_count = 0
    
    logger.info(f"Estimating statistical power (n_sim={n_sim})...")
    
    for i in range(n_sim):
        sample_idx = np.random.choice(len(df), size=len(df), replace=True)
        sample_df = df.iloc[sample_idx]
        
        valid = sample_df[[x_col, y_col]].dropna()
        if len(valid) < 2:
            continue
            
        tau, p_val = scipy.stats.kendalltau(valid[x_col], valid[y_col])
        if p_val < alpha:
            significant_count += 1
    
    power = significant_count / n_sim
    logger.info(f"Estimated power: {power:.4f}")
    return power


def generate_quality_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a quality report summarizing the dataset.
    
    Args:
        df: Input DataFrame.
        output_path: Path to save the report.
    """
    report = {
        "total_samples": len(df),
        "censored_count": int(df['is_censored'].sum()) if 'is_censored' in df.columns else 0,
        "resolved_count": int((~df['is_censored']).sum()) if 'is_censored' in df.columns else len(df),
        "unique_planets": df['planet_name'].nunique() if 'planet_name' in df.columns else 0
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Quality report saved to {output_path}")


def save_power_results(power: float, output_path: str) -> None:
    """
    Save statistical power analysis results.
    
    Args:
        power: Estimated power.
        output_path: Path to save results.
    """
    result = {
        "power_estimate": float(power),
        "power_sufficient": power >= 0.8
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power results saved to {output_path}")


def calculate_ci_width_variable(mixing_ratio_samples: np.ndarray) -> Dict[str, Any]:
    """
    Calculate the 95% CI width of the water mixing ratio distribution.
    
    Args:
        mixing_ratio_samples: Array of bootstrapped mixing ratio values.
        
    Returns:
        Dictionary with CI width and threshold check.
    """
    if len(mixing_ratio_samples) == 0:
        raise ValueError("No mixing ratio samples provided")
        
    ci_lower = np.percentile(mixing_ratio_samples, 2.5)
    ci_upper = np.percentile(mixing_ratio_samples, 97.5)
    ci_width = ci_upper - ci_lower
    
    result = {
        "ci_width": float(ci_width),
        "threshold_met": ci_width <= 0.2
    }
    
    logger.info(f"Variable CI width: {ci_width:.4f} (threshold <= 0.2: {result['threshold_met']})")
    return result


def calculate_ci_width_tau(bootstrap_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the 95% CI width of the Kendall's tau coefficient itself.
    
    Args:
        bootstrap_results: Dictionary containing bootstrap tau values and statistics.
                           Expected keys: 'ci_lower', 'ci_upper'.
                           Alternatively, can accept a list of tau values under 'taus'.
    
    Returns:
        Dictionary with {ci_width_tau, threshold_met}.
    """
    if 'taus' in bootstrap_results:
        taus = np.array(bootstrap_results['taus'])
        ci_lower = np.percentile(taus, 2.5)
        ci_upper = np.percentile(taus, 97.5)
    elif 'ci_lower' in bootstrap_results and 'ci_upper' in bootstrap_results:
        ci_lower = bootstrap_results['ci_lower']
        ci_upper = bootstrap_results['ci_upper']
    else:
        raise ValueError("bootstrap_results must contain 'taus' array or 'ci_lower'/'ci_upper' values")
    
    ci_width_tau = ci_upper - ci_lower
    threshold_met = ci_width_tau <= 0.2
    
    result = {
        "ci_width_tau": float(ci_width_tau),
        "threshold_met": bool(threshold_met)
    }
    
    logger.info(f"Tau CI width: {ci_width_tau:.4f} (threshold <= 0.2: {threshold_met})")
    return result


def save_robustness_report_tau(result: Dict[str, Any], output_path: str) -> None:
    """
    Save the robustness report for Kendall's tau.
    
    Args:
        result: Dictionary with ci_width_tau and threshold_met.
        output_path: Path to save the JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Robustness report (tau) saved to {output_path}")


def main():
    """
    Main entry point for the analysis module.
    Can be run as a script for debugging or integration.
    """
    config = get_config()
    input_path = config.get('analysis_input', 'data/processed/analysis_dataset.csv')
    output_dir = Path(config.get('output_dir', 'results'))
    
    logger.info(f"Starting analysis with input: {input_path}")
    
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    df = load_analysis_data(input_path)
    df = quality_control_filter(df)
    
    # Example usage of calculate_ci_width_tau
    # This function is typically called after bootstrap_kendall_tau
    if 'water_mixing_ratio' in df.columns:
        # Simulate bootstrap for demonstration if not already done
        bootstrap_res, samples = bootstrap_kendall_tau(
            df, 
            x_col='temperature', 
            y_col='water_mixing_ratio',
            n_iterations=100
        )
        
        # Calculate tau CI width
        tau_ci_result = calculate_ci_width_tau(bootstrap_res)
        tau_output_path = output_dir / 'robustness_report_tau.json'
        save_robustness_report_tau(tau_ci_result, str(tau_output_path))
        
        # Calculate variable CI width
        var_ci_result = calculate_ci_width_variable(samples)
        var_output_path = output_dir / 'robustness_report_variable.json'
        save_robustness_report_tau(var_ci_result, str(var_output_path))
    
    logger.info("Analysis complete.")


if __name__ == "__main__":
    main()