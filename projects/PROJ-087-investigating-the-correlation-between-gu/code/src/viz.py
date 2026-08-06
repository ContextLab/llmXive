"""
Visualization module for generating scatterplots, boxplots, and saving all plot artifacts.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import json

from src.config import load_config
from src.logging_config import setup_logger

logger = setup_logger(__name__)
config = load_config()

# Set style for consistent plots
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 8)
plt.rcParams['font.size'] = 12

def generate_scatterplot_with_regression(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    output_path: Path,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None
) -> None:
    """
    Generate a scatterplot with a regression line for a given pair of variables.

    Args:
        data: DataFrame containing the data.
        x_col: Name of the column for the x-axis.
        y_col: Name of the column for the y-axis.
        title: Title of the plot.
        output_path: Path where the plot will be saved.
        x_label: Optional custom label for the x-axis.
        y_label: Optional custom label for the y-axis.
    """
    if x_col not in data.columns or y_col not in data.columns:
        logger.error(f"Columns {x_col} or {y_col} not found in data.")
        raise ValueError(f"Columns {x_col} or {y_col} not found in data.")

    plt.figure()
    sns.regplot(x=x_col, y=y_col, data=data, scatter_kws={'alpha': 0.6}, line_kws={'color': 'red'})
    plt.title(title)
    plt.xlabel(x_label or x_col)
    plt.ylabel(y_label or y_col)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Scatterplot saved to {output_path}")

def generate_boxplot_by_quartile(
    data: pd.DataFrame,
    value_col: str,
    quartile_col: str,
    title: str,
    output_path: Path,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None
) -> None:
    """
    Generate a boxplot grouping a value by sleep quartiles.

    Args:
        data: DataFrame containing the data.
        value_col: Name of the column to plot on the y-axis.
        quartile_col: Name of the column containing quartile groups for the x-axis.
        title: Title of the plot.
        output_path: Path where the plot will be saved.
        x_label: Optional custom label for the x-axis.
        y_label: Optional custom label for the y-axis.
    """
    if value_col not in data.columns or quartile_col not in data.columns:
        logger.error(f"Columns {value_col} or {quartile_col} not found in data.")
        raise ValueError(f"Columns {value_col} or {quartile_col} not found in data.")

    plt.figure()
    sns.boxplot(x=quartile_col, y=value_col, data=data, palette="viridis")
    plt.title(title)
    plt.xlabel(x_label or quartile_col)
    plt.ylabel(y_label or value_col)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Boxplot saved to {output_path}")

def generate_all_quartile_boxplots(
    data: pd.DataFrame,
    diversity_metrics: List[str],
    sleep_quartile_col: str = "sleep_efficiency_quartile",
    output_dir: Path = None
) -> List[Path]:
    """
    Generate boxplots for each diversity metric grouped by sleep efficiency quartiles.

    Args:
        data: DataFrame containing diversity metrics and sleep quartiles.
        diversity_metrics: List of column names representing diversity metrics.
        sleep_quartile_col: Column name for sleep efficiency quartiles.
        output_dir: Directory to save the plots.

    Returns:
        List of paths to the saved plot files.
    """
    if output_dir is None:
        output_dir = Path(config.get("PLOTS_DIR", "data/processed/plots"))
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for metric in diversity_metrics:
        title = f"{metric.replace('_', ' ').title()} by Sleep Efficiency Quartile"
        output_path = output_dir / f"{metric}_by_sleep_quartile.png"
        try:
            generate_boxplot_by_quartile(
                data=data,
                value_col=metric,
                quartile_col=sleep_quartile_col,
                title=title,
                output_path=output_path,
                x_label="Sleep Efficiency Quartile",
                y_label=metric.replace('_', ' ').title()
            )
            saved_paths.append(output_path)
        except Exception as e:
            logger.error(f"Failed to generate boxplot for {metric}: {e}")

    return saved_paths

def save_all_plot_artifacts() -> List[Path]:
    """
    Main entry point to load correlation results, generate plots for significant correlations,
    and save all artifacts to data/processed/plots/.

    Returns:
        List of paths to all saved plot files.
    """
    plots_dir = Path(config.get("PLOTS_DIR", "data/processed/plots"))
    plots_dir.mkdir(parents=True, exist_ok=True)

    correlation_file = Path(config.get("CORRELATION_RESULTS_PATH", "data/processed/correlation_results.csv"))
    if not correlation_file.exists():
        logger.error(f"Correlation results file not found at {correlation_file}")
        raise FileNotFoundError(f"Correlation results file not found at {correlation_file}")

    # Load correlation results
    corr_df = pd.read_csv(correlation_file)
    
    # Filter for meaningful correlations (is_meaningful == True)
    # Assuming the CSV has boolean or 0/1 for is_meaningful
    if 'is_meaningful' in corr_df.columns:
        # Handle potential string "True"/"False" or 1/0
        meaningful_df = corr_df[corr_df['is_meaningful'] == True]
    else:
        logger.warning("Column 'is_meaningful' not found in correlation results. Using all correlations.")
        meaningful_df = corr_df

    if meaningful_df.empty:
        logger.info("No significant associations found. Generating a placeholder report plot.")
        # Create a simple text plot or empty figure to satisfy the requirement
        plt.figure()
        plt.text(0.5, 0.5, "No Significant Associations Found", 
                 horizontalalignment='center', verticalalignment='center',
                 fontsize=20, color='red')
        plt.axis('off')
        plt.tight_layout()
        no_sig_path = plots_dir / "no_significant_associations.png"
        plt.savefig(no_sig_path)
        plt.close()
        return [no_sig_path]

    saved_plots = []
    
    # Load the cleaned data to get actual values for scatterplots
    cleaned_data_path = Path(config.get("CLEANED_DATA_PATH", "data/processed/cleaned_microbiome_sleep.csv"))
    if not cleaned_data_path.exists():
        logger.error(f"Cleaned data file not found at {cleaned_data_path}")
        raise FileNotFoundError(f"Cleaned data file not found at {cleaned_data_path}")
    
    cleaned_df = pd.read_csv(cleaned_data_path)

    # Generate scatterplots for each significant correlation
    for _, row in meaningful_df.iterrows():
        metric = row.get('metric') # Column name for diversity metric
        sleep_var = row.get('sleep_variable') # Column name for sleep metric
        
        if pd.isna(metric) or pd.isna(sleep_var):
            continue

        # Ensure columns exist in cleaned data
        if metric not in cleaned_df.columns or sleep_var not in cleaned_df.columns:
            logger.warning(f"Columns {metric} or {sleep_var} not found in cleaned data. Skipping scatterplot.")
            continue

        title = f"Correlation: {metric.replace('_', ' ').title()} vs {sleep_var.replace('_', ' ').title()}"
        output_path = plots_dir / f"scatter_{metric}_{sleep_var}.png"
        
        try:
            generate_scatterplot_with_regression(
                data=cleaned_df,
                x_col=sleep_var,
                y_col=metric,
                title=title,
                output_path=output_path,
                x_label=sleep_var.replace('_', ' ').title(),
                y_label=metric.replace('_', ' ').title()
            )
            saved_plots.append(output_path)
        except Exception as e:
            logger.error(f"Failed to generate scatterplot for {metric} vs {sleep_var}: {e}")

    # Generate boxplots for all diversity metrics by sleep quartile
    diversity_metrics = [col for col in cleaned_df.columns if 'shannon' in col.lower() or 'simpson' in col.lower() or 'observed' in col.lower()]
    if not diversity_metrics:
        # Fallback if naming convention differs, try to infer from correlation results
        diversity_metrics = list(meaningful_df['metric'].unique())
    
    if 'sleep_efficiency_quartile' in cleaned_df.columns:
        boxplot_paths = generate_all_quartile_boxplots(
            data=cleaned_df,
            diversity_metrics=diversity_metrics,
            sleep_quartile_col="sleep_efficiency_quartile",
            output_dir=plots_dir
        )
        saved_plots.extend(boxplot_paths)
    else:
        logger.warning("Column 'sleep_efficiency_quartile' not found. Skipping boxplot generation by quartile.")

    logger.info(f"Total {len(saved_plots)} plot artifacts saved to {plots_dir}")
    return saved_plots

def main():
    """
    Entry point for the visualization script.
    """
    try:
        plots = save_all_plot_artifacts()
        print(f"Successfully generated {len(plots)} plot artifacts.")
    except Exception as e:
        logger.critical(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
