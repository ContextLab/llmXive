"""
Embedding service for generating sentence embeddings and computing novelty scores.

This module handles:
- Loading the sentence-transformers model (CPU mode)
- Filtering nodes with valid titles
- Batched embedding generation to meet memory constraints
- Computing novelty scores based on cluster centroid distance
"""

import logging
import os
import time
import gc
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from src.lib import config

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE = 32  # Adjust based on memory constraints
MAX_NODE_LATENCY_MS = 50  # Maximum allowed latency per node in milliseconds
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def load_embedding_model() -> SentenceTransformer:
    """
    Load the sentence-transformers model in CPU mode.
    
    Returns:
        SentenceTransformer: The loaded model.
    """
    logger.info(f"Loading embedding model: {MODEL_NAME}")
    try:
        model = SentenceTransformer(MODEL_NAME, device='cpu')
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def filter_valid_nodes(nodes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Filter nodes with valid (non-empty) titles.
    
    Args:
        nodes: List of node dictionaries.
    
    Returns:
        Tuple of (valid_nodes, excluded_node_ids)
    """
    valid_nodes = []
    excluded_ids = []
    
    for node in nodes:
        title = node.get('title', '').strip()
        if title:
            valid_nodes.append(node)
        else:
            excluded_ids.append(node.get('id', 'unknown'))
    
    logger.info(f"Filtered nodes: {len(valid_nodes)} valid, {len(excluded_ids)} excluded")
    return valid_nodes, excluded_ids

def save_excluded_nodes(excluded_ids: List[str], output_path: str) -> None:
    """
    Save excluded node IDs to a CSV file.
    
    Args:
        excluded_ids: List of excluded node IDs.
        output_path: Path to the output CSV file.
    """
    if not excluded_ids:
        logger.info("No excluded nodes to save")
        return
    
    df = pd.DataFrame({'node_id': excluded_ids})
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(excluded_ids)} excluded node IDs to {output_path}")

def generate_embeddings_batched(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = BATCH_SIZE
) -> np.ndarray:
    """
    Generate embeddings for a list of texts in batches.
    
    Args:
        model: The sentence-transformers model.
        texts: List of text strings to embed.
        batch_size: Number of texts per batch.
    
    Returns:
        np.ndarray: Array of embeddings with shape (n_texts, embedding_dim).
    """
    all_embeddings = []
    total_texts = len(texts)
    
    logger.info(f"Generating embeddings for {total_texts} texts in batches of {batch_size}")
    
    for i in range(0, total_texts, batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_start_time = time.time()
        
        # Generate embeddings for the batch
        batch_embeddings = model.encode(
            batch_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        batch_time = time.time() - batch_start_time
        batch_size_actual = len(batch_texts)
        avg_latency_per_node = (batch_time / batch_size_actual) * 1000  # Convert to ms
        
        if avg_latency_per_node > MAX_NODE_LATENCY_MS:
            logger.warning(
                f"Batch {i // batch_size} exceeded latency threshold: "
                f"{avg_latency_per_node:.2f}ms per node (threshold: {MAX_NODE_LATENCY_MS}ms)"
            )
        
        all_embeddings.append(batch_embeddings)
        
        # Log progress
        if (i + batch_size) % (batch_size * 10) == 0 or i + batch_size >= total_texts:
            logger.info(f"Processed {min(i + batch_size, total_texts)}/{total_texts} texts")
    
    # Concatenate all batch embeddings
    all_embeddings = np.vstack(all_embeddings)
    logger.info(f"Generated embeddings with shape: {all_embeddings.shape}")
    return all_embeddings

def process_nodes_for_embeddings(nodes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Process nodes to extract valid titles and prepare for embedding generation.
    
    Args:
        nodes: List of node dictionaries.
    
    Returns:
        Tuple of (processed_nodes, titles, excluded_ids)
    """
    valid_nodes, excluded_ids = filter_valid_nodes(nodes)
    titles = [node['title'] for node in valid_nodes]
    return valid_nodes, titles, excluded_ids

def compute_novelty_scores(
    embeddings: np.ndarray,
    topic_clusters: List[int],
    cluster_ids: Optional[List[int]] = None
) -> np.ndarray:
    """
    Compute novelty scores based on cosine distance to cluster centroids.
    
    Args:
        embeddings: Array of embeddings with shape (n_nodes, embedding_dim).
        topic_clusters: List of topic cluster assignments for each node.
        cluster_ids: Optional list of unique cluster IDs. If None, derived from topic_clusters.
    
    Returns:
        np.ndarray: Array of novelty scores (cosine distances).
    """
    if len(embeddings) == 0:
        return np.array([])
    
    if cluster_ids is None:
        cluster_ids = sorted(set(topic_clusters))
    
    # Compute cluster centroids
    centroids = {}
    for cluster_id in cluster_ids:
        mask = np.array(topic_clusters) == cluster_id
        if np.any(mask):
            centroids[cluster_id] = np.mean(embeddings[mask], axis=0)
        else:
            centroids[cluster_id] = np.zeros(embeddings.shape[1])
    
    # Compute cosine distance to centroid for each node
    novelty_scores = []
    for i, (embedding, cluster_id) in enumerate(zip(embeddings, topic_clusters)):
        centroid = centroids[cluster_id]
        
        # Compute cosine similarity
        dot_product = np.dot(embedding, centroid)
        norm_embedding = np.linalg.norm(embedding)
        norm_centroid = np.linalg.norm(centroid)
        
        if norm_embedding == 0 or norm_centroid == 0:
            cosine_similarity = 0.0
        else:
            cosine_similarity = dot_product / (norm_embedding * norm_centroid)
        
        # Convert to cosine distance
        cosine_distance = 1.0 - cosine_similarity
        novelty_scores.append(cosine_distance)
    
    return np.array(novelty_scores)

def log_memory_profile() -> Dict[str, Any]:
    """
    Log current memory usage statistics.
    
    Returns:
        Dict[str, Any]: Memory usage statistics.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        stats = {
            'rss_mb': memory_info.rss / (1024 * 1024),
            'vms_mb': memory_info.vms / (1024 * 1024)
        }
        logger.info(f"Memory usage: RSS={stats['rss_mb']:.2f}MB, VMS={stats['vms_mb']:.2f}MB")
        return stats
    except ImportError:
        logger.warning("psutil not available, skipping memory profiling")
        return {}

def generate_embeddings_for_dataset(
    nodes: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray, List[str]]:
    """
    Generate embeddings for a dataset of nodes and compute novelty scores.
    
    Args:
        nodes: List of node dictionaries.
        output_path: Optional path to save excluded nodes CSV.
    
    Returns:
        Tuple of (processed_nodes, embeddings, novelty_scores, excluded_ids)
    """
    # Process nodes
    valid_nodes, titles, excluded_ids = process_nodes_for_embeddings(nodes)
    
    if not valid_nodes:
        logger.warning("No valid nodes to process")
        return [], np.array([]), np.array([]), excluded_ids
    
    # Save excluded nodes if output path provided
    if output_path:
        save_excluded_nodes(excluded_ids, output_path)
    
    # Load model
    model = load_embedding_model()
    
    # Generate embeddings
    embeddings = generate_embeddings_batched(model, titles)
    
    # Extract topic clusters (assuming nodes have 'topic_cluster' field)
    topic_clusters = [node.get('topic_cluster', -1) for node in valid_nodes]
    
    # Compute novelty scores
    novelty_scores = compute_novelty_scores(embeddings, topic_clusters)
    
    # Log memory profile
    log_memory_profile()
    
    return valid_nodes, embeddings, novelty_scores, excluded_ids
