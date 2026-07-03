"""
Visualization module for Gene Regulation analysis.
Generates heatmaps of enrichment q-values with clustering.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import pdist

from code.config import DATA_PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_enrichment_matrix() -> pd.DataFrame:
    """
    Load the enrichment matrix from the processed data directory.
    Expected file: data/processed/enrichment_matrix.csv
    
    Returns:
        DataFrame with motifs as rows and cell types as columns, containing q-values.
    """
    input_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Enrichment matrix not found at {input_path}. "
            "Please ensure T024 (generate_enrichment_matrix) has been run successfully."
        )
    
    logger.info(f"Loading enrichment matrix from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate expected columns
    required_cols = ['motif_id', 'cell_type', 'q_value_adj']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(
            f"Enrichment matrix missing required columns. "
            f"Found: {list(df.columns)}, Expected: {required_cols}"
        )
    
    # Pivot to get matrix: rows=motif_id, cols=cell_type, values=q_value_adj
    matrix = df.pivot(index='motif_id', columns='cell_type', values='q_value_adj')
    
    # Handle potential missing values if any cell type is missing for a motif
    matrix = matrix.fillna(np.nan)
    
    logger.info(f"Loaded matrix shape: {matrix.shape}")
    return matrix

def calculate_euclidean_distance_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Euclidean distance between rows (motifs) in the matrix.
    
    Args:
        matrix: DataFrame with q-values (rows=motifs, cols=cell_types)
        
    Returns:
        Distance matrix (pandas DataFrame)
    """
    logger.info("Calculating Euclidean distance matrix for clustering")
    
    # Convert to numpy for scipy
    data = matrix.values
    
    # Calculate pairwise distances
    dists = pdist(data, metric='euclidean')
    
    # Convert back to square form
    dist_matrix = pd.DataFrame(
        squareform(dists),
        index=matrix.index,
        columns=matrix.index
    )
    
    return dist_matrix

def cluster_matrix(
    matrix: pd.DataFrame, 
    method: str = 'average'
) -> tuple:
    """
    Perform hierarchical clustering on the motif matrix.
    
    Args:
        matrix: DataFrame with q-values
        method: Linkage method ('average', 'complete', 'ward', etc.)
        
    Returns:
        Tuple of (ordered_row_indices, linkage_matrix)
    """
    logger.info(f"Performing hierarchical clustering with method: {method}")
    
    # Use only numeric columns
    numeric_matrix = matrix.select_dtypes(include=[np.number])
    
    # Linkage matrix
    linkage_matrix = linkage(
        pdist(numeric_matrix.values, metric='euclidean'), 
        method=method
    )
    
    # Get optimal leaf order
    ordered_indices = leaves_list(linkage_matrix)
    
    return ordered_indices, linkage_matrix

def generate_heatmap(
    matrix: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: str = "TF Motif Enrichment q-values"
) -> Path:
    """
    Generate a heatmap of q-values with Euclidean distance clustering.
    
    Args:
        matrix: DataFrame with q-values (rows=motifs, cols=cell_types)
        output_path: Path to save the heatmap. Defaults to data/processed/heatmap.png
        title: Plot title
        
    Returns:
        Path to the generated heatmap file
    """
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "heatmap.png"
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating heatmap with clustering. Output: {output_path}")
    
    # Handle missing values for plotting
    plot_matrix = matrix.copy()
    # Replace NaN with a sentinel value for plotting, or drop rows/cols with too many NaNs
    # For heatmap, we'll fill NaN with 1.0 (no enrichment) as a conservative estimate
    # or use the median of available values
    if plot_matrix.isnull().any().any():
        logger.warning("Matrix contains NaN values. Filling with 1.0 (no enrichment).")
        plot_matrix = plot_matrix.fillna(1.0)
    
    # Perform clustering
    ordered_indices, _ = cluster_matrix(plot_matrix)
    
    # Reorder matrix for plotting
    ordered_matrix = plot_matrix.iloc[ordered_indices]
    
    # Set up the figure
    plt.figure(figsize=(12, max(10, len(ordered_matrix) * 0.3)))
    
    # Create heatmap
    sns.heatmap(
        ordered_matrix,
        cmap='RdYlBu_r',  # Red-Yellow-Blue reversed (blue=low q-value=significant)
        vmin=0,
        vmax=1,
        cbar_kws={'label': 'Adjusted q-value'},
        linewidths=0.5,
        linecolor='gray',
        annot=False,
        fmt=".2f"
    )
    
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel("Cell Type", fontsize=12)
    plt.ylabel("Motif ID", fontsize=12)
    
    # Rotate x-axis labels if needed
    plt.xticks(rotation=45, ha='right')
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Heatmap successfully saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for generating the enrichment heatmap.
    """
    try:
        # Load data
        matrix = load_enrichment_matrix()
        
        # Generate heatmap
        output_path = generate_heatmap(matrix)
        
        print(f"SUCCESS: Heatmap generated at {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}", exc_info=True)
        print(f"ERROR: Visualization failed - {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
