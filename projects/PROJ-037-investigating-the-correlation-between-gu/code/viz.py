"""
Visualization module for generating PCoA plots and heatmaps.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import squareform, pdist
from skbio import DistanceMatrix
from skbio.stats.ordination import pcoa

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUTS = PROJECT_ROOT / "data" / "outputs"

# Ensure output directories exist
DATA_OUTPUTS.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_correlation_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load correlation results from CSV.

    Args:
        filepath: Path to correlation results CSV. Defaults to standard location.

    Returns:
        DataFrame with correlation results.
    """
    if filepath is None:
        filepath = DATA_OUTPUTS / "correlation_results.csv"
    
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded correlation results with {len(df)} rows from {filepath}")
    return df


def load_beta_diversity_data(
    distance_matrix_path: Optional[str] = None,
    metadata_path: Optional[str] = None
) -> Tuple[DistanceMatrix, pd.DataFrame]:
    """
    Load beta diversity distance matrix and metadata.

    Args:
        distance_matrix_path: Path to distance matrix file.
        metadata_path: Path to metadata file.

    Returns:
        Tuple of (DistanceMatrix, metadata DataFrame).
    """
    if distance_matrix_path is None:
        distance_matrix_path = DATA_PROCESSED / "beta_diversity_distance_matrix.tsv"
    
    if metadata_path is None:
        metadata_path = DATA_PROCESSED / "cohort_merged.csv"

    if not Path(distance_matrix_path).exists():
        raise FileNotFoundError(f"Distance matrix file not found: {distance_matrix_path}")
    
    if not Path(metadata_path).exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    # Load distance matrix
    dm = DistanceMatrix.read(distance_matrix_path)
    
    # Load metadata
    metadata = pd.read_csv(metadata_path)
    metadata.set_index('participant_id', inplace=True)
    
    logger.info(f"Loaded distance matrix with {len(dm.ids)} samples and metadata with {len(metadata)} rows")
    return dm, metadata


def create_distance_matrix(dm: DistanceMatrix) -> np.ndarray:
    """
    Convert skbio DistanceMatrix to numpy array.

    Args:
        dm: skbio DistanceMatrix object.

    Returns:
        Numpy array of distances.
    """
    return np.array(dm.data)


def create_pcoa(
    dm: DistanceMatrix,
    metadata: pd.DataFrame,
    color_column: str = "sleep_quality"
) -> Tuple[Any, pd.DataFrame]:
    """
    Perform PCoA on distance matrix and merge with metadata.

    Args:
        dm: skbio DistanceMatrix object.
        metadata: Metadata DataFrame with participant_id as index.
        color_column: Column in metadata to use for coloring.

    Returns:
        Tuple of (OrdinationResults, metadata with PCoA coordinates).
    """
    # Perform PCoA
    ord_result = pcoa(dm)
    
    # Extract coordinates
    coords = ord_result.samples
    
    # Merge with metadata
    coords_reset = coords.reset_index()
    coords_reset.columns = ['participant_id'] + [f'PC{i+1}' for i in range(coords_reset.shape[1]-1)]
    
    # Merge with metadata
    merged = coords_reset.merge(metadata.reset_index(), on='participant_id')
    merged.set_index('participant_id', inplace=True)
    
    logger.info(f"PCoA completed with {len(merged)} samples")
    return ord_result, merged


def generate_heatmap(
    results_df: pd.DataFrame,
    output_path: Optional[str] = None,
    top_n: int = 20
) -> None:
    """
    Generate a heatmap of taxa-sleep associations.

    Args:
        results_df: DataFrame with correlation results.
        output_path: Path to save the heatmap image.
        top_n: Number of top correlations to display.
    """
    if output_path is None:
        output_path = DATA_OUTPUTS / "heatmap.png"
    
    if results_df.empty:
        logger.warning("Empty results DataFrame, cannot generate heatmap")
        return

    # Sort by absolute correlation and take top N
    results_df = results_df.sort_values(by='abs_correlation', ascending=False).head(top_n)
    
    # Pivot for heatmap
    # Assuming columns: 'taxon', 'sleep_variable', 'correlation', 'p_adj'
    if 'taxon' not in results_df.columns or 'sleep_variable' not in results_df.columns:
        logger.error("Results DataFrame missing required columns 'taxon' or 'sleep_variable'")
        return

    pivot_data = results_df.pivot_table(
        index='taxon',
        columns='sleep_variable',
        values='correlation',
        aggfunc='first'
    )
    
    # Create figure
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        pivot_data,
        annot=True,
        fmt=".3f",
        cmap='coolwarm',
        center=0,
        cbar_kws={'label': 'Correlation Coefficient'}
    )
    plt.title(f'Top {top_n} Taxa-Sleep Associations')
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Heatmap saved to {output_path}")


