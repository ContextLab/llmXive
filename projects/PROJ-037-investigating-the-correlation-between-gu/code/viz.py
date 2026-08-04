import os
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.spatial.distance import squareform
from skbio.stats.ordination import pcoa

# Import from project modules
from config import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.seeding import set_seed

# Configure logging
logger = get_logger(__name__)

def load_correlation_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load correlation results from CSV."""
    if filepath is None:
        config = get_config()
        filepath = config.output_dir / "correlation_results.csv"
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
    
    return pd.read_csv(filepath)

def load_beta_diversity_data(
    biom_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
    processed_cohort_path: Optional[str] = None
) -> Tuple[Any, pd.DataFrame]:
    """
    Load beta diversity distance matrix and metadata for PCoA.
    
    Returns:
        Tuple of (distance_matrix, metadata_df)
    """
    config = get_config()
    
    if processed_cohort_path is None:
        processed_cohort_path = config.processed_dir / "cohort_merged.csv"
    
    if not os.path.exists(processed_cohort_path):
        raise FileNotFoundError(f"Processed cohort not found: {processed_cohort_path}")
    
    # Load metadata
    metadata_df = pd.read_csv(processed_cohort_path)
    
    # We need to calculate beta diversity if not already present
    # For PCoA, we need a distance matrix. We'll calculate Bray-Curtis from the cohort data.
    # The cohort should contain OTU/ASV counts in columns starting with 'OTU_' or similar.
    
    # Identify OTU columns (assuming they start with 'OTU_' or 'ASV_')
    otu_cols = [col for col in metadata_df.columns if col.startswith('OTU_') or col.startswith('ASV_')]
    
    if not otu_cols:
        # Fallback: look for any numeric columns that might be counts
        numeric_cols = metadata_df.select_dtypes(include=[np.number]).columns
        # Exclude known metadata columns
        exclude_cols = ['participant_id', 'age', 'bmi', 'sleep_duration', 'sleep_quality', 
                      'chronotype', 'antibiotic_use', 'sample_id']
        otu_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if not otu_cols:
        raise ValueError("No OTU/ASV count columns found in the processed cohort.")
    
    # Create count matrix
    count_matrix = metadata_df[otu_cols].copy()
    
    # Calculate Bray-Curtis distance
    from scipy.spatial.distance import pdist, squareform
    distance_matrix = squareform(pdist(count_matrix, metric='braycurtis'))
    
    return distance_matrix, metadata_df

def generate_pcoa_ordination(
    output_path: Optional[str] = None,
    color_column: str = "sleep_quality",
    title: str = "PCoA Ordination by Sleep Quality"
) -> str:
    """
    Generate PCoA ordination plot colored by sleep quality scores.
    
    Args:
        output_path: Path to save the plot. If None, uses config default.
        color_column: Column name in metadata to use for coloring points.
        title: Plot title.
        
    Returns:
        Path to the saved plot file.
    """
    config = get_config()
    
    if output_path is None:
        output_path = config.output_dir / "pcoa_sleep_quality.png"
    else:
        output_path = Path(output_path)
    
    logger.info(f"Generating PCoA ordination plot: {output_path}")
    
    # Load data
    distance_matrix, metadata_df = load_beta_diversity_data()
    
    # Ensure color column exists
    if color_column not in metadata_df.columns:
        raise ValueError(f"Color column '{color_column}' not found in metadata. Available: {list(metadata_df.columns)}")
    
    # Perform PCoA
    logger.info("Performing PCoA analysis...")
    pcoa_result = pcoa(distance_matrix)
    
    # Get the sample IDs from the distance matrix
    sample_ids = metadata_df['participant_id'].values
    
    # Extract ordination coordinates (using the first two principal coordinates)
    ordination_df = pd.DataFrame({
        'PC1': pcoa_result.samples['PC1'].values,
        'PC2': pcoa_result.samples['PC2'].values,
        'participant_id': sample_ids,
        color_column: metadata_df[color_column].values
    })
    
    # Calculate variance explained
    variance_explained = pcoa_result.proportion_explained
    pc1_var = variance_explained[0] * 100
    pc2_var = variance_explained[1] * 100
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    
    # Create scatter plot with color gradient
    scatter = plt.scatter(
        ordination_df['PC1'],
        ordination_df['PC2'],
        c=ordination_df[color_column],
        cmap='viridis',
        alpha=0.7,
        edgecolors='k',
        s=60
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label(color_column.replace('_', ' ').title())
    
    # Labels and title
    plt.xlabel(f'PC1 ({pc1_var:.2f}% variance)')
    plt.ylabel(f'PC2 ({pc2_var:.2f}% variance)')
    plt.title(title)
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"PCoA plot saved to: {output_path}")
    return str(output_path)

def create_placeholder_pcoa(output_path: str) -> str:
    """
    Create a placeholder PCoA plot if real data is unavailable.
    NOTE: This is a fallback and should not be used for final results.
    """
    logger.warning("Creating placeholder PCoA plot (no real data available)")
    
    plt.figure(figsize=(10, 8))
    plt.text(0.5, 0.5, "No real data available for PCoA", 
             ha='center', va='center', fontsize=16)
    plt.axis('off')
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    return output_path

def main():
    """Main entry point for PCoA visualization generation."""
    parser = argparse.ArgumentParser(description="Generate PCoA ordination plots")
    parser.add_argument("--output", type=str, default=None,
                      help="Output path for the PCoA plot")
    parser.add_argument("--color", type=str, default="sleep_quality",
                      help="Metadata column to color by")
    parser.add_argument("--title", type=str, default="PCoA Ordination by Sleep Quality",
                      help="Plot title")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        output_path = generate_pcoa_ordination(
            output_path=args.output,
            color_column=args.color,
            title=args.title
        )
        print(f"Successfully generated PCoA plot: {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        print(f"Error: {e}")
        print("Please ensure the processed cohort file exists at data/processed/cohort_merged.csv")
    except Exception as e:
        logger.error(f"Error generating PCoA plot: {e}")
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()