import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def welch_t_test(group1: np.ndarray, group2: np.ndarray) -> dict:
    """
    Perform Welch's independent samples t-test.
    
    Args:
        group1: Array of values for group 1
        group2: Array of values for group 2
        
    Returns:
        Dictionary containing t-statistic, p-value, and degrees of freedom
    """
    if len(group1) == 0 or len(group2) == 0:
        raise ValueError("One or both groups are empty.")
        
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Sample size too small for t-test (need at least 2 per group).")
    
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    
    if var1 == 0 and var2 == 0:
        raise ValueError("Zero variance in both groups. Cannot compute t-test.")
    
    try:
        result = stats.ttest_ind(group1, group2, equal_var=False)
        return {
            't_statistic': float(result.statistic),
            'p_value': float(result.pvalue),
            'df': float(result.df) if hasattr(result, 'df') else None
        }
    except Exception as e:
        logger.error(f"Error during Welch's t-test: {str(e)}")
        raise

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size for independent samples.
    
    Args:
        group1: Array of values for group 1
        group2: Array of values for group 2
        
    Returns:
        Cohen's d value
    """
    if len(group1) == 0 or len(group2) == 0:
        raise ValueError("One or both groups are empty.")
        
    mean1 = np.mean(group1)
    mean2 = np.mean(group2)
    
    std1 = np.std(group1, ddof=1)
    std2 = np.std(group2, ddof=1)
    
    if std1 == 0 and std2 == 0:
        raise ValueError("Zero variance in both groups. Cannot compute Cohen's d.")
    
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    
    if pooled_std == 0:
        raise ValueError("Pooled standard deviation is zero. Cannot compute Cohen's d.")
    
    return (mean1 - mean2) / pooled_std

def calculate_effect_size_ci(group1: np.ndarray, group2: np.ndarray, confidence: float = 0.95) -> dict:
    """
    Calculate confidence interval for Cohen's d.
    
    Args:
        group1: Array of values for group 1
        group2: Array of values for group 2
        confidence: Confidence level (default 0.95)
        
    Returns:
        Dictionary with effect size and confidence interval bounds
    """
    d = calculate_cohen_d(group1, group2)
    n1 = len(group1)
    n2 = len(group2)
    
    # Approximate standard error for Cohen's d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    
    alpha = 1 - confidence
    z_score = stats.norm.ppf(1 - alpha/2)
    
    ci_lower = d - z_score * se_d
    ci_upper = d + z_score * se_d
    
    return {
        'effect_size': d,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'confidence_level': confidence
    }

def bonferroni_correction(p_values: list, num_tests: int) -> list:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of p-values
        num_tests: Number of statistical tests performed
        
    Returns:
        List of corrected p-values
    """
    if not p_values:
        return []
        
    corrected = [min(p * num_tests, 1.0) for p in p_values]
    return corrected

