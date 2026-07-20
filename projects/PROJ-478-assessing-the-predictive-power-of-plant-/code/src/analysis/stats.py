"""
Statistical analysis module for comparing SDM performance.

Implements:
- Paired two-sided t-test on AUC/TSS differences (FR-005)
- Bonferroni correction (FR-008)
- Cohen's d effect size calculation (SC-003)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List, Any
from scipy import stats
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_model_results(results_path: str) -> pd.DataFrame:
    """
    Load model results from a JSON/CSV file containing per-species metrics.
    
    Expected columns: 'species', 'auc_climate', 'auc_traits', 'tss_climate', 'tss_traits'
    """
    logger.info(f"Loading model results from {results_path}")
    
    if results_path.endswith('.csv'):
        df = pd.read_csv(results_path)
    elif results_path.endswith('.json'):
        df = pd.read_json(results_path)
    else:
        raise ValueError(f"Unsupported file format: {results_path}")
    
    required_cols = ['species', 'auc_climate', 'auc_traits', 'tss_climate', 'tss_traits']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in results file: {missing}")
    
    logger.info(f"Loaded {len(df)} species results")
    return df

def calculate_differences(df: pd.DataFrame, metric: str) -> pd.Series:
    """
    Calculate the difference between trait-augmented and climate-only models.
    
    Args:
        df: DataFrame with model results
        metric: Either 'auc' or 'tss'
    
    Returns:
        Series of differences (traits - climate)
    """
    diff_col = f"{metric}_diff"
    df[diff_col] = df[f"{metric}_traits"] - df[f"{metric}_climate"]
    return df[diff_col]

def paired_t_test(differences: pd.Series) -> Dict[str, float]:
    """
    Perform a paired two-sided t-test on the differences.
    
    Args:
        differences: Series of differences (traits - climate)
    
    Returns:
        Dictionary with t-statistic, p-value, and degrees of freedom
    """
    logger.info(f"Performing paired t-test on {len(differences)} differences")
    
    # Remove NaN values
    clean_diff = differences.dropna()
    
    if len(clean_diff) < 2:
        logger.warning("Insufficient data points for t-test (need at least 2)")
        return {
            't_statistic': np.nan,
            'p_value': np.nan,
            'df': len(clean_diff) - 1 if len(clean_diff) >= 1 else 0,
            'n': len(clean_diff)
        }
    
    # Two-sided t-test (testing if mean difference is different from 0)
    t_stat, p_value = stats.ttest_1samp(clean_diff, 0.0)
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'df': len(clean_diff) - 1,
        'n': len(clean_diff),
        'mean_diff': float(clean_diff.mean()),
        'std_diff': float(clean_diff.std())
    }

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of p-values to correct
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with corrected p-values and significance decisions
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {
            'corrected_p_values': [],
            'significant': [],
            'alpha_corrected': alpha,
            'n_tests': 0
        }
    
    # Bonferroni correction: multiply p-values by number of tests
    corrected_p = [min(p * n_tests, 1.0) for p in p_values]
    
    # Determine significance
    alpha_corrected = alpha / n_tests
    significant = [p < alpha_corrected for p in corrected_p]
    
    return {
        'corrected_p_values': corrected_p,
        'significant': significant,
        'alpha_corrected': alpha_corrected,
        'n_tests': n_tests,
        'original_p_values': p_values
    }

def calculate_cohen_d(differences: pd.Series) -> float:
    """
    Calculate Cohen's d effect size for the differences.
    
    Cohen's d = mean(differences) / std(differences)
    
    Args:
        differences: Series of differences
    
    Returns:
        Cohen's d value
    """
    clean_diff = differences.dropna()
    
    if len(clean_diff) < 2:
        logger.warning("Insufficient data points for Cohen's d calculation")
        return np.nan
    
    mean_diff = clean_diff.mean()
    std_diff = clean_diff.std()
    
    if std_diff == 0:
        logger.warning("Standard deviation is zero, cannot calculate Cohen's d")
        return np.nan
    
    return float(mean_diff / std_diff)

def interpret_effect_size(cohen_d: float) -> str:
    """
    Interpret Cohen's d effect size.
    
    Args:
        cohen_d: Cohen's d value
    
    Returns:
        String interpretation of the effect size
    """
    if np.isnan(cohen_d):
        return "undefined"
    
    abs_d = abs(cohen_d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def run_statistical_analysis(
    results_path: str,
    output_path: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.
    
    Performs:
    1. Load model results
    2. Calculate differences for AUC and TSS
    3. Paired t-tests for both metrics
    4. Bonferroni correction
    5. Cohen's d calculation
    
    Args:
        results_path: Path to the model results file (CSV or JSON)
        output_path: Path to save the stats report
        alpha: Significance level for Bonferroni correction
    
    Returns:
        Dictionary containing all analysis results
    """
    logger.info("Starting statistical analysis pipeline")
    
    # Load data
    df = load_model_results(results_path)
    
    # Calculate differences
    auc_diff = calculate_differences(df, 'auc')
    tss_diff = calculate_differences(df, 'tss')
    
    # Perform t-tests
    auc_test_result = paired_t_test(auc_diff)
    tss_test_result = paired_t_test(tss_diff)
    
    # Collect p-values for Bonferroni correction
    p_values = [auc_test_result['p_value'], tss_test_result['p_value']]
    bonferroni_result = bonferroni_correction(p_values, alpha)
    
    # Calculate Cohen's d
    cohen_d_auc = calculate_cohen_d(auc_diff)
    cohen_d_tss = calculate_cohen_d(tss_diff)
    
    # Interpret effect sizes
    effect_auc = interpret_effect_size(cohen_d_auc)
    effect_tss = interpret_effect_size(cohen_d_tss)
    
    # Compile results
    results = {
        'auc_analysis': {
            'mean_difference': auc_test_result['mean_diff'],
            'std_difference': auc_test_result['std_diff'],
            'n_samples': auc_test_result['n'],
            't_statistic': auc_test_result['t_statistic'],
            'p_value': auc_test_result['p_value'],
            'df': auc_test_result['df'],
            'corrected_p_value': bonferroni_result['corrected_p_values'][0],
            'is_significant': bonferroni_result['significant'][0],
            'cohen_d': cohen_d_auc,
            'effect_size_interpretation': effect_auc
        },
        'tss_analysis': {
            'mean_difference': tss_test_result['mean_diff'],
            'std_difference': tss_test_result['std_diff'],
            'n_samples': tss_test_result['n'],
            't_statistic': tss_test_result['t_statistic'],
            'p_value': tss_test_result['p_value'],
            'df': tss_test_result['df'],
            'corrected_p_value': bonferroni_result['corrected_p_values'][1],
            'is_significant': bonferroni_result['significant'][1],
            'cohen_d': cohen_d_tss,
            'effect_size_interpretation': effect_tss
        },
        'bonferroni_correction': {
            'alpha_original': alpha,
            'alpha_corrected': bonferroni_result['alpha_corrected'],
            'n_tests': bonferroni_result['n_tests'],
            'corrected_p_values': bonferroni_result['corrected_p_values'],
            'is_significant_any': any(bonferroni_result['significant'])
        },
        'summary': {
            'total_species': len(df),
            'species_with_valid_metrics': auc_test_result['n'],
            'auc_improvement_detected': auc_test_result['mean_diff'] > 0,
            'tss_improvement_detected': tss_test_result['mean_diff'] > 0,
            'auc_statistically_significant': bonferroni_result['significant'][0],
            'tss_statistically_significant': bonferroni_result['significant'][1]
        }
    }
    
    # Save results
    import json
    from pathlib import Path
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Statistical analysis complete. Results saved to {output_path}")
    logger.info(f"AUC: t={results['auc_analysis']['t_statistic']:.3f}, "
               f"p={results['auc_analysis']['p_value']:.4f}, "
               f"corrected_p={results['auc_analysis']['corrected_p_value']:.4f}, "
               f"Cohen's d={results['auc_analysis']['cohen_d']:.3f} ({effect_auc})")
    logger.info(f"TSS: t={results['tss_analysis']['t_statistic']:.3f}, "
               f"p={results['tss_analysis']['p_value']:.4f}, "
               f"corrected_p={results['tss_analysis']['corrected_p_value']:.4f}, "
               f"Cohen's d={results['tss_analysis']['cohen_d']:.3f} ({effect_tss})")
    
    return results

