import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Tuple, Optional, List

from config import get_output_path, ensure_directories
from utils.logging import get_logger

logger = get_logger(__name__)

def load_association_results() -> pd.DataFrame:
    """
    Load the association results from the previous analysis step.
    Expected file: data/processed/association_results.csv
    """
    path = get_output_path("data/processed/association_results.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Association results not found at {path}. "
                                "Ensure T025 has been completed successfully.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} association results from {path}")
    return df

def load_metadata() -> pd.DataFrame:
    """
    Load the cleaned dataset metadata to get sample information.
    Expected file: data/processed/cleaned_dataset.csv
    """
    path = get_output_path("data/processed/cleaned_dataset.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned dataset not found at {path}. "
                                "Ensure T017 has been completed successfully.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} samples from {path}")
    return df

def select_top_taxa(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """
    Select the top N taxa based on the absolute value of the correlation coefficient.
    This assumes the dataframe contains columns: 'taxon', 'correlation', 'q_value'.
    """
    if 'q_value' in df.columns:
        # Filter for significant taxa if possible, otherwise take top N overall
        significant = df[df['q_value'] < 0.05]
        if len(significant) > 0:
            df = significant
            logger.info(f"Filtered to {len(df)} significant taxa (q < 0.05)")
        else:
            logger.warning("No significant taxa found (q < 0.05). Using top N by |correlation|.")

    if 'correlation' not in df.columns:
        raise KeyError("Association results must contain a 'correlation' column.")

    # Sort by absolute correlation
    df_sorted = df.sort_values(by='correlation', key=lambda x: x.abs(), ascending=False)
    top_df = df_sorted.head(n)
    logger.info(f"Selected top {len(top_df)} taxa for heatmap")
    return top_df

def prepare_heatmap_data(df_taxa: pd.DataFrame, df_metadata: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare data for the heatmap.
    We need a matrix of Taxon x Sample (or Taxon x Group) with abundance or correlation values.
    Since T025 produces association results (Taxon vs Mental Health Score correlation),
    and we don't have the full OTU table in the association results, we will visualize
    the correlation coefficients themselves as a heatmap of Taxa vs Mental Health Variables.

    However, a "Taxa Heatmap" usually implies Taxa x Samples.
    Given the constraints of the current artifacts (only association_results.csv),
    we will create a heatmap of the Top Taxa Correlations against the different Mental Health Metrics
    if available, or just a single column if the correlation is pre-aggregated.

    Re-reading T020/T020a: They calculate correlations for PHQ-9 and GAD-7.
    The output T025 (association_results.csv) likely has rows like:
    [taxon, phq9_corr, phq9_pval, phq9_qval, gad7_corr, gad7_pval, gad7_qval]
    OR
    [taxon, variable, correlation, pval, qval]

    Let's assume the wide format or pivot if necessary.
    If the data is in long format (one row per taxon-variable pair), we pivot.
    If it's wide, we select the correlation columns.

    Strategy:
    1. Identify columns containing 'corr' or 'correlation'.
    2. If multiple mental health variables exist, pivot to show Taxa vs Variables.
    3. If only one, show Taxa vs Sample Groups (if we had groups) or just Taxa vs 1.
    
    Since we need a heatmap of "Top Associated Taxa", and we have correlation coefficients,
    the most informative heatmap is Taxa (rows) x Mental Health Variable (columns) showing the correlation strength.
    """
    # Identify correlation columns
    corr_cols = [c for c in df_taxa.columns if 'corr' in c.lower() or 'coefficient' in c.lower()]
    
    if len(corr_cols) == 0:
        raise ValueError("No correlation columns found in association results.")

    # Filter for the top taxa
    # If we have multiple variables, we want to keep all of them in the heatmap
    # We select the top taxa based on the maximum absolute correlation across all variables
    max_abs_corr = df_taxa[corr_cols].abs().max(axis=1)
    df_top = df_taxa.loc[max_abs_corr.nlargest(20).index].copy()

    # Set taxon as index
    df_top = df_top.set_index('taxon')

    # Ensure we only have numeric columns for the heatmap
    numeric_cols = [c for c in corr_cols if c in df_top.columns]
    heatmap_data = df_top[numeric_cols]

    logger.info(f"Heatmap data shape: {heatmap_data.shape}")
    return heatmap_data

def plot_taxa_heatmap(df: pd.DataFrame, output_path: Path):
    """
    Generate a heatmap of top associated taxa.
    Color intensity is proportional to the correlation coefficient.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 10))

    # Create the heatmap
    # cmap: 'coolwarm' or 'RdBu_r' to show positive/negative
    sns.heatmap(df, annot=False, cmap='RdBu_r', center=0, 
                linewidths=.5, ax=ax, cbar_kws={'label': 'Correlation Coefficient'})

    ax.set_title('Top Associated Taxa vs Mental Health Metrics', fontsize=16, pad=20)
    ax.set_xlabel('Mental Health Variable', fontsize=12)
    ax.set_ylabel('Taxon', fontsize=12)

    # Rotate x-axis labels if they are long
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")

def run_heatmap_visualization():
    """
    Main entry point for generating the taxa heatmap.
    1. Load association results.
    2. Select top taxa.
    3. Prepare data matrix.
    4. Plot and save.
    """
    logger.info("Starting taxa heatmap visualization (T028)")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load data
    df_assoc = load_association_results()
    
    # Select top taxa
    df_top = select_top_taxa(df_assoc, n=20)
    
    # Prepare data
    heatmap_data = prepare_heatmap_data(df_top, load_metadata())
    
    # Define output path
    output_path = get_output_path("results/plots/taxa_heatmap.png")
    
    # Plot
    plot_taxa_heatmap(heatmap_data, output_path)
    
    logger.info("T028 completed successfully.")
    return output_path

def main():
    run_heatmap_visualization()

if __name__ == "__main__":
    main()