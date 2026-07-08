"""
code/geometry.py

Computes Global Linearity (Trustworthiness) and Local Continuity (LCA) metrics
on the high-dimensional space versus the embedding space.

This module implements the geometric diagnostics required for User Story 2.
It relies on the preprocessed high-dimensional data (raw counts or HVG-selected)
and the generated embeddings (PCA, t-SNE, UMAP).

Dependencies:
  - sklearn: for manifold metrics (Trustworthiness, Continuity)
  - numpy: for numerical operations
  - config: for project paths
  - preprocess: for loading preprocessed data
  - embeddings: for loading generated embeddings
"""

import os
import sys
import logging
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
from sklearn.manifold import trustworthiness
from sklearn.metrics import pairwise_distances

# Import from project API surface
from config import Config
from preprocess import deterministic_sample_cells
from embeddings import run_embeddings  # We might need to re-run or load, but usually we load results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GeometryError(Exception):
    """Custom exception for geometry computation errors."""
    pass


def _compute_seed(accession: str) -> int:
    """
    Generates a deterministic random seed from an accession string.
    Used for reproducible sampling if cell count exceeds limits.
    """
    return int(hashlib.md5(accession.encode()).hexdigest(), 16) % (2**32)


def _load_high_dim_data(accession: str, config: Config) -> Tuple[np.ndarray, str]:
    """
    Loads the high-dimensional data (raw counts or HVGs) for a given accession.
    If the dataset is too large (>10,000 cells), it performs deterministic sampling.

    Returns:
        Tuple of (data_matrix, processed_accession_id)
    """
    # The preprocessed data is typically stored in data/processed/<accession>_preprocessed.h5ad or similar
    # Based on T006/T013, the output of preprocess is expected here.
    # We assume the standard output name from preprocess.py if not specified otherwise.
    # Let's assume the file is named <accession>_preprocessed.h5ad based on common patterns
    # or we look for the specific output defined in preprocess.
    
    # Check for the existence of the preprocessed file
    # Assuming the preprocess task outputs to: data/processed/{accession}_preprocessed.h5ad
    # If the actual filename differs, this logic might need adjustment based on T006/T013 implementation details.
    # For now, we construct the path based on standard conventions in the project.
    
    processed_path = config.PROCESSED_DIR / f"{accession}_preprocessed.h5ad"
    
    if not processed_path.exists():
        # Fallback: check if raw data exists and needs preprocessing, but T007 depends on T006/T008
        # So we assume preprocessed data is available.
        raise FileNotFoundError(f"Preprocessed data not found for {accession} at {processed_path}. "
                                "Ensure T006 (preprocess) has run successfully.")

    try:
        import scanpy as sc
        adata = sc.read_h5ad(processed_path)
        
        # Extract the data matrix (X)
        # If X is sparse, convert to dense for sklearn metrics (or use sparse-compatible versions if available)
        # Trustworthiness in sklearn does not support sparse matrices directly in older versions, 
        # but newer ones might. To be safe and robust, we convert to dense if memory allows.
        # Given the sampling constraint (10k cells), dense should be fine.
        
        if hasattr(adata.X, 'toarray'):
            X = adata.X.toarray()
        else:
            X = np.array(adata.X)
        
        logger.info(f"Loaded data for {accession}: shape {X.shape}")
        
        # Apply deterministic sampling if n_cells > 10,000
        n_cells = X.shape[0]
        if n_cells > 10000:
            seed = _compute_seed(accession)
            logger.info(f"Sampling {n_cells} cells to 10,000 for {accession} (seed={seed})")
            X, _ = deterministic_sample_cells(X, max_cells=10000, random_state=seed)
            logger.info(f"Sampled data shape: {X.shape}")
        
        return X, accession
        
    except Exception as e:
        logger.error(f"Error loading data for {accession}: {e}")
        raise GeometryError(f"Failed to load high-dimensional data for {accession}: {e}")


