import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Import existing utilities from project API surface
from config import load_config, get_config_value
from logging_config import get_logger, info, error, warning, debug
from calculate_stability import load_sensitivity_results

def load_flip_rate_config() -> Dict[str, Any]:
    """Load configuration for flip rate calculation."""
    config = load_config()
    return {
        'p_threshold': get_config_value(config, 'sensitivity.p_threshold', 0.05),
        'reference_group': get_config_value(config, 'sensitivity.reference_group', 'Immediate'),
        'comparison_group': get_config_value(config, 'sensitivity.comparison_group', 'Delayed'),
        'output_path': get_config_value(config, 'paths.processed', 'data/processed') + '/significance_flip_rate.csv'
    }

def calculate_significance_flip_rate(
    sensitivity_data: pd.DataFrame,
    p_threshold: float = 0.05,
    reference_group: str = 'Immediate',
    comparison_group: str = 'Delayed'
) -> Tuple[float, pd.DataFrame]:
    """
    Calculate the 'significance flip rate' as required by SC-003.
    
    The flip rate is the proportion of boundary shifts where the *conclusion* 
    (significant vs not significant) changes compared to the baseline.
    
    Args:
        sensitivity_data: DataFrame from sensitivity analysis containing:
            - boundary_shift: float (shift amount in hours)
            - p_value: float (p-value for the comparison)
            - is_significant: bool (p < p_threshold)
        p_threshold: Significance threshold (default 0.05)
        reference_group: The reference group name (e.g., 'Immediate')
        comparison_group: The comparison group name (e.g., 'Delayed')
    
    Returns:
        Tuple of (flip_rate, detailed_results_df)
    """
    if sensitivity_data.empty:
        error("Sensitivity data is empty, cannot calculate flip rate")
        return 0.0, pd.DataFrame()
    
    # Determine baseline significance (at shift=0)
    baseline_row = sensitivity_data[sensitivity_data['boundary_shift'] == 0.0]
    if baseline_row.empty:
        warning("No baseline row (shift=0) found in sensitivity data")
        # Fallback: use the first row as baseline if shift=0 missing
        baseline_row = sensitivity_data.iloc[[0]]
    
    baseline_significant = baseline_row['is_significant'].iloc[0]
    
    # Calculate flip rate: proportion of shifts where significance changed
    flips = sensitivity_data['is_significant'] != baseline_significant
    flip_count = flips.sum()
    total_shifts = len(sensitivity_data)
    
    flip_rate = flip_count / total_shifts if total_shifts > 0 else 0.0
    
    # Create detailed results DataFrame
    detailed_results = sensitivity_data.copy()
    detailed_results['baseline_significant'] = baseline_significant
    detailed_results['is_flip'] = flips
    
    info(f"Calculated significance flip rate: {flip_rate:.4f} ({flip_count}/{total_shifts} shifts)")
    info(f"Baseline significance (shift=0): {baseline_significant}")
    
    return flip_rate, detailed_results

def save_flip_rate_report(
    flip_rate: float,
    detailed_results: pd.DataFrame,
    output_path: str,
    config: Dict[str, Any]
) -> None:
    """Save the flip rate report to CSV."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create summary row
    summary_data = {
        'metric': 'significance_flip_rate',
        'value': flip_rate,
        'threshold': config['p_threshold'],
        'reference_group': config['reference_group'],
        'comparison_group': config['comparison_group'],
        'total_shifts_analyzed': len(detailed_results),
        'flips_observed': detailed_results['is_flip'].sum(),
        'baseline_significant': detailed_results['baseline_significant'].iloc[0] if not detailed_results.empty else None,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv(output_path, index=False)
    info(f"Saved flip rate report to {output_path}")

def main():
    """Main entry point for calculating significance flip rate."""
    logger = get_logger(__name__)
    logger.info("Starting significance flip rate calculation (Task T034)")
    
    try:
        # Load configuration
        config = load_flip_rate_config()
        info(f"Configuration loaded: p_threshold={config['p_threshold']}")
        
        # Load sensitivity analysis results (output from T032)
        sensitivity_path = get_config_value(config, 'paths.processed', 'data/processed') + '/sensitivity_analysis_results.csv'
        info(f"Loading sensitivity data from {sensitivity_path}")
        
        if not os.path.exists(sensitivity_path):
            error(f"Sensitivity analysis results not found at {sensitivity_path}. "
                  "Please run code/sensitivity.py first (Task T032).")
            sys.exit(1)
        
        sensitivity_data = load_sensitivity_results(sensitivity_path)
        
        if sensitivity_data is None or sensitivity_data.empty:
            error("Failed to load sensitivity data or data is empty")
            sys.exit(1)
        
        # Calculate flip rate
        flip_rate, detailed_results = calculate_significance_flip_rate(
            sensitivity_data,
            p_threshold=config['p_threshold'],
            reference_group=config['reference_group'],
            comparison_group=config['comparison_group']
        )
        
        # Save report
        save_flip_rate_report(
            flip_rate,
            detailed_results,
            config['output_path'],
            config
        )
        
        # Also append to the main results file if it exists
        results_path = get_config_value(config, 'paths.processed', 'data/processed') + '/results_metrics.csv'
        if os.path.exists(results_path):
            # Load existing results
            existing_results = pd.read_csv(results_path)
            
            # Check if flip_rate metric already exists
            if 'significance_flip_rate' not in existing_results['metric'].values:
                # Add new row for flip rate
                new_row = pd.DataFrame([{
                    'metric': 'significance_flip_rate',
                    'value': flip_rate,
                    'description': 'Proportion of boundary shifts where significance conclusion changed'
                }])
                updated_results = pd.concat([existing_results, new_row], ignore_index=True)
                updated_results.to_csv(results_path, index=False)
                info(f"Updated {results_path} with flip rate metric")
        
        logger.info(f"Task T034 completed successfully. Flip rate: {flip_rate:.4f}")
        
    except Exception as e:
        error(f"Error in flip rate calculation: {str(e)}")
        raise

if __name__ == "__main__":
    main()
