"""
calculate_flip_rate.py

Implements the calculation of 'significance flip rate' as required by SC-003.
The flip rate is the proportion of sensitivity shifts where the statistical
conclusion (significant vs. not significant) changes compared to the baseline.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import load_config
from logging_config import get_logger, info, error, warning, debug

logger = get_logger(__name__)

def load_flip_rate_config() -> Dict[str, Any]:
    """Load configuration for flip rate calculation."""
    config = load_config()
    # Ensure necessary keys exist with defaults
    if 'sensitivity' not in config:
        config['sensitivity'] = {}
    if 'threshold' not in config['sensitivity']:
        config['sensitivity']['threshold'] = 0.05
    
    return config

def calculate_significance_flip_rate(
    baseline_results: pd.DataFrame,
    sensitivity_results: pd.DataFrame,
    threshold: float = 0.05,
    p_value_column: str = 'p_value'
) -> Tuple[float, pd.DataFrame]:
    """
    Calculate the significance flip rate.
    
    A 'flip' occurs when a comparison that was significant (p < threshold)
    in the baseline becomes non-significant (p >= threshold) in a sensitivity
    run, or vice-versa.
    
    Args:
        baseline_results: DataFrame with baseline model results (must have 
                          comparison identifier and p-value).
        sensitivity_results: DataFrame with sensitivity analysis results 
                             (must have comparison identifier, run identifier, 
                             and p-value).
        threshold: Significance threshold (default 0.05).
        p_value_column: Name of the column containing p-values.
                        
    Returns:
        Tuple of (flip_rate, detailed_flips_df)
    """
    if baseline_results.empty:
        raise ValueError("Baseline results DataFrame is empty.")
    if sensitivity_results.empty:
        raise ValueError("Sensitivity results DataFrame is empty.")
        
    # Ensure p-values are numeric
    baseline_results = baseline_results.copy()
    sensitivity_results = sensitivity_results.copy()
    
    baseline_results[p_value_column] = pd.to_numeric(
        baseline_results[p_value_column], errors='coerce'
    )
    sensitivity_results[p_value_column] = pd.to_numeric(
        sensitivity_results[p_value_column], errors='coerce'
    )
    
    # Drop rows with NaN p-values
    baseline_results = baseline_results.dropna(subset=[p_value_column])
    sensitivity_results = sensitivity_results.dropna(subset=[p_value_column])
    
    # Determine significance in baseline
    baseline_significance = baseline_results[p_value_column] < threshold
    
    # Merge baseline with sensitivity results
    # We need to compare each sensitivity run against the baseline for each comparison
    # Assuming 'comparison' is the identifier column
    comparison_col = 'comparison'
    if comparison_col not in baseline_results.columns:
        # Try to infer from context or raise error
        raise KeyError(f"Comparison column '{comparison_col}' not found in baseline results.")
    
    if comparison_col not in sensitivity_results.columns:
        raise KeyError(f"Comparison column '{comparison_col}' not found in sensitivity results.")
        
    # Create a baseline lookup
    baseline_lookup = baseline_results.set_index(comparison_col)[p_value_column].to_dict()
    baseline_sig_lookup = baseline_significance.set_index(baseline_results[comparison_col]).to_dict()
    
    flip_counts = 0
    total_comparisons = 0
    flip_details = []
    
    # Group sensitivity results by comparison
    for comp_id, group in sensitivity_results.groupby(comparison_col):
        if comp_id not in baseline_lookup:
            continue
            
        baseline_p = baseline_lookup[comp_id]
        baseline_sig = baseline_sig_lookup[comp_id]
        
        for _, row in group.iterrows():
            sens_p = row[p_value_column]
            sens_sig = sens_p < threshold
            
            total_comparisons += 1
            
            # Check for flip
            if baseline_sig != sens_sig:
                flip_counts += 1
                flip_details.append({
                    'comparison': comp_id,
                    'run_id': row.get('run_id', 'unknown'),
                    'baseline_p': baseline_p,
                    'sensitivity_p': sens_p,
                    'baseline_significant': baseline_sig,
                    'sensitivity_significant': sens_sig,
                    'flip': True
                })
            else:
                flip_details.append({
                    'comparison': comp_id,
                    'run_id': row.get('run_id', 'unknown'),
                    'baseline_p': baseline_p,
                    'sensitivity_p': sens_p,
                    'baseline_significant': baseline_sig,
                    'sensitivity_significant': sens_sig,
                    'flip': False
                })
    
    if total_comparisons == 0:
        logger.warning("No valid comparisons found to calculate flip rate.")
        flip_rate = 0.0
    else:
        flip_rate = flip_counts / total_comparisons
        
    flip_df = pd.DataFrame(flip_details)
    
    info(f"Calculated significance flip rate: {flip_rate:.4f} ({flip_counts}/{total_comparisons} comparisons flipped)")
    return flip_rate, flip_df

def save_flip_rate_report(
    flip_rate: float,
    flip_details_df: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Save the flip rate calculation results to a CSV report.
    
    Args:
        flip_rate: The calculated flip rate (float).
        flip_details_df: DataFrame with detailed flip information.
        output_path: Path to save the report CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create summary report
    summary_data = {
        'metric': 'significance_flip_rate',
        'value': flip_rate,
        'total_comparisons': len(flip_details_df),
        'flipped_comparisons': flip_details_df['flip'].sum(),
        'threshold': 0.05
    }
    
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv(output_path, index=False)
    
    info(f"Saved flip rate report to {output_path}")
    
    # Also save detailed flips for debugging/audit
    detailed_path = output_path.parent / f"{output_path.stem}_details.csv"
    flip_details_df.to_csv(detailed_path, index=False)
    info(f"Saved detailed flip analysis to {detailed_path}")

def main():
    """Main entry point for calculating significance flip rate."""
    logger.info("Starting significance flip rate calculation (T034)")
    
    # Load configuration
    config = load_flip_rate_config()
    threshold = config['sensitivity'].get('threshold', 0.05)
    
    # Define paths
    data_dir = project_root / "data" / "processed"
    baseline_path = data_dir / "results_metrics.csv"
    sensitivity_path = data_dir / "sensitivity_analysis_results.csv"
    output_path = data_dir / "significance_flip_rate.csv"
    
    # Check if input files exist
    if not baseline_path.exists():
        error(f"Baseline results file not found: {baseline_path}")
        error("Please run models.py and generate_results_metrics.py first.")
        sys.exit(1)
        
    if not sensitivity_path.exists():
        error(f"Sensitivity results file not found: {sensitivity_path}")
        error("Please run sensitivity.py first to generate sensitivity analysis results.")
        sys.exit(1)
    
    # Load data
    try:
        baseline_results = pd.read_csv(baseline_path)
        sensitivity_results = pd.read_csv(sensitivity_path)
    except Exception as e:
        error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(baseline_results)} baseline results")
    logger.info(f"Loaded {len(sensitivity_results)} sensitivity results")
    
    # Calculate flip rate
    try:
        flip_rate, flip_details = calculate_significance_flip_rate(
            baseline_results,
            sensitivity_results,
            threshold=threshold
        )
    except Exception as e:
        error(f"Failed to calculate flip rate: {e}")
        sys.exit(1)
    
    # Save report
    try:
        save_flip_rate_report(flip_rate, flip_details, output_path)
    except Exception as e:
        error(f"Failed to save flip rate report: {e}")
        sys.exit(1)
    
    logger.info("Significance flip rate calculation completed successfully")
    logger.info(f"Flip rate: {flip_rate:.4f}")
    
    return flip_rate

if __name__ == "__main__":
    main()
