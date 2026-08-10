"""
Unit tests for code entropy and n-gram anomaly detection logic.
This module tests the entropy calculation and n-gram anomaly detection functions 
used to detect LLM-generated code patterns.
"""
import math
import random
import string
import pytest
from pathlib import Path
import sys
from collections import Counter

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.seeds import set_global_seed


def calculate_code_entropy(code_str: str) -> float:
    """
    Calculate the Shannon entropy of a code string based on character frequency.
    
    This is a standalone implementation for testing purposes. In the full pipeline,
    this logic might be part of a detection module, but for this unit test,
    we implement it directly to ensure the test is self-contained and verifies
    the mathematical property of entropy.
    
    Args:
        code_str: The code string to analyze.
        
    Returns:
        The Shannon entropy in bits (float).
    """
    if not code_str:
        return 0.0
    
    # Count character frequencies
    freq = {}
    for char in code_str:
        freq[char] = freq.get(char, 0) + 1
    
    total_chars = len(code_str)
    entropy = 0.0
    
    # Calculate Shannon entropy: H = -sum(p(x) * log2(p(x)))
    for count in freq.values():
        probability = count / total_chars
        if probability > 0:
            entropy -= probability * math.log2(probability)
                
    return entropy


def calculate_ngram_frequencies(text: str, n: int = 4) -> dict:
    """
    Calculate the frequency distribution of n-grams in a text.
    
    Args:
        text: The input text string.
        n: The size of the n-gram (default 4).
        
    Returns:
        Dictionary mapping n-gram strings to their frequencies.
    """
    if len(text) < n:
        return {}
    
    ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
    return dict(Counter(ngrams))


def calculate_ngram_anomaly_score(code_str: str, reference_freqs: dict = None, n: int = 4) -> float:
    """
    Calculate an anomaly score for code based on n-gram frequencies.
    
    This function detects synthetic patterns by comparing n-gram frequencies
    against expected distributions. LLM-generated code often exhibits:
    1. Unusually uniform n-gram distributions
    2. Over-representation of certain common patterns
    3. Under-representation of rare but valid patterns
    
    Args:
        code_str: The code string to analyze.
        reference_freqs: Optional reference frequency distribution. If None,
                       uses a heuristic based on typical code patterns.
        n: The size of the n-gram (default 4).
        
    Returns:
        Anomaly score (float) where higher values indicate more synthetic patterns.
        Scores > 0.5 typically indicate synthetic/LLM-generated code.
    """
    if not code_str or len(code_str) < n:
        return 0.0
    
    ngram_freqs = calculate_ngram_frequencies(code_str, n)
    
    if not ngram_freqs:
        return 0.0
    
    # Normalize frequencies
    total_ngrams = sum(ngram_freqs.values())
    normalized_freqs = {k: v/total_ngrams for k, v in ngram_freqs.items()}
    
    # Calculate entropy of n-gram distribution
    ngram_entropy = 0.0
    for prob in normalized_freqs.values():
        if prob > 0:
            ngram_entropy -= prob * math.log2(prob)
    
    # Calculate uniformity score (how close to uniform distribution)
    max_entropy = math.log2(len(normalized_freqs)) if normalized_freqs else 0
    uniformity_score = ngram_entropy / max_entropy if max_entropy > 0 else 0
    
    # Detect over-representation of common patterns
    # LLMs tend to overuse certain patterns like "if __name__ == '__main__':"
    common_patterns = [
        "if __name__",
        "print(",
        "return ",
        "def ",
        "import ",
        "from ",
    ]
    
    pattern_count = 0
    for pattern in common_patterns:
        if pattern in code_str:
            pattern_count += 1
    
    # Normalize pattern count
    pattern_score = min(pattern_count / len(common_patterns), 1.0)
    
    # Combine scores: synthetic code tends to have:
    # 1. High uniformity (very even n-gram distribution)
    # 2. High pattern score (overuse of common patterns)
    anomaly_score = 0.6 * uniformity_score + 0.4 * pattern_score
    
    return anomaly_score


