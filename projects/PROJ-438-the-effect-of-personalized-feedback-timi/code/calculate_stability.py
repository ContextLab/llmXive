"""
Calculate Significance Stability from Sensitivity Analysis Results.

This module implements Task T033: Calculate and report "significance stability" 
(proportion of shifts where p < 0.05) using output from T032 (sensitivity analysis).

It loads the sensitivity analysis results, computes the proportion of boundary 
shifts where the primary comparison (Immediate vs Delayed) remains significant, 
and saves a detailed report.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from logging_config import get_logger, info, warning, error, debug

# Initialize logger
logger = get_logger(__name__)

def load_sensitivity_results(config: Dict) -> pd.DataFrame:
    """
    Load the sensitivity analysis results from T032.
    
    Expected file: data/processed/sensitivity_analysis_results.csv
    
    Expected columns:
    - shift_type: Description of the boundary shift (e.g., '2h_minus_0.01h')
    - comparison: The pairwise comparison (e.g., 'Immediate vs Delayed')
    - p_value: The p-value for this comparison under this shift
    - significant: Boolean indicating if p < 0.05
    """
    config_path = config.get('paths', {}).get('processed_data', 'data/processed')
    input_file = Path(config_path) / 'sensitivity_analysis_results.csv'
    
    if not input_file.exists():
        error(f"Sensitivity results file not found: {input_file}")
        error("Please ensure T032 (sensitivity.py) has been run successfully.")
        raise FileNotFoundError(f"Sensitivity results file not found: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        info(f"Loaded {len(df)} rows from sensitivity results: {input_file}")
        return df
    except Exception as e:
        error(f"Failed to load sensitivity results: {e}")
        raise

def calculate_significance_stability(df: pd.DataFrame, target_comparison: str = "Immediate vs Delayed") -> Dict:
    """
    Calculate the significance stability metric.
    
    Stability is defined as the proportion of boundary shifts where the 
    primary comparison remains statistically significant (p < 0.05).
    
    Args:
        df: DataFrame containing sensitivity analysis results with columns:
            - comparison: The pairwise comparison name
            - p_value: The p-value
            - significant: Boolean (True if p < 0.05)
        target_comparison: The comparison to focus on for stability calculation.
                           Default: "Immediate vs Delayed"
                           
    Returns:
        Dictionary containing:
        - total_shifts: Total number of boundary shifts analyzed
        - significant_count: Number of shifts where comparison was significant
        - stability_proportion: Proportion of shifts where p < 0.05
        - stability_percentage: Stability as a percentage
        - target_comparison: The comparison analyzed
    """
    if df.empty:
        error("Input DataFrame is empty. Cannot calculate stability.")
        raise ValueError("Input DataFrame is empty.")
    
    # Filter for the target comparison
    target_df = df[df['comparison'] == target_comparison]
    
    if target_df.empty:
        error(f"No data found for comparison: {target_comparison}")
        error(f"Available comparisons: {df['comparison'].unique()}")
        raise ValueError(f"No data found for comparison: {target_comparison}")
    
    total_shifts = len(target_df)
    significant_count = target_df['significant'].sum()
    
    if total_shifts == 0:
        stability_proportion = 0.0
    else:
        stability_proportion = significant_count / total_shifts
    
    stability_percentage = stability_proportion * 100
    
    results = {
        'total_shifts': total_shifts,
        'significant_count': int(significant_count),
        'stability_proportion': stability_proportion,
        'stability_percentage': stability_percentage,
        'target_comparison': target_comparison,
        'breakdown': target_df.to_dict('records')
    }
    
    info(f"Stability calculated: {significant_count}/{total_shifts} ({stability_percentage:.2f}%)")
    return results

def save_stability_report(results: Dict, config: Dict) -> Path:
    """
    Save the stability report to a CSV file.
    
    Output file: data/processed/significance_stability_report.csv
    
    The report includes:
    - Summary metrics (total shifts, significant count, stability proportion)
    - Detailed breakdown of each shift's result
    """
    config_path = config.get('paths', {}).get('processed_data', 'data/processed')
    output_dir = Path(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'significance_stability_report.csv'
    
    # Create summary row
    summary_row = {
        'metric': 'significance_stability',
        'target_comparison': results['target_comparison'],
        'total_shifts': results['total_shifts'],
        'significant_count': results['significant_count'],
        'stability_proportion': results['stability_proportion'],
        'stability_percentage': results['stability_percentage'],
        'interpretation': 'High stability' if results['stability_proportion'] >= 0.9 else 
                        'Moderate stability' if results['stability_proportion'] >= 0.7 else 
                        'Low stability'
    }
    
    # Convert to DataFrame
    summary_df = pd.DataFrame([summary_row])
    
    # Save to CSV
    summary_df.to_csv(output_file, index=False)
    
    info(f"Stability report saved to: {output_file}")
    info(f"Stability: {results['stability_proportion']:.4f} ({results['stability_percentage']:.2f}%)")
    
    return output_file

def main():
    """Main entry point for calculating significance stability."""
    logger.info("Starting significance stability calculation (T033)...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Load sensitivity results from T032
        sensitivity_df = load_sensitivity_results(config)
        
        # Calculate stability
        stability_results = calculate_significance_stability(sensitivity_df)
        
        # Save report
        output_path = save_stability_report(stability_results, config)
        
        logger.info("Significance stability calculation completed successfully.")
        logger.info(f"Output file: {output_path}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Ensure T032 (sensitivity analysis) has been run first.")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during stability calculation: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
