"""
Embeddings service for generating sentence embeddings and computing novelty scores.

This module handles:
- Loading the sentence-transformer model
- Filtering nodes with valid titles for novelty calculation
- Generating embeddings in batches to manage memory
- Computing novelty scores based on centroid distance
- Logging excluded nodes to a CSV file
"""
import logging
import os
import time
import gc
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 32  # Batch size for embedding generation to manage memory

def load_embedding_model(model_name: str = MODEL_NAME) -> SentenceTransformer:
    """
    Load the sentence-transformer model.

    Args:
        model_name: Name of the model to load from sentence-transformers

    Returns:
        Loaded SentenceTransformer model
    """
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"Successfully loaded model: {model_name}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def filter_valid_nodes(nodes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Filter nodes with valid (non-empty) titles for novelty calculation.

    Nodes with missing or empty titles are excluded from novelty calculation
    but are retained in the dataset for citation analysis.

    Args:
        nodes: List of node dictionaries containing 'id' and 'title' fields

    Returns:
        Tuple of (valid_nodes, excluded_node_ids)
        - valid_nodes: List of nodes with valid titles
        - excluded_node_ids: List of node IDs that were excluded
    """
    valid_nodes = []
    excluded_node_ids = []

    for node in nodes:
        node_id = node.get('id')
        title = node.get('title', '')

        # Check if title is missing or empty
        if title is None or (isinstance(title, str) and title.strip() == ''):
            if node_id:
                excluded_node_ids.append(str(node_id))
            logger.debug(f"Excluding node {node_id}: missing or empty title")
        else:
            valid_nodes.append(node)

    logger.info(f"Filtered {len(nodes)} nodes: {len(valid_nodes)} valid, {len(excluded_node_ids)} excluded")
    return valid_nodes, excluded_node_ids

def save_excluded_nodes(excluded_node_ids: List[str], output_path: str) -> None:
    """
    Save excluded node IDs to a CSV file.

    Args:
        excluded_node_ids: List of node IDs that were excluded
        output_path: Path to the output CSV file
    """
    if not excluded_node_ids:
        logger.info("No excluded nodes to save")
        return

    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created directory: {output_dir}")

    # Create DataFrame and save
    df = pd.DataFrame({'node_id': excluded_node_ids})
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(excluded_node_ids)} excluded node IDs to {output_path}")

def generate_embeddings_batched(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = BATCH_SIZE
) -> np.ndarray:
    """
    Generate embeddings for a list of texts in batches to manage memory.

    Args:
        model: Loaded SentenceTransformer model
        texts: List of texts to embed
        batch_size: Number of texts to process in each batch

    Returns:
        NumPy array of embeddings (shape: [num_texts, embedding_dim])
    """
    logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")

    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_num = i // batch_size + 1

        logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)")

        try:
            batch_embeddings = model.encode(batch_texts, show_progress_bar=False, convert_to_numpy=True)
            all_embeddings.append(batch_embeddings)

            # Force garbage collection between batches to manage memory
            if i + batch_size < len(texts):
                gc.collect()
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            raise

    if not all_embeddings:
        return np.array([])

    result = np.vstack(all_embeddings)
    logger.info(f"Generated embeddings with shape: {result.shape}")
    return result

def process_nodes_for_embeddings(
    nodes: List[Dict[str, Any]],
    excluded_log_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Process nodes for embedding generation, filtering out invalid titles.

    Args:
        nodes: List of node dictionaries
        excluded_log_path: Optional path to save excluded node IDs

    Returns:
        Tuple of (valid_nodes, node_ids, texts)
        - valid_nodes: List of nodes with valid titles
        - node_ids: List of corresponding node IDs
        - texts: List of titles for embedding
    """
    valid_nodes, excluded_ids = filter_valid_nodes(nodes)

    node_ids = [node.get('id') for node in valid_nodes]
    texts = [node.get('title', '').strip() for node in valid_nodes]

    # Save excluded nodes if path provided
    if excluded_log_path and excluded_ids:
        save_excluded_nodes(excluded_ids, excluded_log_path)

    return valid_nodes, node_ids, texts

