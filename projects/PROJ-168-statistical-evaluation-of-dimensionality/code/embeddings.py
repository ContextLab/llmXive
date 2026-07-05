import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap
from umap import UMAP as UMAPModel

from config import get_accession_seed, ensure_paths, set_global_seed
from utils import check_resource_abort, time_wrapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_pca(data: np.ndarray, n_components: int = 50, random_state: Optional[int] = None) -> np.ndarray:
    """
    Generate PCA embeddings.
    
    Args:
        data: Input data matrix (n_samples, n_features).
        n_components: Number of principal components.
        random_state: Random seed for reproducibility.
        
    Returns:
        PCA transformed data.
    """
    logger.info(f"Generating PCA with {n_components} components...")
    pca = PCA(n_components=n_components, random_state=random_state)
    embeddings = pca.fit_transform(data)
    logger.info(f"PCA explained variance ratio sum: {np.sum(pca.explained_variance_ratio_):.4f}")
    return embeddings

def generate_tsne(data: np.ndarray, perplexity: int = 30, n_iter: int = 1000, 
                  random_state: Optional[int] = None, n_jobs: int = 1) -> np.ndarray:
    """
    Generate t-SNE embeddings.
    
    Args:
        data: Input data matrix (n_samples, n_features).
        perplexity: t-SNE perplexity parameter.
        n_iter: Number of iterations.
        random_state: Random seed for reproducibility.
        n_jobs: Number of parallel jobs (set to 1 for CPU-only).
        
    Returns:
        t-SNE transformed data.
    """
    logger.info(f"Generating t-SNE (perplexity={perplexity}, n_iter={n_iter})...")
    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        n_iter=n_iter,
        random_state=random_state,
        n_jobs=n_jobs,
        method='barnes_hut',
        learning_rate='auto'
    )
    embeddings = tsne.fit_transform(data)
    return embeddings

def generate_umap(data: np.ndarray, n_neighbors: int = 15, min_dist: float = 0.1,
                  random_state: Optional[int] = None, n_jobs: int = 1) -> np.ndarray:
    """
    Generate UMAP embeddings.
    
    Args:
        data: Input data matrix (n_samples, n_features).
        n_neighbors: UMAP n_neighbors parameter.
        min_dist: UMAP min_dist parameter.
        random_state: Random seed for reproducibility.
        n_jobs: Number of parallel jobs.
        
    Returns:
        UMAP transformed data.
    """
    logger.info(f"Generating UMAP (n_neighbors={n_neighbors}, min_dist={min_dist})...")
    # UMAP random_state handling
    umap_model = UMAPModel(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=2,
        random_state=random_state,
        n_jobs=n_jobs,
        metric='euclidean'
    )
    embeddings = umap_model.fit_transform(data)
    return embeddings

def run_embedding_pipeline(data: np.ndarray, accession: str, 
                           output_dir: Path, pca_components: int = 50) -> Dict[str, str]:
    """
    Run the full embedding pipeline: PCA, t-SNE, and UMAP.
    
    Args:
        data: Preprocessed data matrix (n_samples, n_features).
        accession: Dataset accession ID for seeding and naming.
        output_dir: Directory to save output files.
        pca_components: Number of PCA components.
        
    Returns:
        Dictionary mapping method names to output file paths.
    """
    ensure_paths()
    seed = get_accession_seed(accession)
    set_global_seed(seed)
    
    output_files = {}
    
    # 1. PCA
    logger.info(f"Starting PCA for {accession}...")
    pca_data = generate_pca(data, n_components=pca_components, random_state=seed)
    pca_path = output_dir / f"{accession}_pca.csv"
    pd.DataFrame(pca_data).to_csv(pca_path, index=False)
    output_files['pca'] = str(pca_path)
    logger.info(f"PCA saved to {pca_path}")
    
    # 2. t-SNE
    logger.info(f"Starting t-SNE for {accession}...")
    # Resource check before heavy computation
    check_resource_abort("t-SNE")
    tsne_data = generate_tsne(data, perplexity=30, n_iter=1000, random_state=seed, n_jobs=1)
    tsne_path = output_dir / f"{accession}_tsne.csv"
    pd.DataFrame(tsne_data).to_csv(tsne_path, index=False)
    output_files['tsne'] = str(tsne_path)
    logger.info(f"t-SNE saved to {tsne_path}")
    
    # 3. UMAP
    logger.info(f"Starting UMAP for {accession}...")
    # Resource check before heavy computation
    check_resource_abort("UMAP")
    umap_data = generate_umap(data, n_neighbors=15, min_dist=0.1, random_state=seed, n_jobs=1)
    umap_path = output_dir / f"{accession}_umap.csv"
    pd.DataFrame(umap_data).to_csv(umap_path, index=False)
    output_files['umap'] = str(umap_path)
    logger.info(f"UMAP saved to {umap_path}")
    
    return output_files

def main():
    """
    Entry point for running embeddings on a specific accession.
    Expects environment variables or command line args to specify accession and data path.
    """
    if len(sys.argv) < 3:
        logger.error("Usage: python embeddings.py <accession> <input_csv_path>")
        sys.exit(1)
        
    accession = sys.argv[1]
    input_path = Path(sys.argv[2])
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    logger.info(f"Loading data from {input_path} for {accession}...")
    df = pd.read_csv(input_path)
    # Assume first column is index/cell ID, rest are features
    if df.columns[0] == 'cell_id' or df.columns[0] == 'index':
        data = df.iloc[:, 1:].values
    else:
        data = df.values
        
    output_dir = Path(f"data/processed/{accession}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Running embedding pipeline for {accession}...")
    start_time = time.time()
    
    try:
        results = run_embedding_pipeline(data, accession, output_dir)
        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")
        logger.info(f"Output files: {results}")
    except Exception as e:
        logger.error(f"Pipeline failed for {accession}: {e}")
        raise

if __name__ == "__main__":
    main()