def main():
    """Main entry point for running the statistical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical analysis on SDM results')
    parser.add_argument('--input', type=str, required=True,
                      help='Path to model results file (CSV or JSON)')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to save stats report (JSON)')
    parser.add_argument('--alpha', type=float, default=0.05,
                      help='Significance level for Bonferroni correction')
    
    args = parser.parse_args()
    
    setup_logging()
    results = run_statistical_analysis(args.input, args.output, args.alpha)
    
    print("\n=== Statistical Analysis Results ===")
    print(f"AUC: Mean Diff = {results['auc_analysis']['mean_difference']:.4f}, "
          f"t = {results['auc_analysis']['t_statistic']:.4f}, "
          f"p = {results['auc_analysis']['p_value']:.4f}, "
          f"Bonferroni-corrected p = {results['auc_analysis']['corrected_p_value']:.4f}, "
          f"Cohen's d = {results['auc_analysis']['cohen_d']:.4f} ({results['auc_analysis']['effect_size_interpretation']})")
    print(f"TSS: Mean Diff = {results['tss_analysis']['mean_difference']:.4f}, "
          f"t = {results['tss_analysis']['t_statistic']:.4f}, "
          f"p = {results['tss_analysis']['p_value']:.4f}, "
          f"Bonferroni-corrected p = {results['tss_analysis']['corrected_p_value']:.4f}, "
          f"Cohen's d = {results['tss_analysis']['cohen_d']:.4f} ({results['tss_analysis']['effect_size_interpretation']})")
    print(f"\nSignificance (Bonferroni-corrected α={results['bonferroni_correction']['alpha_corrected']:.4f}):")
    print(f"  AUC: {'SIGNIFICANT' if results['auc_analysis']['is_significant'] else 'NOT significant'}")
    print(f"  TSS: {'SIGNIFICANT' if results['tss_analysis']['is_significant'] else 'NOT significant'}")

if __name__ == '__main__':
    main()
