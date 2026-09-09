import numpy as np
import pandas as pd
from typing import List, Union, Dict, Optional
from collections import Counter
from scipy.special import softmax
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

def shannon_entropy(probs: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Shannon entropy (base 2) of a probability distribution.
    
    Args:
        probs: List or array of probabilities (must sum to 1)
        
    Returns:
        float: Shannon entropy in bits
    """
    probs = np.array(probs)
    # Handle edge cases
    if len(probs) == 0:
        return 0.0
    
    # Filter out zero probabilities to avoid log(0)
    probs = probs[probs > 0]
    
    if len(probs) == 0:
        return 0.0
    
    # Normalize to ensure sum is 1 (handle floating point errors)
    probs = probs / probs.sum()
    
    # Calculate entropy: -sum(p * log2(p))
    entropy = -np.sum(probs * np.log2(probs))
    return float(entropy)

def calculate_diversity_score(
    categories: Union[List[str], str, None],
    merge_threshold: float = 0.0
) -> Optional[float]:
    """
    Calculate diversity score (Shannon entropy) for a list of categories.
    
    Args:
        categories: List of category strings, or None/empty string
        merge_threshold: Threshold for semantic similarity merging (currently unused, reserved for future)
        
    Returns:
        float: Diversity score (entropy), or None if categories is empty/None
    """
    # Handle None or empty input
    if categories is None:
        return None
    
    if isinstance(categories, str):
        if categories.strip() == '':
            return None
        # If it's a string representation of a list, parse it
        try:
            # Try to parse as JSON-like list string
            import json
            categories = json.loads(categories)
        except:
            # If that fails, treat as comma-separated
            categories = [c.strip() for c in categories.split(',') if c.strip()]
    
    # Handle empty list
    if not isinstance(categories, list) or len(categories) == 0:
        return None
    
    # Count category frequencies
    counter = Counter(categories)
    total = sum(counter.values())
    
    if total == 0:
        return None
    
    # Calculate probabilities
    probs = [count / total for count in counter.values()]
    
    # Calculate Shannon entropy
    return shannon_entropy(probs)

def merge_similar_categories(
    categories: List[str],
    similarity_threshold: float = 0.8,
    embeddings: Optional[np.ndarray] = None
) -> List[str]:
    """
    Merge similar categories based on semantic similarity.
    
    Args:
        categories: List of category strings
        similarity_threshold: Minimum similarity to consider categories as same
        embeddings: Pre-computed embeddings for categories (optional)
        
    Returns:
        List[str]: Merged list of categories
    """
    if not categories or len(categories) == 0:
        return []
    
    # For now, return categories as-is since we don't have embeddings
    # This function is a placeholder for future semantic merging
    logger.debug("Semantic category merging not yet implemented - returning original categories")
    return categories

def calculate_batch_diversity_scores(
    df: pd.DataFrame,
    recommendation_col: str = "recommended_categories",
    learner_col: str = "enrolled_categories"
) -> pd.DataFrame:
    """
    Calculate diversity scores for a batch of records.
    
    Args:
        df: DataFrame with category columns
        recommendation_col: Column name for recommended categories
        learner_col: Column name for enrolled categories
        
    Returns:
        pd.DataFrame: DataFrame with added diversity score columns
    """
    result_df = df.copy()
    
    # Calculate recommendation diversity
    result_df['recommendation_diversity_score'] = result_df[recommendation_col].apply(
        lambda x: calculate_diversity_score(x)
    )
    
    # Calculate learner diversity (handles None/empty gracefully)
    result_df['learner_diversity_score'] = result_df[learner_col].apply(
        lambda x: calculate_diversity_score(x)
    )
    
    # Log statistics
    null_rec_scores = result_df['recommendation_diversity_score'].isna().sum()
    null_learner_scores = result_df['learner_diversity_score'].isna().sum()
    
    logger.info(f"Batch diversity calculation complete.")
    logger.info(f"Null recommendation scores: {null_rec_scores}")
    logger.info(f"Null learner scores: {null_learner_scores}")
    
    return result_df