def test_entropy_calculation():
    """
    Asserts code entropy calculation returns float > 0 for random code.
    
    This test verifies that:
    1. The entropy calculation function returns a float.
    2. For a truly random string (high entropy), the value is strictly positive.
    3. The value is within a reasonable range for random ASCII data.
    """
    set_global_seed(42)  # Ensure reproducibility
    
    # Generate a random code-like string with high entropy
    # Using a mix of letters, digits, and symbols to simulate random code
    length = 1000
    random_chars = ''.join(
        random.choices(
            string.ascii_letters + string.digits + string.punctuation + ' ',
            k=length
        )
    )
    
    # Calculate entropy
    entropy = calculate_code_entropy(random_chars)
    
    # Assertions
    assert isinstance(entropy, float), f"Entropy should be a float, got {type(entropy)}"
    assert entropy > 0.0, f"Entropy for random code must be > 0, got {entropy}"
    
    # Random strings should have relatively high entropy (typically > 3.0 for mixed ASCII)
    # This is a sanity check to ensure we aren't getting a trivially small value
    assert entropy > 2.0, f"Random code entropy seems too low: {entropy}"
    
    # Verify that a string with all same characters has 0 entropy
    uniform_string = "a" * 1000
    uniform_entropy = calculate_code_entropy(uniform_string)
    assert uniform_entropy == 0.0, f"Uniform string entropy should be 0, got {uniform_entropy}"
    
    # Verify that a slightly varied string has > 0 entropy
    varied_string = "ab" * 500
    varied_entropy = calculate_code_entropy(varied_string)
    assert varied_entropy > 0.0, f"Varied string entropy should be > 0, got {varied_entropy}"


def test_ngram_anomaly_score():
    """
    Asserts n-gram anomaly detection flags synthetic patterns.
    
    This test verifies that:
    1. The anomaly score function returns a float between 0 and 1.
    2. Synthetic/LLM-like code patterns receive higher anomaly scores.
    3. Natural/human-like code patterns receive lower anomaly scores.
    4. The function correctly identifies over-representation of common patterns.
    """
    set_global_seed(42)
    
    # Test 1: Synthetic pattern (overuse of common patterns, uniform structure)
    synthetic_code = """
    import os
    import sys
    import json
    
    def process_data():
        data = {}
        return data
    
    def analyze_results():
        results = []
        return results
    
    if __name__ == '__main__':
        print("Processing...")
        result = process_data()
        print(result)
    """ * 5  # Repeat to amplify pattern detection
    
    synthetic_score = calculate_ngram_anomaly_score(synthetic_code)
    
    # Assertions for synthetic code
    assert isinstance(synthetic_score, float), f"Anomaly score should be a float, got {type(synthetic_score)}"
    assert 0.0 <= synthetic_score <= 1.0, f"Anomaly score should be between 0 and 1, got {synthetic_score}"
    assert synthetic_score > 0.5, f"Synthetic code should have high anomaly score (> 0.5), got {synthetic_score}"
    
    # Test 2: Natural/human-like code (more varied, less predictable)
    natural_code = """
    # TODO: Refactor this function to handle edge cases better
    def _calculate_metrics(data_list, threshold=0.5):
        if not data_list:
            return None
        
        # Filter out invalid entries
        valid_entries = [x for x in data_list if x.get('valid', False)]
        if len(valid_entries) < 3:
            logger.warning("Insufficient data points")
            return None
        
        # Calculate weighted average
        total_weight = sum(entry['weight'] for entry in valid_entries)
        weighted_sum = sum(entry['value'] * entry['weight'] for entry in valid_entries)
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    # Note: This was added during code review on 2023-10-15
    """
    
    natural_score = calculate_ngram_anomaly_score(natural_code)
    
    # Assertions for natural code
    assert isinstance(natural_score, float), f"Anomaly score should be a float, got {type(natural_score)}"
    assert 0.0 <= natural_score <= 1.0, f"Anomaly score should be between 0 and 1, got {natural_score}"
    assert natural_score < 0.5, f"Natural code should have lower anomaly score (< 0.5), got {natural_score}"
    
    # Test 3: Verify synthetic code scores higher than natural code
    assert synthetic_score > natural_score, \
        f"Synthetic score ({synthetic_score}) should be higher than natural score ({natural_score})"
    
    # Test 4: Edge case - empty string
    empty_score = calculate_ngram_anomaly_score("")
    assert empty_score == 0.0, f"Empty string should have anomaly score of 0, got {empty_score}"
    
    # Test 5: Edge case - very short string
    short_score = calculate_ngram_anomaly_score("abc")
    assert short_score == 0.0, f"Short string (< n-gram size) should have anomaly score of 0, got {short_score}"