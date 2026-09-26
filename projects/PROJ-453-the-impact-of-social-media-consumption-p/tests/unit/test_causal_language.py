"""
Unit tests for causal language scanner.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils import causal_language_scanner

def test_scanner_detects_forbidden_terms():
    """Test that the scanner detects forbidden causal terms."""
    text = "This variable causes the outcome"
    forbidden = ["causes"]
    assert causal_language_scanner(text, forbidden) is True

def test_scanner_allows_associational():
    """Test that associational language is allowed."""
    text = "This variable is associated with the outcome"
    forbidden = ["causes", "leads to"]
    assert causal_language_scanner(text, forbidden) is False