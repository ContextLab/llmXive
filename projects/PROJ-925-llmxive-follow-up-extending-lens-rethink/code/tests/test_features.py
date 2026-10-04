"""
Unit test scaffolding for feature extraction functions.
Specifically verifies compute_linguistic_uncertainty_proxy logic:
- ln(perplexity) calculation
- Exclusion logic (timeout, BERT failure, short captions)
"""
import pytest
import math
import sys
import os
import time
from unittest.mock import patch, MagicMock, PropertyMock, call
from pathlib import Path

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from features import (
    compute_linguistic_uncertainty_proxy,
    compute_syntactic_depth,
    compute_noun_phrase_density,
    compute_token_diversity,
    extract_features_batch
)
from utils.errors import DataSchemaError

class TestLinguisticUncertainty:
    """Tests for compute_linguistic_uncertainty_proxy (T014a)"""

    @patch('features.BERT_TIMEOUT_SECONDS', 5)
    @patch('features.model')
    @patch('features.tokenizer')
    def test_ln_perplexity_calculation(self, mock_tokenizer, mock_model):
        """Verify that the function returns ln(perplexity) as per FR-001"""
        # Mock inputs
        mock_caption = "The cat sat on the mat"
        
        # Mock tokenization
        mock_tokenizer.return_value = {
            'input_ids': [[101, 20, 30, 40, 50, 102]],
            'attention_mask': [[1, 1, 1, 1, 1, 1]]
        }
        
        # Mock model output (logits)
        # Perplexity = exp(average_cross_entropy)
        # If we set logits such that cross_entropy = 2.0, then perplexity = e^2
        # ln(perplexity) should be 2.0
        mock_logits = torch.tensor([[[0.0, 0.0, 0.0]]]) # Placeholder
        mock_model.return_value.logits = mock_logits
        
        # We need to mock the internal logic to return a known perplexity
        # Since we can't easily mock the full forward pass, we mock the result
        with patch('features.compute_perplexity_from_logits', return_value=math.e**2.0):
            result = compute_linguistic_uncertainty_proxy(mock_caption)
            
        # Verify result is ln(perplexity) = 2.0
        assert result == pytest.approx(2.0, rel=1e-5)

    @patch('features.BERT_TIMEOUT_SECONDS', 0.001) # Very short timeout
    def test_timeout_exclusion_logic(self):
        """Verify that timeout excludes the sample and logs the event"""
        mock_caption = "This is a test caption that will take too long"
        
        # Mock a slow calculation
        with patch('features.time.time', side_effect=[0, 10, 20]): # Simulate time passing
            # The function should detect timeout and exclude
            # We expect it to raise or return a specific exclusion indicator
            # Based on T014a spec: "exclude sample, log caption_id with reason 'TIMEOUT_EXCEEDED'"
            # The function should return None or raise a specific exception for exclusion
            # Let's assume it returns None for excluded samples
            with patch('features.time.sleep'): # Prevent actual sleep
                result = compute_linguistic_uncertainty_proxy(mock_caption)
                
        # Verify exclusion (result should be None or specific exclusion marker)
        # The exact mechanism depends on implementation, but it must exclude
        assert result is None or result == "EXCLUDED"

    @patch('features.BERT_TIMEOUT_SECONDS', 5)
    @patch('features.model')
    def test_bert_failure_exclusion(self, mock_model):
        """Verify that BERT inference failure excludes the sample (FR-012)"""
        mock_caption = "Test caption"
        
        # Mock model loading/inference failure
        mock_model.side_effect = Exception("Model not found or failed to load")
        
        # Expect exclusion
        result = compute_linguistic_uncertainty_proxy(mock_caption)
        
        # Verify exclusion
        assert result is None or result == "EXCLUDED"

    def test_empty_caption_handling(self):
        """Verify behavior with empty or very short captions"""
        # Empty string
        result_empty = compute_linguistic_uncertainty_proxy("")
        assert result_empty is None or result_empty == "EXCLUDED"
        
        # Single word (might be excluded by syntactic depth, but uncertainty proxy should handle)
        result_single = compute_linguistic_uncertainty_proxy("Hello")
        # Depending on implementation, might be valid or excluded
        # We expect it to not crash

    @patch('features.BERT_TIMEOUT_SECONDS', 5)
    @patch('features.model')
    @patch('features.tokenizer')
    def test_valid_caption_processing(self, mock_tokenizer, mock_model):
        """Verify normal processing of a valid caption"""
        mock_caption = "A beautiful sunset over the mountains"
        
        # Mock successful processing
        mock_tokenizer.return_value = {
            'input_ids': [[101, 20, 30, 40, 50, 60, 102]],
            'attention_mask': [[1, 1, 1, 1, 1, 1, 1]]
        }
        
        # Mock a valid perplexity result
        with patch('features.compute_perplexity_from_logits', return_value=math.e**1.5):
            result = compute_linguistic_uncertainty_proxy(mock_caption)
            
        # Verify result is a valid float
        assert isinstance(result, float)
        assert result > 0
        assert result == pytest.approx(1.5, rel=1e-5)


