"""
analysis.py: Statistical analysis for User Story 1 (Zero-Shot Adaptation).

Performs paired t-test on aggregated evaluation data to verify:
1. Statistical significance (p < 0.05)
2. Practical significance (>15% improvement in success rate)
3. Statistical power (effect size validation)

Input: Aggregated CSV from aggregate.py (data/results/evaluation_results.csv)
Output: Analysis report and summary statistics
"""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_aggregated_data(csv_path: str) -> pd.DataFrame:
    """
    Load aggregated evaluation results from CSV.
    
    Args:
        csv_path: Path to the aggregated CSV file
        
    Returns:
        DataFrame with columns: object_id, policy_type, success_rate
        
    Raises:
        FileNotFoundError: If CSV doesn't exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Aggregated data not found at {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    required_cols = ['object_id', 'policy_type', 'success_rate']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} records from {csv_path}")
    return df

def prepare_paired_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare paired data for t-test by splitting adaptive vs static policies.
    
    Args:
        df: DataFrame with object_id, policy_type, success_rate
        
    Returns:
        Tuple of (adaptive_rates, static_rates) arrays, paired by object_id
        
    Raises:
        ValueError: If pairing is incomplete or data is invalid
    """
    # Pivot to get paired data
    pivot_df = df.pivot(index='object_id', columns='policy_type', values='success_rate')
    
    # Check for completeness
    if pivot_df.isnull().any().any():
        incomplete_objects = pivot_df[pivot_df.isnull().any(axis=1)].index.tolist()
        raise ValueError(
            f"Incomplete pairing for objects: {incomplete_objects}. "
            "Each object must have both adaptive and static results."
        )
    
    adaptive_rates = pivot_df['adaptive'].values
    static_rates = pivot_df['static'].values
    
    logger.info(f"Prepared {len(adaptive_rates)} paired observations")
    return adaptive_rates, static_rates

def perform_paired_ttest(adaptive: np.ndarray, static: np.ndarray) -> Dict[str, float]:
    """
    Perform paired t-test on adaptive vs static success rates.
    
    Args:
        adaptive: Array of adaptive policy success rates
        static: Array of static policy success rates
        
    Returns:
        Dictionary with t-statistic, p-value, and confidence interval
    """
    # Paired t-test
    t_stat, p_value = stats.ttest_rel(static, adaptive)
    
    # Calculate effect size (Cohen's d for paired samples)
    diff = adaptive - static
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    
    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff
    
    # Calculate 95% confidence interval for mean difference
    n = len(diff)
    mean_diff = np.mean(diff)
    sem = stats.sem(diff)
    confidence_level = 0.95
    dof = n - 1
    t_crit = stats.t.ppf((1 + confidence_level) / 2, dof)
    ci_lower = mean_diff - t_crit * sem
    ci_upper = mean_diff + t_crit * sem
    
    result = {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'mean_difference': float(mean_diff),
        'cohens_d': float(cohens_d),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'n_samples': n
    }
    
    logger.info(f"T-test: t={t_stat:.4f}, p={p_value:.4f}, d={cohens_d:.4f}")
    return result

