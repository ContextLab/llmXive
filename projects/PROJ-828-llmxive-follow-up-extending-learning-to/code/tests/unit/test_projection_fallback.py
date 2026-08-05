"""
test_projection_fallback.py

Unit tests for SVD fallback logic in projection_utils.py.
Specifically tests the "flat spectrum" edge case handling.
"""

import os
import sys
import tempfile
import logging
import pytest
import torch
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.projection_utils import perform_layerwise_svd

@pytest.fixture
def logger():
    logging.basicConfig(level=logging.WARNING)
    return logging.getLogger(__name__)

class TestSVDFallbackLogic:
    """Tests for the flat spectrum fallback logic."""

    def test_flat_spectrum_triggers_fallback(self, logger):
        """
        Test that when cumulative variance < 80% even at max_rank,
        the function defaults to fallback_rank and logs a warning.
        """
        # Create a matrix with a very flat spectrum (e.g., all singular values equal)
        # This simulates a "flat spectrum" where variance is distributed evenly.
        # We can construct this by creating a random orthogonal matrix and scaling S uniformly.
        # Or simpler: just use a random matrix and set a very high target_variance that can't be met.
        
        # Let's create a matrix where singular values are all 1.0
        # U and Vt can be random orthogonal, S = ones
        n_rows, n_cols = 100, 100
        U, _ = torch.linalg.qr(torch.randn(n_rows, n_rows))
        Vt, _ = torch.linalg.qr(torch.randn(n_cols, n_cols))
        S = torch.ones(min(n_rows, n_cols))
        
        # Reconstruct matrix: A = U S Vt
        A = torch.matmul(U, torch.matmul(torch.diag(S), Vt))
        
        dummy_updates = {"test_layer": A}
        
        # Set target_variance to 0.99 (99%) which is impossible with flat spectrum of rank 100
        # if we limit max_rank to 50, we only get 50/100 = 50% variance.
        # So it should trigger fallback.
        target_var = 0.99
        max_rank = 50
        fallback_rank = 10
        
        with patch('src.training.projection_utils.logger') as mock_logger:
            basis, ranks, fallback_triggered = perform_layerwise_svd(
                dummy_updates, 
                target_variance=target_var, 
                max_rank=max_rank, 
                fallback_rank=fallback_rank
            )
            
            # Verify fallback was triggered
            assert fallback_triggered is True, "Fallback should be triggered for flat spectrum"
            
            # Verify rank used is the fallback rank
            assert ranks["test_layer"] == fallback_rank, f"Expected rank {fallback_rank}, got {ranks['test_layer']}"
            
            # Verify warning was logged
            warning_calls = [call for call in mock_logger.warning.call_args_list if "Flat spectrum" in str(call)]
            assert len(warning_calls) > 0, "Expected a 'Flat spectrum' warning to be logged"

    def test_normal_spectrum_does_not_trigger_fallback(self, logger):
        """
        Test that when cumulative variance >= 80% within max_rank,
        the function selects the appropriate k and does NOT trigger fallback.
        """
        # Create a matrix with a decaying spectrum (e.g., S = [1, 0.5, 0.25, ...])
        # This should reach 80% variance quickly.
        n_rows, n_cols = 100, 100
        U, _ = torch.linalg.qr(torch.randn(n_rows, n_rows))
        Vt, _ = torch.linalg.qr(torch.randn(n_cols, n_cols))
        
        # Geometric decay
        k_true = 5
        S = torch.tensor([0.5 ** i for i in range(min(n_rows, n_cols))], dtype=torch.float32)
        
        # Reconstruct
        A = torch.matmul(U, torch.matmul(torch.diag(S), Vt))
        
        dummy_updates = {"test_layer": A}
        
        target_var = 0.80
        max_rank = 50
        fallback_rank = 10
        
        with patch('src.training.projection_utils.logger') as mock_logger:
            basis, ranks, fallback_triggered = perform_layerwise_svd(
                dummy_updates,
                target_variance=target_var,
                max_rank=max_rank,
                fallback_rank=fallback_rank
            )
            
            # Verify fallback was NOT triggered
            assert fallback_triggered is False, "Fallback should not be triggered for normal spectrum"
            
            # Verify rank is small (should be around 5 or so for geometric decay)
            assert ranks["test_layer"] < max_rank, "Rank should be less than max_rank"
            assert ranks["test_layer"] >= 1, "Rank should be at least 1"

    def test_zero_variance_layer(self, logger):
        """
        Test behavior when a layer has zero variance (all zeros).
        """
        dummy_updates = {"zero_layer": torch.zeros(10, 10)}
        
        target_var = 0.80
        max_rank = 50
        fallback_rank = 10
        
        with patch('src.training.projection_utils.logger') as mock_logger:
            basis, ranks, fallback_triggered = perform_layerwise_svd(
                dummy_updates,
                target_variance=target_var,
                max_rank=max_rank,
                fallback_rank=fallback_rank
            )
            
            # Should trigger fallback
            assert fallback_triggered is True
            assert ranks["zero_layer"] == fallback_rank
            # Basis should be valid (k x n)
            assert basis["zero_layer"].shape == (fallback_rank, 10)

    def test_fallback_rank_parameter(self, logger):
        """
        Test that the fallback_rank parameter is respected.
        """
        # Create flat spectrum
        n_rows, n_cols = 50, 50
        U, _ = torch.linalg.qr(torch.randn(n_rows, n_rows))
        Vt, _ = torch.linalg.qr(torch.randn(n_cols, n_cols))
        S = torch.ones(min(n_rows, n_cols))
        A = torch.matmul(U, torch.matmul(torch.diag(S), Vt))
        
        dummy_updates = {"test_layer": A}
        
        custom_fallback = 20
        target_var = 0.99
        max_rank = 10 # Too small to reach 99%
        
        with patch('src.training.projection_utils.logger'):
            basis, ranks, _ = perform_layerwise_svd(
                dummy_updates,
                target_variance=target_var,
                max_rank=max_rank,
                fallback_rank=custom_fallback
            )
            
            assert ranks["test_layer"] == custom_fallback, f"Expected rank {custom_fallback}, got {ranks['test_layer']}"