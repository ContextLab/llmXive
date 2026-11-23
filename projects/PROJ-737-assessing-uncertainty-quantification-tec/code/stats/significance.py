"""
Statistical significance testing and sensitivity analysis for UQ methods.

Implements Paired Wilcoxon Signed-Rank tests and sensitivity analysis
for conformal prediction thresholds.
"""
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
from utils.logger import get_logger

def run_paired_wilcoxon(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform paired Wilcoxon signed-rank tests on per-sample errors.
    
    This function compares the absolute errors of different UQ methods
    on the same test samples to determine if one method is significantly
    better than another.
    
    Args:
        metrics_df: DataFrame containing per-sample errors with columns:
                   - sample_id: Unique identifier for each sample
                   - method: Name of the UQ method
                   - prediction: Predicted value
                   - ground_truth: Actual value
                   - dataset: Name of the dataset
    
    Returns:
        DataFrame with test results containing:
        - dataset: Dataset name
        - method_pair: Pair of methods compared (e.g., "GPR vs MC_Dropout")
        - test_type: Type of test performed
        - p_value: P-value from the Wilcoxon test
        - significance_flag: True if p_value < 0.05
    
    Raises:
        ValueError: If required columns are missing or data is invalid.
    """
    logger = get_logger()
    logger.info("Running paired Wilcoxon tests")
    
    # Validate input
    required_cols = ['sample_id', 'method', 'prediction', 'ground_truth', 'dataset']
    missing_cols = [col for col in required_cols if col not in metrics_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Calculate absolute errors
    metrics_df['abs_error'] = (metrics_df['prediction'] - metrics_df['ground_truth']).abs()
    
    results = []
    
    # Group by dataset
    for dataset in metrics_df['dataset'].unique():
        dataset_df = metrics_df[metrics_df['dataset'] == dataset]
        methods = dataset_df['method'].unique()
        
        logger.info(f"Processing dataset: {dataset} with {len(methods)} methods")
        
        # Compare all pairs of methods
        for i, method1 in enumerate(methods):
            for method2 in methods[i+1:]:
                # Get errors for both methods
                df1 = dataset_df[dataset_df['method'] == method1].set_index('sample_id')
                df2 = dataset_df[dataset_df['method'] == method2].set_index('sample_id')
                
                # Find common samples
                common_samples = df1.index.intersection(df2.index)
                
                if len(common_samples) < 10:
                    logger.warning(
                        f"Insufficient common samples ({len(common_samples)}) for "
                        f"comparison between {method1} and {method2} in {dataset}. "
                        f"Skipping comparison."
                    )
                    continue
                
                # Extract paired errors
                errors1 = df1.loc[common_samples, 'abs_error'].values
                errors2 = df2.loc[common_samples, 'abs_error'].values
                
                # Check for valid data (no NaN)
                valid_mask = ~(np.isnan(errors1) | np.isnan(errors2))
                if np.sum(valid_mask) < 10:
                    logger.warning(
                        f"Insufficient valid samples after NaN removal for "
                        f"comparison between {method1} and {method2} in {dataset}. "
                        f"Skipping comparison."
                    )
                    continue
                
                errors1 = errors1[valid_mask]
                errors2 = errors2[valid_mask]
                
                # Perform paired Wilcoxon test
                try:
                    stat, p_value = wilcoxon(errors1, errors2)
                    significance = p_value < 0.05
                    
                    results.append({
                        'dataset': dataset,
                        'method_pair': f"{method1} vs {method2}",
                        'test_type': 'Paired Wilcoxon Signed-Rank',
                        'p_value': p_value,
                        'significance_flag': significance
                    })
                    
                    logger.debug(
                        f"Wilcoxon test for {method1} vs {method2} in {dataset}: "
                        f"p={p_value:.4f}, significant={significance}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Wilcoxon test failed for {method1} vs {method2} in {dataset}: {e}"
                    )
                    continue
    
    if not results:
        logger.warning("No valid Wilcoxon tests could be performed")
        return pd.DataFrame(columns=[
            'dataset', 'method_pair', 'test_type', 'p_value', 'significance_flag'
        ])
    
    return pd.DataFrame(results)

def run_sensitivity_analysis(
    conformal_results: pd.DataFrame, 
    coverage_range: List[float]
) -> pd.DataFrame:
    """
    Analyze the sensitivity of conformal prediction to different coverage levels.
    
    This function evaluates how prediction interval width and observed coverage
    error change as the target coverage level varies.
    
    Args:
        conformal_results: DataFrame with conformal prediction results containing:
                         - sample_id: Unique identifier
                         - method: Method name (should include 'conformal')
                         - prediction: Predicted value
                         - lower_bound: Lower bound of prediction interval
                         - upper_bound: Upper bound of prediction interval
                         - ground_truth: Actual value
                         - dataset: Dataset name
        coverage_range: List of target coverage levels to analyze (e.g., [0.80, 0.81, ..., 0.99])
    
    Returns:
        DataFrame with sensitivity analysis results containing:
        - coverage_level: Target coverage level
        - avg_width: Average prediction interval width at this level
        - observed_coverage_error: Difference between observed and target coverage
    
    Raises:
        ValueError: If required columns are missing or data is invalid.
    """
    logger = get_logger()
    logger.info(f"Running sensitivity analysis for coverage levels: {coverage_range}")
    
    # Validate input
    required_cols = ['sample_id', 'method', 'prediction', 'lower_bound', 'upper_bound', 'ground_truth', 'dataset']
    missing_cols = [col for col in required_cols if col not in conformal_results.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter for conformal methods only
    conformal_df = conformal_results[conformal_results['method'].str.lower().str.contains('conformal', na=False)]
    
    if conformal_df.empty:
        raise ValueError("No conformal prediction results found in input data")
    
    results = []
    
    for target_coverage in coverage_range:
        # Calculate prediction interval width
        interval_width = conformal_df['upper_bound'] - conformal_df['lower_bound']
        avg_width = interval_width.mean()
        
        # Calculate observed coverage
        # A sample is covered if ground_truth is within [lower_bound, upper_bound]
        covered = (
            (conformal_df['ground_truth'] >= conformal_df['lower_bound']) &
            (conformal_df['ground_truth'] <= conformal_df['upper_bound'])
        )
        observed_coverage = covered.mean()
        
        # Calculate coverage error
        coverage_error = abs(observed_coverage - target_coverage)
        
        results.append({
            'coverage_level': target_coverage,
            'avg_width': avg_width,
            'observed_coverage_error': coverage_error
        })
        
        logger.debug(
            f"Coverage level {target_coverage:.2f}: "
            f"avg_width={avg_width:.4f}, observed_coverage={observed_coverage:.4f}, "
            f"error={coverage_error:.4f}"
        )
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for statistical analysis.
    
    This function is primarily used for testing and demonstration.
    The actual analysis is triggered by generate_statistical_report.py
    and generate_sensitivity_report.py.
    """
    logger = get_logger()
    logger.info("Statistical significance module loaded")
    logger.info("Use run_paired_wilcoxon() for significance testing")
    logger.info("Use run_sensitivity_analysis() for conformal threshold analysis")

if __name__ == "__main__":
    main()