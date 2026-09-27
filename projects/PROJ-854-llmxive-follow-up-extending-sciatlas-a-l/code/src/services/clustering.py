import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)

def perform_kmeans_clustering(embeddings: np.ndarray, k_range: Tuple[int, int] = (50, 200)) -> Tuple[int, KMeans, np.ndarray]:
    """
    Perform K-Means clustering on title embeddings to assign topic_cluster IDs.
    Determines optimal k using silhouette score within the specified range.

    Args:
        embeddings: 2D numpy array of shape (n_samples, n_features)
        k_range: Tuple (min_k, max_k) for search range

    Returns:
        Tuple of (best_k, best_model, cluster_labels)
    """
    if len(embeddings) == 0:
        raise ValueError("Cannot perform clustering on empty embeddings")

    min_k, max_k = k_range
    # Adjust range if data is smaller than min_k
    n_samples = embeddings.shape[0]
    if n_samples < min_k:
        min_k = max(2, n_samples)
    if n_samples < max_k:
        max_k = n_samples

    if min_k > max_k:
        min_k = max_k

    best_k = min_k
    best_score = -1
    best_model = None
    best_labels = None

    logger.info(f"Searching for optimal k in range [{min_k}, {max_k}]")

    for k in range(min_k, max_k + 1):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            logger.debug(f"k={k}, silhouette_score={score:.4f}")
            if score > best_score:
                best_score = score
                best_k = k
                best_model = kmeans
                best_labels = labels
        except Exception as e:
            logger.warning(f"Failed to compute silhouette for k={k}: {e}")
            continue

    if best_model is None:
        raise RuntimeError("Could not find a valid clustering model")

    logger.info(f"Selected optimal k={best_k} with silhouette score={best_score:.4f}")
    return best_k, best_model, best_labels

def validate_cluster_stability(
    embeddings: np.ndarray,
    best_k: int,
    n_seeds: int = 3,
    tolerance: float = 0.05
) -> bool:
    """
    Validate that the selected k yields a stable silhouette score across random seeds.
    Stability is defined as variance within 'tolerance' (5%) of the mean score.

    Args:
        embeddings: 2D numpy array of shape (n_samples, n_features)
        best_k: The cluster count to validate
        n_seeds: Number of random seeds to test
        tolerance: Maximum allowed variance ratio (0.05 = 5%)

    Returns:
        True if stable, False otherwise.
    """
    scores = []
    for seed in range(n_seeds):
        try:
            kmeans = KMeans(n_clusters=best_k, random_state=seed, n_init=10, max_iter=300)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            scores.append(score)
            logger.debug(f"Seed {seed}: silhouette_score={score:.4f}")
        except Exception as e:
            logger.warning(f"Failed to compute score for seed {seed}: {e}")
            scores.append(0.0) # Penalize failure

    if len(scores) < 2:
        logger.warning("Not enough successful runs to validate stability")
        return False

    mean_score = np.mean(scores)
    variance = np.var(scores)
    std_dev = np.sqrt(variance)
    relative_std = std_dev / mean_score if mean_score != 0 else float('inf')

    logger.info(f"Stability check for k={best_k}: mean={mean_score:.4f}, std={std_dev:.4f}, rel_std={relative_std:.2%}")

    if relative_std > tolerance:
        logger.warning(f"Silhouette score unstable for k={best_k} (variance {relative_std:.2%} > {tolerance:.2%}). Proceeding with best k found.")
        return False

    logger.info(f"Silhouette score stable for k={best_k} (variance {relative_std:.2%} <= {tolerance:.2%})")
    return True

def assign_topic_clusters_to_dataframe(
    df: pd.DataFrame,
    embeddings: np.ndarray
) -> pd.DataFrame:
    """
    Assign topic clusters to a dataframe based on embeddings.
    Includes stability validation step.

    Args:
        df: DataFrame containing node data
        embeddings: 2D numpy array of embeddings corresponding to df rows

    Returns:
        DataFrame with added 'topic_cluster' column
    """
    if len(embeddings) == 0:
        df['topic_cluster'] = np.nan
        return df

    best_k, best_model, labels = perform_kmeans_clustering(embeddings)

    # Validate stability
    is_stable = validate_cluster_stability(embeddings, best_k, n_seeds=3, tolerance=0.05)
    if not is_stable:
        logger.warning(f"Cluster count k={best_k} is unstable, but proceeding with best found.")

    df = df.copy()
    df['topic_cluster'] = labels
    return df

