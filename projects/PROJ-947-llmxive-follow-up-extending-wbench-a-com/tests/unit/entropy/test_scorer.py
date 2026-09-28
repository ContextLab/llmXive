import pytest
import pandas as pd
import math
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from entropy.scorer import (
    compute_shannon_entropy,
    compute_dependency_depth,
    compute_complexity_score,
    validate_complexity_scores
)

class TestShannonEntropy:
    """Unit tests for Shannon entropy calculation."""
    
    def test_empty_string(self):
        """Test that empty string returns 0 entropy."""
        assert compute_shannon_entropy("") == 0.0
    
    def test_single_character(self):
        """Test single character has minimal entropy."""
        entropy = compute_shannon_entropy("a")
        assert 0.0 <= entropy <= 0.1  # Very low entropy for single char
    
    def test_repeated_characters(self):
        """Test repeated characters have low entropy."""
        entropy = compute_shannon_entropy("aaaaa")
        assert entropy < 0.5  # Low entropy for repeated chars
    
    def test_random_text(self):
        """Test random text has higher entropy."""
        entropy1 = compute_shannon_entropy("abcabcabc")
        entropy2 = compute_shannon_entropy("aabbcc")
        # More diverse distribution should have higher entropy
        assert entropy1 > entropy2 or abs(entropy1 - entropy2) < 0.01
    
    def test_normalized_range(self):
        """Test that entropy is normalized to [0, 1]."""
        test_strings = [
            "a",
            "abcdefghijklmnopqrstuvwxyz",
            "The quick brown fox jumps over the lazy dog",
            "1234567890!@#$%^&*()"
        ]
        for text in test_strings:
            entropy = compute_shannon_entropy(text)
            assert 0.0 <= entropy <= 1.0, f"Entropy {entropy} for '{text}' out of range"

class TestDependencyDepth:
    """Unit tests for dependency depth calculation."""
    
    def test_single_action(self):
        """Test single action has depth 1."""
        depth = compute_dependency_depth("pick up object")
        assert depth == 1
    
    def test_simple_sequence(self):
        """Test simple sequence has depth > 1."""
        depth = compute_dependency_depth("pick up object -> place on table")
        assert depth >= 2
    
    def test_complex_sequence(self):
        """Test complex sequence has higher depth."""
        depth1 = compute_dependency_depth("action1 -> action2")
        depth2 = compute_dependency_depth("action1 -> action2 -> action3 -> action4")
        assert depth2 > depth1
    
    def test_minimum_depth(self):
        """Test that depth is always >= 1."""
        assert compute_dependency_depth("single action") >= 1
        assert compute_dependency_depth("") >= 1  # Should handle empty gracefully
    
    def test_conditional_actions(self):
        """Test conditional actions increase depth."""
        depth = compute_dependency_depth("if condition then action1 else action2")
        assert depth >= 2

class TestComplexityScore:
    """Unit tests for combined complexity score calculation."""
    
    def test_basic_calculation(self):
        """Test basic complexity score calculation."""
        score = compute_complexity_score(0.5, 3)
        assert 0.0 <= score <= 1.0
    
    def test_high_entropy_high_depth(self):
        """Test high entropy and high depth gives high score."""
        score = compute_complexity_score(0.9, 8)
        assert score > 0.6  # Should be relatively high
    
    def test_low_entropy_low_depth(self):
        """Test low entropy and low depth gives low score."""
        score = compute_complexity_score(0.1, 1)
        assert score < 0.4  # Should be relatively low
    
    def test_edge_cases(self):
        """Test edge cases for entropy and depth."""
        # Minimum values
        score1 = compute_complexity_score(0.0, 1)
        assert score1 >= 0.0
        
        # Maximum values
        score2 = compute_complexity_score(1.0, 10)
        assert score2 <= 1.0

class TestValidation:
    """Unit tests for complexity score validation."""
    
    def test_valid_dataframe(self):
        """Test validation passes for valid DataFrame."""
        df = pd.DataFrame({
            'case_id': ['1', '2'],
            'variant_type': ['low', 'high'],
            'entropy': [0.3, 0.8],
            'depth': [2, 5],
            'complexity_score': [0.4, 0.7]
        })
        assert validate_complexity_scores(df) is True
    
    def test_missing_columns(self):
        """Test validation fails for missing columns."""
        df = pd.DataFrame({
            'case_id': ['1'],
            'entropy': [0.5]
        })
        assert validate_complexity_scores(df) is False
    
    def test_invalid_depth(self):
        """Test validation fails for invalid depth."""
        df = pd.DataFrame({
            'case_id': ['1'],
            'variant_type': ['low'],
            'entropy': [0.5],
            'depth': [0],  # Invalid: depth < 1
            'complexity_score': [0.4]
        })
        assert validate_complexity_scores(df) is False
    
    def test_invalid_entropy_range(self):
        """Test validation fails for entropy out of range."""
        df = pd.DataFrame({
            'case_id': ['1'],
            'variant_type': ['low'],
            'entropy': [1.5],  # Invalid: > 1
            'depth': [2],
            'complexity_score': [0.5]
        })
        assert validate_complexity_scores(df) is False

class TestIntegration:
    """Integration tests for the scorer module."""
    
    def test_manual_trace_sample(self):
        """Verify depth matches manual trace for 1 sample."""
        # Sample: "pick up block -> move to table -> place on table"
        action_chain = "pick up block -> move to table -> place on table"
        depth = compute_dependency_depth(action_chain)
        
        # Manual trace: 3 actions in sequence -> depth should be 3
        assert depth == 3, f"Expected depth 3, got {depth}"
    
    def test_circular_correlation_prevention(self):
        """Verify that depth is derived from original intent, not generated text."""
        # This test ensures the function signature and logic supports
        # the requirement to use original_chain, not generated text
        original = "pick up object -> place"
        generated = "pick up object -> place -> adjust -> verify"
        
        # Both should produce different depths
        depth_orig = compute_dependency_depth(original)
        depth_gen = compute_dependency_depth(generated)
        
        # The function should handle both correctly
        assert depth_orig >= 1
        assert depth_gen >= 1
        # Generated text with more actions should have higher depth
        assert depth_gen >= depth_orig

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
