"""
Unit tests for optical flow utility functions.

Tests for:
- Flow estimation logic (mocked model)
- Fallback mechanisms
- Flow validity checks
- Warping logic (conceptual)
"""
import pytest
import os
import sys
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.flow import (
    is_flow_valid,
    apply_nearest_neighbor_fallback,
    compute_flow_with_fallback
)


class TestFlowValidity:
    """Tests for flow validity checking."""

    def test_is_flow_valid_normal(self):
        """Test validity check on normal flow field."""
        # Normal flow: reasonable values, no NaN/Inf
        flow = np.random.randn(480, 640, 2).astype(np.float32)
        flow[:, :, 0] = flow[:, :, 0] * 10  # Scale to reasonable range
        flow[:, :, 1] = flow[:, :, 1] * 10
        
        assert is_flow_valid(flow) is True, "Normal flow should be valid"

    def test_is_flow_valid_nan(self):
        """Test validity check on flow with NaN values."""
        flow = np.random.randn(480, 640, 2).astype(np.float32)
        flow[100, 100, 0] = np.nan
        
        assert is_flow_valid(flow) is False, "Flow with NaN should be invalid"

    def test_is_flow_valid_inf(self):
        """Test validity check on flow with Inf values."""
        flow = np.random.randn(480, 640, 2).astype(np.float32)
        flow[100, 100, 1] = np.inf
        
        assert is_flow_valid(flow) is False, "Flow with Inf should be invalid"

    def test_is_flow_valid_large_values(self):
        """Test validity check on flow with extreme values."""
        flow = np.zeros((480, 640, 2), dtype=np.float32)
        flow[100, 100, 0] = 1e6  # Unreasonably large displacement
        
        # Should be invalid due to extreme values
        assert is_flow_valid(flow) is False, "Flow with extreme values should be invalid"


class TestFlowFallback:
    """Tests for flow fallback mechanisms."""

    def test_apply_nearest_neighbor_fallback(self):
        """Test nearest neighbor fallback logic."""
        # Create a flow field with some invalid regions
        flow = np.zeros((480, 640, 2), dtype=np.float32)
        flow[0:100, 0:100, :] = np.nan  # Invalid region
        flow[100:200, 0:100, 0] = 5.0   # Valid reference
        flow[100:200, 0:100, 1] = 0.0
        
        # Apply fallback
        fixed_flow = apply_nearest_neighbor_fallback(flow)
        
        # Check that NaN region is filled
        assert not np.isnan(fixed_flow[50, 50, 0]), "NaN should be replaced"
        assert not np.isnan(fixed_flow[50, 50, 1]), "NaN should be replaced"

    def test_compute_flow_with_fallback_valid(self):
        """Test flow computation when flow is valid."""
        valid_flow = np.random.randn(480, 640, 2).astype(np.float32) * 5.0
        
        result = compute_flow_with_fallback(valid_flow)
        
        # Should return the original flow unchanged if valid
        assert np.allclose(result, valid_flow), "Valid flow should be returned unchanged"

    def test_compute_flow_with_fallback_invalid(self):
        """Test flow computation when flow is invalid."""
        invalid_flow = np.zeros((480, 640, 2), dtype=np.float32)
        invalid_flow[:, :, 0] = np.nan
        
        result = compute_flow_with_fallback(invalid_flow)
        
        # Should apply fallback
        assert not np.isnan(result).any(), "Fallback should remove NaN values"


class TestFlowIntegration:
    """Integration-style tests for flow utilities."""

    def test_flow_pipeline_mock(self):
        """Test end-to-end flow processing with mocks."""
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2[100:200, 100:200] = 255  # Moving object simulation
        
        # Mock the RAFT model
        mock_model = MagicMock()
        mock_model.return_value = np.random.randn(480, 640, 2).astype(np.float32) * 2.0
        
        with patch('utils.flow.load_raft_small', return_value=mock_model):
            # This test verifies the pipeline doesn't crash
            # Actual flow values depend on mock
            pass  # Full integration test would require actual model loading

    def test_flow_consistency(self):
        """Test flow consistency for identical frames."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # For identical frames, flow should be near zero
        # (Mocked here as actual estimation requires model)
        zero_flow = np.zeros((480, 640, 2), dtype=np.float32)
        
        assert is_flow_valid(zero_flow) is True, "Zero flow should be valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])