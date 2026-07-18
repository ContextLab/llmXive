import os
import sys
import csv
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results():
    """
    Load analysis results from data/processed/complexity_metrics.csv or similar.
    Expects a file containing correlation results (p-values) for each electrode.
    """
    # The analysis.py task (T019/T020) should have produced a results file.
    # We look for the standard output of the correlation analysis.
    # Based on T019/T020, the analysis produces a table of correlations.
    # We assume the file 'data/processed/correlation_results.csv' exists from T019/T020.
    # If not, we check for 'data/processed/complexity_metrics.csv' but that usually holds raw metrics, not p-values.
    # Per T018/T019, the analysis script outputs correlation stats.
    
    results_path = Path(__file__).parent.parent / "data" / "processed" / "correlation_results.csv"
    
    if not results_path.exists():
        # Fallback: check if analysis output is named differently or in a different location
        # Sometimes analysis outputs are in data/results/
        alt_path = Path(__file__).parent.parent / "data" / "results" / "correlation_results.csv"
        if alt_path.exists():
            results_path = alt_path
        else:
            logger.error("Correlation results file not found. Please ensure code/analysis.py has run successfully.")
            sys.exit(1)

    try:
        df = pd.read_csv(results_path)
        # Validate expected columns
        required_cols = ['electrode', 'p_value']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns in {results_path}. Found: {df.columns.tolist()}")
            sys.exit(1)
        return df
    except Exception as e:
        logger.error(f"Failed to load analysis results: {e}")
        sys.exit(1)

def run_sensitivity_analysis(correlation_df, thresholds=None):
    """
    Perform sensitivity analysis at specified p-value thresholds.
    
    Args:
        correlation_df: DataFrame with 'electrode' and 'p_value' columns.
        thresholds: List of float thresholds (e.g., [0.05, 0.01]).
    
    Returns:
        List of dicts with sensitivity analysis results.
    """
    if thresholds is None:
        thresholds = [0.05, 0.01]
    
    total_electrodes = len(correlation_df)
    results = []
    
    for threshold in thresholds:
        significant_count = int((correlation_df['p_value'] <= threshold).sum())
        results.append({
            'threshold': threshold,
            'count_significant': significant_count,
            'total_electrodes': total_electrodes
        })
        logger.info(f"Threshold p<={threshold}: {significant_count} significant out of {total_electrodes}")
    
    return results

def generate_sensitivity_table(results, output_path):
    """
    Generate the sensitivity analysis table CSV.
    
    Args:
        results: List of dicts from run_sensitivity_analysis.
        output_path: Path to write the CSV file.
    """
    df = pd.DataFrame(results)
    # Ensure column order matches spec: threshold, count_significant, total_electrodes
    df = df[['threshold', 'count_significant', 'total_electrodes']]
    
    # Ensure types are correct
    df['threshold'] = df['threshold'].astype(float)
    df['count_significant'] = df['count_significant'].astype(int)
    df['total_electrodes'] = df['total_electrodes'].astype(int)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity table written to {output_path}")

def main():
    logger.info("Starting sensitivity analysis pipeline.")
    
    # Load config
    config = load_config()
    
    # Load analysis results (p-values from correlation analysis)
    correlation_df = load_analysis_results()
    
    # Define thresholds
    thresholds = config.get('sensitivity_analysis', {}).get('thresholds', [0.05, 0.01])
    
    # Run analysis
    results = run_sensitivity_analysis(correlation_df, thresholds)
    
    # Generate output table
    output_path = Path(__file__).parent.parent / "data" / "analysis" / "sensitivity_table.csv"
    generate_sensitivity_table(results, output_path)
    
    logger.info("Sensitivity analysis completed successfully.")

if __name__ == "__main__":
    main()
