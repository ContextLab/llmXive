"""
Ablation utilities for token counting and similarity analysis.

This module provides utilities for calculating token counts and semantic
similarity, specifically designed to support the ablation study in FR-007.
All utilities rely on the base model configuration defined in config.py.
"""

import logging
from typing import Optional, List

from transformers import AutoTokenizer
from src.utils.config import get_config

logger = logging.getLogger(__name__)

# Global cache for the tokenizer to avoid reloading on every call
_tokenizer_cache: Optional[AutoTokenizer] = None


def get_target_tokenizer() -> AutoTokenizer:
    """
    Retrieves the tokenizer for the base model defined in configuration.

    Returns:
        AutoTokenizer: The tokenizer instance for the configured base model.

    Raises:
        ValueError: If the base model ID is not configured or the tokenizer cannot be loaded.
    """
    global _tokenizer_cache

    if _tokenizer_cache is not None:
        return _tokenizer_cache

    config = get_config()
    base_model_id = config.get('BASE_MODEL_ID')

    if not base_model_id:
        raise ValueError(
            "BASE_MODEL_ID is not configured. Please set it in your environment "
            "or configuration file before using token counting utilities."
        )

    try:
        logger.info(f"Loading tokenizer for base model: {base_model_id}")
        _tokenizer_cache = AutoTokenizer.from_pretrained(base_model_id)
        
        # Ensure pad_token is set if not already
        if _tokenizer_cache.pad_token is None:
            _tokenizer_cache.pad_token = _tokenizer_cache.eos_token
        
        return _tokenizer_cache
    except Exception as e:
        logger.error(f"Failed to load tokenizer for {base_model_id}: {e}")
        raise


def calculate_token_count(text: str) -> int:
    """
    Calculates the number of tokens in a given text using the configured base model tokenizer.

    This function is critical for the ablation study (FR-007) to ensure that
    neutral placeholders match the token length of original critiques.

    Args:
        text (str): The input text to tokenize.

    Returns:
        int: The total number of tokens in the text.

    Example:
        >>> count = calculate_token_count("Hello world")
        >>> assert count > 0
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text)}")

    if not text.strip():
        return 0

    tokenizer = get_target_tokenizer()
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)


def calculate_similarity(text_a: str, text_b: str) -> float:
    """
    Calculates the cosine similarity between two texts using TF-IDF vectorization.

    This utility uses scikit-learn's TfidfVectorizer to ensure CPU safety
    and compliance with the 7GB RAM limit (FR-003). It is used in the
    negative selection logic of T014 to compare critiques against candidate answers.

    Args:
        text_a (str): The first input text.
        text_b (str): The second input text.

    Returns:
        float: The cosine similarity score between 0.0 and 1.0.

    Note:
        If either text is empty, returns 0.0.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        raise ImportError(
            "scikit-learn is required for similarity calculations. "
            "Please install it via 'pip install scikit-learn'."
        )

    if not text_a.strip() or not text_b.strip():
        return 0.0

    try:
        vectorizer = TfidfVectorizer()
        # Fit and transform on both texts to ensure a shared vocabulary
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        
        # Calculate cosine similarity between the two vectors
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return float(similarity_matrix[0][0])
    except Exception as e:
        logger.warning(f"Similarity calculation failed: {e}")
        return 0.0


def verify_token_match(original_text: str, placeholder_text: str, tolerance: int = 1) -> bool:
    """
    Verifies that the placeholder text matches the token count of the original text.

    Args:
        original_text (str): The original text (e.g., a critique).
        placeholder_text (str): The generated placeholder text.
        tolerance (int): Allowed difference in token count (default 1).

    Returns:
        bool: True if the token counts match within the tolerance, False otherwise.
    """
    original_count = calculate_token_count(original_text)
    placeholder_count = calculate_token_count(placeholder_text)
    
    return abs(original_count - placeholder_count) <= tolerance


def main():
    """
    Main entry point for testing the ablation utilities.
    """
    import sys
    import os
    
    # Add project root to path if running as script
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("Testing ablation_utils...")
    
    # Test 1: Token count
    test_text = "This is a test sentence for token counting."
    count = calculate_token_count(test_text)
    print(f"Token count for '{test_text}': {count}")
    assert count > 0, "Token count should be greater than 0"
    
    # Test 2: Similarity
    sim = calculate_similarity("The cat sat on the mat", "The cat sat on the mat")
    print(f"Self-similarity: {sim}")
    assert 0.9 <= sim <= 1.0, "Self-similarity should be close to 1.0"
    
    sim_diff = calculate_similarity("The cat sat on the mat", "The dog ran on the grass")
    print(f"Different text similarity: {sim_diff}")
    
    # Test 3: Token match verification
    is_match = verify_token_match(test_text, test_text)
    print(f"Token match verification: {is_match}")
    assert is_match, "Identical texts should match"
    
    print("All tests passed.")


if __name__ == "__main__":
    main()