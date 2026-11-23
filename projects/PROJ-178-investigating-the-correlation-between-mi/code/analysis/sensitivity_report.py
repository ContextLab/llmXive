import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_sensitivity_results(filepath: str) -> pd.DataFrame:
    """Load sensitivity results from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Results not found at {filepath}")
    return pd.read_csv(path)

def aggregate_and_format_report(threshold_df: pd.DataFrame, subgroup_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate results into a comprehensive report."""
    report = []
    
    # Threshold variation
    if not threshold_df.empty:
        coeffs = threshold_df['coefficient'].dropna()
        if len(coeffs) > 0:
            report.append({
                'metric': 'threshold_variation_range',
                'value': coeffs.max() - coeffs.min()
            })
            report.append({
                'metric': 'threshold_variation_std',
                'value': coeffs.std()
            })
    
    # Subgroup variation
    if not subgroup_df.empty:
        coeffs = subgroup_df['coefficient'].dropna()
        if len(coeffs) > 0:
            report.append({
                'metric': 'subgroup_variation_range',
                'value': coeffs.max() - coeffs.min()
            })
    
    return pd.DataFrame(report)

def write_report(report_df: pd.DataFrame, filepath: str):
    """Write the report to CSV."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(path, index=False)
    logger.info(f"Report written to {filepath}")

def main():
    """Main entry point for generating sensitivity report."""
    logging.basicConfig(level=logging.INFO)
    paths = get_local_paths()
    
    threshold_file = paths['processed'] / 'sensitivity_results.csv'
    subgroup_file = paths['processed'] / 'subgroup_results.csv'
    output_file = paths['processed'] / 'sensitivity_analysis.csv'
    
    if not threshold_file.exists() or not subgroup_file.exists():
        logger.error("Missing sensitivity result files.")
        sys.exit(1)
    
    threshold_df = load_sensitivity_results(str(threshold_file))
    subgroup_df = load_sensitivity_results(str(subgroup_file))
    
    report = aggregate_and_format_report(threshold_df, subgroup_df)
    write_report(report, str(output_file))

if __name__ == '__main__':
    main()
