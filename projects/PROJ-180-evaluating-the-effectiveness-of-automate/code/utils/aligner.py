import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model cache
_embedding_model = None

def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Get or create the embedding model.
    Uses all-MiniLM-L6-v2 as specified in the project requirements.
    
    Args:
        model_name: Name of the sentence-transformers model to use
    
    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model
    
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")
    
    return _embedding_model

def compute_embeddings(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    """
    Compute embeddings for a list of texts.
    
    Args:
        model: SentenceTransformer model instance
        texts: List of text strings to embed
    
    Returns:
        numpy array of embeddings with shape (n_texts, embedding_dim)
    """
    if not texts:
        return np.array([])
    
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings

def cosine_similarity_matrix(embeddings_a: np.ndarray, embeddings_b: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity matrix between two sets of embeddings.
    
    Args:
        embeddings_a: First set of embeddings (n_a, dim)
        embeddings_b: Second set of embeddings (n_b, dim)
    
    Returns:
        Similarity matrix of shape (n_a, n_b)
    """
    if embeddings_a.size == 0 or embeddings_b.size == 0:
        return np.array([])
    
    # Normalize embeddings
    norm_a = np.linalg.norm(embeddings_a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(embeddings_b, axis=1, keepdims=True)
    
    # Avoid division by zero
    norm_a = np.where(norm_a == 0, 1, norm_a)
    norm_b = np.where(norm_b == 0, 1, norm_b)
    
    normalized_a = embeddings_a / norm_a
    normalized_b = embeddings_b / norm_b
    
    # Compute cosine similarity
    similarity_matrix = np.dot(normalized_a, normalized_b.T)
    
    return similarity_matrix

def find_best_matches(similarities: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
    """
    Find the top-k best matches for a set of similarities.
    
    Args:
        similarities: 1D array of similarity scores
        top_k: Number of top matches to return
    
    Returns:
        List of (index, score) tuples for top matches
    """
    if similarities.size == 0:
        return []
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    # Return (index, score) pairs
    return [(int(idx), float(similarities[idx])) for idx in top_indices]

def align_by_semantic_similarity(source_texts: List[str], 
                                target_texts: List[str],
                                threshold: float = 0.65,
                                model_name: str = "all-MiniLM-L6-v2") -> List[Dict[str, Any]]:
    """
    Align source texts to target texts using semantic similarity.
    
    Args:
        source_texts: List of source text strings
        target_texts: List of target text strings
        threshold: Minimum similarity threshold for a match
        model_name: Name of the sentence-transformers model
    
    Returns:
        List of alignment dictionaries with source_idx, target_idx, and similarity
    """
    logger.info(f"Aligning {len(source_texts)} source texts to {len(target_texts)} target texts")
    
    model = get_embedding_model(model_name)
    
    source_embeddings = compute_embeddings(model, source_texts)
    target_embeddings = compute_embeddings(model, target_texts)
    
    similarity_matrix = cosine_similarity_matrix(source_embeddings, target_embeddings)
    
    alignments = []
    for source_idx in range(len(source_texts)):
        similarities = similarity_matrix[source_idx]
        best_matches = find_best_matches(similarities, top_k=1)
        
        if best_matches:
            target_idx, score = best_matches[0]
            if score >= threshold:
                alignments.append({
                    'source_idx': source_idx,
                    'target_idx': target_idx,
                    'similarity': score,
                    'source_text': source_texts[source_idx][:100] + "...",
                    'target_text': target_texts[target_idx][:100] + "..."
                })
    
    logger.info(f"Found {len(alignments)} semantic alignments above threshold {threshold}")
    return alignments

def align_by_ast_diffs(source_code: str, target_code: str) -> Dict[str, Any]:
    """
    Align code snippets using AST-based diff matching.
    This is a placeholder implementation - actual AST diff logic would go here.
    
    Args:
        source_code: Source code string
        target_code: Target code string
    
    Returns:
        Alignment dictionary with match information
    """
    # Placeholder: In a real implementation, this would:
    # 1. Parse both code snippets into ASTs
    # 2. Compute the diff between ASTs
    # 3. Identify matching nodes
    # 4. Return alignment information
    
    return {
        'matched': False,
        'confidence': 0.0,
        'diff_nodes': [],
        'message': 'AST diff not implemented in this version'
    }
