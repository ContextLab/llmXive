"""
Dimensionality reduction module for molecular descriptor analysis.

Implements UMAP dimensionality reduction to project high-dimensional
molecular descriptor space into a 2D embedding for visualization and
cluster analysis.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

try:
    import umap
except ImportError:
    raise ImportError(
        "umap-learn is required. Install with: pip install umap-learn"
    )

from src.config import (
    get_project_root,
    get_data_processed_path,
    load_config,
    set_seeds
)

logger = logging.getLogger(__name__)

# Default UMAP parameters as specified in the plan
DEFAULT_N_NEIGHBORS = 15
DEFAULT_MIN_DIST = 0.1
DEFAULT_N_COMPONENTS = 2
DEFAULT_METRIC = 'euclidean'

def load_descriptors(
    input_path: Optional[Path] = None,
    config: Optional[dict] = None
) -> pd.DataFrame:
    """
    Load the processed descriptor matrix from CSV.
    
    Args:
        input_path: Optional path to the descriptor CSV. If None, uses
                   the default path from config.
        config: Optional configuration dictionary. If None, loads from config.py.
    
    Returns:
        DataFrame containing molecular descriptors with InChIKey as index.
    
    Raises:
        FileNotFoundError: If the descriptor file does not exist.
        ValueError: If the file is empty or lacks required columns.
    """
    if config is None:
        config = load_config()
    
    if input_path is None:
        input_path = get_data_processed_path() / "descriptors.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Descriptor file not found at {input_path}. "
            "Please run US1 data processing first."
        )
    
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError(f"Descriptor file at {input_path} is empty.")
    
    # Ensure InChIKey is the index or a column we can use for merging later
    if 'InChIKey' in df.columns:
        df = df.set_index('InChIKey')
    
    # Filter to numeric columns only for dimensionality reduction
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        raise ValueError(
            f"No numeric descriptor columns found in {input_path}. "
            "Expected columns like 'MolWt', 'LogP', etc."
        )
    
    logger.info(f"Loaded {numeric_df.shape[0]} compounds with {numeric_df.shape[1]} descriptors.")
    return numeric_df

def apply_umap(
    data: pd.DataFrame,
    n_neighbors: int = DEFAULT_N_NEIGHBORS,
    min_dist: float = DEFAULT_MIN_DIST,
    n_components: int = DEFAULT_N_COMPONENTS,
    metric: str = DEFAULT_METRIC,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Apply UMAP dimensionality reduction to the descriptor matrix.
    
    Args:
        data: DataFrame of numeric descriptors (rows=compounds, cols=descriptors).
        n_neighbors: Number of neighbors for UMAP (default 15).
        min_dist: Minimum distance between embedded points (default 0.1).
        n_components: Target dimensionality (default 2).
        metric: Distance metric for UMAP (default 'euclidean').
        random_state: Random seed for reproducibility.
    
    Returns:
        2D numpy array of shape (n_samples, n_components) containing the embedding.
    """
    # Fill NaN values with column median if any exist (UMAP doesn't handle NaN)
    data_filled = data.fillna(data.median())
    
    # Handle constant columns (zero variance) which can cause UMAP to fail
    variance = data_filled.var(axis=0)
    if (variance == 0).any():
        logger.warning(
            f"Removing {sum(variance == 0)} constant descriptor columns "
            "before UMAP to prevent errors."
        )
        data_filled = data_filled.loc[:, variance > 0]
    
    if data_filled.shape[1] == 0:
        raise ValueError(
            "No variable descriptor columns remaining after filtering. "
            "Cannot perform dimensionality reduction."
        )
    
    logger.info(
        f"Applying UMAP with n_neighbors={n_neighbors}, min_dist={min_dist}, "
        f"n_components={n_components}, metric='{metric}'."
    )
    
    # Initialize UMAP
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=n_components,
        metric=metric,
        random_state=random_state
    )
    
    # Fit and transform
    embedding = reducer.fit_transform(data_filled.values)
    
    logger.info(f"UMAP embedding computed: {embedding.shape}")
    return embedding

def save_umap_embedding(
    embedding: np.ndarray,
    index: pd.Index,
    output_path: Optional[Path] = None,
    config: Optional[dict] = None
) -> Path:
    """
    Save the UMAP embedding to a CSV file.
    
    Args:
        embedding: 2D numpy array of the embedding coordinates.
        index: The original index (InChIKeys) to associate with rows.
        output_path: Optional path for output. If None, uses default.
        config: Optional configuration dictionary.
    
    Returns:
        Path to the saved CSV file.
    """
    if config is None:
        config = load_config()
    
    if output_path is None:
        output_path = get_data_processed_path() / "umap_embedding.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create DataFrame with embedding columns
    df = pd.DataFrame(
        embedding,
        index=index,
        columns=[f'UMAP_{i+1}' for i in range(embedding.shape[1])]
    )
    
    df.to_csv(output_path)
    logger.info(f"UMAP embedding saved to {output_path}")
    return output_path

def run_umap_pipeline(
    input_descriptors: Optional[Path] = None,
    output_embedding: Optional[Path] = None,
    n_neighbors: int = DEFAULT_N_NEIGHBORS,
    min_dist: float = DEFAULT_MIN_DIST,
    random_state: Optional[int] = None
) -> Path:
    """
    End-to-end pipeline: Load descriptors -> Apply UMAP -> Save embedding.
    
    Args:
        input_descriptors: Path to input descriptors CSV.
        output_embedding: Path for output embedding CSV.
        n_neighbors: UMAP n_neighbors parameter.
        min_dist: UMAP min_dist parameter.
        random_state: Random seed for reproducibility.
    
    Returns:
        Path to the generated embedding file.
    """
    # Set seeds if provided
    if random_state is not None:
        set_seeds(random_state)
    
    # Load data
    descriptors = load_descriptors(input_descriptors)
    
    # Apply UMAP
    embedding = apply_umap(
        descriptors,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state
    )
    
    # Save result
    return save_umap_embedding(
        embedding,
        descriptors.index,
        output_embedding
    )

def main():
    """
    Main entry point for running the UMAP dimensionality reduction.
    
    Reads from data/processed/descriptors.csv (generated by US1)
    and writes to data/processed/umap_embedding.csv.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = load_config()
    random_state = config.get('RANDOM_SEED', 42)
    
    logger.info("Starting UMAP dimensionality reduction pipeline.")
    
    try:
        output_path = run_umap_pipeline(
            n_neighbors=DEFAULT_N_NEIGHBORS,
            min_dist=DEFAULT_MIN_DIST,
            random_state=random_state
        )
        logger.info(f"Pipeline complete. Output: {output_path}")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()
