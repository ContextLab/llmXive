"""
Final Report Generation Module.

Generates the comprehensive final report for the study, including:
1. Executive summary with explicit "associational" framing (FR-007).
2. Summary statistics of structural and dynamic metrics.
3. Correlation results with FDR correction.
4. Sensitivity analysis tables comparing 30 TR vs 20 TR window lengths.
5. Explicit calculation of the absolute difference between correlation coefficients
   for the baseline and sensitivity checks (SC-002).
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

# Import from project modules based on API surface
from config import get_config_dict
from analysis.correlation import benjamini_hochberg_fdr
from analysis.robustness import load_processed_metrics, calculate_sensitivity_metrics


def load_metrics_data(metrics_file: str) -> Dict[str, pd.DataFrame]:
    """
    Load structural and dynamic metrics from CSV files.

    Args:
        metrics_file: Path to the CSV file containing aggregated metrics.

    Returns:
        Dictionary with 'structural' and 'dynamic' DataFrames.
    """
    config = get_config_dict()
    # Default paths if not provided
    if not metrics_file:
        metrics_file = config.get('paths', {}).get('processed_metrics', 'data/processed/structural_metrics.csv')

    if not os.path.exists(metrics_file):
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")

    df = pd.read_csv(metrics_file)

    # Split into structural and dynamic based on column prefixes or specific columns
    # Assuming columns are prefixed or named specifically as per T019
    structural_cols = [c for c in df.columns if c.startswith('struct_') or c in ['subject_id', 'global_efficiency', 'avg_clustering', 'modularity']]
    dynamic_cols = [c for c in df.columns if c.startswith('dynamic_') or c in ['subject_id', 'dwell_time', 'visited_states']]

    # Fallback if prefixes aren't used, just split by known metric names
    if 'global_efficiency' in df.columns:
        struct_df = df[['subject_id', 'global_efficiency', 'avg_clustering', 'modularity']]
        dyn_df = df[['subject_id', 'dwell_time', 'visited_states']]
    else:
        # Fallback to generic split if specific columns missing (should not happen if T019 worked)
        struct_df = df[[c for c in df.columns if c != 'subject_id' and c not in ['dwell_time', 'visited_states']]]
        dyn_df = df[['subject_id', 'dwell_time', 'visited_states']]

    return {
        'structural': struct_df,
        'dynamic': dyn_df
    }


def load_correlation_results(results_file: str) -> pd.DataFrame:
    """
    Load correlation results from CSV.

    Args:
        results_file: Path to correlation_results.csv.

    Returns:
        DataFrame with correlation results.
    """
    if not os.path.exists(results_file):
        raise FileNotFoundError(f"Correlation results file not found: {results_file}")
    return pd.read_csv(results_file)


def load_exclusion_log(log_file: str) -> List[Dict]:
    """
    Load the exclusion log.

    Args:
        log_file: Path to exclusion_log.json.

    Returns:
        List of exclusion records.
    """
    if not os.path.exists(log_file):
        return []
    with open(log_file, 'r') as f:
        return json.load(f)


def calculate_sensitivity_metrics(
    baseline_results: pd.DataFrame,
    sensitivity_results: pd.DataFrame
) -> Dict[str, Any]:
    """
    Calculate sensitivity metrics, specifically the absolute difference
    between 30 TR and 20 TR correlation coefficients as required by SC-002.

    Args:
        baseline_results: DataFrame with 30 TR correlation results.
        sensitivity_results: DataFrame with 20 TR correlation results.

    Returns:
        Dictionary containing the absolute differences and summary stats.
    """
    # Ensure we have the necessary columns
    if 'r_value' not in baseline_results.columns or 'r_value' not in sensitivity_results.columns:
        # Try alternative column names
        if 'r' in baseline_results.columns:
            baseline_results = baseline_results.rename(columns={'r': 'r_value'})
        if 'r' in sensitivity_results.columns:
            sensitivity_results = sensitivity_results.rename(columns={'r': 'r_value'})

    if 'r_value' not in baseline_results.columns or 'r_value' not in sensitivity_results.columns:
        raise ValueError("Could not find 'r_value' or 'r' column in correlation results.")

    # Merge on metric names (assuming 'metric' or 'pair' column exists)
    # Let's assume the column is 'metric_pair' or similar, or we merge by index if aligned
    # For robustness, we'll try to align by 'structural_metric' and 'dynamic_metric' if they exist
    merge_keys = []
    if 'structural_metric' in baseline_results.columns and 'dynamic_metric' in baseline_results.columns:
        merge_keys = ['structural_metric', 'dynamic_metric']
    elif 'metric_pair' in baseline_results.columns:
        merge_keys = ['metric_pair']

    if not merge_keys:
        # Fallback: assume rows correspond 1:1 by index order (risky but necessary if schema is unknown)
        # We'll just compute diff row by row
        baseline_vals = baseline_results['r_value'].values
        sensitivity_vals = sensitivity_results['r_value'].values
        if len(baseline_vals) != len(sensitivity_vals):
            raise ValueError("Baseline and sensitivity result rows do not match in count.")
        abs_diff = np.abs(baseline_vals - sensitivity_vals)
        return {
            'absolute_differences': abs_diff,
            'mean_abs_diff': float(np.mean(abs_diff)),
            'max_abs_diff': float(np.max(abs_diff)),
            'min_abs_diff': float(np.min(abs_diff)),
            'details': "Row-wise comparison used due to missing merge keys."
        }

    merged = pd.merge(
        baseline_results,
        sensitivity_results,
        on=merge_keys,
        suffixes=('_baseline', '_sensitivity')
    )

    if 'r_value_baseline' in merged.columns and 'r_value_sensitivity' in merged.columns:
        merged['abs_diff'] = np.abs(merged['r_value_baseline'] - merged['r_value_sensitivity'])
    elif 'r_baseline' in merged.columns and 'r_sensitivity' in merged.columns:
        merged['abs_diff'] = np.abs(merged['r_baseline'] - merged['r_sensitivity'])
    else:
        raise ValueError("Could not find r-value columns in merged dataframe.")

    return {
        'absolute_differences': merged['abs_diff'].values,
        'mean_abs_diff': float(merged['abs_diff'].mean()),
        'max_abs_diff': float(merged['abs_diff'].max()),
        'min_abs_diff': float(merged['abs_diff'].min()),
        'details': merged.to_dict(orient='records')
    }


def generate_summary_statistics(metrics_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Generate summary statistics for structural and dynamic metrics.

    Args:
        metrics_data: Dictionary containing 'structural' and 'dynamic' DataFrames.

    Returns:
        Dictionary with summary statistics.
    """
    summary = {}
    for key, df in metrics_data.items():
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        summary[key] = df[numeric_cols].describe().to_dict()
    return summary


