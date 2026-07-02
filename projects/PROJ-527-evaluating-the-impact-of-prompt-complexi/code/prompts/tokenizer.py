"""
Token counting utility using tiktoken.

This module provides functions to count tokens in prompt text using
the cl100k_base encoding (used by GPT-3.5 and GPT-4).
"""
import tiktoken
from typing import List, Tuple, Optional


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text: The text to tokenize
        encoding_name: The tiktoken encoding to use (default: cl100k_base)
        
    Returns:
        Integer count of tokens
    """
    try:
        encoder = tiktoken.get_encoding(encoding_name)
        tokens = encoder.encode(text)
        return len(tokens)
    except Exception as e:
        raise RuntimeError(f"Failed to tokenize text with tiktoken: {e}")


def validate_token_thresholds(tokens: int, label: str) -> bool:
    """
    Validate that token count falls within expected thresholds for a complexity label.
    
    Thresholds (per spec):
    - simple: ≤ 50 tokens
    - moderate: 51-150 tokens
    - complex: 151-300 tokens
    - very_complex: 301-500 tokens
    - degenerate: > 500 tokens
    
    Args:
        tokens: Token count to validate
        label: Complexity label
        
    Returns:
        True if token count is within expected range for the label
    """
    thresholds = {
        "simple": (0, 50),
        "moderate": (51, 150),
        "complex": (151, 300),
        "very_complex": (301, 500),
        "degenerate": (501, float('inf'))
    }
    
    if label not in thresholds:
        return False
    
    min_tokens, max_tokens = thresholds[label]
    return min_tokens <= tokens <= max_tokens


def get_token_breakdown(texts: List[str]) -> List[int]:
    """
    Get token counts for multiple texts.
    
    Args:
        texts: List of text strings to tokenize
        
    Returns:
        List of token counts
    """
    return [count_tokens(text) for text in texts]


def get_token_range(label: str) -> Tuple[int, int]:
    """
    Get the token range bounds for a given complexity label.
    
    Args:
        label: Complexity label
        
    Returns:
        Tuple of (min_tokens, max_tokens)
    """
    thresholds = {
        "simple": (0, 50),
        "moderate": (51, 150),
        "complex": (151, 300),
        "very_complex": (301, 500),
        "degenerate": (501, float('inf'))
    }
    return thresholds.get(label, (0, 0))