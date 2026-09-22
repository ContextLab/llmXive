"""
Generate the final research report for the network topology study.

This module aggregates structural metrics, dynamic metrics, correlation results,
and sensitivity analysis to produce a comprehensive final report.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import configuration utilities
from config import get_config_dict

# Import analysis results loaders (if available, otherwise handle gracefully)
try:
    from analysis.correlation import run_correlation_analysis
except ImportError:
    run_correlation_analysis = None

try:
    from analysis.robustness import load_processed_metrics, run_sensitivity_analysis
except ImportError:
    load_processed_metrics = None
    run_sensitivity_analysis = None

# Import exclusion log utilities
try:
    from main import load_exclusion_log, get_exclusion_log_path
except ImportError:
    def load_exclusion_log(path: Optional[str] = None) -> List[Dict]:
        return []
    
    def get_exclusion_log_path() -> str:
        return "data/logs/exclusion_log.json"

def load_metrics_data(metrics_path: str) -> Dict[str, pd.DataFrame]:
    """
    Load structural and dynamic metrics from CSV files.
    
    Args:
        metrics_path: Base path to the processed metrics directory.
        
    Returns:
        Dictionary containing DataFrames for structural and dynamic metrics.
    """
    config = get_config_dict()
    processed_dir = Path(config['data_dir']) / 'processed'
    
    structural_path = processed_dir / 'structural_metrics.csv'
    dynamic_path = processed_dir / 'dynamic_metrics.csv'
    
    result = {}
    
    if structural_path.exists():
        result['structural'] = pd.read_csv(structural_path)
    else:
        result['structural'] = pd.DataFrame()
        
    if dynamic_path.exists():
        result['dynamic'] = pd.read_csv(dynamic_path)
    else:
        result['dynamic'] = pd.DataFrame()
        
    return result

def load_correlation_results(correlation_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load correlation results if available.
    
    Args:
        correlation_path: Path to correlation results CSV.
        
    Returns:
        DataFrame with correlation results, or empty DataFrame if not found.
    """
    if correlation_path is None:
        config = get_config_dict()
        processed_dir = Path(config['data_dir']) / 'processed'
        correlation_path = str(processed_dir / 'correlation_results.csv')
        
    if os.path.exists(correlation_path):
        return pd.read_csv(correlation_path)
    return pd.DataFrame()

def load_exclusion_log_safe(log_path: Optional[str] = None) -> List[Dict]:
    """
    Safely load the exclusion log.
    
    Args:
        log_path: Path to exclusion log JSON.
        
    Returns:
        List of exclusion records.
    """
    if log_path is None:
        log_path = get_exclusion_log_path()
        
    try:
        return load_exclusion_log(log_path)
    except Exception:
        return []

