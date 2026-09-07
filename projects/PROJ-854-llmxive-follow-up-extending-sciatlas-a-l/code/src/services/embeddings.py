import logging
import os
import time
import gc
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from src.lib.config import get_config, get_path

logger = logging.getLogger(__name__)

# --- Configuration & Helpers ---

def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load the sentence-transformer model.
    Uses CPU explicitly to avoid GPU memory pressure if not requested.
    """
    logger.info(f"Loading embedding model: {model_name}")
    # Force CPU mode for reproducibility and memory safety in this pipeline
    model = SentenceTransformer(model_name, device='cpu')
    logger.info("Model loaded successfully.")
    return model

def filter_valid_nodes(nodes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter nodes that have valid, non-empty titles.
    Returns (valid_nodes, excluded_nodes).
    """
    valid = []
    excluded = []
    for node in nodes:
        title = node.get("title")
        if not title or not isinstance(title, str) or title.strip() == "":
            excluded.append({"node_id": node.get("id"), "reason": "empty_or_missing_title"})
        else:
            valid.append(node)
    return valid, excluded

def save_excluded_nodes(excluded_nodes: List[Dict[str, Any]], output_path: Optional[str] = None):
    """
    Save excluded nodes to a CSV file for logging/audit purposes.
    """
    if not output_path:
        config = get_config()
        output_path = get_path(config, "data", "logs", "excluded_nodes.csv")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df = pd.DataFrame(excluded_nodes)
    if not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} excluded nodes to {output_path}")
    else:
        logger.info("No excluded nodes to save.")

def generate_embeddings_batched(
    model: SentenceTransformer, 
    texts: List[str], 
    batch_size: int = 64
) -> np.ndarray:
    """
    Generate embeddings for a list of texts in strict batches to manage memory.
    
    Args:
        model: The loaded SentenceTransformer model.
        texts: List of text strings to embed.
        batch_size: Number of texts to process in one forward pass.
        
    Returns:
        numpy array of shape (len(texts), embedding_dim).
    """
    if not texts:
        return np.array([])
        
    all_embeddings = []
    total = len(texts)
    
    logger.info(f"Generating embeddings for {total} texts in batches of {batch_size}")
    
    for i in range(0, total, batch_size):
        batch_texts = texts[i : i + batch_size]
        start_time = time.time()
        
        # Generate embeddings for the batch
        batch_embeddings = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
        
        elapsed = time.time() - start_time
        logger.debug(f"Processed batch {i//batch_size + 1}: {len(batch_texts)} texts in {elapsed:.2f}s")
        
        all_embeddings.append(batch_embeddings)
        
        # CRITICAL: Explicitly delete the batch variable and force garbage collection
        # to release memory before the next batch.
        del batch_texts
        del batch_embeddings
        gc.collect()
    
    logger.info("Concatenating embeddings...")
    result = np.vstack(all_embeddings)
    
    # Clean up intermediate list
    del all_embeddings
    gc.collect()
    
    return result

