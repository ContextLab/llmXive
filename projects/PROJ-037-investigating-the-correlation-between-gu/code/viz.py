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
from scipy.spatial.distance import squareform
from skbio import DistanceMatrix
from skbio.stats.ordination import pcoa

# Import from local project modules (API surface)
from utils.logging_utils import setup_logging, get_logger
from utils.seeding import set_seed

# Configure logging
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUTS = PROJECT_ROOT / "data" / "outputs"
COHORT_FILE = DATA_PROCESSED / "cohort_merged.csv"
DISTANCE_MATRIX_FILE = DATA_PROCESSED / "bray_curtis_distance_matrix.tsv"
OUTPUT_PCOA = DATA_OUTPUTS / "pcoa_sleep_quality.png"
OUTPUT_HEATMAP = DATA_OUTPUTS / "heatmap.png"

def load_correlation_results() -> pd.DataFrame:
    """Load the correlation results CSV."""
    results_path = DATA_OUTPUTS / "correlation_results.csv"
    if not results_path.exists():
        raise FileNotFoundError(f"Correlation results not found at {results_path}")
    return pd.read_csv(results_path)

def load_beta_diversity_data() -> DistanceMatrix:
    """Load the pre-computed Bray-Curtis distance matrix."""
    if not DISTANCE_MATRIX_FILE.exists():
        raise FileNotFoundError(
            f"Beta diversity matrix not found at {DISTANCE_MATRIX_FILE}. "
            "Please run code/diversity.py first to generate it."
        )
    # skbio DistanceMatrix can read from a file-like object or path
    return DistanceMatrix.read(DISTANCE_MATRIX_FILE)

def create_distance_matrix(otu_table, metadata):
    """Calculate Bray-Curtis distance matrix from OTU table and metadata."""
    # This is a placeholder if the file doesn't exist, but the file loader is preferred
    # to ensure consistency with the pipeline.
    raise NotImplementedError("Use load_beta_diversity_data() for pre-computed matrix.")

def create_pcoa(distance_matrix, metadata):
    """Perform PCoA on the distance matrix."""
    return pcoa(distance_matrix)

def generate_heatmap(correlations_df, output_path):
    """
    Generate a heatmap of taxa-sleep associations.
    Requires correlations_df with columns: ['taxon', 'variable', 'correlation', 'p_adj']
    """
    if correlations_df.empty:
        logger.warning("Correlation dataframe is empty. Skipping heatmap generation.")
        return

    # Pivot for heatmap: index=taxon, columns=variable, values=correlation
    # Ensure we only have numeric correlation values
    pivot_data = correlations_df.pivot_table(
        index='taxon',
        columns='variable',
        values='correlation',
        aggfunc='first'
    )

    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot_data, annot=True, fmt=".3f", cmap='coolwarm', center=0,
                cbar_kws={'label': 'Correlation Coefficient (Spearman)'})
    plt.title("Taxa-Sleep Associations (Correlation Coefficients)")
    plt.xlabel("Sleep Variable")
    plt.ylabel("Taxon")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")

def generate_pcoa_ordination(metadata_df, output_path):
    """
    Generate a PCoA ordination plot colored by sleep quality scores.
    """
    # 1. Load pre-computed distance matrix
    logger.info(f"Loading beta diversity matrix from {DISTANCE_MATRIX_FILE}...")
    try:
        dm = load_beta_diversity_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # 2. Load metadata to ensure alignment
    if not COHORT_FILE.exists():
        raise FileNotFoundError(f"Cohort file not found at {COHORT_FILE}")
    metadata_df = pd.read_csv(COHORT_FILE)

    # Ensure metadata index matches distance matrix ids
    # DistanceMatrix ids are usually the participant IDs
    if 'participant_id' in metadata_df.columns:
        metadata_df = metadata_df.set_index('participant_id')

    # Filter DM to only include IDs present in metadata (and vice versa)
    common_ids = list(set(dm.ids) & set(metadata_df.index))
    if len(common_ids) == 0:
        raise ValueError("No common participants between distance matrix and metadata.")

    dm_filtered = dm.subset(common_ids)
    metadata_filtered = metadata_df.loc[common_ids]

    # 3. Perform PCoA
    logger.info("Performing PCoA...")
    ordination = create_pcoa(dm_filtered, metadata_filtered)

    # 4. Prepare plot data
    # PCoA scores are in ordination.samples
    # We need to map sleep_quality to the sample IDs
    if 'sleep_quality' not in metadata_filtered.columns:
        raise ValueError("Column 'sleep_quality' not found in metadata.")

    # Create a DataFrame for plotting
    plot_df = pd.DataFrame(ordination.samples, index=common_ids)
    plot_df['sleep_quality'] = metadata_filtered['sleep_quality']

    # 5. Generate Plot
    plt.figure(figsize=(10, 8))
    # Use sleep_quality as the coloring variable
    scatter = plt.scatter(
        plot_df.iloc[:, 0],
        plot_df.iloc[:, 1],
        c=plot_df['sleep_quality'],
        cmap='viridis',
        edgecolors='k',
        alpha=0.7,
        s=50
    )

    plt.xlabel(f"PCoA Axis 1 ({ordination.proportion_explained[0]:.2%} variance)")
    plt.ylabel(f"PCoA Axis 2 ({ordination.proportion_explained[1]:.2%} variance)")
    plt.title("PCoA Ordination Colored by Sleep Quality")

    # Add legend
    cbar = plt.colorbar(scatter)
    cbar.set_label("Sleep Quality Score")
    
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"PCoA plot saved to {output_path}")

def main():
    """Main entry point for visualization tasks."""
    parser = argparse.ArgumentParser(description="Generate visualization artifacts.")
    parser.add_argument("--output-dir", type=str, default=str(DATA_OUTPUTS),
                        help="Directory to save output plots.")
    parser.add_argument("--cohort", type=str, default=str(COHORT_FILE),
                        help="Path to merged cohort CSV.")
    args = parser.parse_args()

    # Setup logging
    setup_logging()
    set_seed(42)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Heatmap
    try:
        logger.info("Generating Heatmap...")
        corr_df = load_correlation_results()
        # Ensure we have the right columns for heatmap
        # Assuming analysis.py produced: taxon, variable, correlation, p_adj
        heatmap_path = output_dir / "heatmap.png"
        generate_heatmap(corr_df, heatmap_path)
    except FileNotFoundError as e:
        logger.warning(f"Skipping Heatmap: {e}")
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")

    # 2. Generate PCoA Plot
    try:
        logger.info("Generating PCoA Ordination Plot...")
        pcoa_path = output_dir / "pcoa_sleep_quality.png"
        # We load metadata inside the function to ensure it matches the DM
        generate_pcoa_ordination(None, pcoa_path)
    except FileNotFoundError as e:
        logger.warning(f"Skipping PCoA Plot: {e}")
    except Exception as e:
        logger.error(f"Error generating PCoA plot: {e}")
        import traceback
        traceback.print_exc()

    logger.info("Visualization tasks completed.")

if __name__ == "__main__":
    main()