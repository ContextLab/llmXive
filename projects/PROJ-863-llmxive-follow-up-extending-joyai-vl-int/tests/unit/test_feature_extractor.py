"""
Unit tests for the feature extraction module, specifically focusing on
edge cases such as dimension mismatches.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.feature_extraction.extractor import FeatureExtractor
from src.utils.validation import ValidationError


class TestFeatureExtractorDimensionMismatch:
    """
    Tests verifying that the FeatureExtractor handles dimension mismatches
    gracefully by raising a clear ValueError.
    """

    @pytest.fixture
    def mock_model(self):
        """Mock a JoyAI-VL-Interaction model with specific hidden state dimensions."""
        mock_model = MagicMock()
        # Simulate a model where hidden_size is 768
        mock_model.config.hidden_size = 768
        mock_model.config.num_attention_heads = 12
        mock_model.config.max_position_embeddings = 512
        
        # Mock the forward pass to return hidden states of expected shape
        mock_hidden_states = MagicMock()
        # Shape: (batch_size, sequence_length, hidden_size)
        mock_hidden_states.last_hidden_state = torch.randn(1, 10, 768) 
        mock_hidden_states.attention_mask = torch.ones(1, 10)
        
        mock_model.return_value = mock_hidden_states
        return mock_model

    @pytest.fixture
    def extractor(self, mock_model):
        """Create an extractor instance with the mock model."""
        # Expected dimension based on mock model config
        expected_dim = 768
        return FeatureExtractor(model=mock_model, expected_feature_dim=expected_dim)

    def test_graceful_failure_on_dimension_mismatch(self, extractor):
        """
        Verify that a ValueError is raised with a clear message containing
        'Expected: X, Actual: Y' when the extracted feature dimension
        does not match the expected schema.
        """
        # Simulate a scenario where the model returns a different dimension
        # than what the extractor expects (e.g., model changed, config mismatch)
        
        # We need to mock the internal extraction logic to return a mismatched shape
        # The extractor usually validates dimensions after extraction.
        # Let's simulate the extraction of a feature vector that is wrong size.
        
        # Create a fake feature vector with WRONG dimension (e.g., 512 instead of 768)
        wrong_dimension_vector = np.random.rand(512)
        
        # The extractor's _extract_single_frame or similar method should catch this.
        # Since we are testing the validation logic, we can directly test the validation
        # helper or the path that calls it.
        
        # Let's assume the extractor has a method validate_dimensions or similar
        # or the error is raised during the extraction loop.
        
        # Simulate the internal state that would trigger the error
        with pytest.raises(ValueError) as excinfo:
            # Directly call a method that validates dimensions if it exists,
            # or simulate the extraction flow that leads to it.
            # For this test, we'll mock the internal _get_hidden_state to return wrong size
            # and ensure the public method raises.
            
            # Mock the internal retrieval to return a vector of size 512
            original_extract = extractor._extract_features_internal
            
            def mock_extract_internal(frame_data):
                # Return a vector of wrong size
                return np.random.rand(512) 
            
            extractor._extract_features_internal = mock_extract_internal
            
            try:
                extractor.process_frame({"frame_id": "test_001", "data": "dummy"})
            finally:
                # Restore
                extractor._extract_features_internal = original_extract
        
        # Verify the exception message contains the required format
        error_message = str(excinfo.value)
        assert "Expected: 768" in error_message
        assert "Actual: 512" in error_message
        assert "Dimension mismatch" in error_message or "mismatch" in error_message.lower()

    def test_dimension_match_success(self, extractor, mock_model):
        """
        Verify that extraction succeeds when dimensions match.
        """
        # Mock the internal extraction to return correct size
        def mock_extract_correct(frame_data):
            return np.random.rand(768)
        
        original_extract = extractor._extract_features_internal
        extractor._extract_features_internal = mock_extract_correct
        
        try:
            result = extractor.process_frame({"frame_id": "test_001", "data": "dummy"})
            assert result is not None
            assert result.shape[0] == 768
        finally:
            extractor._extract_features_internal = original_extract

    def test_error_message_clarity(self, extractor):
        """
        Ensure the error message is user-friendly and actionable.
        """
        wrong_dimension_vector = np.random.rand(1024)
        
        def mock_extract_wrong(frame_data):
            return wrong_dimension_vector
        
        original_extract = extractor._extract_features_internal
        extractor._extract_features_internal = mock_extract_wrong
        
        try:
            with pytest.raises(ValueError) as excinfo:
                extractor.process_frame({"frame_id": "test_001", "data": "dummy"})
            
            msg = str(excinfo.value)
            # Check for specific keywords required by T023/T020 spec
            assert "Expected" in msg
            assert "Actual" in msg
            assert "768" in msg
            assert "1024" in msg
        finally:
            extractor._extract_features_internal = original_extract


# Helper to import torch if needed for mock, though numpy is used for feature vectors
try:
    import torch
except ImportError:
    torch = None

# Note: This test file assumes the existence of src.feature_extraction.extractor.FeatureExtractor
# and its internal structure. If the implementation changes, this test must be updated to
# reflect the actual entry point for validation.
# The core requirement is that a ValueError is raised with the specific format:
# "Expected: X, Actual: Y" on dimension mismatch.