import os
import sys
import csv
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import yaml

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file):
    """Setup logging infrastructure."""
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Ensure the log file path is absolute and directory exists
    log_path = logs_dir / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    fh = logging.FileHandler(log_path, mode='a')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def load_analysis_results():
    """
    Load the main analysis results containing correlation coefficients and p-values.
    Expects data/analysis/correlation_results.csv (produced by T019/T020).
    """
    results_path = Path(__file__).parent.parent / "data" / "analysis" / "correlation_results.csv"
    
    if not results_path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {results_path}. "
                                "Please run code/analysis.py first to generate correlation results.")
    
    df = pd.read_csv(results_path)
    
    # Validate required columns
    required_cols = ['channel', 'p_value']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in analysis results: {missing_cols}")
    
    return df

def run_sensitivity_analysis(results_df, thresholds=[0.05, 0.01]):
    """
    Run sensitivity analysis at specified p-value thresholds.
    
    Args:
        results_df: DataFrame with 'channel' and 'p_value' columns.
        thresholds: List of p-value thresholds to test.
        
    Returns:
        DataFrame with 'threshold' and 'count_significant' columns.
    """
    results = []
    
    for threshold in thresholds:
        # Count channels with p_value <= threshold
        significant_count = (results_df['p_value'] <= threshold).sum()
        results.append({
            'threshold': float(threshold),
            'count_significant': int(significant_count)
        })
    
    return pd.DataFrame(results)

def generate_sensitivity_table(results_df, output_path):
    """
    Generate and save the sensitivity analysis table to CSV.
    
    Args:
        results_df: DataFrame with analysis results (p-values).
        output_path: Path to save the sensitivity table CSV.
    """
    # Run sensitivity analysis
    sensitivity_df = run_sensitivity_analysis(results_df)
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    sensitivity_df.to_csv(output_path, index=False)
    
    return sensitivity_df

def main():
    config = load_config()
    logger = setup_logger('sensitivity_analysis', 'sensitivity_analysis.log')
    
    try:
        logger.info("Starting sensitivity analysis.")
        
        # Load analysis results
        results_df = load_analysis_results()
        logger.info(f"Loaded {len(results_df)} analysis results.")
        
        # Generate sensitivity table
        output_path = Path(__file__).parent.parent / "data" / "analysis" / "sensitivity_table.csv"
        sensitivity_df = generate_sensitivity_table(results_df, output_path)
        
        logger.info(f"Sensitivity table generated and saved to {output_path}")
        logger.info(f"Results:\n{sensitivity_df.to_string(index=False)}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
