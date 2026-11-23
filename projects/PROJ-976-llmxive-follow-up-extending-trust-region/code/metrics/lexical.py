"""
Lexical diversity metrics.
Implements distinct-n ratio and n-gram entropy calculations for text analysis.
"""
from collections import Counter
from typing import List, Dict, Any
import math

def distinct_n_ratio(tokens: List[str], n: int = 4) -> float:
    """
    Calculate the distinct-n ratio.
    distinct-n = (number of unique n-grams) / (total number of n-grams)
    
    Args:
        tokens: List of tokenized words
        n: N-gram size (default 4 for distinct-4)
        
    Returns:
        Ratio of unique n-grams to total n-grams (0.0 to 1.0)
    """
    if not tokens or len(tokens) < n:
        return 0.0

    ngrams = [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    if not ngrams:
        return 0.0
        
    unique_ngrams = set(ngrams)
    return len(unique_ngrams) / len(ngrams)

def ngram_entropy(tokens: List[str], n: int = 4) -> float:
    """
    Calculate the n-gram entropy.
    H = -sum(p(x) * log2(p(x)))
    
    Args:
        tokens: List of tokenized words
        n: N-gram size (default 4)
        
    Returns:
        Entropy value in bits
    """
    if not tokens or len(tokens) < n:
        return 0.0

    ngrams = [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    if not ngrams:
        return 0.0
        
    counts = Counter(ngrams)
    total = len(ngrams)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def compute_lexical_features(text: str) -> Dict[str, float]:
    """
    Compute lexical features for a given text.
    Tokenizes by whitespace and calculates distinct-4 ratio and n-gram entropy.
    
    Args:
        text: Raw input text string
        
    Returns:
        Dictionary with keys:
            - distinct_4_ratio: float
            - ngram_entropy: float
    """
    if not text or not text.strip():
        return {
            "distinct_4_ratio": 0.0,
            "ngram_entropy": 0.0
        }
        
    # Simple whitespace tokenization
    tokens = text.split()
    return {
        "distinct_4_ratio": distinct_n_ratio(tokens, 4),
        "ngram_entropy": ngram_entropy(tokens, 4),
    }

def main():
    """
    Demo entry point for lexical metrics.
    Processes a sample text and prints the computed features.
    """
    text = "This is a sample text. This is another sample text. Different text here."
    features = compute_lexical_features(text)
    print(f"Lexical Features: {features}")

if __name__ == "__main__":
    main()