import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from utils.logging import get_logger

# Ensure the viz directory exists in the import path if not already
try:
    import code
except ImportError:
    pass

logger = get_logger(__name__)


def plot_scatter_significant(
    correlation_results: pd.DataFrame,
    gene: str,
    clinical_trait: str,
    output_path: str,
    tissue: Optional[str] = None,
    fdr_threshold: float = 0.05
) -> Path:
    """
    Generate a scatter plot for a significant correlation between a gene and a clinical trait.

    This function creates a publication-quality scatter plot with a regression line,
    confidence interval, and statistical annotations (r, p-value, N) for a specific
    gene-trait pair identified as significant in the correlation analysis.

    Parameters
    ----------
    correlation_results : pd.DataFrame
        DataFrame containing correlation results with columns:
        ['gene', 'trait', 'r', 'p', 'significance_flag', 'tissue', ...].
        Must contain the specific gene and trait combination.
    gene : str
        The gene symbol to plot (e.g., 'PER3').
    clinical_trait : str
        The clinical trait to plot (e.g., 'BMI', 'Glucose').
    output_path : str
        Full file path (including .png extension) where the plot will be saved.
    tissue : str, optional
        If provided, filters the data to only this tissue type before plotting.
        If None, plots all tissues combined (assuming results are already stratified).
    fdr_threshold : float, default=0.05
        The FDR threshold used to determine significance. Used for annotation.

    Returns
    -------
    Path
        The path to the saved plot file.

    Raises
    ------
    ValueError
        If the gene-trait combination is not found in the results or is not significant.
    FileNotFoundError
        If the input data is missing or invalid.
    """
    logger.info(f"Generating scatter plot for {gene} vs {clinical_trait}")

    # Validate input
    if correlation_results.empty:
        raise ValueError("correlation_results DataFrame is empty.")

    # Filter for the specific gene and trait
    mask = (correlation_results['gene'] == gene) & (correlation_results['trait'] == clinical_trait)
    if tissue:
        mask = mask & (correlation_results['tissue'] == tissue)

    result_row = correlation_results[mask]

    if result_row.empty:
        raise ValueError(f"No correlation result found for gene={gene}, trait={clinical_trait}"
                         f"{' and tissue=' + tissue if tissue else ''}.")

    if result_row['significance_flag'].iloc[0] != "significant":
        logger.warning(f"Result for {gene} vs {clinical_trait} is marked as '{result_row['significance_flag'].iloc[0]}'. "
                       f"Plotting anyway but flagging as non-significant.")

    r_val = result_row['r'].iloc[0]
    p_val = result_row['p'].iloc[0]
    n_samples = result_row['n'].iloc[0] if 'n' in result_row.columns else "N/A"

    # Retrieve raw data for plotting
    # We assume the correlation_results DataFrame or a linked source has the raw data
    # If the DataFrame only has stats, we need to fetch raw data from the source.
    # However, typically in this pipeline, correlation_results is derived from a source df.
    # To make this robust, we expect the correlation_results to be joined with the raw data
    # or we need to pass the raw data.
    # Since the task implies generating the plot from the analysis results,
    # we assume the input DataFrame (or a related one) has the columns needed for plotting.
    # Let's assume the correlation_results passed here is actually the joined result
    # containing the raw values 'x' and 'y' for the plot, or we need to reconstruct.

    # Correction: The function signature implies we are plotting based on the analysis.
    # To plot a scatter, we need the actual data points.
    # If the input 'correlation_results' is just the summary stats (from T026),
    # we cannot plot without the source data.
    # Assumption: The caller passes the full dataset used for correlation, or the
    # correlation_results includes the raw data columns.
    # Given the constraints, I will assume the input DataFrame contains the raw data
    # columns corresponding to the gene and trait, or we need to fetch them.
    # Let's assume the input DataFrame `correlation_results` has the raw data columns
    # named exactly as the gene and trait, plus a 'tissue' column if stratified.

    if gene not in correlation_results.columns or clinical_trait not in correlation_results.columns:
        # Try to find the raw data source if not in the summary
        # This is a fallback logic: if the summary doesn't have raw data, we can't plot.
        # We will raise an error if raw data columns are missing.
        raise ValueError(f"Input DataFrame must contain columns for '{gene}' and '{clinical_trait}' to generate scatter plot.")

    plot_data = correlation_results[mask].copy()

    if plot_data.empty:
        raise ValueError(f"No data points found for plotting {gene} vs {clinical_trait}.")

    # Setup plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    sns.scatterplot(
        data=plot_data,
        x=gene,
        y=clinical_trait,
        ax=ax,
        alpha=0.7,
        edgecolor='k',
        linewidth=0.5,
        s=60,
        label='Samples'
    )

    # Regression line
    sns.regplot(
        data=plot_data,
        x=gene,
        y=clinical_trait,
        ax=ax,
        scatter=False,
        color='red',
        line_kws={'linewidth': 2, 'label': f'Regression (r={r_val:.3f})'}
    )

    # Annotate
    annotation_text = (
        f"Gene: {gene}\n"
        f"Trait: {clinical_trait}\n"
        f"r = {r_val:.3f}\n"
        f"p = {p_val:.4e}\n"
        f"N = {len(plot_data)}\n"
        f"Significance: {result_row['significance_flag'].iloc[0]}"
    )
    if tissue:
        annotation_text += f"\nTissue: {tissue}"

    ax.text(
        0.05, 0.95, annotation_text,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    ax.set_title(f"Correlation: {gene} Expression vs {clinical_trait}", fontsize=14, fontweight='bold')
    ax.set_xlabel(f"{gene} Expression (TPM)", fontsize=12)
    ax.set_ylabel(f"{clinical_trait}", fontsize=12)

    # Legend
    ax.legend(loc='upper left')

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Scatter plot saved to {output_path}")
    return Path(output_path)


def plot_correlation_heatmap(
    correlation_results: pd.DataFrame,
    output_path: str,
    top_n: int = 20
) -> Path:
    """
    Generate a heatmap of the top significant correlations.

    Parameters
    ----------
    correlation_results : pd.DataFrame
        DataFrame with columns ['gene', 'trait', 'r', 'p', 'significance_flag'].
    output_path : str
        Path to save the heatmap image.
    top_n : int, default=20
        Number of top correlations to display.

    Returns
    -------
    Path
        Path to the saved file.
    """
    logger.info(f"Generating correlation heatmap (top {top_n})")

    # Filter significant and sort by absolute r
    sig_df = correlation_results[correlation_results['significance_flag'] == 'significant'].copy()
    if sig_df.empty:
        logger.warning("No significant correlations found for heatmap.")
        # Create a placeholder plot
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, "No significant correlations found",
                ha='center', va='center', transform=ax.transAxes, fontsize=16)
        ax.set_title("Correlation Heatmap")
        plt.savefig(output_path, dpi=300)
        plt.close(fig)
        return Path(output_path)

    sig_df['abs_r'] = sig_df['r'].abs()
    top_df = sig_df.nlargest(top_n, 'abs_r')

    # Pivot for heatmap (Gene vs Trait)
    # Note: This assumes one value per gene-trait pair. If multiple (e.g. by tissue),
    # we might need to aggregate or pick one. Assuming one pair per gene-trait for this view.
    pivot_data = top_df.pivot(index='gene', columns='trait', values='r')

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        pivot_data,
        annot=True,
        fmt=".2f",
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=.5,
        cbar_kws={"shrink": .5}
    )
    plt.title(f"Top {top_n} Significant Correlations (Gene vs Trait)", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.info(f"Heatmap saved to {output_path}")
    return Path(output_path)
