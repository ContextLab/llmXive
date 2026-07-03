"""
Alignment utilities for code review effectiveness evaluation.

This module provides functions for:
1. AST-based diff matching (skeleton provided in T008a)
2. CPU-optimized embedding similarity using sentence-transformers
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Default model as per task specification and project constraints (CPU-only)
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
_model_cache: Optional[Any] = None


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> Any:
    """
    Retrieve or initialize the SentenceTransformer model.
    
    Uses a global cache to avoid reloading the model on every call,
    optimizing for repeated similarity checks during alignment.
    
    Args:
        model_name: The HuggingFace model identifier. Defaults to all-MiniLM-L6-v2.
        
    Returns:
        The initialized SentenceTransformer model.
        
    Raises:
        ImportError: If sentence-transformers is not installed.
    """
    global _model_cache
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        raise ImportError(
            "sentence-transformers is required for embedding alignment. "
            "Install via: pip install sentence-transformers"
        )
    
    if _model_cache is None:
        logger.info(f"Loading embedding model: {model_name}")
        # Load on CPU explicitly as per project constraints
        _model_cache = SentenceTransformer(model_name, device="cpu")
        logger.info("Model loaded successfully.")
    
    return _model_cache


def compute_embeddings(
    texts: List[str], 
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = 32
) -> np.ndarray:
    """
    Compute embeddings for a list of text strings.
    
    Args:
        texts: List of text strings to embed (e.g., code snippets, comments).
        model_name: The model to use for embeddings.
        batch_size: Number of texts to process in a single batch.
        
    Returns:
        A numpy array of shape (len(texts), embedding_dim).
        
    Raises:
        ImportError: If sentence-transformers is not installed.
    """
    if not texts:
        return np.array([])
    
    model = get_embedding_model(model_name)
    embeddings = model.encode(
        texts, 
        batch_size=batch_size, 
        show_progress_bar=False,
        convert_to_numpy=True
    )
    return embeddings


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute the cosine similarity matrix for a set of embeddings.
    
    Args:
        embeddings: Array of shape (n_samples, embedding_dim).
        
    Returns:
        Array of shape (n_samples, n_samples) containing pairwise cosine similarities.
    """
    if embeddings.size == 0:
        return np.array([])
    
    # Normalize embeddings to unit length for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero
    norms = np.where(norms == 0, 1, norms)
    normalized = embeddings / norms
    
    # Matrix multiplication gives cosine similarity
    similarity = np.dot(normalized, normalized.T)
    
    # Clip to [-1, 1] to handle floating point errors
    return np.clip(similarity, -1.0, 1.0)


def find_best_matches(
    query_texts: List[str],
    candidate_texts: List[str],
    threshold: float = 0.5,
    top_k: int = 1
) -> List[List[Tuple[int, float]]]:
    """
    Find the best matching candidates for each query text based on embedding similarity.
    
    This function computes embeddings for both queries and candidates, calculates
    the similarity matrix, and returns the top-k matches above a threshold.
    
    Args:
        query_texts: List of query strings (e.g., tool issues descriptions).
        candidate_texts: List of candidate strings (e.g., human annotations).
        threshold: Minimum similarity score to consider a match valid.
        top_k: Number of top matches to return per query.
        
    Returns:
        A list of lists of tuples (candidate_index, similarity_score).
        Each inner list corresponds to a query and contains its best matches.
        
    Raises:
        ImportError: If sentence-transformers is not installed.
    """
    if not query_texts or not candidate_texts:
        return [[] for _ in query_texts]
    
    # Compute embeddings
    query_emb = compute_embeddings(query_texts)
    candidate_emb = compute_embeddings(candidate_texts)
    
    # Compute similarity matrix (Queries x Candidates)
    # Normalize both
    q_norms = np.linalg.norm(query_emb, axis=1, keepdims=True)
    q_norms = np.where(q_norms == 0, 1, q_norms)
    q_norm = query_emb / q_norms
    
    c_norms = np.linalg.norm(candidate_emb, axis=1, keepdims=True)
    c_norms = np.where(c_norms == 0, 1, c_norms)
    c_norm = candidate_emb / c_norms
    
    similarity_matrix = np.dot(q_norm, c_norm.T)
    
    results = []
    for i, row in enumerate(similarity_matrix):
        # Get indices sorted by similarity descending
        sorted_indices = np.argsort(row)[::-1]
        
        matches = []
        for idx in sorted_indices:
            score = row[idx]
            if score >= threshold:
                matches.append((int(idx), float(score)))
                if len(matches) >= top_k:
                    break
        results.append(matches)
        
    return results


