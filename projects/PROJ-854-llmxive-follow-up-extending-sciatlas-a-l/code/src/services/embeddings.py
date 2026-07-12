import logging
import os
import time
import gc
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

def load_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Load the sentence transformer model.
    """
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    return model

def filter_valid_nodes(
    nodes: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Filter out nodes with missing/empty titles.
    Returns (valid_nodes, excluded_ids).
    """
    valid = []
    excluded = []
    for node in nodes:
        title = node.get('title', '')
        if title and isinstance(title, str) and len(title.strip()) > 0:
            valid.append(node)
        else:
            excluded.append(node.get('id', 'unknown'))
    return valid, excluded

def save_excluded_nodes(excluded_ids: List[str], path: str):
    """
    Save excluded node IDs to a CSV file.
    """
    df = pd.DataFrame({'id': excluded_ids})
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(excluded_ids)} excluded nodes to {path}")

def generate_embeddings_batched(
    model, 
    texts: List[str], 
    batch_size: int = 32
) -> np.ndarray:
    """
    Generate embeddings in batches to manage memory.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.append(embeddings)
        gc.collect()
    return np.vstack(all_embeddings)

def process_nodes_for_embeddings(
    nodes: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], np.ndarray, List[str]]:
    """
    Process nodes: filter valid, generate embeddings.
    """
    valid_nodes, excluded_ids = filter_valid_nodes(nodes)
    if not valid_nodes:
        return [], np.array([]), excluded_ids
    
    texts = [node['title'] for node in valid_nodes]
    model = load_embedding_model()
    embeddings = generate_embeddings_batched(model, texts)
    
    for i, node in enumerate(valid_nodes):
        node['embedding_vector'] = embeddings[i]
    
    return valid_nodes, embeddings, excluded_ids

def compute_novelty_scores(
    embeddings: np.ndarray, 
    clusters: List[int]
) -> List[float]:
    """
    Compute novelty score as cosine distance to cluster centroid.
    """
    if len(embeddings) == 0:
        return []
    
    unique_clusters = np.unique(clusters)
    centroids = {}
    for c in unique_clusters:
        mask = np.array(clusters) == c
        centroids[c] = np.mean(embeddings[mask], axis=0)
    
    scores = []
    for i, emb in enumerate(embeddings):
        c = clusters[i]
        centroid = centroids[c]
        # Cosine distance
        norm_emb = np.linalg.norm(emb)
        norm_cent = np.linalg.norm(centroid)
        if norm_emb == 0 or norm_cent == 0:
            scores.append(0.0)
        else:
            cos_sim = np.dot(emb, centroid) / (norm_emb * norm_cent)
            cos_dist = 1 - cos_sim
            scores.append(float(cos_dist))
    
    return scores

def log_memory_profile():
    """
    Log memory usage.
    """
    try:
        from memory_profiler import memory_usage
        mem = memory_usage(process=False, interval=1, timeout=1)
        logger.info(f"Current memory usage: {max(mem):.2f} MB")
    except ImportError:
        pass
