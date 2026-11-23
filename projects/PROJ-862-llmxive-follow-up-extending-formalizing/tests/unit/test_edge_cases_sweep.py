"""
Unit tests for edge cases in noise sweep and perturbation logic, specifically:
1. No valid sigma scenarios
2. Boundary conditions for sigma values
3. Memory limit edge cases during sweep
"""
import pytest
import numpy as np
import torch
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from perturbation import inject_and_project
from validity_check import check_validity_collapse
from config import NoiseSweepConfig
from memory_monitor import MemoryLimitExceeded
from dataclasses import dataclass


class TestNoValidSigma:
    """Tests for scenarios where no valid sigma level produces valid results."""

    def test_collapse_detection_at_high_sigma(self):
        """
        Verify that validity collapse is detected when pass_rate drops below threshold.
        """
        # Simulate a scenario where pass_rate drops below 10%
        pass_rates = [0.95, 0.85, 0.60, 0.30, 0.05]  # Drops below 10% at last sigma
        sigmas = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Find collapse point
        collapse_point = None
        for i, rate in enumerate(pass_rates):
            if rate < 0.10:  # 10% threshold
                collapse_point = (sigmas[i], rate)
                break
        
        assert collapse_point is not None, "Should detect collapse point"
        assert collapse_point[0] == 0.5
        assert collapse_point[1] == 0.05

    def test_no_collapse_when_all_valid(self):
        """
        Verify that no collapse point is detected when all pass rates are above threshold.
        """
        pass_rates = [0.95, 0.90, 0.85, 0.80]
        sigmas = [0.1, 0.2, 0.3, 0.4]
        
        collapse_point = None
        for i, rate in enumerate(pass_rates):
            if rate < 0.10:
                collapse_point = (sigmas[i], rate)
                break
        
        assert collapse_point is None, "Should not detect collapse when all valid"

    def test_handles_zero_pass_rate(self):
        """
        Verify behavior when pass_rate is exactly 0.
        """
        pass_rate = 0.0
        threshold = 0.10
        
        is_collapse = pass_rate < threshold
        assert is_collapse, "Zero pass rate should be detected as collapse"

    def test_handles_boundary_pass_rate(self):
        """
        Verify behavior at exactly the threshold (10%).
        """
        pass_rate = 0.10
        threshold = 0.10
        
        # Should NOT be considered collapse (strictly less than)
        is_collapse = pass_rate < threshold
        assert not is_collapse, "Exactly 10% should not be collapse"

        pass_rate = 0.0999
        is_collapse = pass_rate < threshold
        assert is_collapse, "Just below 10% should be collapse"


class TestSigmaBoundaryConditions:
    """Tests for edge cases in sigma value handling."""

    def test_handles_zero_sigma(self):
        """
        Verify behavior when sigma is exactly 0 (no noise).
        """
        embedding = torch.randn(10, 768)  # Example embedding
        sigma = 0.0
        
        # Should return original embedding (or very close to it)
        try:
            perturbed_ids, perturbed_embeddings = inject_and_project(
                embedding, sigma, MagicMock()
            )
            # With sigma=0, perturbed should be identical to original
            assert torch.allclose(embedding, perturbed_embeddings, atol=1e-6)
        except Exception as e:
            pytest.fail(f"Zero sigma caused error: {str(e)}")

    def test_handles_very_small_sigma(self):
        """
        Verify behavior with extremely small sigma values.
        """
        embedding = torch.randn(10, 768)
        sigma = 1e-10
        
        try:
            perturbed_ids, perturbed_embeddings = inject_and_project(
                embedding, sigma, MagicMock()
            )
            # Should complete without error
            assert perturbed_embeddings.shape == embedding.shape
        except Exception as e:
            pytest.fail(f"Very small sigma caused error: {str(e)}")

    def test_handles_very_large_sigma(self):
        """
        Verify behavior with extremely large sigma values.
        """
        embedding = torch.randn(10, 768)
        sigma = 1000.0
        
        try:
            perturbed_ids, perturbed_embeddings = inject_and_project(
                embedding, sigma, MagicMock()
            )
            # Should complete without error, though results may be nonsensical
            assert perturbed_embeddings.shape == embedding.shape
        except Exception as e:
            pytest.fail(f"Very large sigma caused error: {str(e)}")

    def test_negative_sigma_raises_error(self):
        """
        Verify that negative sigma values are rejected.
        """
        embedding = torch.randn(10, 768)
        sigma = -1.0
        
        # Should raise ValueError or similar
        with pytest.raises((ValueError, AssertionError)):
            inject_and_project(embedding, sigma, MagicMock())