def compute_cluster_centroids(embeddings: np.ndarray, cluster_labels: List[int]) -> Dict[int, np.ndarray]:
    """
    Compute centroids for each cluster.

    Args:
        embeddings: Array of embeddings (shape: [num_nodes, embedding_dim])
        cluster_labels: List of cluster assignments for each embedding

    Returns:
        Dictionary mapping cluster_id to centroid vector
    """
    unique_clusters = list(set(cluster_labels))
    centroids = {}

    for cluster_id in unique_clusters:
        mask = np.array(cluster_labels) == cluster_id
        cluster_embeddings = embeddings[mask]
        if len(cluster_embeddings) > 0:
            centroids[cluster_id] = np.mean(cluster_embeddings, axis=0)
        else:
            # Fallback for empty clusters (shouldn't happen in practice)
            centroids[cluster_id] = np.zeros(embeddings.shape[1])

    return centroids

def compute_novelty_scores(
    embeddings: np.ndarray,
    cluster_labels: List[int]
) -> np.ndarray:
    """
    Compute novelty scores as cosine distance from cluster centroid.

    Novelty score = cosine distance between node embedding and its cluster centroid.
    Higher scores indicate more novel (outlier) nodes within their cluster.

    Args:
        embeddings: Array of embeddings (shape: [num_nodes, embedding_dim])
        cluster_labels: List of cluster assignments for each embedding

    Returns:
        Array of novelty scores (shape: [num_nodes])
    """
    if len(embeddings) == 0:
        return np.array([])

    centroids = compute_cluster_centroids(embeddings, cluster_labels)
    novelty_scores = np.zeros(len(embeddings))

    for i, (emb, cluster_id) in enumerate(zip(embeddings, cluster_labels)):
        centroid = centroids[cluster_id]

        # Compute cosine similarity
        norm_emb = np.linalg.norm(emb)
        norm_centroid = np.linalg.norm(centroid)

        if norm_emb == 0 or norm_centroid == 0:
            # Handle zero-norm vectors
            novelty_scores[i] = 1.0  # Maximum distance
        else:
            cosine_sim = np.dot(emb, centroid) / (norm_emb * norm_centroid)
            # Convert to distance (1 - similarity)
            novelty_scores[i] = 1.0 - cosine_sim

    return novelty_scores

def log_memory_profile(stage: str) -> None:
    """
    Log current memory usage profile.

    Args:
        stage: Description of the current processing stage
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        logger.info(f"Memory profile at {stage}: RSS={mem_info.rss / 1024 / 1024:.2f} MB, VMS={mem_info.vms / 1024 / 1024:.2f} MB")
    except ImportError:
        logger.debug("psutil not available, skipping memory profiling")
    except Exception as e:
        logger.debug(f"Could not profile memory: {e}")

def generate_embeddings_for_dataset(
    nodes: List[Dict[str, Any]],
    cluster_labels: Optional[List[int]] = None,
    excluded_log_path: Optional[str] = None
) -> Tuple[np.ndarray, List[int], np.ndarray]:
    """
    Generate embeddings and compute novelty scores for a dataset of nodes.

    This is the main entry point for processing a full dataset.

    Args:
        nodes: List of node dictionaries with 'id' and 'title' fields
        cluster_labels: Optional list of cluster assignments (if None, novelty scores won't be computed)
        excluded_log_path: Path to save excluded node IDs CSV

    Returns:
        Tuple of (embeddings, node_ids, novelty_scores)
        - embeddings: Array of embeddings for valid nodes
        - node_ids: List of node IDs for valid nodes
        - novelty_scores: Array of novelty scores (empty array if cluster_labels not provided)
    """
    # Process nodes and filter out invalid titles
    valid_nodes, node_ids, texts = process_nodes_for_embeddings(nodes, excluded_log_path)

    if not valid_nodes:
        logger.warning("No valid nodes found for embedding generation")
        return np.array([]), [], np.array([])

    # Load model
    model = load_embedding_model()

    # Generate embeddings in batches
    embeddings = generate_embeddings_batched(model, texts)

    # Compute novelty scores if cluster labels provided
    novelty_scores = np.array([])
    if cluster_labels is not None and len(cluster_labels) == len(embeddings):
        novelty_scores = compute_novelty_scores(embeddings, cluster_labels)
        logger.info(f"Computed novelty scores for {len(novelty_scores)} nodes")
    else:
        logger.info("No cluster labels provided, skipping novelty score computation")

    log_memory_profile("after_embedding_generation")

    return embeddings, node_ids, novelty_scores
