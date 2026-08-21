import os
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from skbio.stats.ordination import pcoa
from skbio import DistanceMatrix
from skbio.stats.distance import permanova

from utils.logging_utils import get_logger
from utils.seeding import set_seed

logger = get_logger(__name__)

def load_correlation_results(results_path: str = "data/outputs/correlation_results.csv") -> pd.DataFrame:
    """Load correlation results from CSV."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Correlation results file not found: {results_path}")
    return pd.read_csv(results_path)

def load_beta_diversity_data(
    biom_path: str = "data/processed/biom_table.biom",
    metadata_path: str = "data/processed/cohort_merged.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load beta diversity data from BIOM table and metadata.
    Returns (otu_table, metadata).
    """
    try:
        import biom
        table = biom.load_table(biom_path)
        otu_df = table.to_dataframe()
        # Transpose so rows are samples (participants) and columns are taxa
        otu_df = otu_df.T
    except Exception as e:
        logger.error(f"Failed to load BIOM table: {e}")
        raise

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    metadata = pd.read_csv(metadata_path)

    # Ensure participant IDs match
    common_ids = set(otu_df.index) & set(metadata['participant_id'])
    if len(common_ids) == 0:
        raise ValueError("No matching participant IDs between OTU table and metadata")

    otu_df = otu_df.loc[list(common_ids)]
    metadata = metadata[metadata['participant_id'].isin(common_ids)].set_index('participant_id')

    return otu_df, metadata

def generate_heatmap(
    results: pd.DataFrame,
    output_path: str = "data/outputs/heatmap.png",
    top_n: int = 20
) -> None:
    """Generate heatmap of taxa-sleep associations."""
    if results.empty:
        logger.warning("No correlation results to plot. Creating empty heatmap.")
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center', fontsize=20)
        plt.axis('off')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return

    # Filter significant results
    sig_results = results[results['is_significant']].copy()
    if sig_results.empty:
        logger.warning("No significant correlations found. Plotting top N absolute correlations.")
        sig_results = results.nlargest(top_n, 'abs_correlation')

    # Prepare data for heatmap
    heatmap_data = sig_results.pivot_table(
        index='taxa',
        columns='sleep_variable',
        values='correlation',
        aggfunc='first'
    ).fillna(0)

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".3f",
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=.5,
        cbar_kws={"shrink": .5}
    )
    plt.title('Taxa-Sleep Associations (Correlation Coefficients)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")

def generate_pcoa_ordination(
    otu_table: pd.DataFrame,
    metadata: pd.DataFrame,
    output_path: str = "data/outputs/pcoa_sleep_quality.png",
    color_column: str = "sleep_quality_score",
    distance_metric: str = "braycurtis"
) -> None:
    """
    Generate PCoA ordination plot colored by sleep quality scores.
    
    Args:
        otu_table: DataFrame with samples as rows, taxa as columns (counts/relative abundance)
        metadata: DataFrame with samples as index, including the color_column
        output_path: Path to save the plot
        color_column: Column in metadata to use for coloring points
        distance_metric: Distance metric for beta diversity (default: braycurtis)
    """
    logger.info(f"Generating PCoA ordination colored by '{color_column}'")

    # Validate inputs
    if otu_table.empty:
        raise ValueError("OTU table is empty")
    if metadata.empty:
        raise ValueError("Metadata is empty")
    
    # Ensure index alignment
    common_samples = list(set(otu_table.index) & set(metadata.index))
    if len(common_samples) == 0:
        raise ValueError("No common samples between OTU table and metadata")
    
    otu_table = otu_table.loc[common_samples]
    metadata = metadata.loc[common_samples]

    # Check if color column exists
    if color_column not in metadata.columns:
        raise ValueError(f"Color column '{color_column}' not found in metadata. Available: {list(metadata.columns)}")

    # Calculate distance matrix
    logger.info(f"Calculating {distance_metric} distance matrix...")
    try:
        dist_matrix = pdist(otu_table.values, metric=distance_metric)
        distance_matrix = DistanceMatrix(dist_matrix, ids=common_samples)
    except Exception as e:
        logger.error(f"Failed to calculate distance matrix: {e}")
        raise

    # Perform PCoA
    logger.info("Performing PCoA...")
    try:
        pcoa_result = pcoa(distance_matrix)
    except Exception as e:
        logger.error(f"Failed to perform PCoA: {e}")
        raise

    # Prepare plotting data
    pcoa_df = pd.DataFrame(pcoa_result.samples, index=common_samples)
    pcoa_df[color_column] = metadata[color_column]

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 10))

    # Scatter plot with color gradient
    scatter = ax.scatter(
        pcoa_df['PC1'],
        pcoa_df['PC2'],
        c=pcoa_df[color_column],
        cmap='viridis',
        alpha=0.7,
        edgecolors='k',
        linewidth=0.5,
        s=100
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label(color_column.replace('_', ' ').title())

    # Labels and title
    ax.set_xlabel(f'PC1 ({pcoa_result.proportion_explained[0]:.2%} variance)')
    ax.set_ylabel(f'PC2 ({pcoa_result.proportion_explained[1]:.2%} variance)')
    ax.set_title('PCoA Ordination of Gut Microbiome\nColored by Sleep Quality Score')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"PCoA plot saved to {output_path}")

