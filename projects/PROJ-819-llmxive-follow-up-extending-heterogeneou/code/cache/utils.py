"""
Utility functions for the Semantic Cache.

Includes cosine similarity calculation, thresholding logic, and embedding generation.
"""
import numpy as np
from typing import Tuple, Optional, List
from sentence_transformers import SentenceTransformer

# Global model cache to avoid reloading the model on every call
_embedding_model = None

def get_embedding_model() -> SentenceTransformer:
    """
    Lazily loads and returns the CPU-only sentence transformer model.
    Uses a global variable to cache the loaded model.
    
    Returns:
        SentenceTransformer instance.
    """
    global _embedding_model
    if _embedding_model is None:
        # Using a lightweight, CPU-friendly model suitable for semantic search
        # 'all-MiniLM-L6-v2' is standard, fast, and accurate enough for this task.
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    return _embedding_model

def generate_embedding(text: str) -> np.ndarray:
    """
    Generates a dense vector embedding for the input text.
    
    Args:
        text: The input string to embed.
        
    Returns:
        A numpy array representing the embedding vector.
        
    Raises:
        RuntimeError: If embedding generation fails.
    """
    try:
        model = get_embedding_model()
        # encode returns a numpy array by default
        embeddings = model.encode([text], convert_to_numpy=True, show_progress_bar=False)
        return embeddings[0]
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding for text: {str(e)}")

def generate_embeddings_batch(texts: List[str]) -> List[np.ndarray]:
    """
    Generates embeddings for a list of texts in a batched manner for efficiency.
    
    Args:
        texts: A list of input strings.
        
    Returns:
        A list of numpy arrays, each representing an embedding vector.
    """
    if not texts:
        return []
    
    try:
        model = get_embedding_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb for emb in embeddings]
    except Exception as e:
        raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}")

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calculate the cosine similarity between two vectors.
    
    Args:
        vec_a: First vector (numpy array).
        vec_b: Second vector (numpy array).
        
    Returns:
        Cosine similarity score between -1.0 and 1.0. Returns 0.0 if either vector
        has zero norm to avoid division by zero.
    """
    if not isinstance(vec_a, np.ndarray):
        vec_a = np.array(vec_a)
    if not isinstance(vec_b, np.ndarray):
        vec_b = np.array(vec_b)
        
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

def threshold_check(similarity: float, threshold: float) -> bool:
    """
    Check if a similarity score meets a minimum threshold.
    
    Args:
        similarity: The calculated similarity score.
        threshold: The minimum required similarity.
        
    Returns:
        True if similarity >= threshold, False otherwise.
    """
    return similarity >= threshold
