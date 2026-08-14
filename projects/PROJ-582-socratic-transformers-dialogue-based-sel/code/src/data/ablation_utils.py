"""
Utilities for ablation studies, specifically syntactic complexity calculation.
"""

import logging
from typing import Optional, Tuple, List
import re
from transformers import AutoTokenizer
from src.utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_target_tokenizer() -> AutoTokenizer:
    """
    Gets the tokenizer defined in the configuration.
    """
    config = get_config()
    # Use the base model tokenizer for consistency
    return AutoTokenizer.from_pretrained(config.BASE_MODEL_ID, trust_remote_code=True)

def calculate_token_length(text: str, tokenizer: Optional[AutoTokenizer] = None) -> int:
    """
    Calculates the number of tokens in a text string.

    Args:
        text: The input text.
        tokenizer: The tokenizer to use. If None, uses the default from config.

    Returns:
        The token count.
    """
    if tokenizer is None:
        tokenizer = get_target_tokenizer()
    
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)

def load_spacy_model():
    """
    Loads the spaCy model if available.
    """
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except ImportError:
        logger.warning("spaCy not installed. Falling back to regex-based tokenization.")
        return None

def calculate_ngram_entropy(text: str, n: int = 2) -> float:
    """
    Calculates the Shannon entropy of the n-gram distribution in the text.

    Args:
        text: The input text.
        n: The n-gram size (default 2).

    Returns:
        The entropy value.
    """
    import math
    from collections import Counter

    # Simple whitespace tokenization for n-grams if spaCy not available
    words = text.lower().split()
    
    if len(words) < n:
        return 0.0

    ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    total = len(ngrams)
    
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy

def calculate_syntactic_complexity(text: str) -> Dict[str, float]:
    """
    Calculates syntactic complexity metrics for a text.

    Args:
        text: The input text.

    Returns:
        A dictionary with 'token_count' and 'ngram_entropy'.
    """
    tokenizer = get_target_tokenizer()
    token_count = calculate_token_length(text, tokenizer)
    ngram_entropy = calculate_ngram_entropy(text, n=2)
    
    return {
        "token_count": token_count,
        "ngram_entropy": ngram_entropy
    }

def verify_token_match(original_text: str, placeholder_text: str) -> bool:
    """
    Verifies that the placeholder has the same token count as the original.

    Args:
        original_text: The original text.
        placeholder_text: The placeholder text.

    Returns:
        True if token counts match, False otherwise.
    """
    tokenizer = get_target_tokenizer()
    orig_len = calculate_token_length(original_text, tokenizer)
    placeholder_len = calculate_token_length(placeholder_text, tokenizer)
    return orig_len == placeholder_len

def main():
    """Test the complexity calculator."""
    test_text = "This is a test sentence for complexity analysis."
    result = calculate_syntactic_complexity(test_text)
    print(f"Complexity metrics: {result}")

if __name__ == "__main__":
    main()
