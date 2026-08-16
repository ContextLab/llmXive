"""
Metrics module for calculating diversity scores based on Shannon Entropy.
Implements FR-001 and FR-009.
"""
import numpy as np
import pandas as pd
from typing import List, Union, Dict, Optional
from collections import Counter
from scipy.special import softmax
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import logging

logger = logging.getLogger(__name__)

def shannon_entropy(proportions: Union[List[float], np.ndarray], base: int = 2) -> float:
    """
    Calculate Shannon entropy of a probability distribution.
    
    Args:
        proportions: List or array of probabilities (must sum to 1).
        base: Logarithm base (default 2 for bits).
    
    Returns:
        Entropy value.
    
    Raises:
        ValueError: If proportions do not sum to 1 or contain negatives.
    """
    probs = np.array(probes, dtype=float) if isinstance(proportions, list) else proportions
    if np.any(probs < 0):
        raise ValueError("Probabilities cannot be negative.")
    
    # Normalize to ensure sum is 1 (handling floating point errors)
    total = np.sum(probs)
    if total == 0:
        return 0.0
    probs = probs / total
    
    # Filter out zero probabilities to avoid log(0)
    probs = probs[probs > 0]
    
    entropy = -np.sum(probs * np.log(probs) / np.log(base))
    return float(entropy)

def calculate_diversity_score(categories: List[str], category_embeddings: Optional[Dict[str, np.ndarray]] = None, 
                              threshold: float = 0.05, merge: bool = False) -> float:
    """
    Calculate diversity score for a list of categories.
    
    If merge=True and embeddings are provided, merges semantically similar categories
    before calculating entropy (FR-009).
    
    Args:
        categories: List of category strings.
        category_embeddings: Dict mapping category string to embedding vector (optional).
        threshold: Similarity threshold for merging (only used if merge=True).
        merge: Whether to merge similar categories.
    
    Returns:
        Shannon entropy of the category distribution.
    """
    if not categories:
        return 0.0
    
    working_categories = categories
    
    if merge and category_embeddings:
        working_categories = merge_similar_categories(categories, category_embeddings, threshold)
    
    counts = Counter(working_categories)
    total = len(working_categories)
    proportions = [count / total for count in counts.values()]
    
    return shannon_entropy(proportions, base=2)

def merge_similar_categories(categories: List[str], category_embeddings: Dict[str, np.ndarray], 
                             threshold: float = 0.05) -> List[str]:
    """
    Merge categories that are semantically similar based on cosine similarity.
    
    This implements FR-009: Category Merging Logic.
    Categories with cosine similarity >= threshold are merged into a single representative
    (the first occurrence in the unique list).
    
    Args:
        categories: List of category strings (may contain duplicates).
        category_embeddings: Dict mapping category string to embedding vector (numpy array).
        threshold: Cosine similarity threshold. Values >= threshold are merged.
    
    Returns:
        List of categories with similar ones merged to the first occurrence.
    """
    if not categories or not category_embeddings:
        return categories
    
    # Preserve order and remove duplicates for the similarity calculation
    # dict.fromkeys preserves insertion order in Python 3.7+
    unique_cats = list(dict.fromkeys(categories))
    
    if len(unique_cats) <= 1:
        return categories
    
    # Filter to categories that actually have embeddings
    valid_cats = []
    embeds = []
    for cat in unique_cats:
        if cat in category_embeddings:
            valid_cats.append(cat)
            embeds.append(category_embeddings[cat])
    
    if len(valid_cats) < 2:
        return categories
    
    # Normalize embeddings for cosine similarity (sklearn cosine_similarity does this internally 
    # but explicit normalization is safer for numerical stability)
    embeds_arr = np.array(embeds)
    if embeds_arr.shape[0] > 0:
        # Normalize rows
        norms = np.linalg.norm(embeds_arr, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1
        embeds_arr = embeds_arr / norms
    
    sim_matrix = cosine_similarity(embeds_arr)
    
    # Greedy merging strategy:
    # Iterate through categories in order. If a category is similar to a previous one,
    # map it to that previous one.
    merged_map = {cat: cat for cat in unique_cats}
    processed = set()
    
    for i, cat_i in enumerate(valid_cats):
        if cat_i in processed:
            continue
        
        # Check against all subsequent categories
        for j, cat_j in enumerate(valid_cats):
            if i == j:
                continue
            if cat_j in processed:
                continue
            
            # Only check upper triangle (i < j) to merge j into i
            if i < j:
                similarity = sim_matrix[i, j]
                if similarity >= threshold:
                    logger.debug(f"Merging '{cat_j}' into '{cat_i}' (similarity: {similarity:.4f})")
                    merged_map[cat_j] = cat_i
                    processed.add(cat_j)
        
        processed.add(cat_i)
    
    # Apply mapping to the original list (preserving duplicates and order)
    return [merged_map[cat] for cat in categories]