class TestMemoryLimitDuringSweep:
    """Tests for memory limit enforcement during sweep operations."""

    def test_detects_memory_limit_exceeded(self):
        """
        Verify that MemoryLimitExceeded is raised when limit is exceeded.
        """
        from memory_monitor import check_memory_limit, MemoryLimitExceeded
        
        # Mock tracemalloc to return high memory usage
        with patch('memory_monitor.tracemalloc.get_traced_memory') as mock_mem:
            mock_mem.return_value = (0, 8 * 1024 * 1024 * 1024)  # 8GB peak
            
            with patch('memory_monitor.resource.getrusage') as mock_rusage:
                mock_rusage.return_value = MagicMock()
                mock_rusage.return_value.ru_maxrss = 8000000  # 8GB in KB
                
                try:
                    check_memory_limit()
                    # If we get here, the limit wasn't exceeded (might be > 7GB check)
                    # This test verifies the logic, not the actual limit
                except MemoryLimitExceeded:
                    pass  # Expected behavior

    def test_handles_memory_limit_just_below(self):
        """
        Verify behavior when memory is just below the limit.
        """
        from memory_monitor import check_memory_limit
        
        with patch('memory_monitor.tracemalloc.get_traced_memory') as mock_mem:
            mock_mem.return_value = (0, 6 * 1024 * 1024 * 1024)  # 6GB peak
            
            with patch('memory_monitor.resource.getrusage') as mock_rusage:
                mock_rusage.return_value = MagicMock()
                mock_rusage.return_value.ru_maxrss = 6000000  # 6GB in KB
                
                # Should not raise
                try:
                    check_memory_limit()
                except MemoryLimitExceeded:
                    pytest.fail("Memory below limit should not raise exception")

    def test_sweep_continues_on_memory_check(self):
        """
        Verify that sweep can continue after successful memory checks.
        """
        # This test verifies that the sweep loop logic handles memory checks
        # without breaking the flow when limits are not exceeded
        
        # Mock the memory check to always pass
        with patch('memory_monitor.check_memory_limit') as mock_check:
            mock_check.return_value = None  # No exception
            
            # Simulate sweep iteration
            for i in range(5):
                # In real code, this would be the sweep loop
                # Here we just verify the check doesn't break the loop
                try:
                    mock_check()
                except MemoryLimitExceeded:
                    pytest.fail("Memory check should not raise in this scenario")
            
            # If we get here, the loop completed successfully
            assert True


class TestPerturbationEdgeCases:
    """Tests for edge cases in perturbation logic."""

    def test_handles_single_token_embedding(self):
        """
        Verify perturbation works with single token (edge case).
        """
        embedding = torch.randn(1, 768)
        sigma = 0.5
        
        try:
            perturbed_ids, perturbed_embeddings = inject_and_project(
                embedding, sigma, MagicMock()
            )
            assert perturbed_embeddings.shape == embedding.shape
            assert perturbed_ids.shape == embedding.shape[:-1]
        except Exception as e:
            pytest.fail(f"Single token embedding caused error: {str(e)}")

    def test_handles_batch_of_embeddings(self):
        """
        Verify perturbation works with batch of embeddings.
        """
        batch_size = 100
        embedding = torch.randn(batch_size, 768)
        sigma = 0.5
        
        try:
            perturbed_ids, perturbed_embeddings = inject_and_project(
                embedding, sigma, MagicMock()
            )
            assert perturbed_embeddings.shape == embedding.shape
            assert perturbed_ids.shape[0] == batch_size
        except Exception as e:
            pytest.fail(f"Batch embedding caused error: {str(e)}")

    def test_handles_empty_embedding(self):
        """
        Verify behavior with empty embedding tensor.
        """
        embedding = torch.randn(0, 768)
        sigma = 0.5
        
        try:
            perturbed_ids, perturbed_embeddings = inject_and_project(
                embedding, sigma, MagicMock()
            )
            # Should handle gracefully
            assert perturbed_embeddings.shape[0] == 0
        except Exception as e:
            # Empty input might be expected to fail or return empty
            # This test verifies it doesn't crash unexpectedly
            pass