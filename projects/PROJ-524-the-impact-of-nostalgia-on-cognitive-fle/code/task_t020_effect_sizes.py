"""
Task T020: Calculate and report Cohen's d with 95% confidence intervals.

Implements effect size calculation for the nostalgia vs control comparison
on WCST metrics (perseverative_errors, categories_completed).
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List
from scipy import stats
from statsmodels.stats.weightstats import zconfint
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataNotFoundError(Exception):
    """Raised when required input data file is missing."""
    pass

def load_cleaned_dataset() -> pd.DataFrame:
    """
    Load the final cleaned dataset from the processed directory.
    
    Returns:
        pd.DataFrame: The cleaned dataset containing WCST metrics.
        
    Raises:
        DataNotFoundError: If the file does not exist or is empty.
    """
    config = get_config()
    input_path = config['paths']['cleaned_dataset']
    
    if not os.path.exists(input_path):
        raise DataNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise DataNotFoundError(f"Input file is empty: {input_path}")
    
    required_cols = ['stimulus_type', 'perseverative_errors', 'categories_completed']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise DataNotFoundError(f"Missing required columns in {input_path}: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size for two independent groups.
    
    Cohen's d = (mean1 - mean2) / pooled_std
    where pooled_std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1+n2-2))
    
    Args:
        group1: Array of values for group 1 (e.g., nostalgia)
        group2: Array of values for group 2 (e.g., control)
        
    Returns:
        float: Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        logger.warning("Sample size too small for effect size calculation")
        return np.nan
        
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero, cannot calculate Cohen's d")
        return np.nan
        
    return (mean1 - mean2) / pooled_std

def calculate_effect_size_ci(group1: np.ndarray, group2: np.ndarray, 
                             d: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for Cohen's d.
    
    Uses the non-central t-distribution approximation or the standard error method.
    SE_d ≈ sqrt((n1+n2)/(n1*n2) + d^2/(2*(n1+n2)))
    
    Args:
        group1: Array of values for group 1
        group2: Array of values for group 2
        d: The calculated Cohen's d
        alpha: Significance level (default 0.05 for 95% CI)
        
    Returns:
        Tuple[float, float]: (lower_bound, upper_bound)
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return (np.nan, np.nan)
        
    # Standard error of Cohen's d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    
    # Critical value for normal distribution (approximation for large samples)
    # For small samples, a non-central t-distribution would be more accurate,
    # but this approximation is standard for effect size reporting
    z_critical = stats.norm.ppf(1 - alpha/2)
    
    lower = d - z_critical * se_d
    upper = d + z_critical * se_d
    
    return (lower, upper)

def run_effect_size_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run effect size analysis for all primary comparisons.
    
    Calculates Cohen's d and 95% CI for:
    - perseverative_errors (nostalgia vs control)
    - categories_completed (nostalgia vs control)
    
    Args:
        df: Cleaned dataset with stimulus_type, perseverative_errors, categories_completed
        
    Returns:
        Dict[str, Any]: Dictionary containing effect sizes and confidence intervals
    """
    logger.info("Starting effect size analysis")
    
    # Split data by stimulus type
    # Ensure we have both groups
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']
    control_group = df[df['stimulus_type'] == 'control']
    
    if nostalgia_group.empty:
        raise ValueError("No nostalgia group found in data")
    if control_group.empty:
        raise ValueError("No control group found in data")
        
    logger.info(f"Group sizes - Nostalgia: {len(nostalgia_group)}, Control: {len(control_group)}")
    
    results = {}
    
    # Analyze perseverative_errors
    logger.info("Calculating effect size for perseverative_errors")
    pe_nostalgia = nostalgia_group['perseverative_errors'].dropna().values
    pe_control = control_group['perseverative_errors'].dropna().values
    
    if len(pe_nostalgia) > 0 and len(pe_control) > 0:
        d_pe = calculate_cohen_d(pe_nostalgia, pe_control)
        ci_pe = calculate_effect_size_ci(pe_nostalgia, pe_control, d_pe)
        
        results['perseverative_errors'] = {
            'cohen_d': float(d_pe),
            'ci_95_lower': float(ci_pe[0]),
            'ci_95_upper': float(ci_pe[1]),
            'n_nostalgia': len(pe_nostalgia),
            'n_control': len(pe_control),
            'mean_nostalgia': float(np.mean(pe_nostalgia)),
            'mean_control': float(np.mean(pe_control)),
            'std_nostalgia': float(np.std(pe_nostalgia, ddof=1)),
            'std_control': float(np.std(pe_control, ddof=1))
        }
    else:
        logger.warning("Insufficient data for perseverative_errors analysis")
        results['perseverative_errors'] = {
            'cohen_d': None,
            'ci_95_lower': None,
            'ci_95_upper': None,
            'error': "Insufficient data"
        }
        
    # Analyze categories_completed
    logger.info("Calculating effect size for categories_completed")
    cc_nostalgia = nostalgia_group['categories_completed'].dropna().values
    cc_control = control_group['categories_completed'].dropna().values
    
    if len(cc_nostalgia) > 0 and len(cc_control) > 0:
        d_cc = calculate_cohen_d(cc_nostalgia, cc_control)
        ci_cc = calculate_effect_size_ci(cc_nostalgia, cc_control, d_cc)
        
        results['categories_completed'] = {
            'cohen_d': float(d_cc),
            'ci_95_lower': float(ci_cc[0]),
            'ci_95_upper': float(ci_cc[1]),
            'n_nostalgia': len(cc_nostalgia),
            'n_control': len(cc_control),
            'mean_nostalgia': float(np.mean(cc_nostalgia)),
            'mean_control': float(np.mean(cc_control)),
            'std_nostalgia': float(np.std(cc_nostalgia, ddof=1)),
            'std_control': float(np.std(cc_control, ddof=1))
        }
    else:
        logger.warning("Insufficient data for categories_completed analysis")
        results['categories_completed'] = {
            'cohen_d': None,
            'ci_95_lower': None,
            'ci_95_upper': None,
            'error': "Insufficient data"
        }
        
    logger.info("Effect size analysis completed")
    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save effect size results to a JSON file.
    
    Args:
        results: Dictionary containing effect size analysis results
        output_path: Path to save the JSON file
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for Task T020."""
    logger.info("Starting Task T020: Effect Size Calculation")
    
    try:
        # Load data
        df = load_cleaned_dataset()
        
        # Run analysis
        results = run_effect_size_analysis(df)
        
        # Determine output path
        config = get_config()
        output_path = config['paths']['effect_size_results']
        
        # Save results
        save_results(results, output_path)
        
        logger.info("Task T020 completed successfully")
        
        # Print summary
        print("\n=== Effect Size Summary ===")
        for metric, data in results.items():
            if data.get('cohen_d') is not None:
                print(f"{metric}:")
                print(f"  Cohen's d = {data['cohen_d']:.4f}")
                print(f"  95% CI = [{data['ci_95_lower']:.4f}, {data['ci_95_upper']:.4f}]")
            else:
                print(f"{metric}: Unable to calculate (insufficient data)")
                
    except DataNotFoundError as e:
        logger.error(f"Data error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
