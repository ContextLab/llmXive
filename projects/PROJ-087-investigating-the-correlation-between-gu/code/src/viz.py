import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure matplotlib uses a non-interactive backend for headless environments
if not plt.isinteractive():
    plt.switch_backend('Agg')

def generate_boxplot_by_quartile(
    df: pd.DataFrame,
    diversity_metric: str,
    sleep_metric: str,
    output_path: Path,
    title: Optional[str] = None
) -> None:
    """
    Generate a boxplot of a diversity metric grouped by sleep metric quartiles.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the diversity metric and sleep metric columns.
    diversity_metric : str
        Name of the column containing the diversity metric (e.g., 'shannon_diversity').
    sleep_metric : str
        Name of the column containing the sleep metric (e.g., 'sleep_efficiency').
    output_path : Path
        Path where the plot will be saved.
    title : str, optional
        Custom title for the plot. If None, a default title is generated.

    Raises
    ------
    FileNotFoundError
        If the input DataFrame is missing required columns.
    ValueError
        If the input DataFrame is empty or contains NaN values in critical columns.
    """
    # Validate input
    if diversity_metric not in df.columns:
        raise FileNotFoundError(f"Column '{diversity_metric}' not found in DataFrame. Available columns: {list(df.columns)}")
    if sleep_metric not in df.columns:
        raise FileNotFoundError(f"Column '{sleep_metric}' not found in DataFrame. Available columns: {list(df.columns)}")

    # Filter out rows with NaN in the relevant columns
    clean_df = df[[diversity_metric, sleep_metric]].dropna()

    if clean_df.empty:
        raise ValueError(f"No valid data to plot after removing NaN values for '{diversity_metric}' and '{sleep_metric}'.")

    # Create quartile bins for the sleep metric
    clean_df['sleep_quartile'] = pd.qcut(clean_df[sleep_metric], q=4, labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)'])

    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")

    # Create the boxplot
    sns.boxplot(
        x='sleep_quartile',
        y=diversity_metric,
        data=clean_df,
        palette="viridis",
        linewidth=1.5,
        fliersize=3
    )

    # Add labels and title
    xlabel = f'Sleep {sleep_metric.replace("_", " ").title()} Quartile'
    ylabel = f'{diversity_metric.replace("_", " ").title()}'
    plot_title = title if title else f'{ylabel} by {xlabel}'

    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(plot_title, fontsize=14, fontweight='bold')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Boxplot saved to {output_path}")