def generate_pcoa_ordination(
    output_path: Optional[str] = None,
    color_column: str = "sleep_quality"
) -> None:
    """
    Generate a PCoA ordination plot colored by sleep quality scores.

    Args:
        output_path: Path to save the PCoA plot image.
        color_column: Column in metadata to use for coloring.
    """
    if output_path is None:
        output_path = DATA_OUTPUTS / "pcoa_sleep_quality.png"

    logger.info(f"Generating PCoA plot colored by {color_column}")

    # Load data
    try:
        dm, metadata = load_beta_diversity_data()
    except FileNotFoundError as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # Perform PCoA
    ord_result, merged_data = create_pcoa(dm, metadata, color_column)

    # Check if color column exists
    if color_column not in merged_data.columns:
        logger.error(f"Color column '{color_column}' not found in metadata. Available: {merged_data.columns.tolist()}")
        raise ValueError(f"Color column '{color_column}' not found in metadata")

    # Extract PC1 and PC2 coordinates
    pc1_col = 'PC1'
    pc2_col = 'PC2'
    
    if pc1_col not in merged_data.columns or pc2_col not in merged_data.columns:
        logger.error(f"PCoA coordinates not found. Available: {merged_data.columns.tolist()}")
        raise ValueError("PCoA coordinates PC1 and PC2 not found")

    x = merged_data[pc1_col]
    y = merged_data[pc2_col]
    colors = merged_data[color_column]

    # Create plot
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(
        x, y,
        c=colors,
        cmap='viridis',
        alpha=0.7,
        edgecolors='w',
        s=50,
        vmin=colors.min(),
        vmax=colors.max()
    )

    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label(color_column.replace('_', ' ').title())

    # Labels and title
    plt.xlabel(f'PC1 ({ord_result.proportion_explained[0]:.2%} variance explained)')
    plt.ylabel(f'PC2 ({ord_result.proportion_explained[1]:.2%} variance explained)')
    plt.title('PCoA Ordination Colored by Sleep Quality')
    
    # Add legend
    plt.legend(
        title='Sleep Quality',
        loc='best',
        frameon=True,
        fontsize='medium'
    )

    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"PCoA plot saved to {output_path}")


def main():
    """
    Main entry point for visualization scripts.
    """
    parser = argparse.ArgumentParser(description="Generate visualizations for microbiome-sleep analysis")
    parser.add_argument(
        "--type",
        choices=["heatmap", "pcoa"],
        default="pcoa",
        help="Type of visualization to generate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path"
    )
    parser.add_argument(
        "--color-column",
        type=str,
        default="sleep_quality",
        help="Metadata column to color by (for PCoA)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Number of top correlations for heatmap"
    )

    args = parser.parse_args()

    if args.type == "heatmap":
        # Load correlation results
        try:
            results = load_correlation_results()
            generate_heatmap(results, args.output, args.top_n)
        except FileNotFoundError as e:
            logger.error(f"Cannot generate heatmap: {e}")
            sys.exit(1)
    elif args.type == "pcoa":
        try:
            generate_pcoa_ordination(args.output, args.color_column)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Cannot generate PCoA plot: {e}")
            sys.exit(1)
    else:
        logger.error(f"Unknown visualization type: {args.type}")
        sys.exit(1)

    logger.info("Visualization generation completed successfully")


if __name__ == "__main__":
    main()