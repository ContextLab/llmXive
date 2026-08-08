"""
Report Generator for Statistical Model Stability Assessment.

Aggregates results from stability metrics, correlation analysis, and permutation tests
to prepare data for the final markdown report generation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from code.config import RESULTS_DIR, STABILITY_METRICS_FILE, CORRELATION_RESULTS_FILE, PERMUTATION_RESULTS_FILE
from code.utils import safe_execute, log_and_reraise

logger = logging.getLogger(__name__)


def load_stability_metrics(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the stability metrics aggregated from raw evaluations.

    Args:
        filepath: Path to the stability_metrics.csv file. If None, uses default from config.

    Returns:
        DataFrame with stability metrics.
    """
    if filepath is None:
        filepath = RESULTS_DIR / STABILITY_METRICS_FILE

    if not filepath.exists():
        raise FileNotFoundError(f"Stability metrics file not found: {filepath}")

    logger.info(f"Loading stability metrics from {filepath}")
    df = pd.read_csv(filepath)
    
    # Ensure required columns exist
    required_cols = ['dataset_id', 'model_name', 'mean_accuracy', 'cv_accuracy', 'mean_f1', 'cv_f1', 'log_variance_accuracy']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Stability metrics file missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} rows of stability metrics")
    return df


def load_correlation_results(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the correlation results between performance metrics and dataset properties.

    Args:
        filepath: Path to the correlation_results.csv file. If None, uses default from config.

    Returns:
        DataFrame with correlation results.
    """
    if filepath is None:
        filepath = RESULTS_DIR / CORRELATION_RESULTS_FILE

    if not filepath.exists():
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")

    logger.info(f"Loading correlation results from {filepath}")
    df = pd.read_csv(filepath)
    
    # Ensure required columns exist
    required_cols = ['dataset_id', 'model_name', 'metric_type', 'pearson_r', 'pearson_p_value', 
                     'spearman_rho', 'spearman_p_value', 'feature_count', 'sample_size',
                     'regression_slope', 'regression_intercept']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Correlation results file missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} rows of correlation results")
    return df


def load_permutation_results(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the permutation test results comparing variance distributions across models.

    Args:
        filepath: Path to the permutation_results.csv file. If None, uses default from config.

    Returns:
        DataFrame with permutation test results.
    """
    if filepath is None:
        filepath = RESULTS_DIR / PERMUTATION_RESULTS_FILE

    if not filepath.exists():
        raise FileNotFoundError(f"Permutation results file not found: {filepath}")

    logger.info(f"Loading permutation results from {filepath}")
    df = pd.read_csv(filepath)
    
    # Ensure required columns exist
    required_cols = ['dataset_id', 'model_a', 'model_b', 'statistic', 'raw_p_value', 'adj_p_value', 'significant']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Permutation results file missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} rows of permutation results")
    return df


def aggregate_for_report(
    stability_df: pd.DataFrame,
    correlation_df: pd.DataFrame,
    permutation_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Aggregate all result dataframes into a structured dictionary for report generation.

    This function prepares the data in a format that is easy to consume by the templating engine.

    Args:
        stability_df: DataFrame from load_stability_metrics.
        correlation_df: DataFrame from load_correlation_results.
        permutation_df: DataFrame from load_permutation_results.

    Returns:
        Dictionary containing:
            - 'stability_metrics': DataFrame
            - 'correlation_results': DataFrame
            - 'permutation_results': DataFrame
            - 'significant_datasets': List of dataset_ids where adj_p < 0.05
            - 'model_rankings': List of tuples (model_name, mean_cv) sorted by mean_cv
            - 'fdr_summary': Dictionary with FDR calculation details
    """
    logger.info("Aggregating data for report generation")

    # Identify significant variance differences (adj_p < 0.05)
    significant_mask = permutation_df['adj_p_value'] < 0.05
    significant_datasets = permutation_df[significant_mask]['dataset_id'].unique().tolist()
    
    # Rank models by mean CV (lower is better for stability)
    # We calculate mean CV across all datasets for each model
    model_cv_stats = stability_df.groupby('model_name')['cv_accuracy'].mean().reset_index()
    model_cv_stats = model_cv_stats.sort_values('cv_accuracy', ascending=True)
    model_rankings = list(zip(model_cv_stats['model_name'], model_cv_stats['cv_accuracy']))

    # Calculate achieved FDR
    # Count total tests and significant tests
    total_tests = len(permutation_df)
    significant_tests = significant_mask.sum()
    achieved_fdr = significant_tests / total_tests if total_tests > 0 else 0.0

    aggregation = {
        'stability_metrics': stability_df,
        'correlation_results': correlation_df,
        'permutation_results': permutation_df,
        'significant_datasets': significant_datasets,
        'model_rankings': model_rankings,
        'fdr_summary': {
            'total_tests': total_tests,
            'significant_tests': int(significant_tests),
            'achieved_fdr': achieved_fdr,
            'target_fdr': 0.05,
            'method': 'Benjamini-Hochberg'
        }
    }

    logger.info(f"Aggregation complete. Found {len(significant_datasets)} significant datasets.")
    return aggregation


def run_full_report_aggregation(
    stability_path: Optional[Path] = None,
    correlation_path: Optional[Path] = None,
    permutation_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point to load and aggregate all results for the final report.

    Args:
        stability_path: Optional path to stability_metrics.csv.
        correlation_path: Optional path to correlation_results.csv.
        permutation_path: Optional path to permutation_results.csv.

    Returns:
        Aggregated dictionary containing all report data.

    Raises:
        FileNotFoundError: If any required result file is missing.
        ValueError: If data validation fails.
    """
    try:
        stability_df = load_stability_metrics(stability_path)
        correlation_df = load_correlation_results(correlation_path)
        permutation_df = load_permutation_results(permutation_path)
        
        return aggregate_for_report(stability_df, correlation_df, permutation_df)
    except Exception as e:
        log_and_reraise(e, "Failed to aggregate results for report generation")