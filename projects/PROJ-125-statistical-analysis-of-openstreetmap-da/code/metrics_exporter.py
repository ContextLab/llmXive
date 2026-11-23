"""
Metrics Exporter for Urban Heat Island Analysis.

Aggregates results from Cross-Validation, FDR correction, Proxy Validity,
and Sensitivity Analysis into a single CSV report at data/results/metrics.csv.

Implements SC-001, SC-002, SC-003, SC-005, SC-006.
"""
import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from config import get_path
from utils.logging import get_logger

logger = get_logger(__name__)

def load_json_safe(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file safely, returning None if not found or invalid."""
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON {filepath}: {e}")
        return None

def extract_cv_metrics(cv_results_path: Path) -> Dict[str, Any]:
    """
    Extract Cross-Validation metrics from spatial cross-validation output.
    Expected keys: mean_rmse, mean_mae, mean_r2, std_rmse, std_mae, std_r2, n_folds
    """
    data = load_json_safe(cv_results_path)
    if not data:
        return {}
    
    # Handle both flat structure and nested structure
    if 'metrics' in data:
        data = data['metrics']
    
    return {
        'cv_mean_rmse': data.get('mean_rmse'),
        'cv_mean_mae': data.get('mean_mae'),
        'cv_mean_r2': data.get('mean_r2'),
        'cv_std_rmse': data.get('std_rmse'),
        'cv_std_mae': data.get('std_mae'),
        'cv_std_r2': data.get('std_r2'),
        'cv_n_folds': data.get('n_folds'),
    }

def extract_fdr_metrics(fdr_results_path: Path) -> Dict[str, Any]:
    """
    Extract FDR (False Discovery Rate) corrected metrics.
    Expected keys: n_significant_predictors, adjusted_p_values, method
    """
    data = load_json_safe(fdr_results_path)
    if not data:
        return {}
    
    if 'fdr_results' in data:
        data = data['fdr_results']
        
    return {
        'fdr_n_significant': data.get('n_significant_predictors'),
        'fdr_method': data.get('method'),
        # We store the count, not the full array of p-values in the summary CSV
    }

def extract_proxy_gap(proxy_gap_path: Path) -> Dict[str, Any]:
    """
    Extract Proxy Validity Gap metrics.
    Expected keys: literature_max_r2, observed_r2, unexplained_variance_gap
    """
    data = load_json_safe(proxy_gap_path)
    if not data:
        return {}
    
    if 'proxy_gap' in data:
        data = data['proxy_gap']
        
    return {
        'proxy_literature_max_r2': data.get('literature_max_r2'),
        'proxy_observed_r2': data.get('observed_r2'),
        'proxy_unexplained_gap': data.get('unexplained_variance_gap'),
    }

def extract_sensitivity_metrics(sensitivity_path: Path) -> Dict[str, Any]:
    """
    Extract Sensitivity Analysis (GWR Bandwidth Sweep) metrics.
    Expected keys: bandwidth_stability, r2_std, optimal_bandwidth
    """
    data = load_json_safe(sensitivity_path)
    if not data:
        return {}
    
    if 'sensitivity' in data:
        data = data['sensitivity']
        
    return {
        'sens_r2_std': data.get('r2_std'),
        'sens_optimal_bandwidth': data.get('optimal_bandwidth'),
        'sens_n_bandwidths_tested': data.get('n_bandwidths_tested'),
    }

def export_metrics_to_csv(
    cv_results_path: Path,
    fdr_results_path: Path,
    proxy_gap_path: Path,
    sensitivity_path: Path,
    output_path: Path
) -> None:
    """
    Aggregate all metrics into a single CSV row.
    
    Columns (SC-001 to SC-006):
    - cv_mean_rmse, cv_mean_mae, cv_mean_r2 (SC-001, SC-002)
    - fdr_n_significant (SC-003)
    - sens_r2_std (SC-005)
    - proxy_unexplained_gap (SC-006)
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract data from sources
    cv_data = extract_cv_metrics(cv_results_path)
    fdr_data = extract_fdr_metrics(fdr_results_path)
    proxy_data = extract_proxy_gap(proxy_gap_path)
    sens_data = extract_sensitivity_metrics(sensitivity_path)
    
    # Merge all data into a single row
    row = {**cv_data, **fdr_data, **proxy_data, **sens_data}
    
    # Define standard column order for consistency
    columns = [
        'cv_mean_rmse', 'cv_mean_mae', 'cv_mean_r2', 'cv_std_rmse', 'cv_std_mae', 'cv_std_r2', 'cv_n_folds',
        'fdr_n_significant', 'fdr_method',
        'proxy_literature_max_r2', 'proxy_observed_r2', 'proxy_unexplained_gap',
        'sens_r2_std', 'sens_optimal_bandwidth', 'sens_n_bandwidths_tested'
    ]
    
    logger.info(f"Writing metrics to {output_path}")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        writer.writerow(row)
    
    logger.info(f"Metrics export complete. Wrote {len(row)} columns.")

def main():
    """Main entry point for metrics export."""
    logger.info("Starting metrics export (Task T033)...")
    
    # Define paths based on project structure
    data_dir = get_path("data")
    results_dir = data_dir / "results"
    
    # Input files from previous tasks
    cv_results_path = results_dir / "spatial_cv_results.json"
    fdr_results_path = results_dir / "fdr_results.json"
    proxy_gap_path = results_dir / "proxy_gap.json"
    sensitivity_path = results_dir / "sensitivity_results.json"
    
    # Output file
    output_path = results_dir / "metrics.csv"
    
    try:
        export_metrics_to_csv(
            cv_results_path,
            fdr_results_path,
            proxy_gap_path,
            sensitivity_path,
            output_path
        )
        logger.info("Task T033 completed successfully.")
    except Exception as e:
        logger.error(f"Task T033 failed: {e}")
        raise

if __name__ == "__main__":
    main()