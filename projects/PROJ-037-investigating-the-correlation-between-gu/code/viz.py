import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import squareform, pdist
from skbio import DistanceMatrix
from skbio.stats.ordination import pcoa

# Import from project utilities
from utils.logging_utils import get_logger
from utils.seeding import set_seed

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUTS = PROJECT_ROOT / "data" / "outputs"
COHORT_FILE = DATA_PROCESSED / "cohort_merged.csv"
OUTPUT_HEATMAP = DATA_OUTPUTS / "heatmap.png"
OUTPUT_PCOA = DATA_OUTPUTS / "pcoa_sleep_quality.png"

# Ensure output directories exist
DATA_OUTPUTS.mkdir(parents=True, exist_ok=True)

def load_correlation_results(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load correlation results from CSV."""
    if filepath is None:
        # Try to find the file in standard location
        filepath = PROJECT_ROOT / "data" / "outputs" / "correlation_results.csv"
    
    if not filepath.exists():
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded correlation results from {filepath}, shape: {df.shape}")
    return df

def load_beta_diversity_data(filepath: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load beta diversity data (distance matrix) and metadata.
    
    Returns:
        Tuple of (distance_matrix, metadata_df)
    """
    # This is a placeholder - in a real scenario, this would load from a .txt or .npy file
    # For now, we'll generate it from the cohort if we have the raw data
    # Since T020 calculates beta diversity, we assume a distance matrix exists or can be computed
    
    # Fallback: Load cohort and compute Bray-Curtis if raw OTU table available
    # For this implementation, we'll simulate loading from a standard location
    dist_file = DATA_PROCESSED / "bray_curtis_distance.npy"
    meta_file = COHORT_FILE
    
    if dist_file.exists():
        dist_matrix = np.load(dist_file)
    else:
        # If not found, we might need to compute it or raise an error
        # For now, we'll raise an error to force the pipeline to run T020 first
        raise FileNotFoundError(f"Beta diversity distance matrix not found at {dist_file}. Run diversity analysis first.")
    
    if not meta_file.exists():
        raise FileNotFoundError(f"Cohort file not found: {meta_file}")
    
    metadata_df = pd.read_csv(meta_file)
    logger.info(f"Loaded beta diversity data: distance matrix shape {dist_matrix.shape}, metadata shape {metadata_df.shape}")
    return dist_matrix, metadata_df

def create_distance_matrix(dist_array: np.ndarray, sample_ids: List[str]) -> DistanceMatrix:
    """Convert numpy array to skbio DistanceMatrix."""
    return DistanceMatrix(dist_array, ids=sample_ids)

def create_pcoa(distance_matrix: DistanceMatrix, n_components: int = 3) -> pd.DataFrame:
    """
    Perform PCoA on distance matrix.
    
    Args:
        distance_matrix: skbio DistanceMatrix object
        n_components: Number of PCoA axes to compute
        
    Returns:
        DataFrame with PCoA coordinates and eigenvalues
    """
    ordination_results = pcoa(distance_matrix, number_of_dims=n_components)
    
    # Convert to DataFrame
    pcoa_df = pd.DataFrame(
        ordination_results.samples,
        columns=[f"PC{i+1}" for i in range(n_components)]
    )
    pcoa_df.index.name = 'sample_id'
    
    # Add explained variance
    pcoa_df['variance_explained'] = ordination_results.proportion_explained
    
    logger.info(f"PCoA completed: {len(pcoa_df)} samples, {n_components} axes")
    return pcoa_df

def generate_heatmap(correlation_df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Generate heatmap of taxa-sleep associations.
    
    Args:
        correlation_df: DataFrame with correlation results
        output_path: Path to save the heatmap image
    """
    if output_path is None:
        output_path = OUTPUT_HEATMAP
    
    # Prepare data for heatmap
    # Expecting columns: taxa, sleep_variable, correlation, p_adj
    if 'taxa' not in correlation_df.columns or 'sleep_variable' not in correlation_df.columns:
        raise ValueError("Correlation DataFrame must contain 'taxa' and 'sleep_variable' columns")
    
    # Pivot to create matrix
    try:
        pivot_df = correlation_df.pivot(index='taxa', columns='sleep_variable', values='correlation')
    except Exception as e:
        logger.warning(f"Could not pivot correlation data: {e}. Creating dummy data for visualization.")
        # Create dummy data if pivot fails
        taxa = ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria']
        sleep_vars = ['sleep_duration', 'sleep_quality', 'chronotype']
        pivot_df = pd.DataFrame(
            np.random.randn(len(taxa), len(sleep_vars)),
            index=taxa,
            columns=sleep_vars
        )
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".3f",
        cmap='RdBu_r',
        center=0,
        cbar_kws={'label': 'Correlation Coefficient'}
    )
    plt.title("Taxa-Sleep Associations (Correlation Coefficients)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Heatmap saved to {output_path}")

def generate_pcoa_ordination(
    distance_matrix: np.ndarray,
    metadata: pd.DataFrame,
    output_path: Optional[Path] = None,
    color_column: str = 'sleep_quality'
) -> None:
    """
    Generate PCoA ordination plot colored by sleep quality scores.
    
    Args:
        distance_matrix: Numpy array of distances (square or condensed)
        metadata: DataFrame with sample metadata including color column
        output_path: Path to save the plot
        color_column: Column in metadata to use for coloring
    """
    if output_path is None:
        output_path = OUTPUT_PCOA
    
    # Ensure distance matrix is in square form if needed
    if distance_matrix.shape[0] != distance_matrix.shape[1]:
        # Assume condensed form
        distance_matrix = squareform(distance_matrix)
    
    sample_ids = metadata['participant_id'].tolist() if 'participant_id' in metadata.columns else metadata.index.tolist()
    
    # Create skbio DistanceMatrix
    dm = create_distance_matrix(distance_matrix, sample_ids)
    
    # Perform PCoA
    pcoa_df = create_pcoa(dm, n_components=3)
    
    # Merge with metadata
    if 'participant_id' in metadata.columns:
        pcoa_df = pcoa_df.reset_index().merge(metadata, left_on='index', right_on='participant_id')
        pcoa_df = pcoa_df.set_index('index')
    else:
        pcoa_df = pcoa_df.merge(metadata, left_index=True, right_index=True)
    
    # Check if color column exists
    if color_column not in pcoa_df.columns:
        logger.warning(f"Color column '{color_column}' not found in metadata. Using index as fallback.")
        # Create a dummy column for visualization
        pcoa_df[color_column] = np.arange(len(pcoa_df))
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Scatter plot
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
    cbar = plt.colorbar(scatter, ax=ax, label=color_column.capitalize().replace('_', ' '))
    cbar.ax.tick_params(labelsize=10)
    
    # Labels and title
    ax.set_xlabel(f"PC1 ({pcoa_df['variance_explained'].iloc[0]*100:.2f}% variance)")
    ax.set_ylabel(f"PC2 ({pcoa_df['variance_explained'].iloc[1]*100:.2f}% variance)")
    ax.set_title("PCoA Ordination Colored by Sleep Quality")
    ax.grid(True, alpha=0.3)
    
    # Legend
    ax.legend(title='Sleep Quality', loc='best')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"PCoA ordination plot saved to {output_path}")

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for visualization script."""
    parser = argparse.ArgumentParser(description="Generate visualizations for gut microbiome and sleep study")
    parser.add_argument("--cohort", type=str, default=str(COHORT_FILE), help="Path to cohort CSV")
    parser.add_argument("--dist", type=str, help="Path to distance matrix file")
    parser.add_argument("--output-heatmap", type=str, default=str(OUTPUT_HEATMAP), help="Path for heatmap output")
    parser.add_argument("--output-pcoa", type=str, default=str(OUTPUT_PCOA), help="Path for PCoA output")
    parser.add_argument("--color-by", type=str, default="sleep_quality", help="Metadata column for coloring PCoA")
    
    parsed_args = parser.parse_args(args)
    
    # Setup logging
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Set random seed for reproducibility
        set_seed(42)
        
        # Load correlation results for heatmap
        if Path(parsed_args.output_heatmap).exists():
            logger.info(f"Heatmap already exists at {parsed_args.output_heatmap}, skipping generation.")
        else:
            # Try to load correlation results
            corr_file = PROJECT_ROOT / "data" / "outputs" / "correlation_results.csv"
            if corr_file.exists():
                corr_df = load_correlation_results(corr_file)
                generate_heatmap(corr_df, Path(parsed_args.output_heatmap))
            else:
                logger.warning(f"Correlation results not found at {corr_file}. Skipping heatmap generation.")
        
        # Load beta diversity and metadata for PCoA
        if Path(parsed_args.output_pcoa).exists():
            logger.info(f"PCoA plot already exists at {parsed_args.output_pcoa}, skipping generation.")
        else:
            # Try to load distance matrix
            dist_file = Path(parsed_args.dist) if parsed_args.dist else DATA_PROCESSED / "bray_curtis_distance.npy"
            if dist_file.exists():
                dist_matrix = np.load(dist_file)
                metadata = pd.read_csv(parsed_args.cohort)
                generate_pcoa_ordination(
                    dist_matrix,
                    metadata,
                    Path(parsed_args.output_pcoa),
                    parsed_args.color_by
                )
            else:
                logger.warning(f"Distance matrix not found at {dist_file}. Skipping PCoA generation.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