def process_nodes_for_embeddings(
    nodes: List[Dict[str, Any]], 
    model: SentenceTransformer, 
    batch_size: int = 64
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process a list of nodes: filter valid ones, generate embeddings, and attach them.
    
    Returns:
        Tuple of (nodes_with_embeddings, excluded_nodes_list)
    """
    valid_nodes, excluded_nodes = filter_valid_nodes(nodes)
    
    if not valid_nodes:
        logger.warning("No valid nodes found for embedding generation.")
        return [], excluded_nodes
        
    titles = [node["title"] for node in valid_nodes]
    embeddings = generate_embeddings_batched(model, titles, batch_size)
    
    # Attach embeddings back to the node objects
    for i, node in enumerate(valid_nodes):
        node["embedding_vector"] = embeddings[i]
        
    return valid_nodes, excluded_nodes

def compute_cluster_centroids(embeddings: np.ndarray, cluster_labels: np.ndarray) -> np.ndarray:
    """
    Compute the centroid (mean vector) for each unique cluster label.
    """
    unique_labels = np.unique(cluster_labels)
    centroids = []
    
    for label in unique_labels:
        mask = cluster_labels == label
        cluster_embeddings = embeddings[mask]
        centroid = np.mean(cluster_embeddings, axis=0)
        centroids.append(centroid)
        
    return np.array(centroids)

def compute_novelty_scores(
    embeddings: np.ndarray, 
    cluster_labels: np.ndarray, 
    centroids: np.ndarray
) -> np.ndarray:
    """
    Compute novelty score as cosine distance to the cluster centroid.
    """
    novelty_scores = []
    
    for i, emb in enumerate(embeddings):
        label = cluster_labels[i]
        centroid = centroids[label]
        
        # Cosine similarity
        norm_emb = np.linalg.norm(emb)
        norm_cent = np.linalg.norm(centroid)
        
        if norm_emb == 0 or norm_cent == 0:
            similarity = 0.0
        else:
            similarity = np.dot(emb, centroid) / (norm_emb * norm_cent)
        
        # Cosine distance = 1 - similarity
        distance = 1.0 - similarity
        novelty_scores.append(distance)
        
    return np.array(novelty_scores)

def assign_topic_clusters_to_dataframe(
    df: pd.DataFrame, 
    model: SentenceTransformer, 
    k: int = 100, 
    batch_size: int = 64
) -> pd.DataFrame:
    """
    Main pipeline function to assign topic clusters to a dataframe.
    1. Filters nodes with valid titles.
    2. Generates embeddings in batches.
    3. Runs KMeans.
    4. Computes novelty scores.
    5. Returns the dataframe with new columns.
    """
    logger.info(f"Starting topic clustering with k={k}")
    
    # Prepare data
    valid_nodes, excluded_nodes = filter_valid_nodes(df.to_dict('records'))
    save_excluded_nodes(excluded_nodes)
    
    if not valid_nodes:
        logger.error("No valid nodes to cluster.")
        df['topic_cluster'] = None
        df['novelty_score'] = None
        return df
        
    titles = [n["title"] for n in valid_nodes]
    embeddings = generate_embeddings_batched(model, titles, batch_size)
    
    # KMeans Clustering
    logger.info("Running KMeans clustering...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(embeddings)
    
    # Compute Centroids
    centroids = compute_cluster_centroids(embeddings, cluster_labels)
    
    # Compute Novelty
    novelty_scores = compute_novelty_scores(embeddings, cluster_labels, centroids)
    
    # Map back to dataframe
    # We need to align the results with the original dataframe rows
    # Since we filtered out invalid nodes, we assume valid_nodes are a subset.
    # However, the standard flow in this project (based on T023a) suggests
    # we might be processing a clean dataframe or handling nulls later.
    # To be safe and consistent with T023a requirement (null for empty titles):
    
    result_df = df.copy()
    result_df['topic_cluster'] = np.nan
    result_df['novelty_score'] = np.nan
    
    # Create a mapping from node_id to index in valid_nodes
    # Assuming 'id' is the unique identifier
    valid_ids = {n['id']: i for i, n in enumerate(valid_nodes)}
    
    for idx, row in result_df.iterrows():
        node_id = row.get('id')
        if node_id in valid_ids:
            local_idx = valid_ids[node_id]
            result_df.at[idx, 'topic_cluster'] = cluster_labels[local_idx]
            result_df.at[idx, 'novelty_score'] = novelty_scores[local_idx]
    
    logger.info(f"Clustering complete. Assigned {k} clusters.")
    
    # Force cleanup
    del embeddings
    del kmeans
    del centroids
    del novelty_scores
    gc.collect()
    
    return result_df

def log_memory_profile(tag: str = "checkpoint"):
    """
    Log current memory usage using gc and os (basic fallback if memory_profiler not available).
    In a full environment, this would use `memory_profiler` or `psutil`.
    """
    gc.collect()
    # Simple heuristic: count live objects
    total_objects = len(gc.get_objects())
    logger.debug(f"Memory profile at {tag}: {total_objects} live objects tracked by GC")

def generate_embeddings_for_dataset(
    df: pd.DataFrame, 
    model: SentenceTransformer, 
    batch_size: int = 64
) -> pd.DataFrame:
    """
    Generate embeddings for a dataset without clustering (utility function).
    """
    valid_nodes, excluded_nodes = filter_valid_nodes(df.to_dict('records'))
    save_excluded_nodes(excluded_nodes)
    
    if not valid_nodes:
        df['embedding_vector'] = None
        return df
        
    titles = [n["title"] for n in valid_nodes]
    embeddings = generate_embeddings_batched(model, titles, batch_size)
    
    result_df = df.copy()
    result_df['embedding_vector'] = None
    
    valid_ids = {n['id']: i for i, n in enumerate(valid_nodes)}
    for idx, row in result_df.iterrows():
        node_id = row.get('id')
        if node_id in valid_ids:
            local_idx = valid_ids[node_id]
            result_df.at[idx, 'embedding_vector'] = embeddings[local_idx]
    
    del embeddings
    gc.collect()
    
    return result_df