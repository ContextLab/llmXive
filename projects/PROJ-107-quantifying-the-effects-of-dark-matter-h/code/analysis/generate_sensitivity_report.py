import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_project_root, get_data_processed_path
from utils.logging import get_pipeline_logger

# Import from the existing sensitivity module
from analysis.sensitivity import (
    load_statistical_results,
    recompute_bin_assignments,
    run_statistical_test_for_binning,
    calculate_variance,
    run_sensitivity_analysis
)

logger = get_pipeline_logger(__name__)

def calculate_significance_rates(results: List[Dict[str, Any]], p_threshold: float = 0.05) -> Dict[str, float]:
    """
    Calculate the percentage of tests that reject the null hypothesis (p < threshold).
    
    Args:
        results: List of result dictionaries containing 'p_value' keys.
        p_threshold: The significance threshold (default 0.05).
        
    Returns:
        Dict mapping metric names to their significance rates (0.0 to 1.0).
    """
    if not results:
        return {}
        
    significance_counts = {}
    total_counts = {}
    
    for row in results:
        # Identify the metric being tested (usually stored in 'metric' or 'test_name')
        metric = row.get('metric', row.get('test_name', 'unknown'))
        
        p_val = row.get('p_value')
        if p_val is None:
            continue
            
        if metric not in total_counts:
            total_counts[metric] = 0
            significance_counts[metric] = 0
            
        total_counts[metric] += 1
        if p_val < p_threshold:
            significance_counts[metric] += 1
            
    rates = {}
    for metric in total_counts:
        if total_counts[metric] > 0:
            rates[metric] = significance_counts[metric] / total_counts[metric]
        else:
            rates[metric] = 0.0
            
    return rates

def calculate_p_value_variance(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the variance of p-values for each metric across the sensitivity sweep.
    
    Args:
        results: List of result dictionaries from the sensitivity sweep.
        
    Returns:
        Dict mapping metric names to their p-value variance.
    """
    import numpy as np
    
    p_values_by_metric = {}
    
    for row in results:
        metric = row.get('metric', row.get('test_name', 'unknown'))
        p_val = row.get('p_value')
        
        if p_val is not None:
            if metric not in p_values_by_metric:
                p_values_by_metric[metric] = []
            p_values_by_metric[metric].append(p_val)
            
    variances = {}
    for metric, p_vals in p_values_by_metric.items():
        if len(p_vals) > 1:
            variances[metric] = float(np.var(p_vals))
        else:
            variances[metric] = 0.0
            
    return variances

def generate_report(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Generate the sensitivity report comparing significance rates and p-value variance.
    
    This function:
    1. Loads statistical results (from T030 output or default location).
    2. Calculates significance rates across the sensitivity sweep.
    3. Calculates p-value variance for each metric.
    4. Writes a CSV report to the specified output path.
    
    Args:
        input_path: Path to the sensitivity analysis results CSV (from T030).
                   If None, uses default path `data/processed/sensitivity_report.csv`.
        output_path: Path for the final sensitivity report.
                    If None, uses `data/processed/sensitivity_report_final.csv`.
                    
    Returns:
        Path to the generated report.
    """
    if input_path is None:
        input_path = get_data_processed_path() / "sensitivity_report.csv"
    if output_path is None:
        output_path = get_data_processed_path() / "sensitivity_report_final.csv"
        
    logger.info(f"Generating sensitivity report from {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        # If the upstream T030 didn't produce a file, we cannot generate this report.
        # We raise an error to fail loudly as per constraints.
        raise FileNotFoundError(f"Sensitivity analysis input file not found: {input_path}. "
                              "Ensure T030 has completed successfully.")
                             
    # Load the raw sensitivity results
    # The input file from T030 should contain columns like:
    # threshold, metric, p_value, test_name, etc.
    results = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert p_value to float if present
            if 'p_value' in row and row['p_value']:
                try:
                    row['p_value'] = float(row['p_value'])
                except ValueError:
                    row['p_value'] = None
            results.append(row)
            
    if not results:
        logger.warning("No results found in sensitivity input file.")
        
    # Calculate metrics
    significance_rates = calculate_significance_rates(results)
    p_value_variances = calculate_p_value_variance(results)
    
    # Prepare report data
    report_data = []
    metrics = sorted(set(significance_rates.keys()) | set(p_value_variances.keys()))
    
    for metric in metrics:
        rate = significance_rates.get(metric, 0.0)
        variance = p_value_variances.get(metric, 0.0)
        
        # Determine if SC-003 is met (variance <= 0.001)
        sc_003_met = variance <= 0.001
        
        report_data.append({
            'metric': metric,
            'significance_rate': f"{rate:.4f}",
            'p_value_variance': f"{variance:.6f}",
            'sc_003_met': str(sc_003_met),
            'threshold_count': len([r for r in results if r.get('metric') == metric])
        })
        
    # Write the report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['metric', 'significance_rate', 'p_value_variance', 'sc_003_met', 'threshold_count']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_data)
        
    logger.info(f"Sensitivity report generated: {output_path}")
    logger.info(f"SC-003 Check: All variances <= 0.001? {all(r['sc_003_met'] == 'True' for r in report_data)}")
    
    return output_path

def main():
    """Main entry point for generating the sensitivity report."""
    try:
        project_root = get_project_root()
        output_path = get_data_processed_path() / "sensitivity_report_final.csv"
        
        generate_report(output_path=output_path)
        
        logger.info("Sensitivity report generation completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate sensitivity report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())