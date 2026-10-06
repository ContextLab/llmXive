"""
Statistical Analysis Module for Nostalgia and Cognitive Flexibility Study.

This module implements Welch's t-test, effect size calculations, and
statistical reporting for the comparison between nostalgia and control groups.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import TTestIndPower
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataNotFoundError(Exception):
    """Raised when required data files are not found."""
    pass

def get_config_paths() -> Dict[str, str]:
    """
    Get file paths from environment or defaults.
    
    Returns:
        Dict containing 'root', 'processed', and 'results' paths.
    """
    root = os.environ.get('PROJECT_ROOT', str(Path.cwd()))
    return {
        'root': root,
        'processed': os.path.join(root, 'data', 'processed'),
        'results': os.path.join(root, 'data', 'results'),
        'input_file': os.path.join(root, 'data', 'processed', 'final_cleaned_dataset.csv')
    }

def load_cleaned_dataset(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the cleaned dataset from disk.
    
    Args:
        filepath: Optional path to the dataset. If None, uses default path.
        
    Returns:
        DataFrame with cleaned data.
        
    Raises:
        DataNotFoundError: If the file does not exist.
    """
    if filepath is None:
        paths = get_config_paths()
        filepath = paths['input_file']
    
    if not os.path.exists(filepath):
        raise DataNotFoundError(f"Cleaned dataset not found at {filepath}")
    
    logger.info(f"Loading cleaned dataset from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} records")
    return df

