"""
Unit tests for the entropy generator module.

Tests cover:
- Tokenization and chain conversion
- Entropy adjustment logic
- Variant generation with convergence
- ConvergenceError handling
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from entropy.generator import (
    _tokenize_chain,
    _chain_to_string,
    _reweight_tokens,
    _adjust_entropy,
    generate_variant,
    ConvergenceError
)
from entropy.scorer import compute_shannon_entropy

class TestTokenization:
    """Test tokenization utilities."""

    def test_tokenize_chain_basic(self):
        """Test basic tokenization."""
        chain = "move left, grab object, lift up"
        tokens = _tokenize_chain(chain)
        assert len(tokens) > 0
        assert "move" in tokens
        assert "left" in tokens

    def test_tokenize_chain_empty(self):
        """Test empty chain handling."""
        assert _tokenize_chain("") == []
        assert _tokenize_chain(None) == []

    def test_chain_to_string(self):
        """Test conversion back to string."""
        tokens = ["move", "left", "grab"]
        chain = _chain_to_string(tokens)
        assert isinstance(chain, str)
        assert "move" in chain

class TestReweighting:
    """Test token reweighting logic."""

    def test_reweight_increase_entropy(self):
        """Test entropy increase with factor > 1."""
        tokens = ["a", "a", "a", "b"]
        reweighted = _reweight_tokens(tokens, 1.5)
        # Should have more variety or at least not less
        assert len(reweighted) == len(tokens)

    def test_reweight_decrease_entropy(self):
        """Test entropy decrease with factor < 1."""
        tokens = ["a", "b", "c", "d"]
        reweighted = _reweight_tokens(tokens, 0.5)
        assert len(reweighted) == len(tokens)

    def test_reweight_empty(self):
        """Test empty token list."""
        assert _reweight_tokens([], 1.0) == []

class TestEntropyAdjustment:
    """Test entropy adjustment factor calculation."""

    def test_adjust_below_target(self):
        """Test adjustment when entropy is below target range."""
        factor = _adjust_entropy(0.1, (0.3, 0.7))
        assert factor > 1.0  # Should increase entropy

    def test_adjust_above_target(self):
        """Test adjustment when entropy is above target range."""
        factor = _adjust_entropy(0.9, (0.3, 0.7))
        assert factor < 1.0  # Should decrease entropy

    def test_adjust_in_range(self):
        """Test adjustment when already in range."""
        factor = _adjust_entropy(0.5, (0.3, 0.7))
        # Should be close to 1.0 for minor adjustment
        assert 0.9 <= factor <= 1.1

class TestVariantGeneration:
    """Test full variant generation pipeline."""

    def test_generate_low_entropy(self):
        """Test generating low entropy variant."""
        base_chain = "move left, move right, move left, move right, grab, grab"
        chain, entropy, iterations = generate_variant(
            "test_case", base_chain, "low", max_iter=20
        )
        assert entropy < 0.3
        assert iterations <= 20
        assert isinstance(chain, str)
        assert len(chain) > 0

    def test_generate_medium_entropy(self):
        """Test generating medium entropy variant."""
        base_chain = "a b c d e f g h i j k l m n o p"
        chain, entropy, iterations = generate_variant(
            "test_case", base_chain, "medium", max_iter=20
        )
        assert 0.3 <= entropy <= 0.7
        assert iterations <= 20

    def test_generate_high_entropy(self):
        """Test generating high entropy variant."""
        base_chain = "a a a a a a a a"
        chain, entropy, iterations = generate_variant(
            "test_case", base_chain, "high", max_iter=20
        )
        assert entropy > 0.7
        assert iterations <= 20

    def test_invalid_variant_type(self):
        """Test error on invalid variant type."""
        with pytest.raises(Exception):
            generate_variant("test", "a b c", "invalid_type")

    def test_empty_base_chain(self):
        """Test error on empty base chain."""
        with pytest.raises(Exception):
            generate_variant("test", "", "low")

class TestConvergenceError:
    """Test ConvergenceError handling."""

    def test_convergence_error_raised(self):
        """Test that ConvergenceError is raised when max_iter exceeded."""
        # Create a pathological case that won't converge
        # Use a very restrictive max_iter to force failure
        base_chain = "a"
        
        # This should fail to converge with max_iter=1
        with pytest.raises(ConvergenceError) as exc_info:
            generate_variant("test_case", base_chain, "high", max_iter=1)
        
        assert "Failed to converge" in str(exc_info.value)
        assert "test_case" in str(exc_info.value)

    def test_convergence_error_message(self):
        """Test ConvergenceError message content."""
        base_chain = "a"
        
        try:
            generate_variant("case_123", base_chain, "high", max_iter=1)
            assert False, "Should have raised ConvergenceError"
        except ConvergenceError as e:
            error_msg = str(e)
            assert "case_123" in error_msg
            assert "high" in error_msg
            assert "Failed to converge" in error_msg

class TestIntegration:
    """Integration tests for the generator module."""

    def test_entropy_range_validity(self):
        """Test that all generated variants fall within expected ranges."""
        base_chain = "action1 action2 action3 action4 action5"
        
        variants = {}
        for vtype in ['low', 'medium', 'high']:
            chain, entropy, _ = generate_variant("test", base_chain, vtype)
            variants[vtype] = entropy
        
        assert variants['low'] < 0.3
        assert 0.3 <= variants['medium'] <= 0.7
        assert variants['high'] > 0.7

    def test_consistent_results_with_seed(self):
        """Test that results are reproducible with fixed seed."""
        import random
        random.seed(42)
        chain1, entropy1, _ = generate_variant("test", "a b c d", "medium")
        
        random.seed(42)
        chain2, entropy2, _ = generate_variant("test", "a b c d", "medium")
        
        assert chain1 == chain2
        assert abs(entropy1 - entropy2) < 1e-10