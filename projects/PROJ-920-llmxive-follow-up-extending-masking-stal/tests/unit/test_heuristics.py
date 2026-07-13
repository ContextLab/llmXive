"""
Unit tests for heuristics.py utilities.
Specifically verifies technical token ratio calculation as per FR-008.
"""
import pytest
from code.utils.heuristics import calculate_technical_token_ratio, calculate_composite_density
from code.utils.entropy import calculate_shannon_entropy

# Define the technical token list as per FR-008 implementation context
# These are common technical keywords in code/search trajectories
TECHNICAL_TOKENS = {
    "def", "class", "import", "return", "if", "else", "for", "while",
    "True", "False", "None", "lambda", "try", "except", "finally",
    "with", "as", "pass", "break", "continue", "yield", "global",
    "nonlocal", "assert", "raise", "del", "in", "is", "not", "and",
    "or", "from", "async", "await"
}

def test_technical_token_ratio_empty_string():
    """Test that empty string returns 0.0 ratio."""
    text = ""
    ratio = calculate_technical_token_ratio(text)
    assert ratio == 0.0, "Ratio for empty string should be 0.0"

def test_technical_token_ratio_no_technical_tokens():
    """Test text with no technical tokens."""
    text = "this is a plain sentence with no code keywords"
    ratio = calculate_technical_token_ratio(text)
    assert ratio == 0.0, "Ratio should be 0.0 when no technical tokens exist"

def test_technical_token_ratio_all_technical():
    """Test text consisting entirely of technical tokens."""
    text = "def class import return"
    ratio = calculate_technical_token_ratio(text)
    # All 4 tokens are in the set, total 4 tokens
    assert ratio == 1.0, "Ratio should be 1.0 when all tokens are technical"

def test_technical_token_ratio_mixed():
    """Test mixed text with known ratio."""
    # 4 technical tokens, 4 plain tokens -> total 8 tokens -> ratio 0.5
    text = "def return plain sentence class import more words"
    ratio = calculate_technical_token_ratio(text)
    expected_ratio = 4 / 8
    assert ratio == expected_ratio, f"Expected {expected_ratio}, got {ratio}"

def test_technical_token_ratio_case_sensitivity():
    """Verify case sensitivity: 'Def' should not match 'def'."""
    text = "Def def"
    ratio = calculate_technical_token_ratio(text)
    # Only 'def' matches, 'Def' does not. Total 2 tokens.
    assert ratio == 0.5, "Only lowercase technical tokens should count"

def test_composite_density_with_zero_entropy():
    """Test composite density when entropy is zero (clamping logic)."""
    # A string with identical characters has 0 entropy
    text = "aaaa"
    entropy = calculate_shannon_entropy(text)
    tech_ratio = calculate_technical_token_ratio(text)
    
    # If entropy is 0, the formula 0.6*0 + 0.4*ratio should still work
    # unless the implementation explicitly clamps the final result to > 0
    density = calculate_composite_density(text)
    
    # Just verify it returns a float and doesn't crash
    assert isinstance(density, float)
    assert density >= 0.0

def test_composite_density_formula():
    """Verify the composite density formula: 0.6 * Entropy + 0.4 * TechRatio."""
    # Construct a text where we can manually verify components
    # "def def def def" -> 4 tokens, all technical. Ratio = 1.0
    # Entropy of "def def def def" (split by space)
    text = "def def def def"
    
    # Manual calculation:
    # Tokens: ['def', 'def', 'def', 'def'] -> 1 unique out of 4
    # Entropy = - (1 * log2(1)) = 0.0
    # TechRatio = 4/4 = 1.0
    # Expected Density = 0.6 * 0.0 + 0.4 * 1.0 = 0.4
    
    density = calculate_composite_density(text)
    expected = 0.6 * 0.0 + 0.4 * 1.0
    
    assert abs(density - expected) < 1e-9, f"Formula mismatch: got {density}, expected {expected}"