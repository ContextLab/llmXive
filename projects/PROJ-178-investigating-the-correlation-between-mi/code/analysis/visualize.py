import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def load_sensitivity_results(filepath: str) -> pd.DataFrame:
    """Load sensitivity results."""
    return pd.read_csv(filepath)

def plot_threshold_sensitivity(df: pd.DataFrame, output_path: str):
    """Plot threshold sensitivity results."""
    plt.figure(figsize=(10, 6))
    plt.plot(df['threshold'], df['coefficient'], marker='o')
    plt.xlabel('VAF Threshold')
    plt.ylabel('Correlation Coefficient')
    plt.title('Threshold Sensitivity Analysis')
    plt.grid(True)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Threshold plot saved to {output_path}")

def plot_subgroup_comparison(df: pd.DataFrame, output_path: str):
    """Plot subgroup comparison results."""
    plt.figure(figsize=(10, 6))
    plt.bar(df['ancestry'], df['coefficient'])
    plt.xlabel('Ancestry')
    plt.ylabel('Correlation Coefficient')
    plt.title('Subgroup Comparison')
    plt.xticks(rotation=45)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Subgroup plot saved to {output_path}")

def generate_all_plots(threshold_file: str, subgroup_file: str, output_dir: str):
    """Generate all required plots."""
    threshold_df = load_sensitivity_results(threshold_file)
    subgroup_df = load_sensitivity_results(subgroup_file)
    
    plot_threshold_sensitivity(threshold_df, str(Path(output_dir) / 'threshold_sensitivity.png'))
    plot_subgroup_comparison(subgroup_df, str(Path(output_dir) / 'subgroup_comparison.png'))

def main():
    """Main entry point for visualization."""
    logging.basicConfig(level=logging.INFO)
    paths = get_local_paths()
    
    threshold_file = paths['processed'] / 'sensitivity_results.csv'
    subgroup_file = paths['processed'] / 'subgroup_results.csv'
    output_dir = 'paper/figures'
    
    if not threshold_file.exists() or not subgroup_file.exists():
        logger.error("Missing data files for plotting.")
        sys.exit(1)
    
    generate_all_plots(str(threshold_file), str(subgroup_file), output_dir)

if __name__ == '__main__':
    main()
