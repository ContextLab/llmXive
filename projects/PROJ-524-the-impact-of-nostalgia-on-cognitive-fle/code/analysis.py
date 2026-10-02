import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import tt_ind_solve_power
from statsmodels.stats.weightstats import ttest_ind, EffectSize
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Custom exception for missing data
class DataNotFoundError(Exception):
    """Raised when the required input dataset file is missing or empty."""
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def welch_t_test(group1: pd.Series, group2: pd.Series) -> Tuple[float, float]:
    """
    Perform Welch's independent samples t-test.
    
    Args:
        group1: Series of values for group 1 (e.g., nostalgia)
        group2: Series of values for group 2 (e.g., control)
        
    Returns:
        Tuple of (t_statistic, p_value)
        
    Raises:
        ValueError: If sample size is too small (< 10 per group)
        ValueError: If variance is zero in either group
    """
    n1, n2 = len(group1), len(group2)
    
    if n1 < 10 or n2 < 10:
        logger.warning(f"ERR_SMALL_SAMPLE: Sample sizes {n1} and {n2} are below threshold (10)")
        raise ValueError(f"Sample size too small: n1={n1}, n2={n2}. Minimum required is 10 per group.")
    
    var1, var2 = group1.var(), group2.var()
    
    if var1 == 0 or var2 == 0:
        logger.warning("ERR_ZERO_VARIANCE: Zero variance detected in one or both groups")
        raise ValueError("Zero variance detected in one or both groups.")
    
    # Use scipy.stats.ttest_ind with equal_var=False for Welch's t-test
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    return float(t_stat), float(p_val)