def generate_all_quartile_boxplots(
    df: pd.DataFrame,
    correlation_results: pd.DataFrame,
    output_dir: Path,
    diversity_metrics: List[str],
    sleep_metrics: List[str]
) -> List[Path]:
    """
    Generate boxplots for all significant correlations found in the correlation results.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing diversity metrics and sleep metrics.
    correlation_results : pd.DataFrame
        DataFrame containing correlation results with columns 'metric_x', 'metric_y', 'is_meaningful'.
    output_dir : Path
        Directory where plots will be saved.
    diversity_metrics : List[str]
        List of diversity metric column names to consider.
    sleep_metrics : List[str]
        List of sleep metric column names to consider.

    Returns
    -------
    List[Path]
        List of paths to the generated plot files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_plots = []

    # Filter for meaningful correlations
    meaningful = correlation_results[
        (correlation_results['is_meaningful'] == True) |
        (correlation_results['is_moderate'] == True)
    ]

    if meaningful.empty:
        logger.warning("No significant or moderate correlations found to plot.")
        return generated_plots

    for _, row in meaningful.iterrows():
        metric_x = row['metric_x']
        metric_y = row['metric_y']

        # Determine which is diversity and which is sleep based on provided lists
        div_metric = None
        sleep_metric = None

        if metric_x in diversity_metrics and metric_y in sleep_metrics:
            div_metric, sleep_metric = metric_x, metric_y
        elif metric_y in diversity_metrics and metric_x in sleep_metrics:
            div_metric, sleep_metric = metric_y, metric_x
        else:
            # Skip if we can't identify the pair types clearly
            logger.debug(f"Skipping pair {metric_x}, {metric_y} as types are ambiguous.")
            continue

        if div_metric is None or sleep_metric is None:
            continue

        # Generate filename
        safe_div = div_metric.replace("_", "_").replace(" ", "_")
        safe_sleep = sleep_metric.replace("_", "_").replace(" ", "_")
        filename = f"boxplot_{safe_div}_by_{safe_sleep}_quartile.png"
        output_path = output_dir / filename

        try:
            generate_boxplot_by_quartile(
                df=df,
                diversity_metric=div_metric,
                sleep_metric=sleep_metric,
                output_path=output_path,
                title=f"{div_metric} by {sleep_metric} Quartile"
            )
            generated_plots.append(output_path)
        except Exception as e:
            logger.error(f"Failed to generate boxplot for {div_metric} vs {sleep_metric}: {e}")

    return generated_plots


def save_all_plot_artifacts(
    df: pd.DataFrame,
    correlation_results: pd.DataFrame,
    output_dir: Path,
    diversity_metrics: Optional[List[str]] = None,
    sleep_metrics: Optional[List[str]] = None
) -> Dict[str, List[Path]]:
    """
    Save all plot artifacts including scatterplots and boxplots.
    This function acts as the main entry point for T027 and T028 combined.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned dataset with diversity and sleep metrics.
    correlation_results : pd.DataFrame
        Results from correlation analysis.
    output_dir : Path
        Directory to save plots.
    diversity_metrics : List[str], optional
        List of diversity metric names. Defaults to common names if not provided.
    sleep_metrics : List[str], optional
        List of sleep metric names. Defaults to common names if not provided.

    Returns
    -------
    Dict[str, List[Path]]
        Dictionary with keys 'scatterplots' and 'boxplots' containing lists of file paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if diversity_metrics is None:
        diversity_metrics = ['shannon_diversity', 'simpson_diversity', 'observed_otus']
    if sleep_metrics is None:
        sleep_metrics = ['sleep_efficiency', 'sleep_duration_hours']

    results = {
        'scatterplots': [],
        'boxplots': []
    }

    # 1. Generate Boxplots (T028)
    logger.info("Generating boxplots by sleep quartile...")
    results['boxplots'] = generate_all_quartile_boxplots(
        df=df,
        correlation_results=correlation_results,
        output_dir=output_dir,
        diversity_metrics=diversity_metrics,
        sleep_metrics=sleep_metrics
    )

    # 2. Generate Scatterplots (T027 - delegated to existing function if available, else inline)
    # Since T027 is marked completed, we assume generate_scatterplot_with_regression exists.
    # We will attempt to import it. If not, we implement a minimal version here to ensure T028 works standalone.
    from typing import Callable

    try:
        from src.viz import generate_scatterplot_with_regression
    except ImportError:
        # Fallback implementation if T027 wasn't fully merged into this file yet
        def generate_scatterplot_with_regression(
            df, x_col, y_col, output_path, title=None
        ):
            plt.figure(figsize=(8, 6))
            sns.regplot(x=x_col, y=y_col, data=df, scatter_kws={'alpha':0.5})
            plt.title(title or f"{y_col} vs {x_col}")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300)
            plt.close()

    # Generate scatterplots for meaningful correlations
    meaningful = correlation_results[
        (correlation_results['is_meaningful'] == True) |
        (correlation_results['is_moderate'] == True)
    ]

    for _, row in meaningful.iterrows():
        x_col = row['metric_x']
        y_col = row['metric_y']

        # Ensure both columns exist
        if x_col not in df.columns or y_col not in df.columns:
            continue

        safe_x = x_col.replace("_", "_")
        safe_y = y_col.replace("_", "_")
        filename = f"scatterplot_{safe_x}_vs_{safe_y}.png"
        output_path = output_dir / filename

        try:
            generate_scatterplot_with_regression(
                df=df,
                x_col=x_col,
                y_col=y_col,
                output_path=output_path,
                title=f"{y_col} vs {x_col}"
            )
            results['scatterplots'].append(output_path)
        except Exception as e:
            logger.error(f"Failed to generate scatterplot for {x_col} vs {y_col}: {e}")

    logger.info(f"Total plots generated: {len(results['scatterplots'])} scatterplots, {len(results['boxplots'])} boxplots")
    return results


def main():
    """
    Main entry point for T028 execution.
    Loads cleaned data and correlation results, then generates boxplots.
    """
    import json
    from src.config import load_config

    config = load_config()
    data_path = Path(config.get('DATA_PROCESSED_DIR', 'data/processed'))
    plots_dir = Path(config.get('DATA_PROCESSED_DIR', 'data/processed')) / 'plots'

    cleaned_data_file = data_path / 'cleaned_microbiome_sleep.csv'
    correlation_results_file = data_path / 'correlation_results.csv'

    if not cleaned_data_file.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_data_file}")
    if not correlation_results_file.exists():
        raise FileNotFoundError(f"Correlation results file not found: {correlation_results_file}")

    logger.info(f"Loading data from {cleaned_data_file}")
    df = pd.read_csv(cleaned_data_file)

    logger.info(f"Loading correlation results from {correlation_results_file}")
    corr_df = pd.read_csv(correlation_results_file)

    # Identify standard column names dynamically if needed, or assume standard
    # Assuming standard columns based on T016 and T024 outputs
    diversity_cols = [c for c in df.columns if 'diversity' in c.lower() or 'shannon' in c.lower() or 'simpson' in c.lower() or 'otu' in c.lower()]
    sleep_cols = [c for c in df.columns if 'sleep' in c.lower()]

    if not diversity_cols or not sleep_cols:
        logger.warning("Could not automatically detect diversity or sleep columns. Using defaults.")
        diversity_cols = ['shannon_diversity', 'simpson_diversity', 'observed_otus']
        sleep_cols = ['sleep_efficiency', 'sleep_duration_hours']

    save_all_plot_artifacts(
        df=df,
        correlation_results=corr_df,
        output_dir=plots_dir,
        diversity_metrics=diversity_cols,
        sleep_metrics=sleep_cols
    )

    logger.info("T028 Boxplot generation completed successfully.")

if __name__ == "__main__":
    main()