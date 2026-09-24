import pytest
from code_utils import causal_language_scanner

def test_scanner_detects_forbidden_terms():
    """Test that scanner detects forbidden causal terms."""
    text = "Social media causes cognitive decline."
    matches = causal_language_scanner(text)
    assert 'causes' in matches
