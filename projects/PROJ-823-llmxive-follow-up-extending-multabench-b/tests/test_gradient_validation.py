"""
Tests for gradient tracking validation in embedding inference.

These tests ensure that gradient tracking is properly disabled during
inference operations, preventing unnecessary memory consumption and
ensuring correct model behavior.
"""

import pytest
import torch
import torch.nn as nn
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from embeddings.validator import (
    validate_no_gradient_tracking,
    assert_no_grad_context,
    validate_embedding_generator,
    run_validation_suite
)
from embeddings.generator import EmbeddingGenerator


class TestValidateNoGradientTracking:
    """Tests for the validate_no_gradient_tracking function."""
    
    def test_model_in_training_mode_raises_error(self):
        """Test that a model in training mode raises an AssertionError."""
        model = nn.Linear(10, 5)
        model.train()  # Set to training mode
        test_input = torch.randn(1, 10)
        
        with pytest.raises(AssertionError, match="Model is in training mode"):
            validate_no_gradient_tracking(model, test_input)
    
    def test_model_in_eval_mode_passes(self):
        """Test that a model in eval mode passes validation."""
        model = nn.Linear(10, 5)
        model.eval()  # Set to evaluation mode
        test_input = torch.randn(1, 10)
        
        result = validate_no_gradient_tracking(model, test_input)
        assert result is True
    
    def test_output_with_requires_grad_raises_error(self):
        """Test that output requiring gradients raises an error."""
        # Create a model that outputs a tensor with requires_grad=True
        class BadModel(nn.Module):
            def forward(self, x):
                # Force output to require gradients
                return x + torch.ones_like(x, requires_grad=True)
        
        model = BadModel()
        model.eval()
        test_input = torch.randn(1, 10)
        
        with pytest.raises(AssertionError, match="Output tensor requires gradients"):
            validate_no_gradient_tracking(model, test_input)
    
    def test_detaches_input_with_requires_grad(self):
        """Test that input with requires_grad=True is detached."""
        model = nn.Linear(10, 5)
        model.eval()
        test_input = torch.randn(1, 10, requires_grad=True)
        
        # This should not raise an error, but detach the input
        with patch('embeddings.validator.log_warning') as mock_log:
            result = validate_no_gradient_tracking(model, test_input)
            assert result is True
            mock_log.assert_called_once()
    
    def test_parameters_with_accumulated_gradients_raise_error(self):
        """Test that parameters with accumulated gradients raise an error."""
        model = nn.Linear(10, 5)
        model.eval()
        # Simulate accumulated gradients
        for param in model.parameters():
            param.grad = torch.randn_like(param)
        
        test_input = torch.randn(1, 10)
        
        with pytest.raises(AssertionError, match="has accumulated gradients"):
            validate_no_gradient_tracking(model, test_input)
    
    def test_no_grad_context_is_used(self):
        """Test that the function properly uses torch.no_grad context."""
        model = nn.Linear(10, 5)
        model.eval()
        test_input = torch.randn(1, 10)
        
        # Verify that gradients are not computed
        with torch.enable_grad():
            result = validate_no_gradient_tracking(model, test_input)
            assert result is True
            # Check that no gradients were computed
            for param in model.parameters():
                assert param.grad is None


class TestAssertNoGradContext:
    """Tests for the assert_no_grad_context function."""
    
    def test_asserts_when_grad_enabled(self):
        """Test that assertion is raised when gradients are enabled."""
        with torch.enable_grad():
            with pytest.raises(AssertionError, match="Gradient tracking is enabled"):
                assert_no_grad_context()
    
    def test_passes_when_grad_disabled(self):
        """Test that no assertion is raised when gradients are disabled."""
        with torch.no_grad():
            # Should not raise
            assert_no_grad_context()
    
    def test_passes_outside_any_context(self):
        """Test that the function passes in default context (grad disabled by default)."""
        # Default state should have grad disabled
        assert_no_grad_context()


class TestValidateEmbeddingGenerator:
    """Tests for the validate_embedding_generator function."""
    
    def test_invalid_generator_type_raises_type_error(self):
        """Test that a non-EmbeddingGenerator raises TypeError."""
        with pytest.raises(TypeError, match="Invalid generator type"):
            validate_embedding_generator("not a generator")
    
    @patch('embeddings.generator.CLIPModel')
    @patch('embeddings.generator.SentenceTransformer')
    def test_valid_generator_passes(self, mock_clip, mock_st):
        """Test that a valid generator passes validation."""
        # Mock the models
        mock_clip.return_value = nn.Linear(10, 5)
        mock_st.return_value = nn.Linear(10, 5)
        
        generator = EmbeddingGenerator()
        generator.model.eval()
        
        result = validate_embedding_generator(generator)
        assert result is True
    
    def test_generator_in_training_mode_raises_error(self):
        """Test that a generator in training mode raises an error."""
        # Create a mock generator
        generator = Mock(spec=EmbeddingGenerator)
        generator.model = nn.Linear(10, 5)
        generator.model.train()  # Set to training mode
        
        with pytest.raises(AssertionError, match="Model is in training mode"):
            validate_embedding_generator(generator)

class TestRunValidationSuite:
    """Tests for the run_validation_suite function."""
    
    @patch('embeddings.validator.validate_embedding_generator')
    @patch('embeddings.validator.assert_no_grad_context')
    def test_suite_passes_when_all_checks_pass(self, mock_assert, mock_validate):
        """Test that the suite returns passed status when all checks pass."""
        mock_assert.return_value = None
        mock_validate.return_value = True
        
        generator = Mock(spec=EmbeddingGenerator)
        results = run_validation_suite(generator)
        
        assert results['status'] == 'passed'
        assert len(results['errors']) == 0
        assert len(results['details']) == 2
    
    @patch('embeddings.validator.validate_embedding_generator')
    @patch('embeddings.validator.assert_no_grad_context')
    def test_suite_fails_when_context_check_fails(self, mock_assert, mock_validate):
        """Test that the suite returns failed status when context check fails."""
        mock_assert.side_effect = AssertionError("Context failed")
        mock_validate.return_value = True
        
        generator = Mock(spec=EmbeddingGenerator)
        results = run_validation_suite(generator)
        
        assert results['status'] == 'failed'
        assert len(results['errors']) == 1
        assert "Context check" in results['errors'][0]
    
    @patch('embeddings.validator.validate_embedding_generator')
    @patch('embeddings.validator.assert_no_grad_context')
    def test_suite_fails_when_generator_validation_fails(self, mock_assert, mock_validate):
        """Test that the suite returns failed status when generator validation fails."""
        mock_assert.return_value = None
        mock_validate.side_effect = AssertionError("Generator failed")
        
        generator = Mock(spec=EmbeddingGenerator)
        results = run_validation_suite(generator)
        
        assert results['status'] == 'failed'
        assert len(results['errors']) == 1
        assert "Generator validation" in results['errors'][0]
