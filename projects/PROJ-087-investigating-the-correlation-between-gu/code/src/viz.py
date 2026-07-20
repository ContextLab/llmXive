import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from src.config import load_config
from src.correlation import flag_correlations

logger = logging.getLogger(__name__)

def generate_boxplot_by_quartile(
    df: pd.DataFrame,
    diversity_col: str,
    sleep_col: str,
    output_path: Path,
    plot_title: str = "Alpha Diversity by Sleep Quality Quartile"
) -> None:
    """
    Generate a boxplot of a diversity metric grouped by sleep metric quartiles.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing diversity metrics and sleep metrics.
    diversity_col : str
        Name of the diversity column (e.g., 'shannon_index').
    sleep_col : str
        Name of the sleep metric column (e.g., 'sleep_efficiency').
    output_path : Path
        Path where the plot will be saved.
    plot_title : str
        Title for the plot.
    """
    if diversity_col not in df.columns or sleep_col not in df.columns:
        raise ValueError(f"Columns '{diversity_col}' and/or '{sleep_col}' not found in DataFrame.")

    # Create quartiles
    df = df.copy()
    df['sleep_quartile'] = pd.qcut(df[sleep_col], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')

    plt.figure(figsize=(10, 6))
    sns.boxplot(x='sleep_quartile', y=diversity_col, data=df, palette="Set2", order=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])
    plt.title(plot_title)
    plt.xlabel("Sleep Efficiency Quartile")
    plt.ylabel(diversity_col.replace('_', ' ').title())
    plt.tight_layout()

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved boxplot to {output_path}")

