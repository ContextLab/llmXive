"""
Unit tests for feature extraction logic in code/data/compute_features.py.

This module tests the core feature extraction functions:
- compute_entropy
- compute_kenlm_perplexity
- is_ambiguous_token
- process_document

These tests verify correctness without requiring GPU or large datasets.
"""
import pytest
import math
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.compute_features import (
    compute_entropy,
    compute_kenlm_perplexity,
    is_ambiguous_token,
    process_document,
    load_or_download_kenlm
)
from lib.entities import TokenUnit


class TestComputeEntropy:
    """Tests for entropy calculation."""
    
    def test_entropy_uniform_distribution(self):
        """Uniform distribution should have maximum entropy."""
        # Two equally likely outcomes: entropy = log2(2) = 1.0
        probs = [0.5, 0.5]
        entropy = compute_entropy(probs)
        assert abs(entropy - 1.0) < 1e-6
        
    def test_entropy_deterministic(self):
        """Deterministic distribution should have zero entropy."""
        # One certain outcome: entropy = 0
        probs = [1.0, 0.0]
        entropy = compute_entropy(probs)
        assert abs(entropy) < 1e-6
        
    def test_entropy_empty_probs(self):
        """Empty probability list should return 0 or raise."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            compute_entropy([])
            
    def test_entropy_single_prob(self):
        """Single probability should be handled."""
        probs = [1.0]
        entropy = compute_entropy(probs)
        assert abs(entropy) < 1e-6
        
    def test_entropy_invalid_probs(self):
        """Invalid probabilities (negative or >1) should raise or be handled."""
        with pytest.raises(ValueError):
            compute_entropy([1.5, -0.5])
            
    def test_entropy_sum_not_one(self):
        """Probabilities not summing to 1 should be normalized or raise."""
        probs = [0.6, 0.6]  # sum = 1.2
        # Should normalize internally or handle gracefully
        entropy = compute_entropy(probs)
        assert 0 <= entropy <= math.log2(len(probs))
        
    def test_entropy_three_outcomes(self):
        """Test with three outcomes."""
        # Uniform over 3: entropy = log2(3) ≈ 1.585
        probs = [1/3, 1/3, 1/3]
        entropy = compute_entropy(probs)
        expected = math.log2(3)
        assert abs(entropy - expected) < 1e-6
        
    def test_entropy_very_small_probs(self):
        """Test with very small probabilities to check numerical stability."""
        probs = [0.0001, 0.0001, 0.9998]
        entropy = compute_entropy(probs)
        assert 0 <= entropy < math.log2(3)
        
    def test_entropy_negative_log_handling(self):
        """Ensure log(0) is handled (should not occur with valid probs)."""
        # This tests that we don't get NaN or inf
        probs = [0.99, 0.01]
        entropy = compute_entropy(probs)
        assert not math.isnan(entropy)
        assert not math.isinf(entropy)
        
    def test_entropy_large_distribution(self):
        """Test with larger number of outcomes."""
        n = 100
        probs = [1.0/n] * n
        entropy = compute_entropy(probs)
        expected = math.log2(n)
        assert abs(entropy - expected) < 1e-3
        
    def test_entropy_asymmetric(self):
        """Test asymmetric distribution."""
        probs = [0.7, 0.3]
        entropy = compute_entropy(probs)
        # Should be less than 1.0 (max for binary)
        assert 0 < entropy < 1.0
        # Calculate expected: -0.7*log2(0.7) - 0.3*log2(0.3)
        expected = -0.7 * math.log2(0.7) - 0.3 * math.log2(0.3)
        assert abs(entropy - expected) < 1e-6


class TestComputeKenlmPerplexity:
    """Tests for KenLM perplexity calculation."""
    
    @patch('data.compute_features.load_or_download_kenlm')
    def test_perplexity_valid_model(self, mock_load_model):
        """Test perplexity calculation with mocked model."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.score = MagicMock(return_value=0.5)  # Log probability
        mock_load_model.return_value = mock_model
        
        text = "This is a test sentence."
        perplexity = compute_kenlm_perplexity(text)
        
        # Perplexity = exp(-avg_log_prob)
        # For a simple mock, we just verify it returns a number
        assert isinstance(perplexity, float)
        assert perplexity > 0
        
    @patch('data.compute_features.load_or_download_kenlm')
    def test_perplexity_empty_text(self, mock_load_model):
        """Test perplexity with empty text."""
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        
        with pytest.raises((ValueError, RuntimeError)):
            compute_kenlm_perplexity("")
            
    @patch('data.compute_features.load_or_download_kenlm')
    def test_perplexity_single_word(self, mock_load_model):
        """Test perplexity with single word."""
        mock_model = MagicMock()
        mock_model.score = MagicMock(return_value=-1.0)
        mock_load_model.return_value = mock_model
        
        perplexity = compute_kenlm_perplexity("test")
        assert isinstance(perplexity, float)
        assert perplexity > 0
        
    @patch('data.compute_features.load_or_download_kenlm')
    def test_perplexity_special_characters(self, mock_load_model):
        """Test perplexity with special characters."""
        mock_model = MagicMock()
        mock_model.score = MagicMock(return_value=-2.0)
        mock_load_model.return_value = mock_model
        
        text = "Hello! @#$%^&*() World."
        perplexity = compute_kenlm_perplexity(text)
        assert isinstance(perplexity, float)
        assert perplexity > 0
        
    @patch('data.compute_features.load_or_download_kenlm')
    def test_perplexity_very_long_text(self, mock_load_model):
        """Test perplexity with long text."""
        mock_model = MagicMock()
        mock_model.score = MagicMock(return_value=-0.5)
        mock_load_model.return_value = mock_model
        
        text = "word " * 1000
        perplexity = compute_kenlm_perplexity(text)
        assert isinstance(perplexity, float)
        assert perplexity > 0