def calculate_statistical_power(
    effect_size: float, 
    n_samples: int, 
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for the observed effect size.
    
    Args:
        effect_size: Cohen's d
        n_samples: Number of paired observations
        alpha: Significance level
        
    Returns:
        Statistical power (probability of detecting effect if it exists)
    """
    from statsmodels.stats.power import TTestPower
    
    power_analysis = TTestPower()
    power = power_analysis.solve_power(
        effect_size=abs(effect_size),
        nobs1=n_samples,
        alpha=alpha,
        alternative='larger'
    )
    
    return float(power)

def verify_improvement_threshold(
    mean_diff: float, 
    threshold: float = 0.15
) -> Tuple[bool, float]:
    """
    Verify if improvement exceeds the required threshold.
    
    Args:
        mean_diff: Mean difference in success rates (adaptive - static)
        threshold: Required improvement threshold (default 0.15 = 15%)
        
    Returns:
        Tuple of (passes_threshold, actual_improvement_percentage)
    """
    improvement_pct = mean_diff * 100  # Convert to percentage
    passes = mean_diff >= threshold
    return passes, improvement_pct

def generate_analysis_report(
    ttest_results: Dict[str, float],
    power: float,
    threshold_pass: bool,
    improvement_pct: float,
    output_path: str
) -> None:
    """
    Generate and save a comprehensive analysis report.
    
    Args:
        ttest_results: Dictionary from perform_paired_ttest
        power: Statistical power value
        threshold_pass: Whether improvement exceeds threshold
        improvement_pct: Actual improvement percentage
        output_path: Path to save the report
    """
    report_lines = [
        "=" * 60,
        "ZERO-SHOT ADAPTATION ANALYSIS REPORT",
        "=" * 60,
        "",
        "STATISTICAL TEST RESULTS",
        "-" * 40,
        f"Sample Size (n): {ttest_results['n_samples']}",
        f"T-statistic: {ttest_results['t_statistic']:.4f}",
        f"P-value: {ttest_results['p_value']:.6f}",
        f"Mean Difference (adaptive - static): {ttest_results['mean_difference']:.4f} ({ttest_results['mean_difference']*100:.2f}%)",
        f"Cohen's d (Effect Size): {ttest_results['cohens_d']:.4f}",
        f"95% CI: [{ttest_results['ci_lower']:.4f}, {ttest_results['ci_upper']:.4f}]",
        "",
        "STATISTICAL POWER",
        "-" * 40,
        f"Calculated Power: {power:.4f}",
        f"Target Power: 0.80",
        f"Power Sufficient: {'Yes' if power >= 0.80 else 'No (consider larger sample)'}",
        "",
        "THRESHOLD VERIFICATION",
        "-" * 40,
        f"Required Improvement: >15%",
        f"Actual Improvement: {improvement_pct:.2f}%",
        f"Threshold Passed: {'Yes' if threshold_pass else 'No'}",
        "",
        "SIGNIFICANCE VERIFICATION",
        "-" * 40,
        f"P < 0.05: {'Yes' if ttest_results['p_value'] < 0.05 else 'No'}",
        f"Improvement >15%: {'Yes' if threshold_pass else 'No'}",
        "",
        "CONCLUSION",
        "-" * 40,
    ]
    
    # Determine overall conclusion
    if ttest_results['p_value'] < 0.05 and threshold_pass:
        conclusion = "SUCCESS: Adaptive policy shows statistically significant (>0.05) and practically significant (>15%) improvement over static baseline."
    elif ttest_results['p_value'] < 0.05:
        conclusion = "PARTIAL: Statistically significant improvement detected, but practical threshold (>15%) not met."
    elif threshold_pass:
        conclusion = "PARTIAL: Practical improvement detected (>15%), but not statistically significant (p >= 0.05)."
    else:
        conclusion = "FAILURE: No significant improvement detected. Adaptive policy does not outperform static baseline."
    
    report_lines.append(conclusion)
    report_lines.append("=" * 60)
    
    report_text = "\n".join(report_lines)
    
    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Report saved to {output_path}")
    print(report_text)

def run_analysis(
    input_csv: str,
    output_report: str,
    significance_level: float = 0.05,
    improvement_threshold: float = 0.15
) -> Dict[str, Any]:
    """
    Main analysis pipeline.
    
    Args:
        input_csv: Path to aggregated CSV
        output_report: Path for output report
        significance_level: Alpha for t-test
        improvement_threshold: Required improvement percentage
        
    Returns:
        Dictionary with all analysis results
    """
    # Load data
    df = load_aggregated_data(input_csv)
    
    # Prepare paired data
    adaptive_rates, static_rates = prepare_paired_data(df)
    
    # Perform t-test
    ttest_results = perform_paired_ttest(adaptive_rates, static_rates)
    
    # Calculate power
    power = calculate_statistical_power(
        ttest_results['cohens_d'],
        ttest_results['n_samples']
    )
    
    # Verify thresholds
    threshold_pass, improvement_pct = verify_improvement_threshold(
        ttest_results['mean_difference'],
        improvement_threshold
    )
    
    # Generate report
    generate_analysis_report(
        ttest_results,
        power,
        threshold_pass,
        improvement_pct,
        output_report
    )
    
    return {
        'ttest': ttest_results,
        'power': power,
        'threshold_pass': threshold_pass,
        'improvement_pct': improvement_pct,
        'significant': ttest_results['p_value'] < significance_level,
        'meets_requirements': ttest_results['p_value'] < significance_level and threshold_pass
    }

def main():
    """CLI entry point for analysis."""
    parser = argparse.ArgumentParser(
        description='Analyze zero-shot adaptation results with paired t-test'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/results/evaluation_results.csv',
        help='Path to aggregated CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/analysis_report.txt',
        help='Path for output report'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level for t-test'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.15,
        help='Required improvement threshold (default: 0.15 = 15%%)'
    )
    
    args = parser.parse_args()
    
    try:
        results = run_analysis(
            input_csv=args.input,
            output_report=args.output,
            significance_level=args.alpha,
            improvement_threshold=args.threshold
        )
        
        # Exit with appropriate code
        if results['meets_requirements']:
            logger.info("Analysis PASSED: All requirements met.")
            sys.exit(0)
        else:
            logger.warning("Analysis FAILED: Requirements not met.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(4)

if __name__ == '__main__':
    main()