def _load_embedding(accession: str, method: str, config: Config) -> np.ndarray:
    """
    Loads a specific embedding (PCA, t-SNE, UMAP) for a given accession.
    """
    # Assuming embeddings are saved as <accession>_<method>_embedding.csv or .h5ad
    # Based on T008a/T008b, outputs are likely in data/processed/ or a specific embeddings dir.
    # Let's assume the standard output path from embeddings.py: data/processed/{accession}_{method}_embedding.csv
    # or .npy. We'll try .npy first as it's common for numpy arrays, then .csv.
    
    embedding_path = config.PROCESSED_DIR / f"{accession}_{method}_embedding.npy"
    
    if not embedding_path.exists():
        # Try .csv fallback
        embedding_path = config.PROCESSED_DIR / f"{accession}_{method}_embedding.csv"
    
    if not embedding_path.exists():
        raise FileNotFoundError(f"Embedding for {accession} ({method}) not found at {embedding_path}. "
                                "Ensure T008a/T008b (embeddings) has run successfully.")

    try:
        if embedding_path.suffix == '.npy':
            Z = np.load(embedding_path)
        elif embedding_path.suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(embedding_path)
            # Assume first N columns are coordinates
            Z = df.values[:, :2] # Usually 2D for t-SNE/UMAP, PCA might be more
            # If PCA has more dims, we might need to adjust, but Trustworthiness works on any dim
            # Let's take all numeric columns if it's a generic embedding
            if Z.shape[1] == 0:
                Z = df.select_dtypes(include=[np.number]).values
        else:
            raise ValueError(f"Unsupported embedding file format: {embedding_path.suffix}")
        
        logger.info(f"Loaded embedding {method} for {accession}: shape {Z.shape}")
        return Z
        
    except Exception as e:
        logger.error(f"Error loading embedding {method} for {accession}: {e}")
        raise GeometryError(f"Failed to load embedding {method} for {accession}: {e}")


def compute_linearity_metric(X: np.ndarray, Z: np.ndarray, k: int = 15) -> float:
    """
    Computes the Global Linearity metric (Trustworthiness).
    
    Trustworthiness measures how well the local neighborhood structure
    in the high-dimensional space is preserved in the embedding space.
    It penalizes points that are close in the embedding but far in the original space.
    
    Args:
        X: High-dimensional data matrix (n_samples, n_features)
        Z: Embedding matrix (n_samples, n_components)
        k: Number of neighbors (default 15)
        
    Returns:
        Trustworthiness score (0 to 1, higher is better)
    """
    if X.shape[0] != Z.shape[0]:
        raise ValueError("High-dimensional data and embedding must have the same number of samples.")
    
    if k >= X.shape[0]:
        logger.warning(f"k={k} is greater than or equal to sample size {X.shape[0]}. Setting k={X.shape[0]-1}")
        k = max(1, X.shape[0] - 1)
        
    try:
        score = trustworthiness(X, Z, n_neighbors=k)
        return score
    except Exception as e:
        logger.error(f"Error computing trustworthiness: {e}")
        raise GeometryError(f"Trustworthiness computation failed: {e}")


def compute_continuity_metric(X: np.ndarray, Z: np.ndarray, k: int = 15) -> float:
    """
    Computes the Local Continuity metric (Continuity).
    
    Continuity measures how well the local neighborhood structure
    in the embedding space is preserved from the high-dimensional space.
    It penalizes points that are close in the original space but far in the embedding.
    
    Args:
        X: High-dimensional data matrix (n_samples, n_features)
        Z: Embedding matrix (n_samples, n_components)
        k: Number of neighbors (default 15)
        
    Returns:
        Continuity score (0 to 1, higher is better)
    """
    if X.shape[0] != Z.shape[0]:
        raise ValueError("High-dimensional data and embedding must have the same number of samples.")
        
    if k >= X.shape[0]:
        logger.warning(f"k={k} is greater than or equal to sample size {X.shape[0]}. Setting k={X.shape[0]-1}")
        k = max(1, X.shape[0] - 1)

    try:
        # sklearn's trustworthiness is for one direction.
        # Continuity is often defined symmetrically or by swapping X and Z in the trustworthiness formula
        # Specifically: Continuity(X, Z) = Trustworthiness(Z, X)
        score = trustworthiness(Z, X, n_neighbors=k)
        return score
    except Exception as e:
        logger.error(f"Error computing continuity: {e}")
        raise GeometryError(f"Continuity computation failed: {e}")


