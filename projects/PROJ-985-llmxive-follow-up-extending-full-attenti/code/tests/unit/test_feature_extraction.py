import pytest
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.compute_features import compute_entropy, is_ambiguous_token, compute_kenlm_perplexity

def test_compute_entropy_uniform():
    # Uniform distribution: max entropy
    probs = [0.5, 0.5]
    entropy = compute_entropy(probs)
    assert abs(entropy - 1.0) < 0.01

def test_compute_entropy_deterministic():
    # Deterministic: entropy 0
    probs = [1.0, 0.0]
    entropy = compute_entropy(probs)
    assert entropy == 0.0

def test_is_ambiguous_token():
    assert is_ambiguous_token("!!!") == True
    assert is_ambiguous_token("hello") == False
    assert is_ambiguous_token("h3ll0") == False

def test_compute_kenlm_perplexity_empty():
    # Mock model for testing
    class MockModel:
        def score(self, text, bos=True, eos=True):
            return -1.0
    
    model = MockModel()
    pplx = compute_kenlm_perplexity(model, "")
    assert pplx == float('inf')