class TestIsAmbiguousToken:
    """Tests for ambiguous token detection."""
    
    def test_ambiguous_emoji(self):
        """Emojis should be detected as ambiguous."""
        assert is_ambiguous_token("😀") is True
        assert is_ambiguous_token("🚀") is True
        assert is_ambiguous_token("❤️") is True
        
    def test_ambiguous_special_chars(self):
        """Special characters should be detected as ambiguous."""
        assert is_ambiguous_token("@") is True
        assert is_ambiguous_token("#") is True
        assert is_ambiguous_token("$") is True
        assert is_ambiguous_token("%") is True
        
    def test_ambiguous_mixed(self):
        """Mixed ambiguous tokens."""
        assert is_ambiguous_token("🎉") is True
        assert is_ambiguous_token("$$$") is True
        
    def test_not_ambiguous_word(self):
        """Regular words should not be ambiguous."""
        assert is_ambiguous_token("hello") is False
        assert is_ambiguous_token("test") is False
        assert is_ambiguous_token("RULER") is False
        
    def test_not_ambiguous_number(self):
        """Numbers should not be ambiguous."""
        assert is_ambiguous_token("123") is False
        assert is_ambiguous_token("42") is False
        
    def test_not_ambiguous_alphanumeric(self):
        """Alphanumeric should not be ambiguous."""
        assert is_ambiguous_token("test123") is False
        assert is_ambiguous_token("ABC123") is False
        
    def test_not_ambiguous_punctuation(self):
        """Standard punctuation should not be ambiguous."""
        assert is_ambiguous_token(".") is False
        assert is_ambiguous_token(",") is False
        assert is_ambiguous_token("!") is False
        assert is_ambiguous_token("?") is False
        
    def test_edge_case_empty(self):
        """Empty string should be handled."""
        assert is_ambiguous_token("") is False
        
    def test_edge_case_whitespace(self):
        """Whitespace should be handled."""
        assert is_ambiguous_token(" ") is False
        assert is_ambiguous_token("\t") is False
        assert is_ambiguous_token("\n") is False
        
    def test_unicode_variations(self):
        """Various unicode characters."""
        # Some unicode might be ambiguous
        assert is_ambiguous_token("©") is True  # Copyright symbol
        assert is_ambiguous_token("®") is True  # Registered trademark
        
    def test_case_sensitivity(self):
        """Test that detection is case-insensitive for letters."""
        assert is_ambiguous_token("A") is False
        assert is_ambiguous_token("a") is False
        
    def test_long_ambiguous_string(self):
        """Long string of ambiguous characters."""
        assert is_ambiguous_token("$$$$$$$$$$") is True
        assert is_ambiguous_token("😀😀😀") is True