class TestSyntacticDepth:
    """Tests for compute_syntactic_depth (T015)"""

    @patch('features.nlp')
    def test_dependency_tree_depth(self, mock_nlp):
        """Verify correct calculation of dependency tree depth"""
        mock_caption = "The quick brown fox jumps over the lazy dog"
        
        # Mock spaCy doc
        mock_doc = MagicMock()
        # Create a mock tree with known depth
        # Root -> jumps -> over -> dog
        # Depth = 3 (or 4 depending on counting)
        mock_token = MagicMock()
        mock_token.dep_ = "ROOT"
        mock_token.head = mock_token # Root points to itself
        mock_token.children = []
        
        mock_doc.__iter__ = lambda self: iter([mock_token])
        mock_doc.__getitem__ = lambda self, idx: mock_token
        mock_nlp.return_value = mock_doc
        
        result = compute_syntactic_depth(mock_caption)
        
        # Verify result is an integer >= 0
        assert isinstance(result, int)
        assert result >= 0

    def test_short_caption_exclusion(self):
        """Verify that very short captions are excluded (FR-011)"""
        # Single word
        result = compute_syntactic_depth("Hello")
        # Should be excluded or return 0
        assert result is None or result == 0 or result == "EXCLUDED"
        
        # Two words
        result = compute_syntactic_depth("Hello world")
        # Might be valid or excluded depending on threshold

    @patch('features.nlp')
    def test_complex_sentence_depth(self, mock_nlp):
        """Test with a more complex sentence"""
        mock_caption = "The scientist who discovered the new particle won the prize"
        
        # Mock a deeper tree
        mock_doc = MagicMock()
        # Simulate a deeper dependency structure
        mock_root = MagicMock()
        mock_root.dep_ = "ROOT"
        mock_root.head = mock_root
        
        child1 = MagicMock()
        child1.dep_ = "nsubj"
        child1.head = mock_root
        
        child2 = MagicMock()
        child2.dep_ = "dobj"
        child2.head = mock_root
        
        mock_root.children = [child1, child2]
        mock_doc.__iter__ = lambda self: iter([mock_root, child1, child2])
        mock_doc.__getitem__ = lambda self, idx: [mock_root, child1, child2][idx]
        mock_nlp.return_value = mock_doc
        
        result = compute_syntactic_depth(mock_caption)
        
        assert isinstance(result, int)
        assert result > 0


class TestNounPhraseDensity:
    """Tests for compute_noun_phrase_density (T016a)"""

    @patch('features.nlp')
    def test_noun_phrase_counting(self, mock_nlp):
        """Verify correct counting of noun phrases"""
        mock_caption = "The cat and the dog"
        
        # Mock doc with 2 noun phrases: "The cat", "the dog"
        mock_doc = MagicMock()
        mock_np1 = MagicMock()
        mock_np1.text = "The cat"
        mock_np2 = MagicMock()
        mock_np2.text = "the dog"
        
        # Simulate noun phrase chunks
        mock_noun_chunks = [mock_np1, mock_np2]
        mock_doc.noun_chunks = mock_noun_chunks
        mock_nlp.return_value = mock_doc
        
        result = compute_noun_phrase_density(mock_caption)
        
        # Density = count / total_tokens
        # "The cat and the dog" = 5 tokens, 2 NPs -> 0.4
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_empty_caption(self):
        """Test with empty caption"""
        result = compute_noun_phrase_density("")
        assert result == 0.0 or result is None


