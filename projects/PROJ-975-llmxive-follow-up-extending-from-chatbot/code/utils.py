import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

_model = None

def get_model() -> SentenceTransformer:
    """
    Returns the cached SentenceTransformer model.
    Loads 'all-MiniLM-L6-v2' which is CPU-efficient.
    """
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
        # Using a model that works well on CPU and is fast
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_embedding(model: SentenceTransformer, text: str) -> np.ndarray:
    """
    Generates an embedding vector for the given text.
    """
    if not text:
        return np.zeros(384) # Default for empty string if needed
    embeddings = model.encode([text])
    return embeddings[0]

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculates cosine similarity between two vectors.
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def pairwise_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Calculates the pairwise cosine similarity matrix for a set of embeddings.
    embeddings shape: (N, D)
    Returns: (N, N) matrix
    """
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1 # Avoid division by zero
    normalized = embeddings / norms
    
    # Cosine similarity is dot product of normalized vectors
    return np.dot(normalized, normalized.T)

def mean_pairwise_similarity(embeddings: np.ndarray) -> float:
    """
    Calculates the mean of all pairwise cosine similarities (excluding diagonal).
    """
    n = embeddings.shape[0]
    if n < 2:
        return 0.0
    
    sim_matrix = pairwise_cosine_similarity_matrix(embeddings)
    
    # Mask diagonal
    mask = ~np.eye(n, dtype=bool)
    pairwise_sims = sim_matrix[mask]
    
    return float(np.mean(pairwise_sims))

def variance(values: List[float]) -> float:
    """
    Calculates the variance of a list of values.
    """
    if len(values) < 2:
        return 0.0
    mean = np.mean(values)
    return float(np.mean((np.array(values) - mean) ** 2))

def std_dev(values: List[float]) -> float:
    """
    Calculates the standard deviation of a list of values.
    """
    return float(np.sqrt(variance(values)))
