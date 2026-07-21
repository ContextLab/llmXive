import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import os

from src.config import load_config
from src.utils.hashing import compute_sha256

logger = logging.getLogger(__name__)

def generate_scatterplot_with_regression(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path,
    is_significant: bool = False
) -> None:
    """
    Generate a scatterplot with a regression line for a specific correlation.
    """
    plt.figure(figsize=(10, 8))
    sns.set_style("whitegrid")

    # Plot regression line and scatter
    sns.regplot(
        data=df,
        x=x_col,
        y=y_col,
        scatter_kws={'alpha': 0.6, 's': 50},
        line_kws={'color': 'red', 'lw': 2}
    )

    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)

    if is_significant:
        plt.text(
            0.05, 0.95, 'Significant (q < 0.05)',
            transform=plt.gca().transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved scatterplot to {output_path}")

def generate_boxplot_by_quartile(
    df: pd.DataFrame,
    value_col: str,
    quartile_col: str,
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path
) -> None:
    """
    Generate a boxplot of a value column grouped by sleep quartiles.
    """
    plt.figure(figsize=(10, 8))
    sns.set_style("whitegrid")

    # Ensure quartile column is categorical for correct ordering
    if quartile_col in df.columns:
        df[quartile_col] = df[quartile_col].astype('category')
        # Sort categories if they are numeric strings or numbers
        try:
            df[quartile_col] = df[quartile_col].cat.reorder_categories(
                sorted(df[quartile_col].cat.categories, key=lambda x: float(x) if x != 'Missing' else -1)
            )
        except (ValueError, TypeError):
            pass  # Fallback to default order

        sns.boxplot(
            data=df,
            x=quartile_col,
            y=value_col,
            palette="Set2",
            linewidth=1.5
        )
    else:
        # Fallback if column missing (should be caught by caller)
        logger.error(f"Column {quartile_col} not found in dataframe for boxplot")
        plt.title(f"Error: Missing {quartile_col}")

    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved boxplot to {output_path}")

def generate_all_quartile_boxplots(
    df: pd.DataFrame,
    output_dir: Path,
    metrics: List[str]
) -> None:
    """
    Generate boxplots for all diversity metrics grouped by sleep quartile.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    quartile_col = "sleep_efficiency_quartile"

    if quartile_col not in df.columns:
        logger.warning(f"Quartile column '{quartile_col}' not found. Skipping boxplots.")
        return

    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric '{metric}' not found in dataframe. Skipping.")
            continue

        filename = f"boxplot_{metric}_by_sleep_quartile.png"
        filepath = output_dir / filename
        title = f"{metric.replace('_', ' ').title()} by Sleep Efficiency Quartile"
        generate_boxplot_by_quartile(
            df=df,
            value_col=metric,
            quartile_col=quartile_col,
            title=title,
            x_label="Sleep Efficiency Quartile",
            y_label=metric.replace('_', ' ').title(),
            output_path=filepath
        )

def save_all_plot_artifacts() -> None:
    """
    Main entry point to generate and save all plot artifacts to data/processed/plots/.
    This function orchestrates the generation of scatterplots for significant correlations
    and boxplots for diversity metrics by sleep quartile.
    """
    config = load_config()
    plots_dir = Path(config['plots_dir'])
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Load correlation results
    results_path = Path(config['correlation_results_path'])
    if not results_path.exists():
        raise FileNotFoundError(f"Correlation results file not found: {results_path}")
    
    corr_df = pd.read_csv(results_path)
    
    # Load cleaned data for plotting
    cleaned_data_path = Path(config['cleaned_data_path'])
    if not cleaned_data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_data_path}")
    
    data_df = pd.read_csv(cleaned_data_path)

    # 1. Generate Scatterplots for Significant Correlations
    significant_corrs = corr_df[corr_df['is_meaningful'] == True]
    
    if significant_corrs.empty:
        logger.info("No significant correlations found to plot.")
    else:
        logger.info(f"Generating {len(significant_corrs)} scatterplots for significant correlations.")
        for _, row in significant_corrs.iterrows():
            diversity_metric = row['diversity_metric']
            sleep_metric = row['sleep_metric']
            
            # Check if both columns exist in data_df
            if diversity_metric in data_df.columns and sleep_metric in data_df.columns:
                filename = f"scatterplot_{diversity_metric}_vs_{sleep_metric}.png"
                filepath = plots_dir / filename
                
                title = f"{diversity_metric.replace('_', ' ').title()} vs {sleep_metric.replace('_', ' ').title()}"
                generate_scatterplot_with_regression(
                    df=data_df,
                    x_col=sleep_metric,
                    y_col=diversity_metric,
                    title=title,
                    x_label=sleep_metric.replace('_', ' ').title(),
                    y_label=diversity_metric.replace('_', ' ').title(),
                    output_path=filepath,
                    is_significant=True
                )
            else:
                logger.warning(f"Columns {diversity_metric} or {sleep_metric} missing from data for scatterplot.")

    # 2. Generate Boxplots by Sleep Quartile
    diversity_metrics = ['shannon_diversity', 'simpson_diversity', 'observed_otus']
    logger.info("Generating boxplots by sleep quartile.")
    generate_all_quartile_boxplots(
        df=data_df,
        output_dir=plots_dir,
        metrics=diversity_metrics
    )

    logger.info("All plot artifacts saved successfully.")

def main():
    """
    CLI entry point for saving plot artifacts.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    try:
        save_all_plot_artifacts()
        logger.info("Task T030 completed successfully.")
    except Exception as e:
        logger.error(f"Task T030 failed: {e}")
        raise

if __name__ == "__main__":
    main()