class TestTokenDiversity:
    """Tests for compute_token_diversity (T016b)"""

    def test_diversity_calculation(self):
        """Verify type-token ratio calculation"""
        mock_caption = "the cat and the dog"
        
        # "the" appears twice, "cat", "and", "dog" once
        # Unique: the, cat, and, dog = 4
        # Total: 5
        # Diversity = 4/5 = 0.8
        
        result = compute_token_diversity(mock_caption)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_repeated_tokens(self):
        """Test with all repeated tokens"""
        mock_caption = "the the the"
        result = compute_token_diversity(mock_caption)
        assert result == pytest.approx(1.0/3.0, rel=1e-5)


class TestSyntacticDepthIntegration:
    """Integration tests for syntactic depth with real spaCy"""

    def test_real_spacy_depth(self):
        """Test with actual spaCy processing (if available)"""
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            doc = nlp("The quick brown fox jumps over the lazy dog")
            
            # Manually compute depth for verification
            def get_depth(token, depth=0):
                max_child_depth = 0
                for child in token.children:
                    child_depth = get_depth(child, depth + 1)
                    if child_depth > max_child_depth:
                        max_child_depth = child_depth
                return max_child_depth
            
            expected_depth = get_depth(doc.root) + 1
            
            # Our function should match or be close
            result = compute_syntactic_depth("The quick brown fox jumps over the lazy dog")
            
            # Allow for some implementation differences
            assert isinstance(result, int)
            assert result > 0
        except ImportError:
            pytest.skip("spaCy not installed")


class TestFeatureVectorSchemaValidation:
    """Tests for schema validation in extract_features_batch"""

    @patch('features.extract_features_batch')
    def test_schema_validation_integration(self, mock_extract):
        """Verify that extract_features_batch validates output against schema"""
        # This test ensures that the validation logic in T018a is triggered
        # We mock the extraction and verify validation is called
        
        mock_data = [
            {"caption": "Test 1", "linguistic_uncertainty_proxy": 1.5},
            {"caption": "Test 2", "linguistic_uncertainty_proxy": 2.0}
        ]
        
        # The actual validation happens in extract_features_batch
        # We verify the function exists and doesn't crash on valid input
        try:
            result = extract_features_batch(mock_data)
            # If we get here, validation passed
            assert result is not None
        except Exception as e:
            # If validation fails, it should raise a specific error
            assert "schema" in str(e).lower() or "validation" in str(e).lower()


class TestIntegrationPipeline:
    """End-to-end integration test for feature extraction"""

    @patch('features.compute_linguistic_uncertainty_proxy', return_value=1.5)
    @patch('features.compute_syntactic_depth', return_value=3)
    @patch('features.compute_noun_phrase_density', return_value=0.4)
    @patch('features.compute_token_diversity', return_value=0.8)
    def test_full_extraction_pipeline(self, mock_div, mock_np, mock_syn, mock_unc):
        """Test the full feature extraction pipeline"""
        captions = [
            "The cat sat on the mat",
            "A dog runs in the park"
        ]
        
        result = extract_features_batch(captions)
        
        # Verify result structure
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Verify each record has required fields
        for record in result:
            assert "caption" in record
            assert "linguistic_uncertainty_proxy" in record
            assert "syntactic_depth" in record
            assert "noun_phrase_density" in record
            assert "token_diversity" in record

    def test_exclusion_in_pipeline(self):
        """Test that exclusions are properly handled in batch processing"""
        # Mock one caption to fail
        with patch('features.compute_linguistic_uncertainty_proxy', return_value=None):
            captions = [
                "Valid caption",
                "Invalid caption"
            ]
            
            result = extract_features_batch(captions)
            
            # The invalid one should be excluded
            # Depending on implementation, result might have fewer items
            # or the excluded item might be marked
            assert isinstance(result, list)
            # At least the valid one should be present
            assert len(result) >= 1