"""
Unit tests for metrics calculation (T019, T020).
Tests AST edit distance and n-gram entropy.
"""
import pytest
import sys
from pathlib import Path

# Ensure imports work
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from analysis.metrics import (
    tokenize_code, 
    calculate_ngram_entropy, 
    calculate_pairwise_ngram_entropy,
    ast_to_graph, 
    calculate_ast_edit_distance
)

def test_tokenize_code():
    """Test that tokenize_code splits code into tokens."""
    code = "def add(a, b): return a + b"
    tokens = tokenize_code(code)
    assert len(tokens) > 0
    assert "def" in tokens
    assert "add" in tokens

def test_ngram_entropy_identical():
    """Test entropy calculation on identical text (should be 0 or low)."""
    text = "a a a a a"
    entropy = calculate_ngram_entropy(text, n=1)
    # If all tokens are the same, entropy should be 0
    assert entropy == 0.0, f"Entropy for identical tokens should be 0, got {entropy}"

def test_ngram_entropy_varied():
    """Test entropy calculation on varied text."""
    text = "a b c d e f"
    entropy = calculate_ngram_entropy(text, n=1)
    # Varied tokens should have higher entropy
    assert entropy > 0.0

def test_ast_to_graph():
    """Test that AST is converted to a graph structure."""
    code = "x = 1"
    graph = ast_to_graph(code)
    assert graph is not None
    assert len(graph.nodes()) > 0

def test_ast_edit_distance_identical():
    """Test that identical code has 0 AST edit distance (T019)."""
    code1 = "def add(a, b): return a + b"
    code2 = "def add(a, b): return a + b"
    distance = calculate_ast_edit_distance(code1, code2)
    assert distance == 0, f"Identical code should have 0 distance, got {distance}"

def test_ast_edit_distance_different():
    """Test that different code has non-zero AST edit distance."""
    code1 = "def add(a, b): return a + b"
    code2 = "def sub(a, b): return a - b"
    distance = calculate_ast_edit_distance(code1, code2)
    assert distance > 0, f"Different code should have >0 distance, got {distance}"