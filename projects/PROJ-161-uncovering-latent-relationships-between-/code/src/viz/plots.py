"""
Visualization module for generating UMAP scatter plots colored by resistance phenotype.
"""
import os
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.config import get_project_root, get_data_processed_path, load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_umap_embedding() -> pd.DataFrame:
    """
    Load the UMAP embedding from the processed data directory.
    
    Returns:
        DataFrame with UMAP coordinates and associated metadata.
    
    Raises:
        FileNotFoundError: If the embedding file does not exist.
    """
    project_root = get_project_root()
    processed_dir = get_data_processed_path()
    embedding_path = processed_dir / "umap_embedding.csv"
    
    if not embedding_path.exists():
        raise FileNotFoundError(f"UMAP embedding file not found at {embedding_path}")
    
    logger.info(f"Loading UMAP embedding from {embedding_path}")
    df = pd.read_csv(embedding_path)
    
    # Ensure required columns exist
    required_cols = ['umap_1', 'umap_2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in UMAP embedding: {missing_cols}")
        
    return df


def load_resistance_labels() -> Optional[pd.DataFrame]:
    """
    Load resistance labels from the processed descriptors file.
    This assumes the descriptors file contains a 'resistance_label' or similar column.
    If not found, returns None and the plot will be colored by a generic index.
    
    Returns:
        DataFrame with InChIKey and resistance label, or None if not found.
    """
    processed_dir = get_data_processed_path()
    descriptors_path = processed_dir / "descriptors.csv"
    
    if not descriptors_path.exists():
        logger.warning(f"Descriptors file not found at {descriptors_path}. Cannot load resistance labels.")
        return None
        
    logger.info(f"Loading resistance labels from {descriptors_path}")
    df = pd.read_csv(descriptors_path)
    
    # Look for common resistance label column names
    label_cols = ['resistance_label', 'resistance_phenotype', 'phenotype', 'resistance']
    found_col = None
    for col in label_cols:
        if col in df.columns:
            found_col = col
            break
    
    if found_col is None:
        logger.warning("No resistance label column found in descriptors.csv. Plot will use generic indexing.")
        return None
        
    # Return only InChIKey and the label column
    if 'InChIKey' in df.columns:
        return df[['InChIKey', found_col]].rename(columns={found_col: 'resistance_label'})
    else:
        # If no InChIKey, assume the index or a compound_id exists. 
        # For safety, we'll return the whole df and let the merge logic handle it,
        # but typically we need a join key. If InChIKey is missing, we can't merge.
        logger.error("InChIKey column not found in descriptors.csv. Cannot merge with UMAP embedding.")
        return None


def generate_umap_scatter_plot(
    embedding_df: pd.DataFrame,
    labels_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
    title: str = "UMAP Embedding of Molecular Descriptors"
) -> Path:
    """
    Generate a UMAP scatter plot colored by resistance phenotype.
    
    Args:
        embedding_df: DataFrame containing UMAP coordinates (umap_1, umap_2).
        labels_df: Optional DataFrame containing InChIKey and resistance_label for coloring.
        output_path: Path to save the plot. Defaults to data/processed/umap_scatter.png.
        title: Title for the plot.
    
    Returns:
        Path to the saved plot file.
    """
    # Determine output path
    if output_path is None:
        project_root = get_project_root()
        processed_dir = get_data_processed_path()
        output_path = processed_dir / "umap_scatter.png"
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for plotting
    plot_df = embedding_df.copy()
    
    # Merge with labels if available
    if labels_df is not None and 'InChIKey' in plot_df.columns and 'InChIKey' in labels_df.columns:
        plot_df = plot_df.merge(labels_df, on='InChIKey', how='left')
        has_labels = True
    elif labels_df is not None and len(labels_df) == len(plot_df):
        # Assume 1:1 match by position if no key exists (risky but fallback)
        plot_df['resistance_label'] = labels_df['resistance_label'].values
        has_labels = True
    else:
        has_labels = False
        plot_df['resistance_label'] = 'Unknown'
    
    # Set style
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 10))
    
    if has_labels:
        # Sort unique labels for consistent coloring
        unique_labels = plot_df['resistance_label'].dropna().unique()
        # Create a palette
        palette = sns.color_palette("viridis", len(unique_labels)) if len(unique_labels) > 1 else ["#333333"]
        
        # Plot
        scatter = sns.scatterplot(
            data=plot_df,
            x='umap_1',
            y='umap_2',
            hue='resistance_label',
            palette=palette,
            alpha=0.7,
            s=50,
            edgecolor='w',
            linewidth=0.5
        )
        plt.legend(title='Resistance Phenotype', bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        # No labels available, plot single color
        sns.scatterplot(
            data=plot_df,
            x='umap_1',
            y='umap_2',
            color='#333333',
            alpha=0.7,
            s=50,
            edgecolor='w',
            linewidth=0.5
        )
        plt.title(f"{title} (No Resistance Data Available)", fontsize=16)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved UMAP scatter plot to {output_path} (no resistance data)")
        return output_path
    
    plt.title(title, fontsize=16)
    plt.xlabel('UMAP 1', fontsize=12)
    plt.ylabel('UMAP 2', fontsize=12)
    
    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved UMAP scatter plot to {output_path}")
    return output_path


def run_umap_viz_pipeline() -> Path:
    """
    Run the full UMAP visualization pipeline:
    1. Load UMAP embedding
    2. Load resistance labels
    3. Generate and save the scatter plot
    
    Returns:
        Path to the saved plot file.
    """
    logger.info("Starting UMAP visualization pipeline...")
    
    # Load embedding
    embedding_df = load_umap_embedding()
    
    # Load labels
    labels_df = load_resistance_labels()
    
    # Generate plot
    output_path = generate_umap_scatter_plot(embedding_df, labels_df)
    
    return output_path


def main():
    """Entry point for the UMAP visualization script."""
    try:
        output_path = run_umap_viz_pipeline()
        print(f"UMAP scatter plot successfully generated at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate UMAP scatter plot: {e}")
        raise


if __name__ == "__main__":
    main()
