"""
Dimensionality reduction module for UMAP embedding of molecular descriptors.

This module implements the application of UMAP to reduce high-dimensional
molecular descriptor data to a 2D embedding for visualization and clustering.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from umap import UMAP
from src.config import get_project_root, get_data_processed_path, load_config

logger = logging.getLogger(__name__)


def load_descriptors() -> Tuple[pd.DataFrame, pd.Index]:
    """
    Load the processed descriptor matrix from disk.

    Returns:
        Tuple of (descriptor DataFrame, InChIKey index)
        
    Raises:
        FileNotFoundError: If the descriptor file does not exist
        ValueError: If the file is empty or has invalid structure
    """
    project_root = get_project_root()
    descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
    
    if not descriptors_path.exists():
        raise FileNotFoundError(
            f"Descriptor file not found at {descriptors_path}. "
            "Run the data processing pipeline (US1) first."
        )
    
    df = pd.read_csv(descriptors_path)
    
    if df.empty:
        raise ValueError("Descriptor DataFrame is empty. Check data processing pipeline.")
    
    if "InChIKey" not in df.columns:
        raise ValueError(
            "Descriptor DataFrame missing 'InChIKey' column. "
            "Expected columns: InChIKey + descriptor columns."
        )
    
    # Set InChIKey as index for embedding
    df = df.set_index("InChIKey")
    
    # Select only numeric descriptor columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    descriptor_matrix = df[numeric_cols]
    
    logger.info(f"Loaded {len(descriptor_matrix)} compounds with {len(numeric_cols)} descriptors")
    
    return descriptor_matrix, df.index


def apply_umap(
    descriptor_matrix: pd.DataFrame,
    n_components: int = 2,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    metric: str = "euclidean",
    random_state: int = 42
) -> np.ndarray:
    """
    Apply UMAP dimensionality reduction to the descriptor matrix.
    
    Args:
        descriptor_matrix: DataFrame with compounds as rows and descriptors as columns
        n_components: Number of dimensions in the embedding (default: 2)
        n_neighbors: Number of neighbors for UMAP (default: 15)
        min_dist: Minimum distance between embedded points (default: 0.1)
        metric: Distance metric to use (default: 'euclidean')
        random_state: Random seed for reproducibility (default: 42)
        
    Returns:
        2D numpy array of shape (n_samples, n_components) containing the embedding
        
    Raises:
        ValueError: If input matrix is empty or has fewer than 2 samples
    """
    if descriptor_matrix.empty:
        raise ValueError("Cannot apply UMAP to empty descriptor matrix")
    
    if len(descriptor_matrix) < 2:
        raise ValueError(
            f"Need at least 2 samples for UMAP, got {len(descriptor_matrix)}"
        )
    
    logger.info(
        f"Applying UMAP with n_neighbors={n_neighbors}, "
        f"min_dist={min_dist}, metric={metric}"
    )
    
    # Initialize and fit UMAP
    umap_model = UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=random_state,
        verbose=True
    )
    
    # Transform the data
    embedding = umap_model.fit_transform(descriptor_matrix.values)
    
    logger.info(f"UMAP embedding completed. Shape: {embedding.shape}")
    
    return embedding


def save_umap_embedding(
    embedding: np.ndarray,
    indices: pd.Index,
    output_filename: str = "umap_embedding.csv"
) -> Path:
    """
    Save the UMAP embedding to a CSV file.
    
    Args:
        embedding: 2D numpy array of UMAP coordinates
        indices: InChIKey index corresponding to the embedding rows
        output_filename: Name of the output file (default: 'umap_embedding.csv')
        
    Returns:
        Path to the saved file
        
    Raises:
        ValueError: If embedding and indices have mismatched lengths
    """
    if len(embedding) != len(indices):
        raise ValueError(
            f"Embedding length ({len(embedding)}) does not match "
            f"indices length ({len(indices)})"
        )
    
    processed_path = get_data_processed_path()
    output_path = processed_path / output_filename
    
    # Create DataFrame with embedding coordinates
    if embedding.shape[1] == 2:
        embedding_df = pd.DataFrame(
            embedding,
            columns=["UMAP1", "UMAP2"],
            index=indices
        )
    else:
        col_names = [f"UMAP{i+1}" for i in range(embedding.shape[1])]
        embedding_df = pd.DataFrame(embedding, columns=col_names, index=indices)
    
    # Save to CSV
    embedding_df.to_csv(output_path)
    
    logger.info(f"Saved UMAP embedding to {output_path}")
    
    return output_path


def run_umap_pipeline() -> Path:
    """
    Run the complete UMAP pipeline: load descriptors, apply UMAP, save embedding.
    
    Returns:
        Path to the saved embedding file
        
    Raises:
        FileNotFoundError: If input data files are missing
        RuntimeError: If any step in the pipeline fails
    """
    logger.info("Starting UMAP pipeline")
    
    try:
        # Load descriptors
        descriptor_matrix, indices = load_descriptors()
        
        # Apply UMAP
        embedding = apply_umap(descriptor_matrix)
        
        # Save embedding
        output_path = save_umap_embedding(embedding, indices)
        
        logger.info("UMAP pipeline completed successfully")
        
        return output_path
        
    except FileNotFoundError as e:
        logger.error(f"Missing input data: {e}")
        raise
    except Exception as e:
        logger.error(f"UMAP pipeline failed: {e}")
        raise RuntimeError(f"UMAP pipeline failed: {e}") from e


def main():
    """Main entry point for the UMAP dimensionality reduction script."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        output_path = run_umap_pipeline()
        print(f"UMAP embedding saved to: {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())