"""
Statistical significance testing module for uncertainty quantification assessment.

Implements Paired Wilcoxon Signed-Rank tests as mandated by FR-004 (amended).
"""
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

from utils.logger import get_logger

logger = get_logger(__name__)

def run_paired_wilcoxon(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform paired Wilcoxon signed-rank tests on per-sample errors for method pairs.
    
    This function implements the statistical contract required by FR-004 (amended).
    It compares methods on the SAME test set (paired design), not independent samples.
    
    Args:
        metrics_df: DataFrame with columns:
            - sample_id: Unique identifier for each sample
            - method: Name of the UQ method
            - prediction: Predicted value
            - ground_truth: Actual value
            - dataset: Dataset name
        
    Returns:
        DataFrame with statistical test results:
            - dataset: Dataset name
            - method_pair: String representation of the pair (e.g., "GPR vs MC_Dropout")
            - statistic: Wilcoxon test statistic
            - p_value: Two-sided p-value
            - significant: Boolean flag (True if p < 0.05)
    
    Raises:
        ValueError: If required columns are missing or if paired data cannot be constructed
        RuntimeError: If statistical test fails for any method pair
    """
    required_columns = {'sample_id', 'method', 'prediction', 'ground_truth', 'dataset'}
    if not required_columns.issubset(metrics_df.columns):
        missing = required_columns - set(metrics_df.columns)
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"DataFrame missing required columns: {missing}")
    
    # Calculate absolute errors (or signed errors, depending on test requirement)
    # For Wilcoxon signed-rank, we typically use signed differences
    metrics_df = metrics_df.copy()
    metrics_df['error'] = metrics_df['prediction'] - metrics_df['ground_truth']
    
    results = []
    
    # Group by dataset
    for dataset_name, dataset_df in metrics_df.groupby('dataset'):
        logger.info(f"Processing dataset: {dataset_name}")
        
        # Check minimum sample size (per spec assumptions)
        n_samples = len(dataset_df['sample_id'].unique())
        if n_samples < 100:
            logger.warning(f"Dataset {dataset_name} has only {n_samples} samples. "
                         "Results may be inconclusive.")
        
        methods = dataset_df['method'].unique()
        logger.info(f"Found {len(methods)} methods: {methods}")
        
        # Generate all unique pairs of methods
        for i in range(len(methods)):
            for j in range(i + 1, len(methods)):
                method_a = methods[i]
                method_b = methods[j]
                
                # Filter data for each method
                df_a = dataset_df[dataset_df['method'] == method_a].set_index('sample_id')
                df_b = dataset_df[dataset_df['method'] == method_b].set_index('sample_id')
                
                # Find common samples (should be all if same test set)
                common_samples = df_a.index.intersection(df_b.index)
                
                if len(common_samples) < 10:
                    logger.warning(f"Not enough common samples ({len(common_samples)}) "
                                 f"for {method_a} vs {method_b} in {dataset_name}. Skipping.")
                    continue
                
                # Extract paired errors
                errors_a = df_a.loc[common_samples, 'error'].values
                errors_b = df_b.loc[common_samples, 'error'].values
                
                # Calculate differences (paired design)
                differences = errors_a - errors_b
                
                # Remove zero differences (Wilcoxon requirement)
                non_zero_mask = differences != 0
                if np.sum(non_zero_mask) < 10:
                    logger.warning(f"Too many zero differences for {method_a} vs {method_b}. "
                                 "Skipping test.")
                    continue
                
                differences = differences[non_zero_mask]
                
                try:
                    # Perform paired Wilcoxon signed-rank test
                    statistic, p_value = wilcoxon(differences, zero_method='wilcox')
                    
                    result = {
                        'dataset': dataset_name,
                        'method_pair': f"{method_a} vs {method_b}",
                        'statistic': statistic,
                        'p_value': p_value,
                        'significant': p_value < 0.05,
                        'n_samples': len(differences)
                    }
                    results.append(result)
                    
                    logger.info(f"Wilcoxon test for {dataset_name}: "
                              f"{method_a} vs {method_b} -> p={p_value:.4f}, "
                              f"significant={result['significant']}")
                    
                except Exception as e:
                    logger.error(f"Wilcoxon test failed for {method_a} vs {method_b} in "
                               f"{dataset_name}: {str(e)}")
                    raise RuntimeError(f"Statistical test failed: {str(e)}") from e
    
    if not results:
        logger.warning("No valid statistical tests were performed. Check data quality.")
        return pd.DataFrame(columns=['dataset', 'method_pair', 'statistic', 'p_value', 
                                   'significant', 'n_samples'])
    
    results_df = pd.DataFrame(results)
    logger.info(f"Completed {len(results)} paired Wilcoxon tests.")
    return results_df

def run_sensitivity_analysis(conformal_results: pd.DataFrame, 
                           coverage_range: Tuple[float, float] = (0.80, 0.99),
                           step_size: float = 0.01) -> pd.DataFrame:
    """
    Perform sensitivity analysis on conformal prediction thresholds.
    
    Sweeps coverage levels and reports width/error trade-offs.
    
    Args:
        conformal_results: DataFrame with conformal prediction results
        coverage_range: Tuple of (min_coverage, max_coverage)
        step_size: Step size for coverage sweep
        
    Returns:
        DataFrame with sensitivity analysis results:
            - coverage_level: Target coverage level
            - avg_width: Average prediction interval width
            - observed_coverage: Actual coverage achieved
            - coverage_error: Difference between target and observed
    """
    logger.info("Starting sensitivity analysis for conformal predictions")
    
    coverage_levels = np.arange(coverage_range[0], coverage_range[1] + step_size, step_size)
    results = []
    
    for target_coverage in coverage_levels:
        # Filter results for this coverage level (assuming conformal_results has coverage column)
        if 'coverage_level' in conformal_results.columns:
            subset = conformal_results[conformal_results['coverage_level'] >= target_coverage - 0.005]
        else:
            # If coverage_level not present, use all data and calculate
            subset = conformal_results
        
        if len(subset) == 0:
            logger.warning(f"No data for coverage level {target_coverage:.2f}")
            continue
        
        # Calculate average interval width
        if 'interval_width' in subset.columns:
            avg_width = subset['interval_width'].mean()
        else:
            # Calculate from bounds if available
            if 'upper_bound' in subset.columns and 'lower_bound' in subset.columns:
                widths = subset['upper_bound'] - subset['lower_bound']
                avg_width = widths.mean()
            else:
                logger.warning("Cannot calculate interval width: missing required columns")
                continue
        
        # Calculate observed coverage
        if 'ground_truth' in subset.columns and 'lower_bound' in subset.columns and 'upper_bound' in subset.columns:
            within_bounds = (subset['ground_truth'] >= subset['lower_bound']) & \
                          (subset['ground_truth'] <= subset['upper_bound'])
            observed_coverage = within_bounds.mean()
        else:
            logger.warning("Cannot calculate observed coverage: missing required columns")
            continue
        
        coverage_error = abs(observed_coverage - target_coverage)
        
        results.append({
            'coverage_level': target_coverage,
            'avg_width': avg_width,
            'observed_coverage': observed_coverage,
            'coverage_error': coverage_error
        })
    
    if not results:
        logger.warning("Sensitivity analysis produced no results")
        return pd.DataFrame(columns=['coverage_level', 'avg_width', 'observed_coverage', 'coverage_error'])
    
    return pd.DataFrame(results)