def create_placeholder_pcoa(output_path: str = "data/outputs/pcoa_sleep_quality.png") -> None:
    """Create a placeholder PCoA plot if real data is unavailable."""
    logger.warning("Creating placeholder PCoA plot (no real data available)")
    plt.figure(figsize=(12, 10))
    plt.text(0.5, 0.5, 'PCoA Plot\n(Please run analysis with real data)', 
             ha='center', va='center', fontsize=20, color='gray')
    plt.axis('off')
    plt.title('Placeholder: PCoA Ordination')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Placeholder plot saved to {output_path}")

def main():
    """Main entry point for visualization tasks."""
    parser = argparse.ArgumentParser(description="Generate visualizations for microbiome-sleep analysis")
    parser.add_argument('--heatmap', action='store_true', help='Generate heatmap of taxa-sleep associations')
    parser.add_argument('--pcoa', action='store_true', help='Generate PCoA ordination plot')
    parser.add_argument('--results-path', type=str, default='data/outputs/correlation_results.csv',
                      help='Path to correlation results CSV')
    parser.add_argument('--biom-path', type=str, default='data/processed/biom_table.biom',
                      help='Path to BIOM table')
    parser.add_argument('--metadata-path', type=str, default='data/processed/cohort_merged.csv',
                      help='Path to merged cohort metadata')
    parser.add_argument('--output-dir', type=str, default='data/outputs',
                      help='Output directory for plots')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    set_seed(args.seed)

    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if args.heatmap:
        logger.info("Generating heatmap...")
        try:
            results = load_correlation_results(args.results_path)
            generate_heatmap(results, str(output_path / "heatmap.png"))
        except Exception as e:
            logger.error(f"Failed to generate heatmap: {e}")
            # Create placeholder if data unavailable
            create_placeholder_pcoa(str(output_path / "heatmap.png"))

    if args.pcoa:
        logger.info("Generating PCoA ordination plot...")
        try:
            otu_table, metadata = load_beta_diversity_data(args.biom_path, args.metadata_path)
            generate_pcoa_ordination(
                otu_table, 
                metadata, 
                str(output_path / "pcoa_sleep_quality.png"),
                color_column="sleep_quality_score"
            )
        except Exception as e:
            logger.error(f"Failed to generate PCoA plot: {e}")
            # Create placeholder if data unavailable
            create_placeholder_pcoa(str(output_path / "pcoa_sleep_quality.png"))

    if not args.heatmap and not args.pcoa:
        logger.info("No visualization task specified. Use --heatmap or --pcoa flags.")

if __name__ == "__main__":
    main()