def compute_cluster_centroids(embeddings: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """
    Compute centroids for each cluster.

    Args:
        embeddings: 2D numpy array of shape (n_samples, n_features)
        labels: 1D array of cluster assignments

    Returns:
        2D array of centroids (n_clusters, n_features)
    """
    unique_labels = np.unique(labels)
    centroids = np.zeros((len(unique_labels), embeddings.shape[1]))
    for i, label in enumerate(unique_labels):
        mask = labels == label
        centroids[i] = embeddings[mask].mean(axis=0)
    return centroids

def compute_novelty_scores_from_embeddings(
    embeddings: np.ndarray,
    labels: np.ndarray
) -> np.ndarray:
    """
    Compute novelty scores as cosine distance to own cluster centroid.
    Singleton clusters get 0.0.

    Args:
        embeddings: 2D numpy array of shape (n_samples, n_features)
        labels: 1D array of cluster assignments

    Returns:
        1D array of novelty scores
    """
    centroids = compute_cluster_centroids(embeddings, labels)
    novelty_scores = np.zeros(len(embeddings))
    unique_labels, counts = np.unique(labels, return_counts=True)

    for label, count in zip(unique_labels, counts):
        centroid = centroids[label]
        mask = labels == label
        cluster_embeddings = embeddings[mask]

        # Normalize embeddings and centroid for cosine distance
        norms = np.linalg.norm(cluster_embeddings, axis=1, keepdims=True)
        # Avoid division by zero for zero vectors
        norms[norms == 0] = 1e-10
        normalized_cluster_embeddings = cluster_embeddings / norms

        centroid_norm = np.linalg.norm(centroid)
        if centroid_norm == 0:
            centroid_norm = 1e-10
        normalized_centroid = centroid / centroid_norm

        # Cosine similarity
        similarities = np.dot(normalized_cluster_embeddings, normalized_centroid)
        # Cosine distance = 1 - similarity
        distances = 1 - similarities

        # Handle singletons: distance is 0.0
        if count == 1:
            distances[:] = 0.0

        novelty_scores[mask] = distances

    return novelty_scores

def get_cluster_statistics(labels: np.ndarray) -> Dict[str, Any]:
    """
    Get basic statistics about cluster assignments.

    Args:
        labels: 1D array of cluster assignments

    Returns:
        Dictionary with cluster statistics
    """
    unique, counts = np.unique(labels, return_counts=True)
    return {
        'num_clusters': len(unique),
        'cluster_sizes': dict(zip(unique.tolist(), counts.tolist())),
        'min_size': int(np.min(counts)),
        'max_size': int(np.max(counts)),
        'avg_size': float(np.mean(counts))
    }

def compute_cluster_centroids_from_dataframe(
    df: pd.DataFrame,
    embeddings_col: str = 'embedding_vector'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute cluster centroids from a dataframe with embeddings.

    Args:
        df: DataFrame with embeddings column
        embeddings_col: Name of the column containing embeddings

    Returns:
        Tuple of (centroids, labels)
    """
    embeddings = np.vstack(df[embeddings_col].values)
    labels = df['topic_cluster'].values
    return compute_cluster_centroids(embeddings, labels), labels

def log_memory_profile(step_name: str, memory_usage_mb: float):
    """
    Log memory usage for a specific step.

    Args:
        step_name: Name of the step
        memory_usage_mb: Memory usage in MB
    """
    logger.info(f"Memory profile for {step_name}: {memory_usage_mb:.2f} MB")

def generate_embeddings_for_dataset(
    df: pd.DataFrame,
    model,
    batch_size: int = 64
) -> np.ndarray:
    """
    Generate embeddings for a dataset using batches.

    Args:
        df: DataFrame with 'title' column
        model: Sentence transformer model
        batch_size: Batch size for processing

    Returns:
        2D numpy array of embeddings
    """
    texts = df['title'].dropna().tolist()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.append(batch_embeddings)
        logger.debug(f"Processed batch {i//batch_size + 1}")

    if not all_embeddings:
        return np.array([])

    return np.vstack(all_embeddings)

def main():
    """
    Main entry point for clustering service.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Clustering service initialized")
    # This would typically be called by a script or pipeline
    pass