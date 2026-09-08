"""
Embedding service for generating sentence embeddings and computing novelty scores.

This module handles:
1. Loading the sentence-transformers model
2. Filtering invalid nodes (empty/null titles)
3. Batched embedding generation
4. Computing cluster centroids
5. Calculating novelty scores based on centroid distance
"""
import logging
import os
import time
import gc
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
from pathlib import Path

from sentence_transformers import SentenceTransformer

from src.lib.config import get_data_path, get_logs_path, ensure_directories

logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 64
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 output dimension

# Global model cache
_model_cache: Optional[SentenceTransformer] = None


def load_embedding_model(device: str = "cpu") -> SentenceTransformer:
    """
    Load the sentence-transformers model.
    
    Uses a global cache to avoid reloading the model multiple times.
    
    Args:
        device: Device to load the model on ('cpu' or 'cuda')
        
    Returns:
        Loaded SentenceTransformer model
    """
    global _model_cache
    
    if _model_cache is not None:
        logger.info("Using cached embedding model")
        return _model_cache
    
    logger.info(f"Loading embedding model: {MODEL_NAME} on {device}")
    start_time = time.perf_counter()
    
    try:
        model = SentenceTransformer(MODEL_NAME, device=device)
        _model_cache = model
        
        elapsed = time.perf_counter() - start_time
        logger.info(f"Model loaded successfully in {elapsed:.2f}s")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise


