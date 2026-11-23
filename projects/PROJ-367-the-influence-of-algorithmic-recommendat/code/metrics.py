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

def calculate_shannon_entropy(categories: List[str]) -> float:
    """
    Calculate Shannon entropy (base 2) for a list of categories.
    
    This function counts the frequency of each category, converts these
    frequencies to probabilities, and then calculates the Shannon entropy.
    
    Args:
        categories: List of category strings
        
    Returns:
        float: Shannon entropy in bits. Returns 0.0 if the list is empty.
    """
    if not categories:
        return 0.0
    
    # Count category frequencies
    counter = Counter(categories)
    total = sum(counter.values())
    
    if total == 0:
        return 0.0
    
    # Calculate probabilities
    probs = [count / total for count in counter.values()]
    
    # Calculate Shannon entropy using the existing shannon_entropy function
    return shannon_entropy(probs)

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
    
    This function delegates to the merger module to perform the actual merging
    using pre-trained embeddings. It ensures that diversity scores are calculated
    on merged category labels as per FR-009.
    
    Args:
        categories: List of category strings
        similarity_threshold: Minimum similarity to consider categories as same
        embeddings: Pre-computed embeddings for categories (optional, ignored if provided)
        
    Returns:
        List[str]: Merged list of categories
    """
    if not categories or len(categories) == 0:
        return []
    
    try:
        from merger import merge_similar_categories as merger_func
        # Use the merger module's function which handles embeddings internally
        return merger_func(categories, similarity_threshold=similarity_threshold)
    except ImportError:
        logger.warning("merger module not found, returning original categories")
        return categories

def calculate_batch_diversity_scores(
    df: pd.DataFrame,
    recommendation_col: str = "recommended_categories",
    learner_col: str = "enrolled_categories",
    merge_threshold: float = 0.8
) -> pd.DataFrame:
    """
    Calculate diversity scores for a batch of records.
    
    This function calculates Shannon entropy for both recommended and enrolled
    categories. It applies semantic similarity merging to category lists before
    calculating entropy to ensure consistency with FR-009.
    
    Args:
        df: DataFrame with category columns
        recommendation_col: Column name for recommended categories
        learner_col: Column name for enrolled categories
        merge_threshold: Threshold for semantic similarity merging
        
    Returns:
        pd.DataFrame: DataFrame with added diversity score columns
    """
    result_df = df.copy()
    
    # Apply merging to category lists before calculating entropy
    def get_merged_and_score(categories, col_name):
        if categories is None or (isinstance(categories, str) and categories.strip() == ''):
            return None
        
        # Parse if string
        if isinstance(categories, str):
            try:
                import json
                categories = json.loads(categories)
            except:
                categories = [c.strip() for c in categories.split(',') if c.strip()]
        
        if not isinstance(categories, list) or len(categories) == 0:
            return None
        
        # Merge similar categories
        merged = merge_similar_categories(categories, similarity_threshold=merge_threshold)
        
        # Calculate entropy on merged categories
        return calculate_shannon_entropy(merged)
    
    # Calculate recommendation diversity (on merged categories)
    result_df['recommendation_diversity_score'] = result_df[recommendation_col].apply(
        lambda x: get_merged_and_score(x, recommendation_col)
    )
    
    # Calculate learner diversity (on merged categories)
    result_df['learner_diversity_score'] = result_df[learner_col].apply(
        lambda x: get_merged_and_score(x, learner_col)
    )
    
    # Log statistics
    null_rec_scores = result_df['recommendation_diversity_score'].isna().sum()
    null_learner_scores = result_df['learner_diversity_score'].isna().sum()
    total_rows = len(result_df)
    
    logger.info(f"Batch diversity calculation complete.")
    logger.info(f"Total rows: {total_rows}")
    logger.info(f"Null recommendation scores: {null_rec_scores}")
    logger.info(f"Null learner scores: {null_learner_scores}")
    
    return result_df