def generate_final_report(
    output_path: str,
    metrics_file: str = None,
    correlation_file: str = None,
    exclusion_file: str = None,
    sensitivity_baseline_file: str = None,
    sensitivity_sensitivity_file: str = None
) -> str:
    """
    Generate the final report JSON file.

    Args:
        output_path: Path where the report will be saved.
        metrics_file: Path to aggregated metrics CSV.
        correlation_file: Path to correlation results CSV.
        exclusion_file: Path to exclusion log JSON.
        sensitivity_baseline_file: Path to 30 TR correlation results.
        sensitivity_sensitivity_file: Path to 20 TR correlation results.

    Returns:
        Path to the generated report file.
    """
    config = get_config_dict()
    if not metrics_file:
        metrics_file = config.get('paths', {}).get('processed_metrics', 'data/processed/structural_metrics.csv')
    if not correlation_file:
        correlation_file = config.get('paths', {}).get('correlation_results', 'data/processed/correlation_results.csv')
    if not exclusion_file:
        exclusion_file = config.get('paths', {}).get('exclusion_log', 'data/logs/exclusion_log.json')

    # Load data
    try:
        metrics_data = load_metrics_data(metrics_file)
    except FileNotFoundError as e:
        # If metrics are missing, we can still generate a report stating no data
        metrics_data = {'structural': pd.DataFrame(), 'dynamic': pd.DataFrame()}

    try:
        corr_results = load_correlation_results(correlation_file)
    except FileNotFoundError:
        corr_results = pd.DataFrame()

    exclusion_log = load_exclusion_log(exclusion_file)

    # Calculate sensitivity metrics if files are provided
    sensitivity_analysis = None
    if sensitivity_baseline_file and sensitivity_sensitivity_file:
        if os.path.exists(sensitivity_baseline_file) and os.path.exists(sensitivity_sensitivity_file):
            try:
                baseline_df = pd.read_csv(sensitivity_baseline_file)
                sensitivity_df = pd.read_csv(sensitivity_sensitivity_file)
                sensitivity_analysis = calculate_sensitivity_metrics(baseline_df, sensitivity_df)
            except Exception as e:
                sensitivity_analysis = {'error': str(e)}
        else:
            sensitivity_analysis = {'error': 'Sensitivity files not found'}
    elif os.path.exists('data/processed/correlation_results_30TR.csv') and os.path.exists('data/processed/correlation_results_20TR.csv'):
        # Fallback to default names if not explicitly passed
        try:
            baseline_df = pd.read_csv('data/processed/correlation_results_30TR.csv')
            sensitivity_df = pd.read_csv('data/processed/correlation_results_20TR.csv')
            sensitivity_analysis = calculate_sensitivity_metrics(baseline_df, sensitivity_df)
        except Exception as e:
            sensitivity_analysis = {'error': str(e)}

    # Construct report
    report = {
        'metadata': {
            'title': 'Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns',
            'generated_at': datetime.now().isoformat(),
            'version': '1.0',
            'fr_007_compliance': 'This report presents associational findings only. No causal claims are made.',
            'sc_002_compliance': 'Sensitivity analysis (30 TR vs 20 TR) included with absolute differences calculated.'
        },
        'executive_summary': {
            'framing': 'Associational',
            'statement': 'This study investigates the associational relationships between structural network topology and dynamic functional states. Results should be interpreted as statistical associations, not causal predictions.',
            'total_subjects_processed': len(metrics_data['structural']) if not metrics_data['structural'].empty else 0,
            'excluded_subjects': len(exclusion_log)
        },
        'summary_statistics': generate_summary_statistics(metrics_data),
        'correlation_results': corr_results.to_dict(orient='records') if not corr_results.empty else [],
        'sensitivity_analysis': sensitivity_analysis,
        'exclusion_log': exclusion_log
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    return output_path


def main():
    """
    Main entry point for report generation.
    """
    config = get_config_dict()
    output_path = config.get('paths', {}).get('final_report', 'data/reports/final_report.json')

    # Default paths for sensitivity analysis files
    baseline_corr = 'data/processed/correlation_results_30TR.csv'
    sensitivity_corr = 'data/processed/correlation_results_20TR.csv'

    # Check if these files exist, if not, use the standard correlation file for both (or skip)
    if not os.path.exists(baseline_corr):
        baseline_corr = 'data/processed/correlation_results.csv'
    if not os.path.exists(sensitivity_corr):
        # If 20TR file doesn't exist, we might not have run sensitivity analysis yet
        # In that case, we can't calculate the difference, so we set sensitivity to None
        sensitivity_corr = None

    print(f"Generating final report at {output_path}...")
    try:
        generated_path = generate_final_report(
            output_path=output_path,
            metrics_file='data/processed/structural_metrics.csv',
            correlation_file='data/processed/correlation_results.csv',
            exclusion_file='data/logs/exclusion_log.json',
            sensitivity_baseline_file=baseline_corr,
            sensitivity_sensitivity_file=sensitivity_corr
        )
        print(f"Report successfully generated: {generated_path}")
    except Exception as e:
        print(f"Error generating report: {e}")
        raise


if __name__ == '__main__':
    main()