def filter_valid_nodes(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter nodes with valid titles for embedding generation.
    
    Separates nodes into:
    - Valid: non-empty, non-null titles
    - Invalid: empty string or null titles
    
    Args:
        df: DataFrame containing node data with 'title' column
        
    Returns:
        Tuple of (valid_nodes_df, invalid_nodes_df)
    """
    if 'title' not in df.columns:
        raise ValueError("DataFrame must contain 'title' column")
    
    # Create boolean masks
    is_not_null = df['title'].notna()
    is_not_empty = df['title'].astype(str).str.strip() != ''
    
    valid_mask = is_not_null & is_not_empty
    invalid_mask = ~valid_mask
    
    valid_df = df[valid_mask].copy()
    invalid_df = df[invalid_mask].copy()
    
    logger.info(f"Filtered nodes: {len(valid_df)} valid, {len(invalid_df)} invalid")
    
    return valid_df, invalid_df


def save_excluded_nodes(invalid_df: pd.DataFrame, reason: str) -> None:
    """
    Save excluded nodes to a CSV log file.
    
    Args:
        invalid_df: DataFrame of excluded nodes
        reason: Reason for exclusion (e.g., 'empty_title', 'null_title')
    """
    if invalid_df.empty:
        logger.debug("No invalid nodes to save")
        return
    
    logs_path = get_logs_path()
    ensure_directories()
    
    excluded_file = Path(logs_path) / "excluded_nodes.csv"
    
    # Prepare data for saving
    if 'id' in invalid_df.columns:
        log_data = invalid_df[['id']].copy()
        log_data['reason'] = reason
    else:
        # If no ID column, create a generic log
        log_data = pd.DataFrame({
            'node_id': range(len(invalid_df)),
            'reason': reason
        })
    
    # Append to existing file if it exists
    if excluded_file.exists():
        existing = pd.read_csv(excluded_file)
        combined = pd.concat([existing, log_data], ignore_index=True)
        combined.to_csv(excluded_file, index=False)
    else:
        log_data.to_csv(excluded_file, index=False)
    
    logger.info(f"Saved {len(log_data)} excluded nodes to {excluded_file}")


def generate_embeddings_batched(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
    device: str = "cpu"
) -> np.ndarray:
    """
    Generate embeddings for a list of texts in batches.
    
    Args:
        model: Loaded SentenceTransformer model
        texts: List of text strings to embed
        batch_size: Number of texts to process per batch
        device: Device to use for encoding
        
    Returns:
        numpy array of embeddings with shape (len(texts), embedding_dimension)
    """
    if not texts:
        logger.warning("Empty text list provided for embedding")
        return np.array([]).reshape(0, EMBEDDING_DIMENSION)
    
    logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
    
    all_embeddings = []
    total_start = time.perf_counter()
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_start = time.perf_counter()
        
        # Generate embeddings for the batch
        batch_embeddings = model.encode(
            batch_texts,
            device=device,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        batch_time = time.perf_counter() - batch_start
        logger.debug(f"Batch {i//batch_size + 1}: {len(batch_texts)} texts in {batch_time:.3f}s")
        
        all_embeddings.append(batch_embeddings)
        
        # Force garbage collection periodically
        if i % (batch_size * 10) == 0:
            gc.collect()
    
    total_time = time.perf_counter() - total_start
    avg_time_per_text = (total_time / len(texts)) * 1000  # ms
    
    logger.info(f"Generated all embeddings in {total_time:.2f}s "
               f"(avg {avg_time_per_text:.2f}ms per text)")
    
    return np.vstack(all_embeddings)

def process_nodes_for_embeddings(
    df: pd.DataFrame,
    batch_size: int = DEFAULT_BATCH_SIZE,
    device: str = "cpu"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process a DataFrame of nodes: filter valid ones, generate embeddings,
    and save excluded nodes.
    
    Args:
        df: DataFrame with node data including 'title' column
        batch_size: Batch size for embedding generation
        device: Device for model inference
        
    Returns:
        Tuple of (processed_df_with_embeddings, excluded_df)
    """
    # Filter valid and invalid nodes
    valid_df, invalid_df = filter_valid_nodes(df)
    
    # Save excluded nodes
    if not invalid_df.empty:
        # Determine reasons for exclusion
        null_mask = invalid_df['title'].isna()
        empty_mask = ~null_mask & (invalid_df['title'].astype(str).str.strip() == '')
        
        if null_mask.any():
            null_df = invalid_df[null_mask]
            save_excluded_nodes(null_df, 'null_title')
        
        if empty_mask.any():
            empty_df = invalid_df[empty_mask]
            save_excluded_nodes(empty_df, 'empty_title')
    
    # Return early if no valid nodes
    if valid_df.empty:
        logger.warning("No valid nodes to process")
        return df, invalid_df
    
    # Extract texts
    texts = valid_df['title'].tolist()
    
    # Load model if not already loaded
    model = load_embedding_model(device=device)
    
    # Generate embeddings
    embeddings = generate_embeddings_batched(
        model=model,
        texts=texts,
        batch_size=batch_size,
        device=device
    )
    
    # Assign embeddings to the valid DataFrame
    valid_df = valid_df.copy()
    valid_df['embedding_vector'] = list(embeddings)
    
    # Initialize invalid_df with null embeddings
    invalid_df = invalid_df.copy()
    invalid_df['embedding_vector'] = [None] * len(invalid_df)
    
    # Combine back
    result_df = pd.concat([valid_df, invalid_df], ignore_index=True)
    
    # Sort by original index to maintain order
    if 'original_index' in result_df.columns:
        result_df = result_df.sort_values('original_index').drop('original_index', axis=1)
    
    return result_df, invalid_df


def compute_cluster_centroids(
    embeddings: np.ndarray,
    cluster_labels: np.ndarray
) -> np.ndarray:
    """
    Compute centroids for each cluster.
    
    Args:
        embeddings: Array of embeddings with shape (n_samples, n_features)
        cluster_labels: Array of cluster assignments with shape (n_samples,)
        
    Returns:
        Array of centroids with shape (n_clusters, n_features)
    """
    if embeddings.shape[0] == 0:
        return np.array([])
    
    unique_clusters = np.unique(cluster_labels)
    n_clusters = len(unique_clusters)
    n_features = embeddings.shape[1]
    
    centroids = np.zeros((n_clusters, n_features))
    
    for i, cluster_id in enumerate(unique_clusters):
        cluster_mask = cluster_labels == cluster_id
        cluster_embeddings = embeddings[cluster_mask]
        centroids[i] = np.mean(cluster_embeddings, axis=0)
    
    return centroids


def compute_novelty_scores(
    embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    centroids: np.ndarray
) -> np.ndarray:
    """
    Compute novelty scores as cosine distance to cluster centroid.
    
    Args:
        embeddings: Array of embeddings with shape (n_samples, n_features)
        cluster_labels: Array of cluster assignments with shape (n_samples,)
        centroids: Array of centroids with shape (n_clusters, n_features)
        
    Returns:
        Array of novelty scores with shape (n_samples,)
    """
    if embeddings.shape[0] == 0:
        return np.array([])
    
    novelty_scores = np.zeros(len(embeddings))
    
    for i, (emb, cluster_id) in enumerate(zip(embeddings, cluster_labels)):
        # Find centroid for this cluster
        centroid_idx = np.where(np.arange(len(centroids)) == cluster_id)[0]
        if len(centroid_idx) == 0:
            novelty_scores[i] = 0.0
            continue
        
        centroid = centroids[centroid_idx[0]]
        
        # Compute cosine similarity
        norm_emb = np.linalg.norm(emb)
        norm_cent = np.linalg.norm(centroid)
        
        if norm_emb == 0 or norm_cent == 0:
            novelty_scores[i] = 0.0
        else:
            similarity = np.dot(emb, centroid) / (norm_emb * norm_cent)
            # Convert similarity to distance
            novelty_scores[i] = 1.0 - similarity
    
    return novelty_scores


def assign_topic_clusters_to_dataframe(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    novelty_scores: np.ndarray
) -> pd.DataFrame:
    """
    Assign topic cluster and novelty score columns to a DataFrame.
    
    Args:
        df: Original DataFrame
        embeddings: Embeddings array (used for validation)
        cluster_labels: Cluster assignments
        novelty_scores: Novelty scores
        
    Returns:
        DataFrame with added 'topic_cluster' and 'novelty_score' columns
    """
    result_df = df.copy()
    result_df['topic_cluster'] = cluster_labels
    result_df['novelty_score'] = novelty_scores
    
    return result_df


def generate_embeddings_for_dataset(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    device: str = "cpu"
) -> pd.DataFrame:
    """
    Main entry point for generating embeddings for a dataset.
    
    Args:
        df: Input DataFrame with 'title' column
        output_path: Optional path to save excluded nodes log
        batch_size: Batch size for processing
        device: Device for model inference
        
    Returns:
        DataFrame with embeddings, topic clusters, and novelty scores
    """
    logger.info("Starting embedding generation for dataset")
    
    # Process nodes and generate embeddings
    processed_df, invalid_df = process_nodes_for_embeddings(
        df=df,
        batch_size=batch_size,
        device=device
    )
    
    # Filter valid nodes for clustering
    valid_df = processed_df[processed_df['embedding_vector'].notna()].copy()
    
    if valid_df.empty:
        logger.warning("No valid embeddings for clustering")
        return processed_df
    
    # Extract embeddings
    embeddings = np.vstack(valid_df['embedding_vector'].tolist())
    
    # Perform k-means clustering (k=100 as per spec)
    from sklearn.cluster import KMeans
    
    logger.info(f"Performing k-means clustering with k=100")
    kmeans = KMeans(n_clusters=100, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(embeddings)
    
    # Compute centroids
    centroids = compute_cluster_centroids(embeddings, cluster_labels)
    
    # Compute novelty scores
    novelty_scores = compute_novelty_scores(embeddings, cluster_labels, centroids)
    
    # Map back to full dataframe
    valid_indices = valid_df.index
    full_cluster_labels = np.full(len(processed_df), -1, dtype=int)
    full_novelty_scores = np.full(len(processed_df), np.nan, dtype=float)
    
    full_cluster_labels[valid_indices] = cluster_labels
    full_novelty_scores[valid_indices] = novelty_scores
    
    processed_df['topic_cluster'] = full_cluster_labels
    processed_df['novelty_score'] = full_novelty_scores
    
    logger.info(f"Generated embeddings and novelty scores for {len(valid_df)} nodes")
    
    return processed_df


def log_memory_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Log memory usage profile for the embedding process.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with memory profile metrics
    """
    try:
        import resource
        
        # Get current memory usage
        mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert to MB
        
        profile = {
            'input_rows': len(df),
            'peak_memory_mb': mem_usage,
            'peak_memory_gb': mem_usage / 1024
        }
        
        logger.info(f"Memory profile: {profile}")
        return profile
        
    except ImportError:
        logger.warning("resource module not available, skipping memory profiling")
        return {}
