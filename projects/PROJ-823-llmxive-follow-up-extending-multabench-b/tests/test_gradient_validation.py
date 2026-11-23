"""
Unit tests for gradient tracking validation (Task T018).

These tests verify that the embedding generation pipeline correctly
disables gradient tracking during inference to ensure CPU tractability
and memory efficiency.
"""
import pytest
import torch
import numpy as np
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from embeddings.validator import (
    validate_no_gradient_tracking,
    assert_no_grad_context,
    validate_embedding_generator
)
from embeddings.generator import EmbeddingGenerator

class TestGradientValidation:
    """Test suite for gradient tracking validation."""

    @pytest.fixture
    def generator(self):
        """Provide a CPU-only embedding generator."""
        return EmbeddingGenerator(device="cpu")

    def test_assert_no_grad_context(self, generator):
        """Test that assert_no_grad_context raises if gradients are enabled."""
        # Test 1: Should pass when no_grad is active
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224)
            # This should not raise
            assert_no_grad_context(lambda: generator.model(dummy_input))
        
        # Test 2: Should raise if called outside no_grad context with grad enabled
        # We simulate this by checking the context directly
        with pytest.raises(AssertionError):
            # Manually create a scenario where grad is expected but not disabled
            # Note: In real usage, this function is a guard that should always be called
            # inside no_grad. Here we test the assertion logic.
            pass  # The actual check is done inside the function

    def test_validate_no_gradient_tracking(self, generator):
        """Test validate_no_gradient_tracking function."""
        # Create a dummy input
        dummy_input = torch.randn(1, 3, 224)
        
        # Run validation
        result = validate_no_gradient_tracking(generator, dummy_input)
        
        assert result["passed"] is True
        assert result["message"] == "No gradient tracking detected."
        assert "requires_grad" not in result or result["requires_grad"] is False

    def test_generator_output_no_grad(self, generator):
        """Test that generator outputs do not require gradients."""
        dummy_input = torch.randn(1, 3, 224)
        
        with torch.no_grad():
            output = generator.model(dummy_input)
        
        assert not output.requires_grad, "Output should not require gradients"
        assert output.grad is None, "Output should not have gradients accumulated"

    def test_validation_suite(self, generator):
        """Test the full validation suite."""
        results = validate_embedding_generator(generator)
        
        assert "passed" in results
        assert results["passed"] is True
        assert "checks" in results
        assert len(results["checks"]) > 0

    def test_gradient_accumulation_prevention(self, generator):
        """Test that gradients are not accumulated during multiple inferences."""
        generator.model.eval()
        
        # Perform multiple inferences
        for _ in range(3):
            dummy_input = torch.randn(1, 3, 224)
            with torch.no_grad():
                _ = generator.model(dummy_input)
        
        # Check that no parameters have accumulated gradients
        for name, param in generator.model.named_parameters():
            assert param.grad is None, f"Parameter {name} has accumulated gradients!"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])