def calculate_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: Series of values for group 1
        group2: Series of values for group 2
        
    Returns:
        Cohen's d value
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(ddof=1), group2.std(ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("ERR_ZERO_VARIANCE: Pooled standard deviation is zero")
        return 0.0
    
    cohens_d = (mean1 - mean2) / pooled_std
    return float(cohens_d)

def calculate_effect_size_ci(group1: pd.Series, group2: pd.Series, confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Calculate Cohen's d with 95% confidence interval.
    
    Args:
        group1: Series of values for group 1
        group2: Series of values for group 2
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (cohens_d, ci_lower, ci_upper)
    """
    n1, n2 = len(group1), len(group2)
    d = calculate_cohen_d(group1, group2)
    
    # Approximate standard error of Cohen's d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    
    z_score = stats.norm.ppf(1 - (1 - confidence) / 2)
    ci_lower = d - z_score * se_d
    ci_upper = d + z_score * se_d
    
    return float(d), float(ci_lower), float(ci_upper)

def bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of corrected p-values
    """
    n = len(p_values)
    if n == 0:
        return []
    
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected

def calculate_power_and_mdes(group1: pd.Series, group2: pd.Series, alpha: float = 0.05, power: float = 0.8) -> Dict[str, float]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    
    Args:
        group1: Series of values for group 1
        group2: Series of values for group 2
        alpha: Significance level (default 0.05)
        power: Desired power (default 0.8)
        
    Returns:
        Dictionary with 'observed_power' and 'mdes'
    """
    n1, n2 = len(group1), len(group2)
    d = calculate_cohen_d(group1, group2)
    
    # Calculate observed power
    try:
        observed_power = tt_ind_solve_power(
            effect_size=abs(d),
            nobs1=n1,
            alpha=alpha,
            ratio=n2/n1,
            power=None
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}")
        observed_power = 0.0
    
    # Calculate MDES for desired power
    try:
        mdes = tt_ind_solve_power(
            effect_size=None,
            nobs1=n1,
            alpha=alpha,
            ratio=n2/n1,
            power=power
        )
    except Exception as e:
        logger.warning(f"MDES calculation failed: {e}")
        mdes = 0.0
    
    return {
        'observed_power': float(observed_power),
        'mdes': float(mdes)
    }

def run_sensitivity_analysis(p_value: float, thresholds: List[float] = [0.01, 0.04, 0.05, 0.06, 0.10]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by testing significance across thresholds.
    
    Args:
        p_value: The p-value to test
        thresholds: List of significance thresholds to test
        
    Returns:
        Dictionary with sensitivity results
    """
    results = {}
    for thresh in thresholds:
        results[f'sig_at_{thresh}'] = p_value < thresh
    
    # Check borderline range (0.04 <= p <= 0.06)
    is_borderline = 0.04 <= p_value <= 0.06
    results['is_sensitive_to_threshold'] = is_borderline
    
    return results

def run_analysis(df: pd.DataFrame, metric: str, group_col: str = 'stimulus_type', 
               group1_val: str = 'nostalgia', group2_val: str = 'control') -> Dict[str, Any]:
    """
    Run statistical analysis for a specific metric.
    
    Args:
        df: Cleaned dataframe
        metric: Column name for the metric (e.g., 'perseverative_errors')
        group_col: Column name for group assignment
        group1_val: Value for group 1 (nostalgia)
        group2_val: Value for group 2 (control)
        
    Returns:
        Dictionary with analysis results
    """
    group1 = df[df[group_col] == group1_val][metric]
    group2 = df[df[group_col] == group2_val][metric]
    
    if len(group1) == 0 or len(group2) == 0:
        raise ValueError(f"Empty group detected: group1={len(group1)}, group2={len(group2)}")
    
    try:
        t_stat, p_val = welch_t_test(group1, group2)
        cohens_d, ci_lower, ci_upper = calculate_effect_size_ci(group1, group2)
        power_mdes = calculate_power_and_mdes(group1, group2)
        sensitivity = run_sensitivity_analysis(p_val)
        
        return {
            'metric': metric,
            'group1_size': len(group1),
            'group2_size': len(group2),
            't_statistic': t_stat,
            'p_value': p_val,
            'cohens_d': cohens_d,
            'ci_95_lower': ci_lower,
            'ci_95_upper': ci_upper,
            'observed_power': power_mdes['observed_power'],
            'mdes': power_mdes['mdes'],
            'sensitivity': sensitivity
        }
    except ValueError as e:
        logger.error(f"Analysis failed for {metric}: {e}")
        return {
            'metric': metric,
            'error': str(e),
            'status': 'failed'
        }

def run_full_analysis(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run full analysis pipeline on the cleaned dataset.
    
    Args:
        input_path: Path to the cleaned dataset CSV
        output_path: Path to save the statistical report JSON
        
    Returns:
        Dictionary with full analysis results
        
    Raises:
        DataNotFoundError: If input file is missing or empty
    """
    # CRITICAL: Ensure we are reading from the real input file
    if not os.path.exists(input_path):
        logger.error(f"DataNotFoundError: Input file not found: {input_path}")
        raise DataNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        raise DataNotFoundError(f"Failed to read input file: {e}")
    
    if df.empty:
        logger.error(f"DataNotFoundError: Input file is empty: {input_path}")
        raise DataNotFoundError(f"Input file is empty: {input_path}")
    
    logger.info(f"Loaded dataset with {len(df)} rows from {input_path}")
    
    # Define metrics to analyze
    metrics = ['perseverative_errors', 'categories_completed']
    results = {}
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found in dataset, skipping")
            continue
        
        try:
            analysis_result = run_analysis(df, metric)
            results[metric] = analysis_result
        except Exception as e:
            logger.error(f"Failed to analyze {metric}: {e}")
            results[metric] = {'error': str(e), 'status': 'failed'}
    
    # Apply Bonferroni correction to p-values
    p_values = [results[m]['p_value'] for m in metrics if 'p_value' in results[m]]
    if p_values:
        corrected_p_values = bonferroni_correction(p_values)
        for i, metric in enumerate(metrics):
            if metric in results and 'p_value' in results[metric]:
                results[metric]['p_value_corrected'] = corrected_p_values[i]
    
    # Compile final report
    report = {
        'input_file': input_path,
        'total_records': len(df),
        'analysis_results': results,
        'metadata': {
            'timestamp': pd.Timestamp.now().isoformat(),
            'python_version': os.sys.version,
            'packages': {
                'pandas': pd.__version__,
                'scipy': stats.__version__,
                'numpy': np.__version__
            }
        }
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write report to file
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Analysis complete. Report saved to {output_path}")
    return report

def main():
    """Main entry point for the analysis script."""
    # Default paths
    input_path = 'data/processed/final_cleaned_dataset.csv'
    output_path = 'data/results/statistical_report.json'
    
    # Allow override via environment variables
    input_path = os.getenv('ANALYSIS_INPUT_PATH', input_path)
    output_path = os.getenv('ANALYSIS_OUTPUT_PATH', output_path)
    
    try:
        report = run_full_analysis(input_path, output_path)
        print(json.dumps(report, indent=2))
    except DataNotFoundError as e:
        logger.error(f"CRITICAL: {e}")
        print(json.dumps({'error': str(e), 'status': 'failed'}, indent=2))
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(json.dumps({'error': str(e), 'status': 'failed'}, indent=2))
        raise

if __name__ == '__main__':
    main()