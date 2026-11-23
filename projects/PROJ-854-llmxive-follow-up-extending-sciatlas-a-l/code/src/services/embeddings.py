import logging
import os
import time
import gc
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load the sentence-transformers model.
    """
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def filter_valid_nodes(df: pd.DataFrame, title_col: str = 'title') -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter out nodes with empty or null titles.
    Returns cleaned dataframe and list of excluded records with reasons.
    """
    excluded = []
    valid_mask = df[title_col].notna() & (df[title_col].str.strip() != '')
    
    for idx in df[~valid_mask].index:
        reason = "null_title" if pd.isna(df.loc[idx, title_col]) else "empty_title"
        excluded.append({
            'id': df.loc[idx, 'id'],
            'title': str(df.loc[idx, title_col]) if not pd.isna(df.loc[idx, title_col]) else None,
            'reason': reason
        })
    
    return df[valid_mask].copy(), excluded

def save_excluded_nodes(excluded: List[Dict[str, Any]], output_path: str):
    """
    Save excluded nodes to a JSON file for audit.
    """
    import json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(excluded, f, indent=2)
    logger.info(f"Saved {len(excluded)} excluded nodes to {output_path}")

def generate_embeddings_batched(model: SentenceTransformer, texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Generate embeddings in batches to manage memory.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        start_time = time.time()
        embeddings = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
        elapsed = time.time() - start_time
        logger.debug(f"Batch {i//batch_size + 1}: {len(batch)} texts processed in {elapsed:.2f}s")
        all_embeddings.append(embeddings)
        # Explicit garbage collection for large batches
        if i % (batch_size * 10) == 0:
            gc.collect()
    
    return np.vstack(all_embeddings) if all_embeddings else np.array([])

def process_nodes_for_embeddings(df: pd.DataFrame, title_col: str = 'title') -> List[str]:
    """
    Prepare titles for embedding generation.
    """
    return df[title_col].astype(str).tolist()

def compute_cluster_centroids(embeddings: np.ndarray, cluster_ids: np.ndarray) -> np.ndarray:
    """
    Compute the centroid (mean) embedding for each cluster.
    """
    unique_clusters = np.unique(cluster_ids)
    centroids = np.zeros((len(unique_clusters), embeddings.shape[1]))
    
    for i, cluster_id in enumerate(unique_clusters):
        mask = cluster_ids == cluster_id
        if np.any(mask):
            centroids[i] = embeddings[mask].mean(axis=0)
        else:
            centroids[i] = np.zeros(embeddings.shape[1])
    
    return centroids

def compute_novelty_scores(embeddings: np.ndarray, cluster_ids: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """
    Compute cosine distance between each node's embedding and its OWN cluster centroid.
    
    Logic:
    1. Calculate cosine similarity between node embedding and its cluster centroid.
    2. Convert to distance: 1 - similarity.
    3. Handle singletons: If a node is the only member of its cluster, assign 0.0.
    
    Args:
        embeddings: (N, D) array of node embeddings.
        cluster_ids: (N,) array of cluster IDs for each node.
        centroids: (K, D) array of cluster centroids, where K is number of clusters.
    
    Returns:
        (N,) array of novelty scores.
    """
    if len(embeddings) == 0:
        return np.array([])
    
    # Map cluster_id to centroid index
    unique_clusters = np.unique(cluster_ids)
    cluster_to_idx = {cid: i for i, cid in enumerate(unique_clusters)}
    
    novelty_scores = np.zeros(len(embeddings))
    
    # Normalize embeddings and centroids for cosine similarity
    # Handle potential zero-norm vectors (though unlikely with sentence transformers)
    norm_embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10)
    norm_centroids = centroids / (np.linalg.norm(centroids, axis=1, keepdims=True) + 1e-10)
    
    # Count cluster sizes to identify singletons
    unique, counts = np.unique(cluster_ids, return_counts=True)
    singleton_mask = np.isin(cluster_ids, unique[counts == 1])
    
    for i, (emb, cid) in enumerate(zip(norm_embeddings, cluster_ids)):
        if singleton_mask[i]:
            # Singleton cluster: assign 0.0 as per spec
            novelty_scores[i] = 0.0
        else:
            # Get centroid for this node's cluster
            c_idx = cluster_to_idx[cid]
            centroid = norm_centroids[c_idx]
            
            # Cosine similarity
            sim = np.dot(emb, centroid)
            # Clamp to [-1, 1] to avoid numerical errors
            sim = np.clip(sim, -1.0, 1.0)
            
            # Cosine distance
            dist = 1.0 - sim
            novelty_scores[i] = max(0.0, dist) # Ensure non-negative
    
    return novelty_scores

def assign_topic_clusters_to_dataframe(df: pd.DataFrame, embeddings: np.ndarray, k: int = 100) -> pd.DataFrame:
    """
    Perform K-Means clustering on embeddings and assign topic_cluster IDs to the dataframe.
    """
    from sklearn.cluster import KMeans
    
    logger.info(f"Performing K-Means clustering with k={k}...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(embeddings)
    
    df = df.copy()
    df['topic_cluster'] = cluster_ids
    logger.info("Topic clusters assigned.")
    return df

def compute_cluster_centroids_from_dataframe(df: pd.DataFrame, embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Helper to compute centroids given a dataframe with topic_cluster and embeddings.
    """
    cluster_ids = df['topic_cluster'].values
    centroids = compute_cluster_centroids(embeddings, cluster_ids)
    return centroids, cluster_ids

def get_cluster_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Return basic statistics about the clusters.
    """
    unique, counts = np.unique(df['topic_cluster'], return_counts=True)
    stats = {
        'num_clusters': len(unique),
        'min_cluster_size': int(counts.min()),
        'max_cluster_size': int(counts.max()),
        'avg_cluster_size': float(counts.mean()),
        'singleton_count': int(np.sum(counts == 1))
    }
    return stats

def log_memory_profile(step: str, memory_gb: float):
    """
    Log memory usage for a specific step.
    """
    logger.info(f"Memory profile for {step}: {memory_gb:.2f} GB")

def generate_embeddings_for_dataset(df: pd.DataFrame, model: SentenceTransformer, title_col: str = 'title', batch_size: int = 32) -> np.ndarray:
    """
    End-to-end function to generate embeddings for a dataset.
    """
    valid_df, excluded = filter_valid_nodes(df, title_col)
    if excluded:
        save_excluded_nodes(excluded, 'data/processed/excluded_nodes.json')
    
    if valid_df.empty:
        logger.warning("No valid nodes found for embedding generation.")
        return np.array([])
    
    texts = process_nodes_for_embeddings(valid_df, title_col)
    embeddings = generate_embeddings_batched(model, texts, batch_size)
    
    # Re-attach embeddings to valid_df if needed, or return aligned
    return embeddings

def main():
    """
    Main entry point for novelty calculation script.
    This function is intended to be called by run_novelty_calculation.py
    """
    logger.info("Starting novelty calculation pipeline...")
    
    # Load data (placeholder for actual loading logic)
    # In a real scenario, this would load from data/processed/subgraph_with_clusters.parquet
    # For now, we assume the calling script passes the dataframe and embeddings
    pass

if __name__ == "__main__":
    main()
