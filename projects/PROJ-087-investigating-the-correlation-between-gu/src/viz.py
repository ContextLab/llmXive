"""
Visualization module for the Gut Microbiome and Sleep Quality study.
Generates scatterplots with regression lines and boxplots by sleep quartiles.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_scatterplot_with_regression(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Path,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    figsize: tuple = (10, 6)
) -> None:
    """
    Generate a scatterplot with a regression line for significant correlations.

    Args:
        data: DataFrame containing the data.
        x_col: Name of the column for the x-axis.
        y_col: Name of the column for the y-axis.
        output_path: Path to save the plot.
        title: Optional title for the plot.
        x_label: Optional label for the x-axis.
        y_label: Optional label for the y-axis.
        figsize: Tuple of (width, height) for the figure.
    """
    if x_col not in data.columns or y_col not in data.columns:
        raise ValueError(f"Columns '{x_col}' and/or '{y_col}' not found in data. "
                         f"Available columns: {list(data.columns)}")

    # Filter out NaN values for plotting
    plot_data = data[[x_col, y_col]].dropna()

    if len(plot_data) == 0:
        logger.warning(f"No valid data points for scatterplot: {x_col} vs {y_col}")
        # Create an empty plot to satisfy the requirement of producing a file
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_title(title or f"{x_col} vs {y_col}")
        ax.set_xlabel(x_label or x_col)
        ax.set_ylabel(y_label or y_col)
        ax.text(0.5, 0.5, "No data available", transform=ax.transAxes, ha='center')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=figsize)

    # Scatter plot
    sns.scatterplot(data=plot_data, x=x_col, y=y_col, ax=ax, alpha=0.6, edgecolor='k', s=50)

    # Regression line
    sns.regplot(data=plot_data, x=x_col, y=y_col, ax=ax, scatter=False, color='red', line_kws={'linewidth': 2})

    # Labels and title
    ax.set_title(title or f"Correlation: {x_col} vs {y_col}", fontsize=14, fontweight='bold')
    ax.set_xlabel(x_label or x_col, fontsize=12)
    ax.set_ylabel(y_label or y_col, fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Scatterplot saved to {output_path}")

def generate_boxplot_by_quartile(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Path,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    figsize: tuple = (10, 6)
) -> None:
    """
    Generate a boxplot of a variable grouped by sleep quartiles.

    Args:
        data: DataFrame containing the data.
        x_col: Name of the column to group by (e.g., sleep_efficiency).
        y_col: Name of the column to plot (e.g., Shannon diversity).
        output_path: Path to save the plot.
        title: Optional title for the plot.
        x_label: Optional label for the x-axis.
        y_label: Optional label for the y-axis.
        figsize: Tuple of (width, height) for the figure.
    """
    if x_col not in data.columns or y_col not in data.columns:
        raise ValueError(f"Columns '{x_col}' and/or '{y_col}' not found in data. "
                         f"Available columns: {list(data.columns)}")

    # Calculate quartiles
    quartiles = pd.qcut(data[x_col], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')

    # Create a copy to avoid SettingWithCopyWarning
    plot_data = data.copy()
    plot_data['Quartile'] = quartiles

    # Filter out NaN values
    plot_data = plot_data.dropna(subset=[x_col, y_col])

    if len(plot_data) == 0:
        logger.warning(f"No valid data points for boxplot: {x_col} vs {y_col}")
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_title(title or f"Boxplot: {y_col} by {x_col} Quartiles")
        ax.set_xlabel(x_label or x_col)
        ax.set_ylabel(y_label or y_col)
        ax.text(0.5, 0.5, "No data available", transform=ax.transAxes, ha='center')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=figsize)

    # Boxplot
    sns.boxplot(data=plot_data, x='Quartile', y=y_col, ax=ax, palette='viridis', linewidth=1.5)

    # Labels and title
    ax.set_title(title or f"{y_col} by {x_col} Quartiles", fontsize=14, fontweight='bold')
    ax.set_xlabel(x_label or "Sleep Efficiency Quartile", fontsize=12)
    ax.set_ylabel(y_label or y_col, fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Boxplot saved to {output_path}")

def generate_all_quartile_boxplots(
    data: pd.DataFrame,
    sleep_col: str,
    diversity_cols: List[str],
    output_dir: Path
) -> None:
    """
    Generate boxplots for multiple diversity metrics grouped by sleep quartiles.

    Args:
        data: DataFrame containing the data.
        sleep_col: Name of the sleep metric column (e.g., 'sleep_efficiency').
        diversity_cols: List of diversity metric column names.
        output_dir: Directory to save the plots.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for col in diversity_cols:
        output_path = output_dir / f"boxplot_{col}_by_{sleep_col}.png"
        generate_boxplot_by_quartile(
            data=data,
            x_col=sleep_col,
            y_col=col,
            output_path=output_path,
            title=f"{col} by {sleep_col} Quartiles",
            x_label=sleep_col,
            y_label=col
        )

