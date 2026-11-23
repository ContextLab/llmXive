import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import scanpy as sc
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.preprocessing import LabelEncoder
from leidenalg import VertexPartition, find_partition
import igraph as ig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/clustering.log')
    ]
)
logger = logging.getLogger(__name__)

class ClusteringError(Exception):
    """Custom exception for clustering operations."""
    pass

def load_preprocessed_data(file_path: str) -> sc.AnnData:
    """
    Load preprocessed AnnData object from file.

    Args:
        file_path: Path to the .h5ad file

    Returns:
        AnnData object

    Raises:
        ClusteringError: If file cannot be loaded
    """
    try:
        logger.info(f"Loading preprocessed data from {file_path}")
        adata = sc.read_h5ad(file_path)
        logger.info(f"Loaded data with shape: {adata.shape}")
        return adata
    except Exception as e:
        raise ClusteringError(f"Failed to load preprocessed data: {e}")

def run_leiden_clustering(
    adata: sc.AnnData,
    resolution: float = 0.5,
    random_state: int = 42,
    n_neighbors: int = 15
) -> np.ndarray:
    """
    Run Leiden clustering on the AnnData object.

    Args:
        adata: AnnData object with PCA embeddings
        resolution: Leiden resolution parameter
        random_state: Random seed for reproducibility
        n_neighbors: Number of neighbors for graph construction

    Returns:
        Array of cluster labels

    Raises:
        ClusteringError: If clustering fails
    """
    try:
        logger.info(f"Running Leiden clustering with resolution={resolution}, n_neighbors={n_neighbors}")

        # Ensure PCA embeddings are available
        if 'X_pca' not in adata.obsm:
            raise ClusteringError("PCA embeddings not found in AnnData object. Run PCA first.")

        # Build KNN graph
        sc.pp.neighbors(adata, use_rep='X_pca', n_neighbors=n_neighbors, random_state=random_state)

        # Run Leiden clustering
        sc.tl.leiden(adata, resolution=resolution, random_state=random_state)

        # Extract cluster labels
        labels = np.array(adata.obs['leiden'], dtype=int)

        logger.info(f"Clustering complete. Found {len(np.unique(labels))} clusters.")
        return labels

    except Exception as e:
        raise ClusteringError(f"Leiden clustering failed: {e}")

def calculate_silhouette_score(
    adata: sc.AnnData,
    labels: np.ndarray,
    use_rep: str = 'X_pca'
) -> float:
    """
    Calculate silhouette score for clustering evaluation.

    Args:
        adata: AnnData object
        labels: Cluster labels
        use_rep: Representation to use for distance calculation

    Returns:
        Silhouette score
    """
    try:
        from sklearn.metrics import silhouette_score

        if use_rep not in adata.obsm:
            raise ClusteringError(f"Representation '{use_rep}' not found in AnnData object")

        embeddings = adata.obsm[use_rep]
        score = silhouette_score(embeddings, labels)
        logger.info(f"Silhouette score: {score:.4f}")
        return score

    except Exception as e:
        logger.error(f"Silhouette score calculation failed: {e}")
        raise ClusteringError(f"Silhouette score calculation failed: {e}")

def optimize_resolution(
    adata: sc.AnnData,
    resolution_range: List[float],
    random_state: int = 42,
    n_neighbors: int = 15
) -> Tuple[float, float]:
    """
    Find optimal Leiden resolution by maximizing silhouette score.

    Args:
        adata: AnnData object
        resolution_range: List of resolution values to test
        random_state: Random seed
        n_neighbors: Number of neighbors

    Returns:
        Tuple of (best_resolution, best_score)
    """
    best_resolution = None
    best_score = -np.inf

    logger.info(f"Optimizing resolution over {len(resolution_range)} values...")

    for res in resolution_range:
        try:
            labels = run_leiden_clustering(adata, resolution=res, random_state=random_state, n_neighbors=n_neighbors)
            score = calculate_silhouette_score(adata, labels)

            if score > best_score:
                best_score = score
                best_resolution = res

            logger.info(f"Resolution {res}: Silhouette score = {score:.4f}")

        except Exception as e:
            logger.warning(f"Failed to evaluate resolution {res}: {e}")

    if best_resolution is None:
        raise ClusteringError("Could not find a valid resolution")

    logger.info(f"Optimal resolution: {best_resolution} with score: {best_score:.4f}")
    return best_resolution, best_score

