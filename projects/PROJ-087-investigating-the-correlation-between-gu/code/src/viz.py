import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from src.logging_config import setup_logger
from src.config import load_config

logger = setup_logger(__name__)

def generate_boxplot_by_sleep_quartile(
    correlation_results_path: str,
    diversity_metrics_path: str,
    output_dir: str,
    output_filename_prefix: str = "boxplot_sleep_quartile_",
    diversity_metric: str = "shannon_diversity",
    sleep_metric: str = "sleep_efficiency"
) -> List[Path]:
    """
    Generate boxplots of a diversity metric grouped by sleep metric quartiles.

    This function:
    1. Loads correlation results to identify significant pairs (if needed for filtering).
    2. Loads diversity metrics and sleep data.
    3. Bins the sleep metric into quartiles (Q1, Q2, Q3, Q4).
    4. Generates a boxplot for the specified diversity metric across these quartiles.
    5. Saves the plot to the output directory.

    Args:
        correlation_results_path: Path to the CSV with correlation results (for context).
        diversity_metrics_path: Path to the CSV containing diversity indices and sleep data.
        output_dir: Directory to save the generated plots.
        output_filename_prefix: Prefix for the output filename.
        diversity_metric: Column name for the diversity metric to plot.
        sleep_metric: Column name for the sleep metric used for binning.

    Returns:
        List of Path objects pointing to the generated plot files.
    """
    logger.info(f"Generating boxplot for {diversity_metric} by {sleep_metric} quartiles.")

    config = load_config()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        diversity_df = pd.read_csv(diversity_metrics_path)
    except FileNotFoundError:
        logger.error(f"Data file not found: {diversity_metrics_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading {diversity_metrics_path}: {e}")
        raise

    if diversity_metric not in diversity_df.columns:
        raise ValueError(f"Column '{diversity_metric}' not found in {diversity_metrics_path}")
    if sleep_metric not in diversity_df.columns:
        raise ValueError(f"Column '{sleep_metric}' not found in {diversity_metrics_path}")

    # Create a copy to avoid modifying the original
    plot_df = diversity_df[[diversity_metric, sleep_metric]].dropna()

    if plot_df.empty:
        logger.warning("No data available after dropping NaNs for plotting.")
        return []

    # Create quartile bins
    # qcut raises an error if all values are the same or if there are too few unique values
    try:
        plot_df['sleep_quartile'] = pd.qcut(plot_df[sleep_metric], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])
    except ValueError as e:
        # Fallback if qcut fails (e.g., not enough unique values)
        logger.warning(f"pd.qcut failed: {e}. Falling back to quantile-based bins with labels.")
        quantiles = plot_df[sleep_metric].quantile([0.25, 0.5, 0.75]).values
        plot_df['sleep_quartile'] = pd.cut(
            plot_df[sleep_metric],
            bins=[-np.inf, quantiles[0], quantiles[1], quantiles[2], np.inf],
            labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)']
        )

    # Setup plot
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")

    # Create boxplot
    sns.boxplot(
        x='sleep_quartile',
        y=diversity_metric,
        data=plot_df,
        palette="viridis",
        linewidth=1.5
    )

    # Add jittered stripplot for individual points
    sns.stripplot(
        x='sleep_quartile',
        y=diversity_metric,
        data=plot_df,
        color="black",
        alpha=0.3,
        size=4,
        jitter=True,
        linewidth=0.5
    )

    plt.title(f'{diversity_metric} Distribution by {sleep_metric} Quartiles', fontsize=14, pad=15)
    plt.xlabel(f'{sleep_metric} Quartile', fontsize=12)
    plt.ylabel(diversity_metric.replace('_', ' ').title(), fontsize=12)

    # Add statistical annotation if possible (simple mean marker)
    # Calculate means for annotation
    means = plot_df.groupby('sleep_quartile')[diversity_metric].mean()
    for i, (cat, val) in enumerate(means.items()):
        plt.text(i, val, f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()

    # Save figure
    output_filename = f"{output_filename_prefix}{diversity_metric}_vs_{sleep_metric}.png"
    full_output_path = output_path / output_filename
    plt.savefig(full_output_path, dpi=300)
    plt.close()

    logger.info(f"Boxplot saved to {full_output_path}")
    return [full_output_path]


def generate_all_boxplots(
    diversity_metrics_path: str,
    output_dir: str,
    correlation_results_path: Optional[str] = None
) -> List[Path]:
    """
    Generate boxplots for all significant diversity-sleep pairs found in correlation results.
    If correlation_results_path is None, generates boxplots for all available diversity metrics
    against 'sleep_efficiency' (or a default).

    Args:
        diversity_metrics_path: Path to the CSV with diversity indices and sleep data.
        output_dir: Directory to save plots.
        correlation_results_path: Optional path to correlation results to filter for significant pairs.

    Returns:
        List of paths to generated plots.
    """
    logger.info("Generating all boxplots by sleep quartile.")
    config = load_config()
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Determine which diversity metrics to plot
    diversity_df = pd.read_csv(diversity_metrics_path)
    diversity_columns = [c for c in diversity_df.columns if c.endswith('_diversity') or 'observed_otus' in c.lower()]
    sleep_columns = [c for c in diversity_df.columns if 'sleep' in c.lower() and c != 'sample_id']

    if not sleep_columns:
        logger.warning("No sleep metric columns found in diversity data.")
        return []

    # Default sleep metric
    default_sleep_metric = 'sleep_efficiency' if 'sleep_efficiency' in sleep_columns else sleep_columns[0]

    if correlation_results_path and Path(correlation_results_path).exists():
        corr_df = pd.read_csv(correlation_results_path)
        # Filter for meaningful correlations (q < 0.05 and |r| > 0.3)
        significant = corr_df[
            (corr_df['q_value'] < 0.05) &
            (corr_df['abs_r'].abs() > 0.3)
        ]

        if significant.empty:
            logger.info("No significant correlations found. Generating plots for all available metrics.")
            pairs_to_plot = [(col, default_sleep_metric) for col in diversity_columns if col in diversity_df.columns]
        else:
            pairs_to_plot = []
            for _, row in significant.iterrows():
                div_col = row.get('diversity_metric')
                sleep_col = row.get('sleep_metric')
                if div_col and sleep_col and div_col in diversity_df.columns and sleep_col in diversity_df.columns:
                    pairs_to_plot.append((div_col, sleep_col))
    else:
        logger.info("No correlation results provided. Generating plots for all diversity metrics vs default sleep metric.")
        pairs_to_plot = [(col, default_sleep_metric) for col in diversity_columns if col in diversity_df.columns]

    if not pairs_to_plot:
        logger.warning("No pairs to plot.")
        return []

    for div_metric, sleep_metric in pairs_to_plot:
        try:
            files = generate_boxplot_by_sleep_quartile(
                correlation_results_path=correlation_results_path,
                diversity_metrics_path=diversity_metrics_path,
                output_dir=str(output_dir_path),
                diversity_metric=div_metric,
                sleep_metric=sleep_metric
            )
            generated_files.extend(files)
        except Exception as e:
            logger.error(f"Failed to generate boxplot for {div_metric} vs {sleep_metric}: {e}")
            continue

    return generated_files


def main():
    """
    Main entry point for generating boxplots.
    Expects environment variables or config to point to input data.
    """
    config = load_config()
    diversity_path = config.get('DATA_PROCESSED_DIVERSITY', 'data/processed/diversity_metrics.csv')
    correlation_path = config.get('DATA_PROCESSED_CORRELATION', 'data/processed/correlation_results.csv')
    output_dir = config.get('DATA_PROCESSED_PLOTS', 'data/processed/plots')

    # Ensure input files exist
    if not Path(diversity_path).exists():
        logger.error(f"Input file not found: {diversity_path}")
        return 1

    if not Path(correlation_path).exists():
        logger.warning(f"Correlation results not found at {correlation_path}. Generating plots for all metrics.")
        correlation_path = None

    try:
        files = generate_all_boxplots(
            diversity_metrics_path=diversity_path,
            output_dir=output_dir,
            correlation_results_path=correlation_path
        )
        logger.info(f"Successfully generated {len(files)} boxplots.")
        return 0
    except Exception as e:
        logger.error(f"Boxplot generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())