"""
analysis.py - Statistical Analysis for Virtual Tactile Adaptation

Performs paired t-tests on aggregated evaluation data to validate the adaptive policy
against the static baseline. Calculates statistical power and verifies improvement thresholds.
"""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from scipy import stats

# Import logging configuration from the project's existing module
try:
    from logging_config import setup_analysis_logger
except ImportError:
    # Fallback if logging_config is not yet imported in this specific environment context
    def setup_analysis_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
        return logger

logger = setup_analysis_logger('analysis')

# Constants
DEFAULT_INPUT_PATH = "data/results/eval_logs.csv"
DEFAULT_OUTPUT_PATH = "data/results/analysis_report.csv"
P_VALUE_THRESHOLD = 0.05
IMPROVEMENT_THRESHOLD = 0.15  # 15%

def load_aggregated_data(input_path):
    """
    Load the aggregated evaluation logs.
    
    Args:
        input_path (str): Path to the CSV file containing evaluation results.
        
    Returns:
        pd.DataFrame: The loaded data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Aggregated data file not found at {input_path}. "
                                "Ensure T014 (aggregate.py) has run successfully.")
    
    df = pd.read_csv(input_path)
    
    required_columns = ['object_id', 'policy_type', 'success_rate']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def prepare_paired_data(df):
    """
    Prepare data for paired t-test by pivoting the dataframe.
    
    The data must be paired by 'object_id' with one success_rate for 'adaptive'
    and one for 'static'.
    
    Args:
        df (pd.DataFrame): The loaded evaluation data.
        
    Returns:
        tuple: (adaptive_rates, static_rates, object_ids)
    """
    # Pivot to get one row per object_id
    pivot_df = df.pivot_table(
        index='object_id', 
        columns='policy_type', 
        values='success_rate', 
        aggfunc='first'
    )
    
    # Ensure both policies are present for every object
    if 'adaptive' not in pivot_df.columns or 'static' not in pivot_df.columns:
        raise ValueError("Both 'adaptive' and 'static' policy types must be present for pairing.")
    
    adaptive_rates = pivot_df['adaptive'].values
    static_rates = pivot_df['static'].values
    object_ids = pivot_df.index.values
    
    logger.info(f"Prepared {len(object_ids)} paired samples for analysis.")
    return adaptive_rates, static_rates, object_ids

def perform_paired_ttest(adaptive_rates, static_rates):
    """
    Perform a paired t-test.
    
    Args:
        adaptive_rates (np.array): Success rates for the adaptive policy.
        static_rates (np.array): Success rates for the static policy.
        
    Returns:
        dict: Dictionary containing t-statistic, p-value, and mean difference.
    """
    if len(adaptive_rates) != len(static_rates):
        raise ValueError("Input arrays must have the same length for paired t-test.")
    
    t_stat, p_value = stats.ttest_rel(adaptive_rates, static_rates)
    mean_diff = np.mean(adaptive_rates) - np.mean(static_rates)
    
    logger.info(f"Paired t-test results: t={t_stat:.4f}, p={p_value:.6f}, mean_diff={mean_diff:.4f}")
    return {
        't_statistic': t_stat,
        'p_value': p_value,
        'mean_difference': mean_diff,
        'adaptive_mean': np.mean(adaptive_rates),
        'static_mean': np.mean(static_rates)
    }

def calculate_statistical_power(adaptive_rates, static_rates, alpha=0.05):
    """
    Calculate statistical power (effect size and power).
    
    Uses Cohen's d for effect size and approximates power based on sample size.
    
    Args:
        adaptive_rates (np.array): Success rates for adaptive.
        static_rates (np.array): Success rates for static.
        alpha (float): Significance level.
        
    Returns:
        dict: Effect size (Cohen's d) and estimated power.
    """
    n = len(adaptive_rates)
    mean_diff = np.mean(adaptive_rates) - np.mean(static_rates)
    std_diff = np.std(adaptive_rates - static_rates, ddof=1)
    
    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff
    
    # Approximate power using normal distribution for large n, or t-distribution logic
    # For simplicity and robustness with small n, we use scipy's effect size logic if available,
    # otherwise a standard approximation.
    # Power = P(t > t_critical | non-central t)
    # Using a simplified approximation:
    from statsmodels.stats.power import TTestPower
    power_analysis = TTestPower()
    try:
        power = power_analysis.solve_power(effect_size=cohens_d, nobs1=n, alpha=alpha, alternative='larger')
    except Exception:
        # Fallback if statsmodels is not fully functional or parameters are edge cases
        # Standard approximation for power given effect size d and n
        # z_beta = sqrt(n) * |d| - z_alpha
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha)
        z_beta = np.sqrt(n) * abs(cohens_d) - z_alpha
        power = norm.cdf(z_beta)
    
    logger.info(f"Statistical Power Analysis: Cohen's d={cohens_d:.4f}, Power={power:.4f}")
    return {
        'cohens_d': cohens_d,
        'power': power,
        'sample_size': n
    }

def verify_improvement_threshold(adaptive_mean, static_mean, threshold=0.15):
    """
    Verify if the adaptive policy shows >15% improvement over static.
    
    Improvement is calculated as: (Adaptive - Static) / Static
    If Static is 0, we check if Adaptive > 0 (absolute improvement).
    
    Args:
        adaptive_mean (float): Mean success rate of adaptive.
        static_mean (float): Mean success rate of static.
        threshold (float): Required improvement threshold (0.15).
        
    Returns:
        dict: Verification result.
    """
    if static_mean == 0:
        if adaptive_mean > 0:
            relative_improvement = float('inf')
            passed = True
        else:
            relative_improvement = 0.0
            passed = False
    else:
        relative_improvement = (adaptive_mean - static_mean) / static_mean
        passed = relative_improvement > threshold
    
    logger.info(f"Improvement Check: Relative Improvement = {relative_improvement:.2%}, Threshold = {threshold:.2%}, Passed = {passed}")
    return {
        'relative_improvement': relative_improvement,
        'threshold': threshold,
        'passed': passed
    }

def generate_analysis_report(ttest_results, power_results, improvement_results, output_path):
    """
    Generate a summary CSV report of the analysis.
    
    Args:
        ttest_results (dict): Results from paired t-test.
        power_results (dict): Results from power analysis.
        improvement_results (dict): Results from threshold verification.
        output_path (str): Path to save the report.
    """
    report_data = {
        'metric': [
            't_statistic', 'p_value', 'adaptive_mean', 'static_mean', 
            'mean_difference', 'cohens_d', 'statistical_power', 
            'relative_improvement', 'improvement_threshold', 
            'significance_passed', 'improvement_passed'
        ],
        'value': [
            ttest_results['t_statistic'],
            ttest_results['p_value'],
            ttest_results['adaptive_mean'],
            ttest_results['static_mean'],
            ttest_results['mean_difference'],
            power_results['cohens_d'],
            power_results['power'],
            improvement_results['relative_improvement'],
            improvement_results['threshold'],
            ttest_results['p_value'] < P_VALUE_THRESHOLD,
            improvement_results['passed']
        ]
    }
    
    report_df = pd.DataFrame(report_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report_df.to_csv(output_path, index=False)
    logger.info(f"Analysis report saved to {output_path}")
    return report_df

def run_analysis(input_path, output_path):
    """
    Main execution flow for the analysis task.
    
    Args:
        input_path (str): Path to aggregated data.
        output_path (str): Path for the output report.
        
    Returns:
        bool: True if all criteria (p < 0.05, >15% improvement) are met.
    """
    try:
        # 1. Load Data
        df = load_aggregated_data(input_path)
        
        # 2. Prepare Paired Data
        adaptive_rates, static_rates, object_ids = prepare_paired_data(df)
        
        # 3. Perform T-Test
        ttest_results = perform_paired_ttest(adaptive_rates, static_rates)
        
        # 4. Calculate Power
        power_results = calculate_statistical_power(adaptive_rates, static_rates)
        
        # 5. Verify Improvement Threshold
        improvement_results = verify_improvement_threshold(
            ttest_results['adaptive_mean'], 
            ttest_results['static_mean']
        )
        
        # 6. Generate Report
        generate_analysis_report(ttest_results, power_results, improvement_results, output_path)
        
        # 7. Final Verification
        significance_passed = ttest_results['p_value'] < P_VALUE_THRESHOLD
        improvement_passed = improvement_results['passed']
        
        logger.info("="*50)
        logger.info("FINAL VERIFICATION")
        logger.info(f"P-value < {P_VALUE_THRESHOLD}: {significance_passed}")
        logger.info(f"Improvement > {improvement_results['threshold']:.2%}: {improvement_passed}")
        logger.info("="*50)
        
        if significance_passed and improvement_passed:
            logger.info("SUCCESS: All statistical criteria met.")
            return True
        else:
            logger.warning("FAILURE: Statistical criteria not met.")
            return False
            
    except Exception as e:
        logger.error(f"Analysis failed with error: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Perform statistical analysis on evaluation results.")
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT_PATH,
                        help=f"Path to aggregated CSV data (default: {DEFAULT_INPUT_PATH})")
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_PATH,
                        help=f"Path to output report CSV (default: {DEFAULT_OUTPUT_PATH})")
    
    args = parser.parse_args()
    
    success = run_analysis(args.input, args.output)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()