def calculate_fidelity_metrics(
    cluster_labels: np.ndarray,
    ground_truth_labels: np.ndarray
) -> Dict[str, float]:
    """
    Calculate clustering fidelity metrics (ARI and NMI).

    Args:
        cluster_labels: Predicted cluster labels
        ground_truth_labels: Ground truth labels

    Returns:
        Dictionary with ARI and NMI scores
    """
    try:
        # Ensure labels are properly encoded
        le = LabelEncoder()
        cluster_labels_encoded = le.fit_transform(cluster_labels)
        gt_labels_encoded = le.fit_transform(ground_truth_labels)

        # Calculate metrics
        ari = adjusted_rand_score(gt_labels_encoded, cluster_labels_encoded)
        nmi = normalized_mutual_info_score(gt_labels_encoded, cluster_labels_encoded)

        logger.info(f"ARI: {ari:.4f}, NMI: {nmi:.4f}")

        return {
            'ari': float(ari),
            'nmi': float(nmi)
        }

    except Exception as e:
        raise ClusteringError(f"Fidelity metrics calculation failed: {e}")

def process_accession(
    accession: str,
    processed_path: Path,
    labels_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Process a single accession: cluster and calculate fidelity metrics.

    Args:
        accession: Dataset accession ID
        processed_path: Path to processed AnnData file
        labels_path: Path to ground truth labels CSV
        output_dir: Directory to save results

    Returns:
        Dictionary with results
    """
    try:
        logger.info(f"Processing accession: {accession}")

        # Load data
        adata = load_preprocessed_data(str(processed_path))

        # Load ground truth labels
        if not labels_path.exists():
            raise ClusteringError(f"Labels file not found: {labels_path}")

        labels_df = pd.read_csv(labels_path)
        # Assume first column is the label column
        if labels_df.shape[1] < 1:
            raise ClusteringError("Labels file is empty or malformed")

        ground_truth = labels_df.iloc[:, 0].values

        # Optimize resolution
        resolution_range = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        best_res, best_score = optimize_resolution(
            adata,
            resolution_range=resolution_range,
            random_state=42
        )

        # Run final clustering with optimal resolution
        cluster_labels = run_leiden_clustering(
            adata,
            resolution=best_res,
            random_state=42
        )

        # Calculate fidelity metrics
        fidelity = calculate_fidelity_metrics(cluster_labels, ground_truth)

        # Save clustered data
        adata.obs['leiden'] = cluster_labels
        clustered_path = output_dir.parent / f"{accession}_clustered.h5ad"
        adata.write_h5ad(str(clustered_path))

        # Prepare results
        results = {
            'accession': accession,
            'optimal_resolution': float(best_res),
            'silhouette_score': float(best_score),
            'fidelity': fidelity,
            'n_clusters': int(len(np.unique(cluster_labels))),
            'n_cells': int(adata.n_obs)
        }

        # Save results
        output_path = output_dir / f"{accession}_fidelity.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_path}")
        return results

    except Exception as e:
        logger.error(f"Failed to process accession {accession}: {e}")
        raise

def main():
    """Main entry point for clustering script."""
    import argparse
    from config import Config

    parser = argparse.ArgumentParser(description='Clustering and Fidelity Analysis')
    parser.add_argument('--accession', type=str, required=True, help='Dataset accession ID')
    parser.add_argument('--mode', type=str, choices=['cluster', 'fidelity'], default='fidelity',
                      help='Operation mode: cluster or fidelity')
    args = parser.parse_args()

    config = Config()

    processed_path = Path(config.DATA_PROCESSED) / f"{args.accession}_processed.h5ad"
    labels_path = Path(config.DATA_RAW) / f"{args.accession}_labels.csv"
    output_dir = Path(config.RESULTS) / "fidelity"

    try:
        if args.mode == 'fidelity':
            results = process_accession(args.accession, processed_path, labels_path, output_dir)
            print(json.dumps(results, indent=2))
        else:
            # Just cluster mode (for Snakemake dependency)
            adata = load_preprocessed_data(str(processed_path))
            resolution_range = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            best_res, best_score = optimize_resolution(
                adata,
                resolution_range=resolution_range,
                random_state=42
            )
            cluster_labels = run_leiden_clustering(
                adata,
                resolution=best_res,
                random_state=42
            )
            adata.obs['leiden'] = cluster_labels
            output_path = Path(config.DATA_PROCESSED) / f"{args.accession}_clustered.h5ad"
            adata.write_h5ad(str(output_path))
            logger.info(f"Clustered data saved to {output_path}")

    except ClusteringError as e:
        logger.error(f"Clustering error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()