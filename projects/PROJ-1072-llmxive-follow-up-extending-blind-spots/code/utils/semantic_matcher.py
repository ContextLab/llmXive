import logging
from typing import List, Optional, Tuple
import numpy as np
import torch

from sentence_transformers import SentenceTransformer

from .logging_config import get_logger

logger = get_logger(__name__)

def encode_texts(texts: List[str], model: SentenceTransformer) -> np.ndarray:
    """
    Encode a list of texts into embeddings.
    
    Args:
        texts: List of text strings to encode
        model: SentenceTransformer model instance
    
    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    if not texts:
        return np.array([])
    
    try:
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return np.array(embeddings, dtype=np.float32)
    except Exception as e:
        logger.error(f"Encoding failed: {e}")
        raise

def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding array (shape: (1, dim) or (dim,))
        embedding2: Second embedding array (shape: (1, dim) or (dim,))
    
    Returns:
        Cosine similarity score (scalar or 1x1 array)
    """
    # Ensure inputs are 2D
    if embedding1.ndim == 1:
        embedding1 = embedding1.reshape(1, -1)
    if embedding2.ndim == 1:
        embedding2 = embedding2.reshape(1, -1)
    
    # Convert to torch tensors for stable computation
    e1 = torch.from_numpy(embedding1).float()
    e2 = torch.from_numpy(embedding2).float()
    
    # Normalize
    e1_norm = torch.nn.functional.normalize(e1, p=2, dim=1)
    e2_norm = torch.nn.functional.normalize(e2, p=2, dim=1)
    
    # Compute similarity
    sim = torch.matmul(e1_norm, e2_norm.T)
    
    return sim.detach().cpu().numpy()

def is_paraphrase(text1: str, text2: str, model: SentenceTransformer, threshold: float = 0.7) -> bool:
    """
    Determine if two texts are paraphrases using semantic similarity.
    
    Args:
        text1: First text string
        text2: Second text string
        model: SentenceTransformer model instance
        threshold: Similarity threshold for paraphrase detection
    
    Returns:
        True if similarity >= threshold, False otherwise
    """
    if not text1 or not text2:
        return False
    
    try:
        embeddings = encode_texts([text1, text2], model)
        sim = cosine_similarity(embeddings[0], embeddings[1])
        similarity_score = float(sim[0][0])
        
        logger.debug(f"Similarity between texts: {similarity_score:.4f} (threshold: {threshold})")
        
        return similarity_score >= threshold
    except Exception as e:
        logger.warning(f"Paraphrase check failed: {e}")
        return False

def batch_is_paraphrase(texts1: List[str], texts2: List[str], model: SentenceTransformer, threshold: float = 0.7) -> List[bool]:
    """
    Batch check for paraphrases between two lists of texts.
    
    Args:
        texts1: List of first texts
        texts2: List of second texts
        model: SentenceTransformer model instance
        threshold: Similarity threshold
    
    Returns:
        List of booleans indicating if each pair is a paraphrase
    """
    if len(texts1) != len(texts2):
        raise ValueError("texts1 and texts2 must have the same length")
    
    results = []
    for t1, t2 in zip(texts1, texts2):
        results.append(is_paraphrase(t1, t2, model, threshold))
    
    return results