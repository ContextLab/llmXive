import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.manifold import TSNE
import umap
from sklearn.decomposition import PCA

from config import Config
from utils import time_wrapper, ResourceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingError(Exception):
    """Custom exception for embedding generation failures."""
    pass

def generate_pca(
    data: np.ndarray,
    n_components: int = 50,
    random_state: int = 42
) -> np.ndarray:
    """
    Generate PCA embedding.

    Args:
        data: Input data matrix (n_samples, n_features)
        n_components: Number of principal components
        random_state: Random seed for reproducibility

    Returns:
        PCA transformed data
    """
    logger.info(f"Generating PCA with {n_components} components...")
    pca = PCA(n_components=n_components, random_state=random_state)
    embedding = pca.fit_transform(data)
    logger.info(f"PCA explained variance ratio sum: {sum(pca.explained_variance_ratio_):.4f}")
    return embedding

def generate_tsne(
    data: np.ndarray,
    perplexity: int = 30,
    n_iter: int = 1000,
    random_state: int = 42,
    n_jobs: int = 1
) -> np.ndarray:
    """
    Generate t-SNE embedding.

    Args:
        data: Input data matrix (n_samples, n_features)
        perplexity: Perplexity parameter for t-SNE
        n_iter: Number of iterations
        random_state: Random seed
        n_jobs: Number of parallel jobs (set to 1 for CPU-only)

    Returns:
        t-SNE transformed data
    """
    logger.info(f"Generating t-SNE (perplexity={perplexity}, n_iter={n_iter})...")
    
    # Resource check before starting heavy computation
    monitor = ResourceMonitor()
    monitor.start()
    
    try:
        tsne = TSNE(
            n_components=2,
            perplexity=perplexity,
            n_iter=n_iter,
            random_state=random_state,
            n_jobs=n_jobs,
            method='barnes_hut'  # Use Barnes-Hut for CPU efficiency
        )
        embedding = tsne.fit_transform(data)
        
        monitor.stop()
        logger.info(f"t-SNE completed. Peak RAM: {monitor.get_peak_ram_mb():.2f} MB")
        return embedding
    except MemoryError:
        logger.error("Memory error during t-SNE computation")
        raise EmbeddingError("t-SNE computation failed due to insufficient memory")
    finally:
        monitor.stop()

def generate_umap(
    data: np.ndarray,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    random_state: int = 42,
    n_jobs: int = 1
) -> np.ndarray:
    """
    Generate UMAP embedding.

    Args:
        data: Input data matrix (n_samples, n_features)
        n_neighbors: Number of neighbors for UMAP
        min_dist: Minimum distance between points
        random_state: Random seed
        n_jobs: Number of parallel jobs (set to 1 for CPU-only)

    Returns:
        UMAP transformed data
    """
    logger.info(f"Generating UMAP (n_neighbors={n_neighbors}, min_dist={min_dist})...")
    
    # Resource check before starting heavy computation
    monitor = ResourceMonitor()
    monitor.start()
    
    try:
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=2,
            random_state=random_state,
            n_jobs=n_jobs
        )
        embedding = reducer.fit_transform(data)
        
        monitor.stop()
        logger.info(f"UMAP completed. Peak RAM: {monitor.get_peak_ram_mb():.2f} MB")
        return embedding
    except MemoryError:
        logger.error("Memory error during UMAP computation")
        raise EmbeddingError("UMAP computation failed due to insufficient memory")
    finally:
        monitor.stop()