def calculate_sensitivity_metrics(sensitivity_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate and aggregate sensitivity analysis metrics.
    
    Args:
        sensitivity_path: Path to sensitivity results.
        
    Returns:
        Dictionary with sensitivity metrics.
    """
    config = get_config_dict()
    processed_dir = Path(config['data_dir']) / 'processed'
    
    # Try to load density sensitivity results
    density_sensitivity_path = processed_dir / 'structural_density_sensitivity.csv'
    sensitivity_comparison_path = processed_dir / 'sensitivity_comparison.csv'
    
    result = {
        'density_analysis': {},
        'window_length_validation': {}
    }
    
    if density_sensitivity_path.exists():
        df = pd.read_csv(density_sensitivity_path)
        # Calculate summary statistics per metric across densities
        metrics = ['global_efficiency', 'clustering_coefficient', 'modularity']
        for metric in metrics:
            if metric in df.columns:
                result['density_analysis'][metric] = {
                    'mean': df[metric].mean(),
                    'std': df[metric].std(),
                    'min': df[metric].min(),
                    'max': df[metric].max()
                }
                
    if sensitivity_comparison_path.exists():
        df = pd.read_csv(sensitivity_comparison_path)
        if 'abs_diff_r' in df.columns:
            result['window_length_validation'] = {
                'mean_abs_diff': df['abs_diff_r'].mean(),
                'max_abs_diff': df['abs_diff_r'].max(),
                'significant_changes': (df['abs_diff_r'] > 0.1).sum()
            }
            
    return result

def generate_summary_statistics(metrics_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Generate summary statistics for the dataset.
    
    Args:
        metrics_data: Dictionary with structural and dynamic metrics.
        
    Returns:
        Dictionary with summary statistics.
    """
    summary = {
        'total_subjects': 0,
        'processed_subjects': 0,
        'excluded_subjects': 0,
        'structural_metrics_summary': {},
        'dynamic_metrics_summary': {}
    }
    
    # Count subjects
    if not metrics_data['structural'].empty:
        summary['total_subjects'] = len(metrics_data['structural']['subject_id'].unique())
        summary['processed_subjects'] = len(metrics_data['structural'])
        
    exclusions = load_exclusion_log_safe()
    summary['excluded_subjects'] = len(exclusions)
    
    # Structural metrics summary
    if not metrics_data['structural'].empty:
        struct_df = metrics_data['structural']
        numeric_cols = struct_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            summary['structural_metrics_summary'][col] = {
                'mean': float(struct_df[col].mean()),
                'std': float(struct_df[col].std()),
                'min': float(struct_df[col].min()),
                'max': float(struct_df[col].max())
            }
            
    # Dynamic metrics summary
    if not metrics_data['dynamic'].empty:
        dyn_df = metrics_data['dynamic']
        numeric_cols = dyn_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col != 'subject_id' and col != 'state_id':
                summary['dynamic_metrics_summary'][col] = {
                    'mean': float(dyn_df[col].mean()),
                    'std': float(dyn_df[col].std()),
                    'min': float(dyn_df[col].min()),
                    'max': float(dyn_df[col].max())
                }
                
    return summary

def generate_final_report(
    summary_stats: Dict[str, Any],
    correlation_results: pd.DataFrame,
    sensitivity_metrics: Dict[str, Any],
    exclusions: List[Dict],
    output_path: str
) -> Dict[str, Any]:
    """
    Assemble the final research report.
    
    Args:
        summary_stats: Summary statistics from generate_summary_statistics.
        correlation_results: Correlation analysis results.
        sensitivity_metrics: Sensitivity analysis metrics.
        exclusions: List of excluded subjects.
        output_path: Path to save the final report.
        
    Returns:
        The final report dictionary.
    """
    config = get_config_dict()
    
    # Build correlation summary
    correlation_summary = {
        'total_correlations': 0,
        'significant_correlations': 0,
        'fdr_corrected_significant': 0,
        'top_correlations': []
    }
    
    if not correlation_results.empty:
        correlation_summary['total_correlations'] = len(correlation_results)
        if 'p_value_fdr' in correlation_results.columns:
            correlation_summary['significant_correlations'] = int(
                (correlation_results['p_value'] < 0.05).sum()
            )
            correlation_summary['fdr_corrected_significant'] = int(
                (correlation_results['p_value_fdr'] < 0.05).sum()
            )
            
        # Get top correlations
        if 'r_value' in correlation_results.columns:
            sorted_corr = correlation_results.sort_values('r_value', key=abs, ascending=False)
            top_n = min(10, len(sorted_corr))
            correlation_summary['top_correlations'] = sorted_corr.head(top_n).to_dict('records')
            
    # Build final report
    report = {
        'title': 'Investigation of Network Topology Influence on Brain Activity',
        'config': {
            'window_length_baseline': config.get('WINDOW_LENGTH_BASELINE', 30),
            'window_length_validation': config.get('WINDOW_LENGTH_VALIDATION', 20),
            'k_means_k': config.get('K_MEANS_K', 5),
            'density_threshold_baseline': config.get('DENSITY_THRESHOLD_BASELINE', 0.15)
        },
        'dataset_summary': summary_stats,
        'correlation_analysis': correlation_summary,
        'sensitivity_analysis': sensitivity_metrics,
        'exclusion_log': exclusions,
        'methodological_notes': [
            "All structural metrics computed using proportional density thresholding.",
            "Dynamic states extracted using Leave-One-Out K-Means to ensure independence.",
            "Correlations tested with normality checks (Shapiro-Wilk) and FDR corrected.",
            "Results are associational; no causal claims are made."
        ],
        'warnings': []
    }
    
    # Add warnings if needed
    if summary_stats['excluded_subjects'] > 0:
        report['warnings'].append(
            f"{summary_stats['excluded_subjects']} subjects were excluded due to data quality issues."
        )
        
    if correlation_summary['fdr_corrected_significant'] == 0:
        report['warnings'].append(
            "No significant correlations survived FDR correction at q=0.05."
        )
        
    # Save report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    return report

def main():
    """
    Main entry point for report generation.
    """
    print("Starting final report generation...")
    
    # Load configuration
    config = get_config_dict()
    output_dir = Path(config['data_dir']) / 'processed'
    output_path = output_dir / 'final_report.json'
    
    # Load metrics
    print("Loading metrics data...")
    metrics_data = load_metrics_data(config['data_dir'])
    
    # Load correlation results
    print("Loading correlation results...")
    correlation_results = load_correlation_results()
    
    # Calculate sensitivity metrics
    print("Calculating sensitivity metrics...")
    sensitivity_metrics = calculate_sensitivity_metrics()
    
    # Load exclusions
    print("Loading exclusion log...")
    exclusions = load_exclusion_log_safe()
    
    # Generate summary statistics
    print("Generating summary statistics...")
    summary_stats = generate_summary_statistics(metrics_data)
    
    # Generate final report
    print("Generating final report...")
    report = generate_final_report(
        summary_stats=summary_stats,
        correlation_results=correlation_results,
        sensitivity_metrics=sensitivity_metrics,
        exclusions=exclusions,
        output_path=str(output_path)
    )
    
    print(f"Final report saved to: {output_path}")
    print(f"Processed {summary_stats['processed_subjects']} subjects.")
    print(f"Excluded {summary_stats['excluded_subjects']} subjects.")
    
    if not correlation_results.empty:
        print(f"Found {report['correlation_analysis']['fdr_corrected_significant']} "
              f"significant correlations after FDR correction.")
              
    return report

if __name__ == '__main__':
    main()