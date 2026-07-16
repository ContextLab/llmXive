"""
Utility functions for embeddings, similarity calculations, and statistical metrics.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global model cache
_model_cache: Optional[SentenceTransformer] = None

def get_model() -> SentenceTransformer:
    """
    Get or initialize the sentence transformer model (CPU-only).
    Uses a lightweight model suitable for CPU execution.
    """
    global _model_cache
    if _model_cache is None:
        logger.info("Loading sentence-transformer model (CPU-only)...")
        # Using 'all-MiniLM-L6-v2' for speed and low memory footprint
        _model_cache = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        logger.info("Model loaded successfully")
    return _model_cache

def get_embedding(text: str, model: Optional[SentenceTransformer] = None) -> np.ndarray:
    """
    Get embedding for a single text string.
    
    Args:
        text: Input text string
        model: Optional pre-loaded model (if None, loads default)
    
    Returns:
        Numpy array of embedding vector
    """
    if model is None:
        model = get_model()
    
    embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
    return embedding

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Cosine similarity value between -1 and 1
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def pairwise_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Calculate pairwise cosine similarity matrix for a set of embeddings.
    
    Args:
        embeddings: 2D numpy array of shape (n_samples, n_features)
    
    Returns:
        2D numpy array of shape (n_samples, n_samples) with similarity values
    """
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    
    # Calculate similarity matrix
    similarity_matrix = np.dot(normalized, normalized.T)
    
    return similarity_matrix

def mean_pairwise_similarity(embeddings: np.ndarray) -> float:
    """
    Calculate the mean of all pairwise cosine similarities (excluding diagonal).
    
    Args:
        embeddings: 2D numpy array of shape (n_samples, n_features)
    
    Returns:
        Mean pairwise similarity value
    """
    n = embeddings.shape[0]
    if n <= 1:
        return 0.0
    
    similarity_matrix = pairwise_cosine_similarity_matrix(embeddings)
    
    # Exclude diagonal (self-similarity)
    mask = ~np.eye(n, dtype=bool)
    similarities = similarity_matrix[mask]
    
    return float(np.mean(similarities))

def variance(values: List[float]) -> float:
    """
    Calculate variance of a list of values.
    
    Args:
        values: List of numerical values
    
    Returns:
        Variance value
    """
    if len(values) < 2:
        return 0.0
    
    return float(np.var(values))

def std_dev(values: List[float]) -> float:
    """
    Calculate standard deviation of a list of values.
    
    Args:
        values: List of numerical values
    
    Returns:
        Standard deviation value
    """
    if len(values) < 2:
        return 0.0
    
    return float(np.std(values))