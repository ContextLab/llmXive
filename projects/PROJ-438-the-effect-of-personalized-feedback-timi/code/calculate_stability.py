import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

from config import load_config, get_config_value
from logging_config import get_logger, info, error, warning

def load_sensitivity_results(filepath: str) -> pd.DataFrame:
    """Load sensitivity analysis results from CSV."""
    if not os.path.exists(filepath):
        error(f"Sensitivity results file not found: {filepath}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filepath)
        info(f"Loaded {len(df)} rows from {filepath}")
        return df
    except Exception as e:
        error(f"Failed to load sensitivity results: {e}")
        return pd.DataFrame()

def calculate_significance_stability(
    sensitivity_data: pd.DataFrame,
    p_threshold: float = 0.05
) -> Tuple[float, pd.DataFrame]:
    """
    Calculate 'significance stability' as the proportion of shifts where p < 0.05.
    
    This is the proportion of boundary variations that maintain the same 
    significance conclusion as the baseline (shift=0).
    
    Args:
        sensitivity_data: DataFrame with columns:
            - boundary_shift: float
            - p_value: float
            - is_significant: bool
        p_threshold: Significance threshold (default 0.05)
    
    Returns:
        Tuple of (stability_rate, detailed_results_df)
    """
    if sensitivity_data.empty:
        error("Sensitivity data is empty")
        return 0.0, pd.DataFrame()
    
    # Determine baseline significance (at shift=0)
    baseline_row = sensitivity_data[sensitivity_data['boundary_shift'] == 0.0]
    if baseline_row.empty:
        warning("No baseline row (shift=0) found")
        baseline_row = sensitivity_data.iloc[[0]]
    
    baseline_significant = baseline_row['is_significant'].iloc[0]
    
    # Stability: proportion of shifts with SAME significance as baseline
    stable = sensitivity_data['is_significant'] == baseline_significant
    stability_rate = stable.sum() / len(sensitivity_data)
    
    # Create detailed results
    detailed_results = sensitivity_data.copy()
    detailed_results['baseline_significant'] = baseline_significant
    detailed_results['is_stable'] = stable
    
    info(f"Calculated significance stability: {stability_rate:.4f}")
    info(f"Baseline significance (shift=0): {baseline_significant}")
    
    return stability_rate, detailed_results

def save_stability_report(
    stability_rate: float,
    detailed_results: pd.DataFrame,
    output_path: str,
    config: Dict
) -> None:
    """Save stability report to CSV."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary_data = {
        'metric': 'significance_stability',
        'value': stability_rate,
        'threshold': config['p_threshold'],
        'total_shifts_analyzed': len(detailed_results),
        'stable_shifts': detailed_results['is_stable'].sum(),
        'baseline_significant': detailed_results['baseline_significant'].iloc[0] if not detailed_results.empty else None,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv(output_path, index=False)
    info(f"Saved stability report to {output_path}")

def main():
    """Main entry point for Task T033 - Stability calculation."""
    logger = get_logger(__name__)
    logger.info("Starting significance stability calculation (Task T033)")
    
    try:
        config = load_config()
        p_threshold = get_config_value(config, 'sensitivity.p_threshold', 0.05)
        
        sensitivity_path = get_config_value(config, 'paths.processed', 'data/processed') + '/sensitivity_analysis_results.csv'
        sensitivity_data = load_sensitivity_results(sensitivity_path)
        
        if sensitivity_data.empty:
            error("No sensitivity data available")
            sys.exit(1)
        
        stability_rate, detailed_results = calculate_significance_stability(
            sensitivity_data, p_threshold
        )
        
        output_path = get_config_value(config, 'paths.processed', 'data/processed') + '/significance_stability_report.csv'
        save_stability_report(stability_rate, detailed_results, output_path, {'p_threshold': p_threshold})
        
        logger.info(f"Task T033 completed. Stability: {stability_rate:.4f}")
        
    except Exception as e:
        error(f"Error in stability calculation: {e}")
        raise

if __name__ == "__main__":
    main()