"""
Metrics Exporter for User Story 3.

Aggregates results from Cross-Validation, FDR, Proxy Validity, and Sensitivity
analysis into a single `data/results/metrics.csv` file.

Implements SC-001, SC-002, SC-003, SC-005, SC-006.
"""
import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.logging import get_main_logger
from config import PATHS

logger = get_main_logger(__name__)

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if not found."""
    if not path.exists():
        logger.warning(f"File not found for metrics source: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {path}: {e}")
        return None

def extract_cv_metrics(cv_results: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract aggregated cross-validation metrics from spatial_cv_results.json.
    Expected keys: mean_rmse, mean_mae, mean_r2, std_rmse, std_mae, std_r2.
    """
    metrics = {}
    if not cv_results:
        return metrics

    # Handle potential nesting if results are in a 'results' key
    data = cv_results.get('results', cv_results)

    # Standardize keys based on typical output from run_spatial_cross_validation
    mapping = {
        'mean_rmse': 'cv_mean_rmse',
        'mean_mae': 'cv_mean_mae',
        'mean_r2': 'cv_mean_r2',
        'std_rmse': 'cv_std_rmse',
        'std_mae': 'cv_std_mae',
        'std_r2': 'cv_std_r2',
        'best_model': 'best_model_name' # Optional: store best model type
    }

    for src_key, dest_key in mapping.items():
        if src_key in data:
            val = data[src_key]
            if isinstance(val, (int, float)):
                metrics[dest_key] = float(val)
            else:
                metrics[dest_key] = str(val)

    return metrics

def extract_fdr_metrics(fdr_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract FDR adjusted p-values and significance flags.
    Returns a flat dict of 'pval_<var>' and 'sig_<var>'.
    """
    metrics = {}
    if not fdr_results:
        return metrics

    data = fdr_results.get('results', fdr_results)
    p_values = data.get('adjusted_p_values', {})
    
    for var, p_val in p_values.items():
        clean_var = var.replace(" ", "_").replace("-", "_")
        metrics[f'pval_{clean_var}'] = float(p_val)
        metrics[f'sig_{clean_var}'] = float(p_val) < 0.05

    return metrics

def extract_proxy_gap(proxy_results: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract the Unexplained Variance Gap from proxy_validity results.
    """
    metrics = {}
    if not proxy_results:
        return metrics

    data = proxy_results.get('results', proxy_results)
    
    # Expected keys from calculate_unexplained_variance_gap
    if 'unexplained_variance_gap' in data:
        metrics['proxy_gap'] = float(data['unexplained_variance_gap'])
    if 'literature_max_r2' in data:
        metrics['lit_max_r2'] = float(data['literature_max_r2'])
    if 'observed_r2' in data:
        metrics['obs_r2'] = float(data['observed_r2'])

    return metrics

def extract_sensitivity_metrics(sens_results: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract GWR bandwidth sweep stability metrics.
    """
    metrics = {}
    if not sens_results:
        return metrics

    data = sens_results.get('results', sens_results)
    
    if 'r2_std_dev' in data:
        metrics['gwr_r2_stability'] = float(data['r2_std_dev'])
    if 'best_bandwidth' in data:
        metrics['gwr_best_bandwidth'] = float(data['best_bandwidth'])
    
    return metrics

def export_metrics_to_csv(
    output_path: Path,
    cv_path: Optional[Path] = None,
    fdr_path: Optional[Path] = None,
    proxy_path: Optional[Path] = None,
    sens_path: Optional[Path] = None
) -> None:
    """
    Aggregate all metric sources and write a single CSV row.
    
    SC-001: Performance Metrics (RMSE, MAE, R2)
    SC-002: Statistical Significance (Adjusted P-values)
    SC-003: Model Stability (Sensitivity)
    SC-005: Proxy Validity (Unexplained Variance Gap)
    SC-006: Literature Comparison (Gap calculation)
    """
    if cv_path is None:
        cv_path = PATHS.get('results_dir', Path('data/results')) / 'spatial_cv_results.json'
    if fdr_path is None:
        fdr_path = PATHS.get('results_dir', Path('data/results')) / 'fdr_results.json'
    if proxy_path is None:
        proxy_path = PATHS.get('results_dir', Path('data/results')) / 'proxy_validity_results.json'
    if sens_path is None:
        sens_path = PATHS.get('results_dir', Path('data/results')) / 'sensitivity_results.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load all sources
    cv_data = load_json_safe(cv_path)
    fdr_data = load_json_safe(fdr_path)
    proxy_data = load_json_safe(proxy_path)
    sens_data = load_json_safe(sens_path)

    # Aggregate metrics
    all_metrics = {}
    
    # Add CV Metrics
    all_metrics.update(extract_cv_metrics(cv_data))
    
    # Add FDR Metrics
    all_metrics.update(extract_fdr_metrics(fdr_data))
    
    # Add Proxy Validity Metrics
    all_metrics.update(extract_proxy_gap(proxy_data))
    
    # Add Sensitivity Metrics
    all_metrics.update(extract_sensitivity_metrics(sens_data))

    # Add timestamp
    import datetime
    all_metrics['export_timestamp'] = datetime.datetime.now().isoformat()

    # Write to CSV
    # Determine all keys to ensure consistent columns if file exists
    fieldnames = sorted(all_metrics.keys())
    
    file_exists = output_path.exists()
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(all_metrics)

    logger.info(f"Metrics exported successfully to {output_path}")

def main():
    """Entry point for metrics export."""
    logger.info("Starting metrics export process...")
    
    # Define paths relative to project root
    results_dir = PATHS.get('results_dir', Path('data/results'))
    output_file = results_dir / 'metrics.csv'
    
    # Define source files based on previous tasks
    cv_file = results_dir / 'spatial_cv_results.json'
    fdr_file = results_dir / 'fdr_results.json'
    proxy_file = results_dir / 'proxy_validity_results.json'
    sens_file = results_dir / 'sensitivity_results.json'
    
    export_metrics_to_csv(
        output_path=output_file,
        cv_path=cv_file,
        fdr_path=fdr_file,
        proxy_path=proxy_file,
        sens_path=sens_file
    )
    
    logger.info("Metrics export completed.")

if __name__ == "__main__":
    main()
