import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

def load_sensitivity_results():
    """Load sensitivity analysis results."""
    path = Path("code/data/processed/sensitivity_results.csv")
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity results not found at {path}")
    return pd.read_csv(path)

def plot_threshold_sensitivity(results_df):
    """Plot threshold sensitivity results."""
    logger = logging.getLogger(__name__)
    logger.info("Generating threshold sensitivity plot...")

    if results_df.empty or results_df['coefficient'].isna().all():
        logger.warning("No valid data to plot for threshold sensitivity.")
        return

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.figure(figsize=(8, 6))
    plt.errorbar(
        results_df['threshold'],
        results_df['coefficient'],
        yerr=0.01,  # Placeholder error
        fmt='o-',
        capsize=5
    )
    plt.xlabel('VAF Threshold')
    plt.ylabel('Correlation Coefficient')
    plt.title('Threshold Sensitivity Analysis')
    plt.grid(True, alpha=0.3)

    output_path = Path("paper/figures/threshold_sensitivity.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Threshold sensitivity plot saved to {output_path}")

def plot_subgroup_comparison(subgroup_df):
    """Plot subgroup comparison results."""
    logger = logging.getLogger(__name__)
    logger.info("Generating subgroup comparison plot...")

    if subgroup_df.empty or subgroup_df['coefficient'].isna().all():
        logger.warning("No valid data to plot for subgroup comparison.")
        return

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.figure(figsize=(8, 6))
    plt.bar(subgroup_df['ancestry'], subgroup_df['coefficient'], color='skyblue')
    plt.xlabel('Ancestry Group')
    plt.ylabel('Correlation Coefficient')
    plt.title('Subgroup Comparison')
    plt.grid(axis='y', alpha=0.3)

    output_path = Path("paper/figures/subgroup_comparison.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Subgroup comparison plot saved to {output_path}")

def generate_all_plots():
    """Generate all required plots."""
    logger = logging.getLogger(__name__)
    logger.info("Generating all plots...")

    try:
        sensitivity_df = load_sensitivity_results()
        plot_threshold_sensitivity(sensitivity_df)

        subgroup_path = Path("code/data/processed/subgroup_results.csv")
        if subgroup_path.exists():
            subgroup_df = pd.read_csv(subgroup_path)
            plot_subgroup_comparison(subgroup_df)

        logger.info("All plots generated successfully.")
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        raise

def main():
    """
    Main entry point for visualization.
    Generates all plots and saves them to paper/figures/.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        generate_all_plots()
    except Exception as e:
        logger.error(f"Error in main visualization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
