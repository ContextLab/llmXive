"""
Cross-dataset comparison logic for TNG-100 vs Millennium-II vs WDM.

This module implements the comparison logic required for Task T033.
It compares statistical results across datasets, handling cases where
some datasets may be missing (logged as gaps in metadata).

Dependencies:
  - T031-Analyze output: data/processed/millennium_results.csv (if available)
  - T031-WDM-Analyze output: data/processed/wdm_results.csv (if available)
  - T025 output: data/processed/statistical_results.csv (TNG-100 baseline)
"""

import os
import sys
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from utils.config import get_project_root, get_data_processed_path, get_output_path
from utils.logging import get_pipeline_logger, log_task_start, log_task_end
from analysis.metadata_utils import load_metadata, save_metadata, add_associational_only_flag_to_csv

# Configure logging
logger = get_pipeline_logger(__name__)


def load_statistical_results(dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Load statistical results for a specific dataset.

    Args:
        dataset_name: One of 'tng', 'millennium', 'wdm'

    Returns:
        DataFrame with results, or None if file doesn't exist
    """
    root = get_project_root()
    if dataset_name == 'tng':
        path = root / 'data' / 'processed' / 'statistical_results.csv'
    elif dataset_name == 'millennium':
        path = root / 'data' / 'processed' / 'millennium_results.csv'
    elif dataset_name == 'wdm':
        path = root / 'data' / 'processed' / 'wdm_results.csv'
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    if not path.exists():
        logger.warning(f"Dataset file not found: {path}")
        return None

    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} rows from {dataset_name} results: {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {dataset_name} results: {e}")
        return None


def compare_statistical_metrics(
    tng_results: pd.DataFrame,
    other_results: pd.DataFrame,
    metric_columns: List[str] = ['p_value', 'effect_size', 'correlation']
) -> Dict[str, Any]:
    """
    Compare statistical metrics between TNG-100 and another dataset.

    Args:
        tng_results: TNG-100 statistical results
        other_results: Results from another dataset
        metric_columns: Columns to compare

    Returns:
        Dictionary with comparison metrics
    """
    comparison = {
        'datasets': ['tng', 'other'],
        'metrics_compared': metric_columns,
        'differences': {}
    }

    for col in metric_columns:
        if col not in tng_results.columns or col not in other_results.columns:
            logger.warning(f"Column {col} not found in both datasets, skipping")
            continue

        tng_vals = tng_results[col].dropna()
        other_vals = other_results[col].dropna()

        if len(tng_vals) == 0 or len(other_vals) == 0:
            logger.warning(f"No valid values for {col} in one or both datasets")
            continue

        # Calculate mean difference
        mean_diff = other_vals.mean() - tng_vals.mean()

        # Calculate relative difference (percentage)
        if tng_vals.mean() != 0:
            rel_diff = (mean_diff / abs(tng_vals.mean())) * 100
        else:
            rel_diff = float('inf') if mean_diff != 0 else 0

        comparison['differences'][col] = {
            'mean_tng': float(tng_vals.mean()),
            'mean_other': float(other_vals.mean()),
            'mean_difference': float(mean_diff),
            'relative_difference_pct': float(rel_diff),
            'tng_count': int(len(tng_vals)),
            'other_count': int(len(other_vals))
        }

    return comparison


def compare_significance_rates(
    tng_results: pd.DataFrame,
    other_results: pd.DataFrame,
    significance_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Compare significance rates (proportion of tests with p < threshold)
    between datasets.

    Args:
        tng_results: TNG-100 statistical results
        other_results: Results from another dataset
        significance_threshold: P-value threshold for significance

    Returns:
        Dictionary with significance rate comparison
    """
    def get_significance_rate(df: pd.DataFrame, threshold: float) -> Tuple[float, int, int]:
        """Calculate significance rate and counts."""
        if 'p_value' not in df.columns:
            logger.warning("No p_value column found")
            return 0.0, 0, 0

        valid_p = df['p_value'].dropna()
        if len(valid_p) == 0:
            return 0.0, 0, 0

        significant = (valid_p < threshold).sum()
        total = len(valid_p)
        rate = significant / total if total > 0 else 0.0

        return rate, int(significant), int(total)

    tng_rate, tng_sig, tng_total = get_significance_rate(tng_results, significance_threshold)
    other_rate, other_sig, other_total = get_significance_rate(other_results, significance_threshold)

    return {
        'significance_threshold': significance_threshold,
        'tng': {
            'rate': float(tng_rate),
            'significant_count': tng_sig,
            'total_count': tng_total
        },
        'other': {
            'rate': float(other_rate),
            'significant_count': other_sig,
            'total_count': other_total
        },
        'rate_difference': float(other_rate - tng_rate)
    }


def generate_cross_dataset_report(
    comparison_results: List[Dict[str, Any]],
    significance_comparisons: List[Dict[str, Any]],
    missing_datasets: List[str]
) -> pd.DataFrame:
    """
    Generate a consolidated cross-dataset comparison report.

    Args:
        comparison_results: List of metric comparison dictionaries
        significance_comparisons: List of significance rate comparison dictionaries
        missing_datasets: List of dataset names that were not available

    Returns:
        DataFrame with the comparison report
    """
    report_rows = []

    # Add dataset availability status
    all_datasets = ['tng', 'millennium', 'wdm']
    for ds in all_datasets:
        report_rows.append({
            'dataset': ds,
            'status': 'available' if ds not in missing_datasets else 'missing',
            'note': '' if ds not in missing_datasets else f'Dataset not available (gap logged in metadata)'
        })

    # Add metric comparisons
    for comp in comparison_results:
        for metric, stats in comp.get('differences', {}).items():
            report_rows.append({
                'dataset': f"{comp['datasets'][0]} vs {comp['datasets'][1]}",
                'metric': metric,
                'status': 'available',
                'mean_difference': stats.get('mean_difference', None),
                'relative_diff_pct': stats.get('relative_difference_pct', None),
                'tng_mean': stats.get('mean_tng', None),
                'other_mean': stats.get('mean_other', None),
                'note': ''
            })

    # Add significance rate comparisons
    for sig_comp in significance_comparisons:
        report_rows.append({
            'dataset': f"{sig_comp['datasets'][0]} vs {sig_comp['datasets'][1]}",
            'metric': 'significance_rate',
            'status': 'available',
            'mean_difference': sig_comp.get('rate_difference', None),
            'relative_diff_pct': None,
            'tng_mean': sig_comp.get('tng', {}).get('rate', None),
            'other_mean': sig_comp.get('other', {}).get('rate', None),
            'note': f"Threshold: {sig_comp.get('significance_threshold', 0.05)}"
        })

    report_df = pd.DataFrame(report_rows)

    # Apply associational_only flag
    report_df['associational_only'] = True

    return report_df


def run_cross_dataset_comparison() -> Dict[str, Any]:
    """
    Main function to run cross-dataset comparison.

    Returns:
        Dictionary with comparison results and report path
    """
    log_task_start(logger, "T033", "Cross-dataset comparison")

    root = get_project_root()
    output_dir = get_data_processed_path()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load datasets
    logger.info("Loading TNG-100 statistical results...")
    tng_results = load_statistical_results('tng')

    if tng_results is None:
        logger.error("TNG-100 results not found. Cannot perform comparison.")
        log_task_end(logger, "T033", "failed", "TNG-100 results not found")
        return {'status': 'failed', 'reason': 'TNG-100 results not found'}

    missing_datasets = []
    comparison_results = []
    significance_comparisons = []

    # Compare with Millennium-II
    logger.info("Loading Millennium-II results...")
    millennium_results = load_statistical_results('millennium')
    if millennium_results is not None:
        logger.info("Performing TNG vs Millennium-II comparison...")
        comp = compare_statistical_metrics(tng_results, millennium_results)
        comparison_results.append({
            'datasets': ['tng', 'millennium'],
            **comp
        })

        sig_comp = compare_significance_rates(tng_results, millennium_results)
        sig_comp['datasets'] = ['tng', 'millennium']
        significance_comparisons.append(sig_comp)
    else:
        missing_datasets.append('millennium')
        logger.warning("Millennium-II results not available. Skipping comparison.")

    # Compare with WDM
    logger.info("Loading WDM results...")
    wdm_results = load_statistical_results('wdm')
    if wdm_results is not None:
        logger.info("Performing TNG vs WDM comparison...")
        comp = compare_statistical_metrics(tng_results, wdm_results)
        comparison_results.append({
            'datasets': ['tng', 'wdm'],
            **comp
        })

        sig_comp = compare_significance_rates(tng_results, wdm_results)
        sig_comp['datasets'] = ['tng', 'wdm']
        significance_comparisons.append(sig_comp)
    else:
        missing_datasets.append('wdm')
        logger.warning("WDM results not available. Skipping comparison.")

    # Generate report
    logger.info("Generating cross-dataset comparison report...")
    report_df = generate_cross_dataset_report(
        comparison_results,
        significance_comparisons,
        missing_datasets
    )

    # Save report
    output_path = output_dir / 'cross_dataset_comparison.csv'
    report_df.to_csv(output_path, index=False)
    logger.info(f"Saved cross-dataset comparison report to: {output_path}")

    # Apply associational_only flag to the output file
    try:
        add_associational_only_flag_to_csv(output_path)
        logger.info("Applied associational_only flag to cross-dataset comparison report")
    except Exception as e:
        logger.warning(f"Could not apply associational_only flag: {e}")

    # Update metadata with gap information
    metadata_path = root / 'data' / 'metadata.yaml'
    if metadata_path.exists():
        metadata = load_metadata()
        if 'data_gaps' not in metadata:
            metadata['data_gaps'] = {}

        for ds in missing_datasets:
            metadata['data_gaps'][ds] = {
                'status': 'not_available',
                'description': f'{ds.capitalize()} dataset results not found',
                'impact': f'SC-004 (cross-dataset validation) partially not measurable for {ds}',
                'timestamp': pd.Timestamp.now().isoformat()
            }

        save_metadata(metadata)
        logger.info(f"Updated metadata with gaps for missing datasets: {missing_datasets}")

    # Log summary
    summary = {
        'status': 'completed',
        'tng_available': True,
        'millennium_available': 'millennium' not in missing_datasets,
        'wdm_available': 'wdm' not in missing_datasets,
        'comparisons_performed': len(comparison_results),
        'missing_datasets': missing_datasets,
        'report_path': str(output_path)
    }

    if missing_datasets:
        summary['note'] = f"Comparisons incomplete due to missing datasets: {missing_datasets}"
        summary['sc_004_status'] = 'partially_not_measurable'
    else:
        summary['sc_004_status'] = 'measurable'

    log_task_end(logger, "T033", "completed", f"Performed {len(comparison_results)} comparisons")

    return summary


def main():
    """Entry point for command-line execution."""
    result = run_cross_dataset_comparison()
    print(f"Cross-dataset comparison completed: {result}")
    return result


if __name__ == "__main__":
    main()
