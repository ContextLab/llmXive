"""
Ablation utilities for token counting and semantic similarity.

Implements CPU-safe semantic similarity using TF-IDF and cosine similarity
as required by FR-003 (7GB RAM limit).
"""
import logging
from typing import Optional, List, Union

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer

from src.utils.config import get_config

logger = logging.getLogger(__name__)

_tokenizer: Optional[AutoTokenizer] = None

def get_target_tokenizer() -> AutoTokenizer:
    """
    Load the tokenizer for the base model defined in config.
    
    Returns:
        AutoTokenizer: The configured tokenizer.
        
    Raises:
        ValueError: If the tokenizer cannot be loaded.
    """
    global _tokenizer
    if _tokenizer is None:
        config = get_config()
        model_id = config.BASE_MODEL_ID
        if not model_id:
            raise ValueError("BASE_MODEL_ID is not configured in config.py")
        
        logger.info(f"Loading tokenizer for model: {model_id}")
        try:
            _tokenizer = AutoTokenizer.from_pretrained(model_id)
            # Ensure padding side is right for consistent processing
            if _tokenizer.pad_token is None:
                _tokenizer.pad_token = _tokenizer.eos_token
        except Exception as e:
            logger.error(f"Failed to load tokenizer for {model_id}: {e}")
            raise
    return _tokenizer

def calculate_token_count(text: str) -> int:
    """
    Calculate the number of tokens in a given text using the configured tokenizer.
    
    Args:
        text: The input string to tokenize.
        
    Returns:
        int: The number of tokens.
        
    Raises:
        ValueError: If the tokenizer is not available.
    """
    if not text:
        return 0
    
    tokenizer = get_target_tokenizer()
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)

def calculate_similarity(text_a: str, text_b: str) -> float:
    """
    Calculate the cosine similarity between two texts using TF-IDF vectorization.
    
    This implementation uses scikit-learn's TfidfVectorizer and cosine_similarity
    to ensure CPU safety and compliance with FR-003 (7GB RAM limit).
    
    Args:
        text_a: The first input string.
        text_b: The second input string.
        
    Returns:
        float: The cosine similarity score between 0.0 and 1.0.
               Returns 0.0 if either text is empty or if vectorization fails.
    """
    if not text_a or not text_b:
        return 0.0
    
    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer()
        
        # Fit and transform the two texts
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        
        # Calculate cosine similarity between the two vectors
        # cosine_similarity returns a 2x2 matrix, we want the off-diagonal element
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return float(similarity_matrix[0][0])
        
    except Exception as e:
        logger.warning(f"Similarity calculation failed for texts of length {len(text_a)} and {len(text_b)}: {e}")
        return 0.0

def verify_token_match(original_text: str, placeholder_text: str, tolerance: int = 1) -> bool:
    """
    Verify that the placeholder text matches the token count of the original text.
    
    Args:
        original_text: The original text string.
        placeholder_text: The placeholder text string.
        tolerance: Acceptable difference in token count (default 1).
        
    Returns:
        bool: True if token counts match within tolerance, False otherwise.
    """
    original_count = calculate_token_count(original_text)
    placeholder_count = calculate_token_count(placeholder_text)
    
    return abs(original_count - placeholder_count) <= tolerance

def calculate_syntactic_complexity(text: str) -> float:
    """
    Calculate a simple syntactic complexity metric based on token count and length.
    
    This is a placeholder implementation that can be expanded with more
    sophisticated metrics (e.g., dependency tree depth, clause count).
    
    Args:
        text: The input text.
        
    Returns:
        float: A complexity score (higher = more complex).
    """
    if not text:
        return 0.0
    
    token_count = calculate_token_count(text)
    char_count = len(text)
    
    # Simple heuristic: weighted combination of token count and average token length
    avg_token_length = char_count / token_count if token_count > 0 else 0
    complexity = (token_count * 0.7) + (avg_token_length * 0.3)
    
    return complexity

def main():
    """Main entry point for standalone testing."""
    print("Testing ablation utilities...")
    
    # Test token counting
    test_text = "This is a test sentence."
    count = calculate_token_count(test_text)
    print(f"Token count for '{test_text}': {count}")
    assert count > 0, "Token count should be positive"
    
    # Test similarity
    text_a = "The cat sat on the mat."
    text_b = "The dog sat on the rug."
    text_c = "The cat sat on the mat."
    
    sim_same = calculate_similarity(text_a, text_c)
    sim_diff = calculate_similarity(text_a, text_b)
    
    print(f"Similarity (same): {sim_same}")
    print(f"Similarity (diff): {sim_diff}")
    assert 0 <= sim_same <= 1, "Similarity should be between 0 and 1"
    assert 0 <= sim_diff <= 1, "Similarity should be between 0 and 1"
    assert sim_same >= sim_diff, "Identical texts should have higher similarity"
    
    print("All tests passed.")

if __name__ == "__main__":
    main()