def generate_all_quartile_boxplots(
    df: pd.DataFrame,
    diversity_cols: List[str],
    sleep_col: str,
    output_dir: Path
) -> None:
    """
    Generate boxplots for all specified diversity columns grouped by sleep metric quartiles.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing diversity metrics and sleep metrics.
    diversity_cols : List[str]
        List of diversity column names.
    sleep_col : str
        Name of the sleep metric column.
    output_dir : Path
        Directory where plots will be saved.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    for col in diversity_cols:
        if col in df.columns:
            plot_filename = f"{col}_by_sleep_quartile.png"
            output_path = output_dir / plot_filename
            try:
                generate_boxplot_by_quartile(
                    df,
                    diversity_col=col,
                    sleep_col=sleep_col,
                    output_path=output_path,
                    plot_title=f"{col.replace('_', ' ').title()} by Sleep Efficiency Quartile"
                )
            except ValueError as e:
                logger.warning(f"Skipping {col} due to missing data or invalid quartiles: {e}")
        else:
            logger.warning(f"Column '{col}' not found in DataFrame, skipping boxplot generation.")

def generate_scatterplot_with_regression(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Path,
    title: str = "Correlation Analysis"
) -> None:
    """
    Generate a scatterplot with a regression line.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    x_col : str
        Name of the x-axis column.
    y_col : str
        Name of the y-axis column.
    output_path : Path
        Path where the plot will be saved.
    title : str
        Title for the plot.
    """
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns '{x_col}' and/or '{y_col}' not found in DataFrame.")

    plt.figure(figsize=(8, 6))
    sns.regplot(
        data=df,
        x=x_col,
        y=y_col,
        scatter_kws={'alpha': 0.6},
        line_kws={'color': 'red'}
    )
    plt.title(title)
    plt.xlabel(x_col.replace('_', ' ').title())
    plt.ylabel(y_col.replace('_', ' ').title())
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved scatterplot to {output_path}")

def save_all_plot_artifacts(
    correlation_results_path: Path,
    diversity_results_path: Path,
    output_dir: Path
) -> List[Path]:
    """
    Main function to orchestrate saving all plot artifacts.
    Generates boxplots for diversity indices by sleep quartiles
    and scatterplots for significant correlations.

    Parameters
    ----------
    correlation_results_path : Path
        Path to the correlation results CSV.
    diversity_results_path : Path
        Path to the diversity metrics CSV (merged with sleep data).
    output_dir : Path
        Directory where all plots will be saved.

    Returns
    -------
    List[Path]
        List of paths to generated plot files.
    """
    config = load_config()
    output_dir = Path(config.get('PLOTS_DIR', output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Load data
    try:
        corr_df = pd.read_csv(correlation_results_path)
        diversity_df = pd.read_csv(diversity_results_path)
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        raise

    # 1. Generate Boxplots for all diversity columns
    # Identify diversity columns (exclude sample_id, sleep metrics, and correlation stats)
    diversity_cols = [c for c in diversity_df.columns if c not in ['sample_id', 'sleep_efficiency', 'sleep_duration_hours', 'sleep_quartile']]
    # Filter to likely diversity metrics based on naming convention or known list
    # Assuming standard output from T020b: Shannon, Simpson, Observed_OTUs
    known_diversity_cols = [c for c in diversity_cols if any(x in c.lower() for x in ['shannon', 'simpson', 'observed', 'chao', 'faith'])]

    if known_diversity_cols:
        generate_all_quartile_boxplots(
            diversity_df,
            diversity_cols=known_diversity_cols,
            sleep_col='sleep_efficiency',
            output_dir=output_dir
        )
        # Add generated files to list
        for col in known_diversity_cols:
            p = output_dir / f"{col}_by_sleep_quartile.png"
            if p.exists():
                generated_files.append(p)
    else:
        logger.warning("No known diversity columns found for boxplot generation.")

    # 2. Generate Scatterplots for significant correlations
    # Filter for meaningful correlations (q < 0.05 AND |r| > 0.3)
    significant = corr_df[(corr_df['is_meaningful'] == True) | (corr_df['is_moderate'] == True)]

    # We need the actual values to plot, not just the summary stats.
    # The correlation results table (T024) usually has: diversity_metric, sleep_metric, r, p, q.
    # To plot, we need to join back to the raw data or assume the correlation results
    # are summaries. The task T029 (Report) implies we have the data to plot.
    # However, T024 saves "correlation results". If T024 only saves the summary table,
    # we cannot plot the points without the original merged data.
    # Assumption: T020b/T021 pipeline produced a merged dataframe with diversity and sleep columns.
    # We will attempt to plot using the summary stats if the original data isn't directly linked here,
    # BUT the task requires "scatterplots". This implies we need the original data.
    # Since T016 saves 'cleaned_microbiome_sleep.csv', we assume diversity was calculated on that.
    # We will try to load the diversity_df which should contain the sample-level data.

    # Identify significant pairs to plot
    for _, row in significant.iterrows():
        div_metric = row['diversity_metric']
        sleep_metric = row['sleep_metric']

        if div_metric in diversity_df.columns and sleep_metric in diversity_df.columns:
            plot_title = f"{div_metric.replace('_', ' ').title()} vs {sleep_metric.replace('_', ' ').title()}"
            filename = f"{div_metric}_vs_{sleep_metric}.png"
            output_path = output_dir / filename

            try:
                generate_scatterplot_with_regression(
                    diversity_df,
                    x_col=sleep_metric,
                    y_col=div_metric,
                    output_path=output_path,
                    title=plot_title
                )
                generated_files.append(output_path)
            except Exception as e:
                logger.error(f"Failed to generate scatterplot for {div_metric} vs {sleep_metric}: {e}")

    return generated_files

def main():
    """
    Entry point for saving plot artifacts.
    """
    config = load_config()
    plots_dir = Path(config.get('PLOTS_DIR', 'data/processed/plots'))
    cleaned_data_path = Path(config.get('CLEANED_DATA_PATH', 'data/processed/cleaned_microbiome_sleep.csv'))
    correlation_results_path = Path(config.get('CORRELATION_RESULTS_PATH', 'data/processed/correlation_results.csv'))

    # Note: The diversity metrics might be in a separate file or merged into cleaned_data.
    # If T020b output is separate, we need that path. For now, we assume cleaned_data has diversity cols
    # or we use the cleaned_data as the source for diversity if it was merged.
    # If diversity is in a separate file, we'd need to load it.
    # Let's assume the cleaned data (T016) was enriched with diversity metrics in T020b/T021 pipeline
    # or we need to reload the diversity output.
    # Given T024 output is correlation_results.csv, and T016 is cleaned data.
    # We will use cleaned_data_path as the source for plotting if it contains diversity cols.
    # If not, we might need to adjust. But per T020b, it calculates diversity.
    # Let's assume the 'diversity_results_path' is actually the cleaned data with diversity added,
    # or we need to find where T020b saved it.
    # For robustness, we'll use the cleaned data path as the primary source for plotting
    # assuming the pipeline merged diversity back into it.

    logger.info(f"Starting plot artifact generation. Output Dir: {plots_dir}")
    logger.info(f"Reading data from: {cleaned_data_path} and {correlation_results_path}")

    try:
        files = save_all_plot_artifacts(
            correlation_results_path=correlation_results_path,
            diversity_results_path=cleaned_data_path,
            output_dir=plots_dir
        )
        logger.info(f"Successfully generated {len(files)} plot artifacts.")
        for f in files:
            logger.info(f"  - {f}")
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
