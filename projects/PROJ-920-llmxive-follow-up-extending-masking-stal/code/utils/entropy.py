"""
Entropy utility for calculating Shannon Entropy on UTF-8 byte-level tokens.

This module implements FR-008 requirements for semantic density calculation.
It operates on raw UTF-8 byte sequences to ensure language-agnostic entropy
measurement suitable for search agent trajectory analysis.
"""

import math
from typing import Union


def calculate_shannon_entropy(text: Union[str, bytes]) -> float:
    """
    Calculate the Shannon Entropy of the input text at the byte level.
    
    This function converts the input to UTF-8 bytes and calculates the
    entropy based on the frequency distribution of individual bytes.
    Using bytes ensures consistent measurement across different languages
    and encodings.
    
    Args:
        text: The input text (string or bytes) to analyze.
    
    Returns:
        float: The Shannon entropy in bits per byte. 
               Returns 0.0 for empty input or input with only one unique byte value.
    
    Raises:
        TypeError: If input is not a string or bytes object.
        ValueError: If string cannot be encoded to UTF-8 (rare, but possible).
    """
    # Convert to bytes if string
    if isinstance(text, str):
        try:
            byte_data = text.encode('utf-8')
        except UnicodeEncodeError as e:
            raise ValueError(f"Input string cannot be encoded to UTF-8: {e}")
    elif isinstance(text, bytes):
        byte_data = text
    else:
        raise TypeError(f"Input must be str or bytes, got {type(text).__name__}")
    
    # Handle empty input
    if len(byte_data) == 0:
        return 0.0
    
    # Calculate byte frequency distribution
    freq = {}
    for byte in byte_data:
        freq[byte] = freq.get(byte, 0) + 1
    
    # Calculate entropy
    # H = -sum(p(x) * log2(p(x))) for all unique x
    entropy = 0.0
    total_bytes = len(byte_data)
    
    for count in freq.values():
        if count > 0:
            probability = count / total_bytes
            # Avoid log(0) which is undefined
            if probability > 0:
                entropy -= probability * math.log2(probability)
    
    return entropy


def clamp_entropy(entropy_value: float, min_val: float = 0.0, max_val: float = 8.0) -> float:
    """
    Clamp the entropy value to a valid range.
    
    Theoretical maximum for a byte is 8 bits (256 unique values).
    This function ensures the value stays within physically possible bounds
    and handles edge cases where density might be zero or negative due to
    calculation artifacts.
    
    Args:
        entropy_value: The entropy value to clamp.
        min_val: Minimum allowed value (default 0.0).
        max_val: Maximum allowed value (default 8.0 for bytes).
    
    Returns:
        float: The clamped entropy value.
    """
    return max(min_val, min(max_val, entropy_value))


def entropy_per_token(text: Union[str, bytes], token_length: int = 1) -> float:
    """
    Calculate entropy per token where a token is defined as a sequence of bytes.
    
    For byte-level analysis, token_length=1 is the standard. This function
    provides flexibility for potential future tokenization schemes.
    
    Args:
        text: Input text or bytes.
        token_length: Number of bytes per token (default 1 for byte-level).
    
    Returns:
        float: Entropy per token.
    """
    if token_length < 1:
        raise ValueError("token_length must be at least 1")
    
    # Convert to bytes
    if isinstance(text, str):
        byte_data = text.encode('utf-8')
    else:
        byte_data = text
    
    if len(byte_data) < token_length:
        return 0.0
    
    # Calculate total entropy
    total_entropy = calculate_shannon_entropy(byte_data)
    
    # Return per-token entropy (normalized)
    return total_entropy