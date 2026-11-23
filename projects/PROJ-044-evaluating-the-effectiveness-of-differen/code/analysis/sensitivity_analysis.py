"""
T025: Implement sensitivity analysis sweep for α across a range of representative values.

This module calculates slope ratios for accuracy vs. ε curves for α=0.1 and α=1.0
as part of the sensitivity analysis.

Dependencies:
- T027a (Time Filter)
- T035 (Utility Collapse Filter)

Input: results/filtered_data.csv (produced by T035)
Output: results/sensitivity_analysis.csv, results/sensitivity_report.md
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# Import from existing project modules
from analysis.stats import load_filtered_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ALPHA_VALUES = [0.1, 0.5, 1.0]  # Representative α values per task description
EPSILON_TARGETS = [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]  # Representative ε values
OUTPUT_DIR = Path("results")

def calculate_slope(
    df: pd.DataFrame, 
    alpha: float, 
    epsilon_values: List[float]
) -> Dict[float, float]:
    """
    Calculate the slope of accuracy vs. ε for a specific α value.
    
    Args:
        df: Filtered DataFrame with columns: alpha, epsilon, global_accuracy
        alpha: The α value to filter by
        epsilon_values: List of ε values to consider
        
    Returns:
        Dictionary mapping ε to accuracy (or slope if only two points)
    """
    # Filter by α
    alpha_df = df[df['alpha'] == alpha].copy()
    
    if alpha_df.empty:
        logger.warning(f"No data found for alpha={alpha}")
        return {}
    
    # Group by epsilon and calculate mean accuracy
    epsilon_acc = alpha_df.groupby('epsilon')['global_accuracy'].mean().reset_index()
    epsilon_acc = epsilon_acc[epsilon_acc['epsilon'].isin(epsilon_values)]
    
    if len(epsilon_acc) < 2:
        logger.warning(f"Insufficient data points for alpha={alpha} (need >= 2)")
        return {}
    
    # Sort by epsilon
    epsilon_acc = epsilon_acc.sort_values('epsilon')
    
    # Calculate slope using linear regression
    x = epsilon_acc['epsilon'].values
    y = epsilon_acc['global_accuracy'].values
    
    # Use scipy.stats.linregress for slope calculation
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    logger.info(f"Slope for alpha={alpha}: {slope:.6f} (r²={r_value**2:.4f})")
    
    # Return individual accuracies for each epsilon
    return dict(zip(epsilon_acc['epsilon'], epsilon_acc['global_accuracy']))

def calculate_slope_ratio(
    slope_alpha_01: float, 
    slope_alpha_10: float
) -> float:
    """
    Calculate the ratio of slopes between α=0.1 and α=1.0.
    
    This ratio indicates how much more (or less) sensitive the model is to 
    privacy budget changes under high heterogeneity (α=0.1) vs. balanced (α=1.0).
    
    Args:
        slope_alpha_01: Slope for α=0.1
        slope_alpha_10: Slope for α=1.0
        
    Returns:
        Slope ratio (slope_01 / slope_10)
    """
    if abs(slope_alpha_10) < 1e-10:
        logger.warning("Slope for α=1.0 is near zero, ratio may be unstable")
        return float('inf') if slope_alpha_01 > 0 else float('-inf')
    
    ratio = slope_alpha_01 / slope_alpha_10
    logger.info(f"Slope ratio (α=0.1 / α=1.0): {ratio:.4f}")
    return ratio

def generate_sensitivity_analysis(
    df: pd.DataFrame,
    output_dir: Path = OUTPUT_DIR
) -> Tuple[pd.DataFrame, Dict]:
    """
    Main function to generate sensitivity analysis results.
    
    Args:
        df: Filtered DataFrame from T035
        output_dir: Directory to save results
        
    Returns:
        Tuple of (results DataFrame, analysis metadata dict)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    slopes = {}
    
    # Calculate slopes for each α value
    for alpha in ALPHA_VALUES:
        acc_map = calculate_slope(df, alpha, EPSILON_TARGETS)
        if acc_map:
            slopes[alpha] = acc_map
            # Store per-epsilon accuracy for this alpha
            for epsilon, accuracy in acc_map.items():
                results.append({
                    'alpha': alpha,
                    'epsilon': epsilon,
                    'accuracy': accuracy
                })
    
    # Calculate slope ratios between key pairs
    analysis_metadata = {
        'slopes': {},
        'slope_ratios': {}
    }
    
    if 0.1 in slopes and 1.0 in slopes:
        # Extract slopes (linear regression coefficient)
        # We need to recalculate the actual slope value, not just the accuracies
        slope_01 = _calculate_regression_slope(df, 0.1, EPSILON_TARGETS)
        slope_10 = _calculate_regression_slope(df, 1.0, EPSILON_TARGETS)
        
        if slope_01 is not None and slope_10 is not None:
            ratio = calculate_slope_ratio(slope_01, slope_10)
            analysis_metadata['slopes']['alpha_01'] = slope_01
            analysis_metadata['slopes']['alpha_10'] = slope_10
            analysis_metadata['slope_ratios']['alpha_01_vs_10'] = ratio
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results
    results_csv_path = output_dir / 'sensitivity_analysis.csv'
    results_df.to_csv(results_csv_path, index=False)
    logger.info(f"Saved sensitivity analysis to {results_csv_path}")
    
    # Generate report
    report_path = output_dir / 'sensitivity_report.md'
    _generate_report(results_df, analysis_metadata, report_path)
    
    return results_df, analysis_metadata