def align_by_semantic_similarity(
    tool_issues: List[Dict[str, Any]],
    ground_truth_items: List[Dict[str, Any]],
    text_key: str = "description",
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Align tool issues with ground truth items using semantic similarity.
    
    This is the CPU-optimized interface required by T008b. It extracts text
    descriptions from the input dictionaries, computes embeddings, and returns
    alignment pairs where similarity exceeds the threshold.
    
    Args:
        tool_issues: List of dicts representing tool issues (must contain text_key).
        ground_truth_items: List of dicts representing ground truth (must contain text_key).
        text_key: The key in the dicts containing the text to embed.
        threshold: Similarity threshold for a valid alignment.
        
    Returns:
        List of alignment records containing tool_id, ground_truth_id, and score.
    """
    if not tool_issues or not ground_truth_items:
        return []
    
    # Extract texts
    query_texts = [item.get(text_key, "") for item in tool_issues]
    candidate_texts = [item.get(text_key, "") for item in ground_truth_items]
    
    # Filter empty texts to avoid embedding errors
    valid_query_indices = [i for i, t in enumerate(query_texts) if t.strip()]
    valid_candidate_indices = [i for i, t in enumerate(candidate_texts) if t.strip()]
    
    if not valid_query_indices or not valid_candidate_indices:
        logger.warning("No valid text content found for alignment.")
        return []
    
    # Compute embeddings only for valid items
    valid_query_texts = [query_texts[i] for i in valid_query_indices]
    valid_candidate_texts = [candidate_texts[i] for i in valid_candidate_indices]
    
    query_emb = compute_embeddings(valid_query_texts)
    candidate_emb = compute_embeddings(valid_candidate_texts)
    
    # Similarity matrix
    q_norms = np.linalg.norm(query_emb, axis=1, keepdims=True)
    q_norms = np.where(q_norms == 0, 1, q_norms)
    q_norm = query_emb / q_norms
    
    c_norms = np.linalg.norm(candidate_emb, axis=1, keepdims=True)
    c_norms = np.where(c_norms == 0, 1, c_norms)
    c_norm = candidate_emb / c_norms
    
    similarity_matrix = np.dot(q_norm, c_norm.T)
    
    alignments = []
    for i, q_idx in enumerate(valid_query_indices):
        for j, c_idx in enumerate(valid_candidate_indices):
            score = float(similarity_matrix[i, j])
            if score >= threshold:
                alignments.append({
                    "tool_issue_index": q_idx,
                    "tool_issue_id": tool_issues[q_idx].get("id", q_idx),
                    "ground_truth_index": c_idx,
                    "ground_truth_id": ground_truth_items[c_idx].get("id", c_idx),
                    "similarity_score": score
                })
    
    logger.info(f"Generated {len(alignments)} semantic alignments above threshold {threshold}.")
    return alignments


# Placeholder for AST alignment (implemented in T008a)
def align_by_ast_diffs(tool_issues: List[Dict], ground_truth_items: List[Dict]) -> List[Dict]:
    """
    Placeholder for AST-based alignment logic.
    
    This function is a stub to satisfy the interface requirement for T008a.
    The actual implementation of AST parsing and diff matching belongs in T008a.
    """
    # This is intentionally a stub as per task separation.
    # T008a will implement the real logic here.
    return []