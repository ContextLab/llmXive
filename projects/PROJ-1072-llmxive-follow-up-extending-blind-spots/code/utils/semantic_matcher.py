import logging
from typing import List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from .logging_config import get_logger

logger = get_logger(__name__)
_model: Optional[SentenceTransformer] = None

def encode_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Encode a list of texts into embeddings.
    
    Args:
        texts: List of strings to encode.
        model_name: Name of the sentence-transformer model.
        
    Returns:
        Numpy array of embeddings.
    """
    global _model
    if _model is None:
        logger.info(f"Loading model: {model_name}")
        _model = SentenceTransformer(model_name)
    embeddings = _model.encode(texts, convert_to_numpy=True)
    return embeddings

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec_a: First vector.
        vec_b: Second vector.
        
    Returns:
        Cosine similarity score.
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

def is_paraphrase(text_a: str, text_b: str, threshold: float = 0.75, model_name: str = "all-MiniLM-L6-v2") -> Tuple[bool, float]:
    """
    Check if two texts are paraphrases based on cosine similarity.
    
    Args:
        text_a: First text.
        text_b: Second text.
        threshold: Similarity threshold.
        model_name: Model name for encoding.
        
    Returns:
        Tuple of (is_paraphrase, similarity_score).
    """
    embeddings = encode_texts([text_a, text_b], model_name)
    sim = cosine_similarity(embeddings[0], embeddings[1])
    return sim >= threshold, sim

def batch_is_paraphrase(texts_a: List[str], texts_b: List[str], threshold: float = 0.75, model_name: str = "all-MiniLM-L6-v2") -> List[Tuple[bool, float]]:
    """
    Check paraphrase relationship for batches of texts.
    
    Args:
        texts_a: List of first texts.
        texts_b: List of second texts.
        threshold: Similarity threshold.
        model_name: Model name for encoding.
        
    Returns:
        List of (is_paraphrase, score) tuples.
    """
    if len(texts_a) != len(texts_b):
        raise ValueError("Lists must be of equal length")
    
    all_texts = texts_a + texts_b
    embeddings = encode_texts(all_texts, model_name)
    
    results = []
    for i in range(len(texts_a)):
        vec_a = embeddings[i]
        vec_b = embeddings[len(texts_a) + i]
        sim = cosine_similarity(vec_a, vec_b)
        results.append((sim >= threshold, sim))
    
    return results
