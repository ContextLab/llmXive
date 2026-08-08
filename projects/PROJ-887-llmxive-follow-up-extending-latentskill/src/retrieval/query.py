"""
Query module for LatentSkill retrieval.

This module handles the generation of query vectors from text descriptions
using the all-MiniLM-L6-v2 model and manages logging for retrieval latency
and similarity scores as required by SC-003.
"""

import logging
import time
from typing import List, Dict, Any, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from ..utils.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Global cache for the model to avoid reloading
_model_cache: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """
    Retrieve or initialize the SentenceTransformer model.
    Uses a singleton pattern to ensure the model is loaded only once.
    """
    global _model_cache
    if _model_cache is None:
        logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
        start_time = time.perf_counter()
        _model_cache = SentenceTransformer("all-MiniLM-L6-v2")
        load_duration = time.perf_counter() - start_time
        logger.info(f"Model loaded in {load_duration:.4f} seconds")
    return _model_cache


def generate_query_vector(
    query_text: str,
    model: SentenceTransformer | None = None
) -> np.ndarray:
    """
    Generate a query vector from a text description.

    Args:
        query_text: The text description of the task.
        model: Optional pre-loaded model instance.

    Returns:
        A normalized numpy array representing the query embedding.
    """
    if model is None:
        model = get_model()

    start_time = time.perf_counter()
    # Generate embedding
    embedding = model.encode(query_text, convert_to_numpy=True)
    end_time = time.perf_counter()

    latency_ms = (end_time - start_time) * 1000
    logger.info(f"Text-to-vector latency for query '{query_text[:20]}...': {latency_ms:.2f} ms")

    # Ensure L2 normalization for cosine similarity consistency
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    else:
        logger.warning("Generated zero vector for query, returning normalized zeros.")
        # Return a zero vector of the expected dimension (384 for MiniLM)
        embedding = np.zeros_like(embedding)

    return embedding


def query_skill_database(
    query_text: str,
    skill_vectors: np.ndarray,
    skill_metadata: List[Dict[str, Any]],
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Query the skill database to find the most similar skill vectors.

    This function calculates cosine similarity between the query vector
    and all vectors in the database, logs the top similarity scores,
    and returns the top-k matches with their metadata and scores.

    Args:
        query_text: The text description of the target task.
        skill_vectors: A 2D numpy array of shape (N, D) containing flattened, normalized skill vectors.
        skill_metadata: A list of dictionaries containing metadata for each skill vector.
        top_k: The number of top matches to return.

    Returns:
        A list of dictionaries containing metadata and similarity scores for the top-k matches.
    """
    if skill_vectors.shape[0] == 0:
        logger.warning("Skill database is empty.")
        return []

    # Generate query vector
    query_vector = generate_query_vector(query_text)

    # Calculate cosine similarities (dot product since vectors are normalized)
    # shape: (D,) @ (N, D).T -> (N,)
    similarities = np.dot(skill_vectors, query_vector)

    # Get indices of top_k matches
    # Use argpartition for efficiency if N is very large, but sort for exact top_k if N is moderate
    if len(similarities) > top_k * 10:
        top_indices = np.argpartition(similarities, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
    else:
        top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    logger.info(f"Retrieved top {len(top_indices)} matches for query '{query_text[:20]}...'")

    for idx in top_indices:
        score = float(similarities[idx])
        metadata = skill_metadata[idx].copy()
        metadata['similarity_score'] = score
        results.append(metadata)

        # Log individual similarity scores as required by SC-003
        logger.info(f"Match: {metadata.get('skill_name', 'Unknown')} | "
                    f"Source: {metadata.get('source', 'Unknown')} | "
                    f"Similarity: {score:.6f}")

    return results


def batch_query_skill_database(
    query_texts: List[str],
    skill_vectors: np.ndarray,
    skill_metadata: List[Dict[str, Any]],
    top_k: int = 3
) -> List[List[Dict[str, Any]]]:
    """
    Process multiple queries against the skill database.

    Args:
        query_texts: A list of text descriptions.
        skill_vectors: A 2D numpy array of skill vectors.
        skill_metadata: A list of metadata dictionaries.
        top_k: The number of top matches to return per query.

    Returns:
        A list of result lists, one for each query.
    """
    total_start = time.perf_counter()
    all_results = []

    for i, text in enumerate(query_texts):
        logger.info(f"Processing batch query {i+1}/{len(query_texts)}")
        results = query_skill_database(text, skill_vectors, skill_metadata, top_k)
        all_results.append(results)

    total_duration = time.perf_counter() - total_start
    logger.info(f"Batch query processing complete. Total time: {total_duration:.4f} seconds")

    return all_results

def load_skill_index(index_path: str) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Load the skill index from disk.

    Args:
        index_path: Path to the .npz file containing the skill index.

    Returns:
        A tuple of (vectors, metadata_list).
    """
    logger.info(f"Loading skill index from {index_path}")
    try:
        data = np.load(index_path, allow_pickle=True)
        vectors = data['vectors']
        metadata_raw = data['metadata']
        
        # Convert metadata array to list of dicts if necessary
        if isinstance(metadata_raw, np.ndarray) and metadata_raw.dtype == object:
            metadata_list = [item.item() if hasattr(item, 'item') else item for item in metadata_raw]
        else:
            metadata_list = list(metadata_raw)
            
        logger.info(f"Loaded {len(vectors)} skill vectors")
        return vectors, metadata_list
    except FileNotFoundError:
        logger.error(f"Skill index file not found at {index_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading skill index: {e}")
        raise