def calculate_power_and_mdes(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> dict:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    
    Args:
        effect_size: Observed effect size (Cohen's d)
        n1: Sample size of group 1
        n2: Sample size of group 2
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary with power and MDES values
    """
    if n1 < 2 or n2 < 2:
        raise ValueError("Sample size too small for power analysis (need at least 2 per group).")
    
    # Calculate power using t-test power function
    n_per_group = (n1 + n2) / 2
    try:
        power_result = stats.ttost_ind(n1, n2, effect_size, 0.05, 0.05) # Placeholder for proper power calc
        # Using a simplified approximation for power
        from statsmodels.stats.power import TTestIndPower
        power_analysis = TTestIndPower()
        power = power_analysis.power(effect_size=effect_size, nobs1=n_per_group, alpha=alpha, ratio=n2/n1)
    except Exception:
        # Fallback calculation if statsmodels not available or fails
        # Simplified approximation
        se = np.sqrt(1/n1 + 1/n2)
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = (abs(effect_size) / se) - z_alpha
        power = stats.norm.cdf(z_beta)
    
    # Calculate MDES for 80% power
    target_power = 0.8
    try:
        from statsmodels.stats.power import TTestIndPower
        power_analysis = TTestIndPower()
        mdes = power_analysis.solve_power(effect_size=None, nobs1=n_per_group, alpha=alpha, power=target_power, ratio=n2/n1)
    except Exception:
        # Fallback approximation
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(target_power)
        mdes = (z_alpha + z_beta) * np.sqrt(1/n1 + 1/n2)
    
    return {
        'power': float(power),
        'mdes': float(mdes),
        'alpha': alpha,
        'target_power': target_power,
        'sample_sizes': {'n1': n1, 'n2': n2}
    }

def run_analysis(df: pd.DataFrame, metric: str, group_col: str = 'stimulus_type', 
                 nostalgia_val: str = 'nostalgia', control_val: str = 'control') -> dict:
    """
    Run statistical analysis for a specific metric.
    
    Args:
        df: DataFrame containing the data
        metric: Name of the metric column to analyze
        group_col: Column name for grouping
        nostalgia_val: Value in group_col representing nostalgia group
        control_val: Value in group_col representing control group
        
    Returns:
        Dictionary with analysis results
    """
    if metric not in df.columns:
        raise ValueError(f"Metric column '{metric}' not found in dataframe.")
    
    nostalgia_data = df[df[group_col] == nostalgia_val][metric].dropna().values
    control_data = df[df[group_col] == control_val][metric].dropna().values
    
    logger.info(f"Analyzing {metric}: Nostalgia (n={len(nostalgia_data)}), Control (n={len(control_data)})")
    
    # Error handling for small sample sizes
    if len(nostalgia_data) < 2 or len(control_data) < 2:
        raise ValueError(f"Sample size too small for {metric}: Nostalgia n={len(nostalgia_data)}, Control n={len(control_data)}. Minimum 2 per group required.")
    
    # Error handling for zero variance
    var_nostalgia = np.var(nostalgia_data, ddof=1)
    var_control = np.var(control_data, ddof=1)
    
    if var_nostalgia == 0 and var_control == 0:
        raise ValueError(f"Zero variance in both groups for {metric}. Cannot perform statistical test.")
    
    try:
        t_result = welch_t_test(nostalgia_data, control_data)
    except ValueError as e:
        logger.error(f"t-test failed for {metric}: {str(e)}")
        raise
    
    try:
        cohens_d = calculate_cohen_d(nostalgia_data, control_data)
        ci_result = calculate_effect_size_ci(nostalgia_data, control_data)
    except ValueError as e:
        logger.error(f"Effect size calculation failed for {metric}: {str(e)}")
        raise
    
    power_result = calculate_power_and_mdes(cohens_d, len(nostalgia_data), len(control_data))
    
    return {
        'metric': metric,
        'nostalgia_n': len(nostalgia_data),
        'control_n': len(control_data),
        'nostalgia_mean': float(np.mean(nostalgia_data)),
        'control_mean': float(np.mean(control_data)),
        't_statistic': t_result['t_statistic'],
        'p_value': t_result['p_value'],
        'degrees_of_freedom': t_result['df'],
        'cohens_d': cohens_d,
        'effect_size_ci': ci_result,
        'power': power_result['power'],
        'mdes': power_result['mdes']
    }

def run_full_analysis(df: pd.DataFrame, metrics: list, group_col: str = 'stimulus_type') -> dict:
    """
    Run full analysis pipeline for multiple metrics.
    
    Args:
        df: DataFrame containing the data
        metrics: List of metric columns to analyze
        group_col: Column name for grouping
        
    Returns:
        Dictionary with all analysis results and corrected p-values
    """
    results = {}
    p_values = []
    
    for metric in metrics:
        try:
            result = run_analysis(df, metric, group_col)
            results[metric] = result
            p_values.append(result['p_value'])
        except Exception as e:
            logger.error(f"Analysis failed for {metric}: {str(e)}")
            results[metric] = {'error': str(e)}
    
    # Apply Bonferroni correction
    corrected_p_values = bonferroni_correction(p_values, len(metrics))
    
    # Add corrected p-values to results
    for i, metric in enumerate(metrics):
        if metric in results and 'error' not in results[metric]:
            results[metric]['corrected_p_value'] = corrected_p_values[i]
    
    return results

def main():
    """Main entry point for the analysis module."""
    config_path = os.getenv('CONFIG_PATH', 'data/config.yaml')
    data_path = os.getenv('DATA_PATH', 'data/processed/cleaned_dataset.csv')
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return
    
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} records from {data_path}")
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        return
    
    metrics = ['perseverative_errors', 'categories_completed']
    available_metrics = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        logger.error("No valid metrics found in dataset.")
        return
    
    try:
        results = run_full_analysis(df, available_metrics)
        
        # Save results
        output_path = os.getenv('OUTPUT_PATH', 'data/results/statistical_report.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Analysis complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()