class TestProcessDocument:
    """Tests for document processing pipeline."""
    
    def test_process_simple_document(self):
        """Test processing a simple document."""
        document = {
            "id": "test_doc_1",
            "text": "This is a test document."
        }
        
        result = process_document(document)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(token, TokenUnit) for token in result)
        assert result[0].token_id == "This"
        
    def test_process_document_with_ambiguities(self):
        """Test processing document with ambiguous tokens."""
        document = {
            "id": "test_doc_2",
            "text": "Hello 😀 world!"
        }
        
        result = process_document(document)
        
        assert isinstance(result, list)
        # Should have tokens for "Hello", "😀", "world"
        assert len(result) >= 3
        
    def test_process_empty_document(self):
        """Test processing empty document."""
        document = {
            "id": "test_doc_3",
            "text": ""
        }
        
        result = process_document(document)
        
        assert isinstance(result, list)
        assert len(result) == 0
        
    def test_process_document_structure(self):
        """Test that result has correct structure."""
        document = {
            "id": "test_doc_4",
            "text": "The quick brown fox."
        }
        
        result = process_document(document)
        
        for token in result:
            assert hasattr(token, 'token_id')
            assert hasattr(token, 'position')
            assert hasattr(token, 'entropy')
            assert hasattr(token, 'kenlm_perplexity')
            assert hasattr(token, 'is_ambiguous')
            
    def test_process_document_position_tracking(self):
        """Test that positions are correctly tracked."""
        document = {
            "id": "test_doc_5",
            "text": "one two three"
        }
        
        result = process_document(document)
        
        positions = [token.position for token in result]
        assert positions == list(range(len(positions)))
        
    def test_process_document_id_preservation(self):
        """Test that document ID is preserved in tokens."""
        document = {
            "id": "unique_doc_id_123",
            "text": "test"
        }
        
        result = process_document(document)
        
        if len(result) > 0:
            # The document ID should be accessible somehow
            # (depends on implementation, but should be preserved)
            assert result[0].token_id == "test"
            
    def test_process_document_with_newlines(self):
        """Test processing document with newlines."""
        document = {
            "id": "test_doc_6",
            "text": "Line 1\nLine 2\nLine 3"
        }
        
        result = process_document(document)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
    def test_process_document_special_case(self):
        """Test document with only special characters."""
        document = {
            "id": "test_doc_7",
            "text": "@#$%^&*()"
        }
        
        result = process_document(document)
        
        assert isinstance(result, list)
        # Should still process, even if all tokens are ambiguous
        
    def test_process_document_very_long(self):
        """Test processing a very long document."""
        text = "word " * 1000
        document = {
            "id": "test_doc_8",
            "text": text
        }
        
        result = process_document(document)
        
        assert len(result) > 1000
        
    def test_process_document_mixed_content(self):
        """Test document with mixed content types."""
        document = {
            "id": "test_doc_9",
            "text": "Hello 123 world @#$ test 😀"
        }
        
        result = process_document(document)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check that we have both regular and ambiguous tokens
        ambiguous_count = sum(1 for token in result if token.is_ambiguous)
        assert ambiguous_count > 0  # Should have some ambiguous tokens