def split_by_stimulus_type(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset by stimulus type (nostalgia vs control).
    
    Args:
        df: Input DataFrame with 'stimulus_type' column.
        
    Returns:
        Tuple of (nostalgia_group, control_group) DataFrames.
        
    Raises:
        ValueError: If stimulus_type column is missing or groups are empty.
    """
    if 'stimulus_type' not in df.columns:
        raise ValueError("Column 'stimulus_type' not found in dataset")
    
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia'].copy()
    control_group = df[df['stimulus_type'] == 'control'].copy()
    
    if len(nostalgia_group) == 0:
        raise ValueError("No records found for nostalgia group")
    if len(control_group) == 0:
        raise ValueError("No records found for control group")
    
    logger.info(f"Split data: Nostalgia (n={len(nostalgia_group)}), Control (n={len(control_group)})")
    return nostalgia_group, control_group

def save_grouped_data(nostalgia_group: pd.DataFrame, control_group: pd.DataFrame, 
                     output_path: str) -> None:
    """
    Save grouped data to JSON file.
    
    Args:
        nostalgia_group: Nostalgia group DataFrame.
        control_group: Control group DataFrame.
        output_path: Path to save the grouped data.
    """
    grouped_data = {
        'nostalgia': nostalgia_group.to_dict(orient='records'),
        'control': control_group.to_dict(orient='records')
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(grouped_data, f, indent=2)
    
    logger.info(f"Saved grouped data to {output_path}")

def welch_t_test(group1: pd.Series, group2: pd.Series) -> Tuple[float, float]:
    """
    Perform Welch's independent samples t-test.
    
    This is the recommended test for comparing two independent groups
    with potentially unequal variances and sample sizes.
    
    Args:
        group1: Series of values for group 1 (nostalgia).
        group2: Series of values for group 2 (control).
        
    Returns:
        Tuple of (t_statistic, p_value).
    """
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    return t_stat, p_val

def bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of corrected p-values.
    """
    n_tests = len(p_values)
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def calculate_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: Series of values for group 1.
        group2: Series of values for group 2.
        
    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero, returning 0 for Cohen's d")
        return 0.0
    
    cohens_d = (mean1 - mean2) / pooled_std
    return cohens_d

def calculate_effect_size_ci(group1: pd.Series, group2: pd.Series, 
                            alpha: float = 0.05) -> Tuple[float, float, float]:
    """
    Calculate Cohen's d with 95% confidence interval.
    
    Args:
        group1: Series of values for group 1.
        group2: Series of values for group 2.
        alpha: Significance level (default 0.05 for 95% CI).
        
    Returns:
        Tuple of (cohens_d, ci_lower, ci_upper).
    """
    d = calculate_cohen_d(group1, group2)
    n1, n2 = len(group1), len(group2)
    
    # Standard error of Cohen's d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d ** 2) / (2 * (n1 + n2)))
    
    # Critical value for 95% CI
    z_critical = stats.norm.ppf(1 - alpha / 2)
    
    ci_lower = d - z_critical * se_d
    ci_upper = d + z_critical * se_d
    
    return d, ci_lower, ci_upper

def calculate_power_and_mdes(group1: pd.Series, group2: pd.Series, 
                             alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    
    Args:
        group1: Series of values for group 1.
        group2: Series of values for group 2.
        alpha: Significance level.
        
    Returns:
        Dictionary with power and MDES values.
    """
    n1, n2 = len(group1), len(group2)
    d = calculate_cohen_d(group1, group2)
    
    # Calculate power
    power_analysis = TTestIndPower()
    power = power_analysis.power(effect_size=abs(d), nobs1=n1, alpha=alpha, ratio=n2/n1)
    
    # Calculate MDES for 80% power
    mdes = power_analysis.solve_power(power=0.8, nobs1=n1, alpha=alpha, ratio=n2/n1)
    
    return {
        'statistical_power': float(power),
        'minimum_detectable_effect_size': float(mdes),
        'alpha': alpha,
        'sample_size_nostalgia': n1,
        'sample_size_control': n2
    }

def run_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.
    
    Args:
        df: Cleaned DataFrame with stimulus_type column.
        
    Returns:
        Dictionary containing all statistical results.
    """
    nostalgia_group, control_group = split_by_stimulus_type(df)
    
    metrics = ['perseverative_errors', 'categories_completed']
    results = {
        'report_metadata': {
            'task_id': 'T018',
            'description': 'Welch\'s t-test analysis',
            'analysis_method': "Welch's independent samples t-test",
            'correction_method': 'Bonferroni'
        },
        'comparisons': []
    }
    
    raw_p_values = []
    
    for metric in metrics:
        if metric not in nostalgia_group.columns or metric not in control_group.columns:
            logger.warning(f"Metric {metric} not found in dataset, skipping")
            continue
        
        group1_vals = nostalgia_group[metric]
        group2_vals = control_group[metric]
        
        # Check for zero variance
        if group1_vals.var(ddof=1) == 0 and group2_vals.var(ddof=1) == 0:
            logger.warning(f"Zero variance in both groups for {metric}, skipping")
            continue
        
        # Perform Welch's t-test
        t_stat, p_val = welch_t_test(group1_vals, group2_vals)
        raw_p_values.append(p_val)
        
        # Calculate effect size
        cohens_d, ci_lower, ci_upper = calculate_effect_size_ci(group1_vals, group2_vals)
        
        # Calculate power and MDES
        power_results = calculate_power_and_mdes(group1_vals, group2_vals)
        
        comparison = {
            'metric': metric,
            'group_nostalgia': {
                'n': len(group1_vals),
                'mean': float(group1_vals.mean()),
                'std': float(group1_vals.std(ddof=1))
            },
            'group_control': {
                'n': len(group2_vals),
                'mean': float(group2_vals.mean()),
                'std': float(group2_vals.std(ddof=1))
            },
            't_statistic': float(t_stat),
            'p_value_raw': float(p_val),
            'effect_size': {
                'cohen_d': float(cohens_d),
                'ci_95_lower': float(ci_lower),
                'ci_95_upper': float(ci_upper)
            },
            'power_analysis': power_results
        }
        results['comparisons'].append(comparison)
    
    # Apply Bonferroni correction
    corrected_p_values = bonferroni_correction(raw_p_values)
    results['p_values'] = raw_p_values
    results['t_statistics'] = [comp['t_statistic'] for comp in results['comparisons']]
    results['corrected_p_values'] = corrected_p_values
    
    # Update comparisons with corrected p-values
    for i, comp in enumerate(results['comparisons']):
        comp['p_value_corrected'] = corrected_p_values[i]
    
    # Summary
    significant_at_05 = sum(1 for p in corrected_p_values if p < 0.05)
    significant_at_01 = sum(1 for p in corrected_p_values if p < 0.01)
    avg_power = np.mean([comp['power_analysis']['statistical_power'] for comp in results['comparisons']])
    avg_mdes = np.mean([comp['power_analysis']['minimum_detectable_effect_size'] for comp in results['comparisons']])
    
    results['summary'] = {
        'total_comparisons': len(results['comparisons']),
        'significant_at_alpha_05': significant_at_05,
        'significant_at_alpha_01': significant_at_01,
        'average_power': float(avg_power),
        'average_mdes': float(avg_mdes)
    }
    
    return results

def save_report(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical results to JSON file.
    
    Args:
        results: Dictionary containing statistical results.
        output_path: Path to save the report.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved statistical report to {output_path}")

def run_full_analysis(input_path: Optional[str] = None, 
                     output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full analysis pipeline from input file to output report.
    
    Args:
        input_path: Path to cleaned dataset. If None, uses default.
        output_path: Path to save report. If None, uses default.
        
    Returns:
        Dictionary containing all statistical results.
    """
    paths = get_config_paths()
    
    if input_path is None:
        input_path = paths['input_file']
    if output_path is None:
        output_path = os.path.join(paths['results'], 'statistical_report.json')
    
    # Load data
    df = load_cleaned_dataset(input_path)
    
    # Run analysis
    results = run_analysis(df)
    
    # Save report
    save_report(results, output_path)
    
    return results

def main():
    """Main entry point for the analysis script."""
    try:
        logger.info("Starting statistical analysis (T018: Welch's t-test)")
        results = run_full_analysis()
        logger.info("Analysis completed successfully")
        logger.info(f"Results saved to {os.path.join(get_config_paths()['results'], 'statistical_report.json')}")
        return 0
    except DataNotFoundError as e:
        logger.error(f"Data Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())