def run_embeddings(
    data: np.ndarray,
    output_dir: str,
    n_components_pca: int = 50,
    tsne_perplexity: int = 30,
    tsne_n_iter: int = 1000,
    umap_n_neighbors: int = 15,
    umap_min_dist: float = 0.1,
    random_state: int = 42,
    cell_labels: Optional[pd.Series] = None,
    accession: str = "unknown"
) -> Dict[str, str]:
    """
    Run all embeddings (PCA, t-SNE, UMAP) and save results.

    Args:
        data: Input data matrix (n_samples, n_features)
        output_dir: Directory to save embeddings
        n_components_pca: Number of PCA components
        tsne_perplexity: t-SNE perplexity
        tsne_n_iter: t-SNE iterations
        umap_n_neighbors: UMAP n_neighbors
        umap_min_dist: UMAP min_dist
        random_state: Random seed
        cell_labels: Optional cell labels for metadata
        accession: Dataset accession identifier

    Returns:
        Dictionary mapping embedding type to output file path
    """
    config = Config()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # 1. PCA
    try:
        pca_embedding = generate_pca(data, n_components=n_components_pca, random_state=random_state)
        pca_file = output_path / f"{accession}_pca.csv"
        pca_df = pd.DataFrame(pca_embedding, columns=[f"PC{i+1}" for i in range(pca_embedding.shape[1])])
        if cell_labels is not None:
            pca_df['cell_label'] = cell_labels.values
        pca_df.to_csv(pca_file, index=False)
        results['pca'] = str(pca_file)
        logger.info(f"PCA embedding saved to {pca_file}")
    except Exception as e:
        logger.error(f"PCA failed: {e}")
        raise EmbeddingError(f"PCA generation failed: {e}")
    
    # 2. t-SNE
    try:
        tsne_embedding = generate_tsne(
            data,
            perplexity=tsne_perplexity,
            n_iter=tsne_n_iter,
            random_state=random_state,
            n_jobs=1  # CPU-only as per spec
        )
        tsne_file = output_path / f"{accession}_tsne.csv"
        tsne_df = pd.DataFrame(tsne_embedding, columns=["tSNE1", "tSNE2"])
        if cell_labels is not None:
            tsne_df['cell_label'] = cell_labels.values
        tsne_df.to_csv(tsne_file, index=False)
        results['tsne'] = str(tsne_file)
        logger.info(f"t-SNE embedding saved to {tsne_file}")
    except EmbeddingError:
        logger.error("t-SNE failed due to resource constraints")
        raise
    except Exception as e:
        logger.error(f"t-SNE failed: {e}")
        raise EmbeddingError(f"t-SNE generation failed: {e}")
    
    # 3. UMAP
    try:
        umap_embedding = generate_umap(
            data,
            n_neighbors=umap_n_neighbors,
            min_dist=umap_min_dist,
            random_state=random_state,
            n_jobs=1  # CPU-only as per spec
        )
        umap_file = output_path / f"{accession}_umap.csv"
        umap_df = pd.DataFrame(umap_embedding, columns=["UMAP1", "UMAP2"])
        if cell_labels is not None:
            umap_df['cell_label'] = cell_labels.values
        umap_df.to_csv(umap_file, index=False)
        results['umap'] = str(umap_file)
        logger.info(f"UMAP embedding saved to {umap_file}")
    except EmbeddingError:
        logger.error("UMAP failed due to resource constraints")
        raise
    except Exception as e:
        logger.error(f"UMAP failed: {e}")
        raise EmbeddingError(f"UMAP generation failed: {e}")
    
    return results

def main():
    """
    Main entry point for embedding generation.
    Expects preprocessed data in data/processed/ directory.
    """
    config = Config()
    processed_dir = Path(config.PROCESSED_DATA_DIR)
    output_dir = Path(config.EMBEDDINGS_DIR)
    
    if not processed_dir.exists():
        logger.error(f"Processed data directory not found: {processed_dir}")
        sys.exit(1)
    
    # Find all processed count matrices
    count_files = list(processed_dir.glob("*_processed_counts.csv"))
    
    if not count_files:
        logger.warning("No processed count matrices found.")
        sys.exit(0)
    
    all_results = {}
    
    for count_file in count_files:
        accession = count_file.stem.replace("_processed_counts", "")
        logger.info(f"Processing embeddings for accession: {accession}")
        
        try:
            # Load data
            data_df = pd.read_csv(count_file, index_col=0)
            # Assume first column is cell labels if present, otherwise use index
            if 'cell_label' in data_df.columns:
                cell_labels = data_df['cell_label']
                data = data_df.drop(columns=['cell_label']).values
            else:
                cell_labels = None
                data = data_df.values
            
            # Run embeddings
            results = run_embeddings(
                data=data,
                output_dir=str(output_dir),
                n_components_pca=config.PCA_COMPONENTS,
                tsne_perplexity=config.TSNE_PERPLEXITY,
                tsne_n_iter=config.TSNE_N_ITER,
                umap_n_neighbors=config.UMAP_N_NEIGHBORS,
                umap_min_dist=config.UMAP_MIN_DIST,
                random_state=config.RANDOM_SEED,
                cell_labels=cell_labels,
                accession=accession
            )
            all_results[accession] = results
            logger.info(f"Successfully generated embeddings for {accession}")
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for {accession}: {e}")
            all_results[accession] = {"error": str(e)}
    
    # Save summary
    summary_file = output_dir / "embedding_summary.json"
    import json
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Embedding summary saved to {summary_file}")

if __name__ == "__main__":
    main()