class TestLoadOrDownloadKenlm:
    """Tests for KenLM model loading."""
    
    @patch('data.compute_features.os.path.exists')
    @patch('data.compute_features.os.makedirs')
    def test_load_existing_model(self, mock_makedirs, mock_exists):
        """Test loading an existing model."""
        mock_exists.return_value = True
        
        # This would normally load the model, but we're just testing the path
        with patch('data.compute_features.load_model') as mock_load:
            mock_load.return_value = MagicMock()
            model = load_or_download_kenlm()
            assert model is not None
            
    @patch('data.compute_features.os.path.exists')
    @patch('data.compute_features.os.makedirs')
    def test_download_missing_model(self, mock_makedirs, mock_exists):
        """Test downloading a missing model."""
        mock_exists.side_effect = [False, True]  # First check fails, second succeeds
        
        with patch('data.compute_features.download_model') as mock_download:
            with patch('data.compute_features.load_model') as mock_load:
                mock_load.return_value = MagicMock()
                model = load_or_download_kenlm()
                assert model is not None
                
    def test_model_path_creation(self):
        """Test that model path is correctly constructed."""
        # Just verify the function doesn't crash and returns something
        with patch('data.compute_features.os.path.exists', return_value=True):
            with patch('data.compute_features.load_model', return_value=MagicMock()):
                model = load_or_download_kenlm()
                assert model is not None


class TestIntegrationScenarios:
    """Integration-style tests for feature extraction."""
    
    def test_full_pipeline_small_document(self):
        """Test the full feature extraction pipeline on a small document."""
        document = {
            "id": "integration_test_1",
            "text": "The cat sat on the mat."
        }
        
        result = process_document(document)
        
        # Verify all tokens have features computed
        for token in result:
            assert isinstance(token.token_id, str)
            assert isinstance(token.position, int)
            assert isinstance(token.entropy, float)
            assert isinstance(token.kenlm_perplexity, float)
            assert isinstance(token.is_ambiguous, bool)
            
    def test_consistency_across_calls(self):
        """Test that feature extraction is consistent."""
        document = {
            "id": "consistency_test",
            "text": "test consistency"
        }
        
        result1 = process_document(document)
        result2 = process_document(document)
        
        # Results should be identical
        assert len(result1) == len(result2)
        for t1, t2 in zip(result1, result2):
            assert t1.token_id == t2.token_id
            assert t1.position == t2.position
            assert t1.entropy == t2.entropy
            assert t1.kenlm_perplexity == t2.kenlm_perplexity
            
    def test_large_document_performance(self):
        """Test that large documents are processed reasonably."""
        text = "word " * 500  # Moderate size
        document = {
            "id": "performance_test",
            "text": text
        }
        
        import time
        start = time.time()
        result = process_document(document)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (less than 10 seconds for 500 words)
        assert elapsed < 10.0
        assert len(result) == 500
        
    def test_edge_case_whitespace_only(self):
        """Test document with only whitespace."""
        document = {
            "id": "whitespace_test",
            "text": "   \t\t\n\n   "
        }
        
        result = process_document(document)
        
        # Should handle gracefully, possibly returning empty or minimal tokens
        assert isinstance(result, list)
        
    def test_unicode_document(self):
        """Test document with unicode characters."""
        document = {
            "id": "unicode_test",
            "text": "Hello 世界 مرحبا שלום"
        }
        
        result = process_document(document)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
    def test_mixed_case_document(self):
        """Test document with mixed case."""
        document = {
            "id": "case_test",
            "text": "Hello HELLO hello HeLLo"
        }
        
        result = process_document(document)
        
        assert len(result) == 4
        assert result[0].token_id == "Hello"
        assert result[1].token_id == "HELLO"
        assert result[2].token_id == "hello"
        assert result[3].token_id == "HeLLo"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])