def save_all_plot_artifacts(
    results_df: pd.DataFrame,
    diversity_df: pd.DataFrame,
    plots_dir: Path
) -> None:
    """
    Main function to generate and save all plot artifacts.
    Reads significant correlations from results_df and generates scatterplots.
    Generates boxplots for diversity metrics by sleep quartiles.

    Args:
        results_df: DataFrame with correlation results (must have 'is_meaningful' column).
        diversity_df: DataFrame with diversity indices and sleep metrics.
        plots_dir: Directory to save the plots.
    """
    plots_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating plots in {plots_dir}")

    # 1. Generate Scatterplots for significant correlations
    significant_corrs = results_df[results_df['is_meaningful'] == True]

    if significant_corrs.empty:
        logger.info("No significant correlations found. Skipping scatterplot generation.")
    else:
        for _, row in significant_corrs.iterrows():
            x_col = row['diversity_metric']
            y_col = row['sleep_metric']

            # Check if columns exist in diversity_df
            if x_col not in diversity_df.columns or y_col not in diversity_df.columns:
                logger.warning(f"Skipping scatterplot for {x_col} vs {y_col}: columns missing in data.")
                continue

            output_path = plots_dir / f"scatter_{x_col}_vs_{y_col}.png"
            generate_scatterplot_with_regression(
                data=diversity_df,
                x_col=x_col,
                y_col=y_col,
                output_path=output_path,
                title=f"Significant Correlation: {x_col} vs {y_col} (r={row['r']:.3f}, q={row['q']:.3f})",
                x_label=x_col,
                y_label=y_col
            )

    # 2. Generate Boxplots for diversity metrics by sleep quartiles
    sleep_metrics = ['sleep_efficiency', 'sleep_duration_hours']
    diversity_metrics = ['shannon', 'simpson', 'observed_otus']

    for sleep_col in sleep_metrics:
        if sleep_col in diversity_df.columns:
            # Filter diversity metrics that exist in the dataframe
            existing_div_cols = [c for c in diversity_metrics if c in diversity_df.columns]
            if existing_div_cols:
                generate_all_quartile_boxplots(
                    data=diversity_df,
                    sleep_col=sleep_col,
                    diversity_cols=existing_div_cols,
                    output_dir=plots_dir
                )

def main():
    """
    Entry point for the visualization module.
    Loads data and generates plots.
    """
    from src.config import load_config
    import json

    config = load_config()
    plots_dir = Path(config.get('PLOTS_DIR', 'data/processed/plots'))
    results_path = Path(config.get('CORRELATION_RESULTS_PATH', 'data/processed/correlation_results.csv'))
    cleaned_data_path = Path(config.get('CLEANED_DATA_PATH', 'data/processed/cleaned_microbiome_sleep.csv'))

    logger.info("Starting visualization pipeline...")

    # Load correlation results
    if not results_path.exists():
        logger.error(f"Correlation results file not found: {results_path}")
        raise FileNotFoundError(f"Correlation results file not found: {results_path}")

    results_df = pd.read_csv(results_path)

    # Load cleaned data (diversity metrics + sleep metrics)
    if not cleaned_data_path.exists():
        logger.error(f"Cleaned data file not found: {cleaned_data_path}")
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_data_path}")

    diversity_df = pd.read_csv(cleaned_data_path)

    # Generate plots
    save_all_plot_artifacts(
        results_df=results_df,
        diversity_df=diversity_df,
        plots_dir=plots_dir
    )

    logger.info("Visualization pipeline completed successfully.")

if __name__ == "__main__":
    main()