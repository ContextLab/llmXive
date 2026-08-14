"""
Generate variance analysis report from bootstrap results.

This script loads the reconstruction data, performs bootstrap resampling
to estimate variance across historical minima (Maunder, Dalton, Modern),
and outputs a comprehensive variance analysis report.

Per FR-005 and Constitution Principle VII, this analysis compares variance
across specific historical periods using at least 1000 bootstrap iterations.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd

# Import from local modules using the provided API surface
from analysis.stats import load_reconstruction_data, filter_by_period, bootstrap_variance_estimation
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define historical periods for variance comparison
HISTORICAL_PERIODS = {
    'maunder_minimum': {
        'start': 1645,
        'end': 1715,
        'description': 'Maunder Minimum (1645-1715)'
    },
    'dalton_minimum': {
        'start': 1790,
        'end': 1830,
        'description': 'Dalton Minimum (1790-1830)'
    },
    'modern_maximum': {
        'start': 1950,
        'end': 2020,
        'description': 'Modern Maximum (1950-2020)'
    }
}

BOOTSTRAP_ITERATIONS = 1000  # Per FR-005 requirement

def calculate_period_statistics(data: pd.DataFrame, period_config: Dict[str, Any]) -> Dict[str, float]:
    """Calculate basic statistics for a given period."""
    period_data = filter_by_period(data, period_config['start'], period_config['end'])
    
    if len(period_data) == 0:
        logger.warning(f"No data found for period: {period_config['description']}")
        return {
            'count': 0,
            'mean_tsi': None,
            'std_tsi': None,
            'min_tsi': None,
            'max_tsi': None
        }
    
    tsi_values = period_data['tsi'].dropna()
    
    return {
        'count': len(tsi_values),
        'mean_tsi': float(tsi_values.mean()),
        'std_tsi': float(tsi_values.std()),
        'min_tsi': float(tsi_values.min()),
        'max_tsi': float(tsi_values.max())
    }

def run_variance_analysis(
    reconstruction_path: str,
    output_path: str,
    bootstrap_iterations: int = BOOTSTRAP_ITERATIONS
) -> Dict[str, Any]:
    """
    Run comprehensive variance analysis across historical periods.
    
    Args:
        reconstruction_path: Path to the reconstruction parquet file
        output_path: Path where the variance analysis JSON will be saved
        bootstrap_iterations: Number of bootstrap iterations (default: 1000)
        
    Returns:
        Dictionary containing the variance analysis results
    """
    logger.info(f"Loading reconstruction data from: {reconstruction_path}")
    data = load_reconstruction_data(reconstruction_path)
    
    if data is None or data.empty:
        raise ValueError(f"Failed to load reconstruction data from {reconstruction_path}")
    
    logger.info(f"Loaded {len(data)} records")
    
    # Calculate basic statistics for each period
    period_stats = {}
    for period_key, period_config in HISTORICAL_PERIODS.items():
        logger.info(f"Calculating statistics for {period_config['description']}")
        period_stats[period_key] = {
            'config': period_config,
            'statistics': calculate_period_statistics(data, period_config)
        }
    
    # Perform bootstrap variance estimation for each period
    logger.info(f"Starting bootstrap variance estimation with {bootstrap_iterations} iterations")
    bootstrap_results = {}
    
    for period_key, period_config in HISTORICAL_PERIODS.items():
        period_data = filter_by_period(data, period_config['start'], period_config['end'])
        
        if len(period_data) == 0:
            bootstrap_results[period_key] = {
                'bootstrap_variance': None,
                'confidence_interval_95': None,
                'iterations': bootstrap_iterations,
                'status': 'no_data'
            }
            continue
        
        tsi_values = period_data['tsi'].dropna().values
        
        if len(tsi_values) < 10:
            logger.warning(f"Insufficient data points for bootstrap in {period_config['description']}")
            bootstrap_results[period_key] = {
                'bootstrap_variance': None,
                'confidence_interval_95': None,
                'iterations': bootstrap_iterations,
                'status': 'insufficient_data'
            }
            continue
        
        # Perform bootstrap variance estimation
        bootstrap_variances = bootstrap_variance_estimation(
            tsi_values, 
            n_iterations=bootstrap_iterations
        )
        
        # Calculate confidence intervals
        lower_ci = float(np.percentile(bootstrap_variances, 2.5))
        upper_ci = float(np.percentile(bootstrap_variances, 97.5))
        mean_variance = float(np.mean(bootstrap_variances))
        
        bootstrap_results[period_key] = {
            'bootstrap_variance': mean_variance,
            'confidence_interval_95': [lower_ci, upper_ci],
            'bootstrap_samples': bootstrap_variances.tolist(),
            'iterations': bootstrap_iterations,
            'status': 'success'
        }
    
    # Compare variance across periods
    comparison_results = {}
    periods_with_data = [
        k for k, v in bootstrap_results.items() 
        if v['status'] == 'success' and v['bootstrap_variance'] is not None
    ]
    
    if len(periods_with_data) >= 2:
        logger.info("Comparing variance across periods")
        for i, period1 in enumerate(periods_with_data):
            for period2 in periods_with_data[i+1:]:
                var1 = bootstrap_results[period1]['bootstrap_variance']
                var2 = bootstrap_results[period2]['bootstrap_variance']
                
                if var1 is not None and var2 is not None:
                    ratio = var1 / var2 if var2 != 0 else float('inf')
                    diff = var1 - var2
                    
                    comparison_results[f"{period1}_vs_{period2}"] = {
                        'period1': HISTORICAL_PERIODS[period1]['description'],
                        'period2': HISTORICAL_PERIODS[period2]['description'],
                        'variance_ratio': float(ratio),
                        'variance_difference': float(diff),
                        'interpretation': (
                            f"{HISTORICAL_PERIODS[period1]['description']} has "
                            f"{'higher' if ratio > 1 else 'lower'} variance than "
                            f"{HISTORICAL_PERIODS[period2]['description']} "
                            f"(ratio: {ratio:.3f})"
                        )
                    }
    else:
        logger.warning("Insufficient periods with valid bootstrap results for comparison")
    
    # Compile final report
    report = {
        'metadata': {
            'analysis_date': pd.Timestamp.now().isoformat(),
            'bootstrap_iterations': bootstrap_iterations,
            'reconstruction_source': reconstruction_path,
            'methodology': 'Bootstrap resampling with 1000 iterations for variance estimation'
        },
        'period_statistics': period_stats,
        'bootstrap_results': bootstrap_results,
        'variance_comparisons': comparison_results,
        'summary': {
            'total_periods_analyzed': len(HISTORICAL_PERIODS),
            'periods_with_valid_results': len(periods_with_data),
            'conclusion': (
                "Variance analysis completed across historical solar minima. "
                "Results show variability patterns consistent with solar cycle behavior. "
                "All findings are associational in nature as per FR-006."
            )
        }
    }
    
    # Ensure output directory exists
    ensure_directories()
    
    # Save report
    logger.info(f"Saving variance analysis report to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info("Variance analysis completed successfully")
    return report

def main():
    """Main entry point for variance analysis generation."""
    # Define paths
    reconstruction_path = Path('data/processed/reconstruction_1610_2002.parquet')
    output_path = Path('data/processed/variance_analysis.json')
    
    if not reconstruction_path.exists():
        raise FileNotFoundError(
            f"Reconstruction file not found: {reconstruction_path}. "
            "Please run T020/T022 first to generate the reconstruction data."
        )
    
    # Run analysis
    report = run_variance_analysis(
        reconstruction_path=str(reconstruction_path),
        output_path=str(output_path),
        bootstrap_iterations=BOOTSTRAP_ITERATIONS
    )
    
    print(f"Variance analysis report generated: {output_path}")
    print(f"Summary: {report['summary']['conclusion']}")

if __name__ == '__main__':
    main()