def _calculate_regression_slope(
    df: pd.DataFrame,
    alpha: float,
    epsilon_values: List[float]
) -> Optional[float]:
    """Helper to get the actual regression slope value."""
    alpha_df = df[df['alpha'] == alpha].copy()
    if alpha_df.empty:
        return None
    
    epsilon_acc = alpha_df.groupby('epsilon')['global_accuracy'].mean().reset_index()
    epsilon_acc = epsilon_acc[epsilon_acc['epsilon'].isin(epsilon_values)]
    
    if len(epsilon_acc) < 2:
        return None
    
    epsilon_acc = epsilon_acc.sort_values('epsilon')
    x = epsilon_acc['epsilon'].values
    y = epsilon_acc['global_accuracy'].values
    
    slope, _, _, _, _ = stats.linregress(x, y)
    return slope

def _generate_report(
    results_df: pd.DataFrame,
    analysis_metadata: Dict,
    report_path: Path
):
    """Generate a markdown report of the sensitivity analysis."""
    with open(report_path, 'w') as f:
        f.write("# Sensitivity Analysis Report\n\n")
        f.write("## Overview\n")
        f.write("This report presents the sensitivity analysis of accuracy vs. privacy budget (ε) ")
        f.write("across different data heterogeneity levels (α).\n\n")
        
        f.write("## Key Findings\n")
        if 'slope_ratios' in analysis_metadata and 'alpha_01_vs_10' in analysis_metadata['slope_ratios']:
            ratio = analysis_metadata['slope_ratios']['alpha_01_vs_10']
            f.write(f"- **Slope Ratio (α=0.1 / α=1.0)**: {ratio:.4f}\n")
            if ratio > 1:
                f.write("  - Interpretation: Model is more sensitive to privacy budget changes under high heterogeneity (α=0.1).\n")
            elif ratio < 1:
                f.write("  - Interpretation: Model is less sensitive to privacy budget changes under high heterogeneity (α=0.1).\n")
            else:
                f.write("  - Interpretation: Similar sensitivity across heterogeneity levels.\n")
        
        f.write("\n## Slope Values\n")
        if 'slopes' in analysis_metadata:
            for alpha_key, slope_val in analysis_metadata['slopes'].items():
                f.write(f"- {alpha_key}: {slope_val:.6f}\n")
        
        f.write("\n## Detailed Results\n")
        f.write("Accuracy vs. ε for each α value:\n\n")
        f.write("| Alpha | Epsilon | Accuracy |\n")
        f.write("|-------|---------|----------|\n")
        for _, row in results_df.iterrows():
            f.write(f"| {row['alpha']:.1f} | {row['epsilon']:.2f} | {row['accuracy']:.4f} |\n")
        
        f.write("\n## Methodology\n")
        f.write("- Data source: `results/filtered_data.csv` (filtered by T027a and T035)\n")
        f.write("- α values tested: 0.1, 0.5, 1.0\n")
        f.write("- ε values tested: 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0\n")
        f.write("- Slope calculated via linear regression (scipy.stats.linregress)\n")
        f.write("- Slope ratio = slope(α=0.1) / slope(α=1.0)\n")

def main():
    """Entry point for the sensitivity analysis script."""
    logger.info("Starting sensitivity analysis (T025)...")
    
    # Load filtered data
    filtered_df = load_filtered_data()
    
    if filtered_df is None or filtered_df.empty:
        logger.error("No filtered data available. Ensure T027a and T035 have completed.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(filtered_df)} records from filtered data")
    
    # Run analysis
    results_df, metadata = generate_sensitivity_analysis(filtered_df)
    
    logger.info("Sensitivity analysis completed successfully")
    logger.info(f"Results saved to results/sensitivity_analysis.csv")
    logger.info(f"Report saved to results/sensitivity_report.md")
    
    # Print summary
    if 'slope_ratios' in metadata and 'alpha_01_vs_10' in metadata['slope_ratios']:
        ratio = metadata['slope_ratios']['alpha_01_vs_10']
        logger.info(f"Slope ratio (α=0.1 vs α=1.0): {ratio:.4f}")

if __name__ == "__main__":
    main()