def compute_geometry_metrics(accession: str, methods: List[str], k: int = 15, config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Computes Global Linearity (Trustworthiness) and Local Continuity (LCA) for a dataset.
    
    Args:
        accession: The GEO accession ID (e.g., GSE131907)
        methods: List of embedding methods to evaluate (e.g., ['pca', 'tsne', 'umap'])
        k: Number of neighbors for the metrics
        config: Config instance. If None, uses default Config.
        
    Returns:
        Dictionary containing the computed metrics.
    """
    if config is None:
        config = Config()
        
    results = {
        "accession": accession,
        "k": k,
        "metrics": {}
    }
    
    try:
        # Load high-dimensional data (with sampling if needed)
        X, _ = _load_high_dim_data(accession, config)
        
        for method in methods:
            logger.info(f"Computing geometry metrics for {accession} using {method}...")
            
            # Load embedding
            Z = _load_embedding(accession, method, config)
            
            # Compute metrics
            trust_score = compute_linearity_metric(X, Z, k)
            continuity_score = compute_continuity_metric(X, Z, k)
            
            results["metrics"][method] = {
                "trustworthiness": float(trust_score),
                "continuity": float(continuity_score)
            }
            
            logger.info(f"  Trustworthiness: {trust_score:.4f}, Continuity: {continuity_score:.4f}")
            
    except Exception as e:
        logger.error(f"Failed to compute geometry metrics for {accession}: {e}")
        results["error"] = str(e)
        
    return results


def run_geometry_analysis(accessions: Optional[List[str]] = None, config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Runs the geometry analysis for all configured accessions.
    
    Args:
        accessions: List of accessions to process. If None, uses Config.GSE_ACCESSIONS.
        config: Config instance.
        
    Returns:
        Aggregated results dictionary.
    """
    if config is None:
        config = Config()
        
    if accessions is None:
        accessions = config.GSE_ACCESSIONS
        
    all_results = {
        "config": {
            "k": 15,
            "accessions": accessions
        },
        "datasets": {}
    }
    
    methods = ["pca", "tsne", "umap"]
    
    for accession in accessions:
        logger.info(f"Processing geometry for {accession}...")
        dataset_results = compute_geometry_metrics(accession, methods, k=15, config=config)
        all_results["datasets"][accession] = dataset_results
        
    return all_results


def save_geometry_results(results: Dict[str, Any], output_path: Optional[Path] = None, config: Optional[Config] = None) -> Path:
    """
    Saves the geometry results to a JSON file.
    
    Args:
        results: The results dictionary from run_geometry_analysis.
        output_path: Optional specific output path.
        config: Config instance to derive default path if output_path is None.
        
    Returns:
        The path where the file was saved.
    """
    if config is None:
        config = Config()
        
    if output_path is None:
        output_path = config.RESULTS_DIR / "geometry_metrics.json"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Geometry results saved to {output_path}")
    return output_path


def main():
    """
    Main entry point for the geometry analysis script.
    """
    logger.info("Starting Geometry Analysis (T007)...")
    
    try:
        config = Config()
        
        # Run analysis
        results = run_geometry_analysis(config=config)
        
        # Save results
        output_file = save_geometry_results(results, config=config)
        
        logger.info(f"Geometry Analysis completed successfully. Results: {output_file}")
        
        # Print summary to stdout for quick verification
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Geometry Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
