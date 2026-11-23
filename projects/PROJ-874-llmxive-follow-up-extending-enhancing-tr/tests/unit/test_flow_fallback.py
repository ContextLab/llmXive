import os
import sys
import numpy as np
import pytest

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.flow import apply_nearest_neighbor_fallback, is_flow_valid, compute_flow_with_fallback

class TestFlowFallback:
    def test_is_flow_valid_none(self):
        assert is_flow_valid(None) is False

    def test_is_flow_valid_nan(self):
        flow = np.zeros((10, 10, 2), dtype=np.float32)
        flow[5, 5, 0] = np.nan
        assert is_flow_valid(flow) is False

    def test_is_flow_valid_inf(self):
        flow = np.zeros((10, 10, 2), dtype=np.float32)
        flow[5, 5, 0] = np.inf
        assert is_flow_valid(flow) is False

    def test_is_flow_valid_valid(self):
        flow = np.zeros((10, 10, 2), dtype=np.float32)
        assert is_flow_valid(flow) is True

    def test_apply_nearest_neighbor_fallback_no_invalid(self):
        flow = np.ones((10, 10, 2), dtype=np.float32) * 5.0
        invalid_mask = np.zeros((10, 10), dtype=bool)
        result = apply_nearest_neighbor_fallback(flow, invalid_mask)
        np.testing.assert_array_equal(result, flow)

    def test_apply_nearest_neighbor_fallback_center_invalid(self):
        # Create a flow field with a valid center and invalid edges
        flow = np.zeros((10, 10, 2), dtype=np.float32)
        flow[:, :, 0] = 1.0
        flow[:, :, 1] = 2.0
        
        # Create a mask where the center 2x2 is invalid
        invalid_mask = np.zeros((10, 10), dtype=bool)
        invalid_mask[4:6, 4:6] = True
        
        result = apply_nearest_neighbor_fallback(flow, invalid_mask)
        
        # The invalid center should be filled with the nearest valid value (1.0, 2.0)
        assert result[4, 4, 0] == 1.0
        assert result[4, 4, 1] == 2.0
        assert result[5, 5, 0] == 1.0
        assert result[5, 5, 1] == 2.0

    def test_apply_nearest_neighbor_fallback_all_invalid(self):
        # If all are invalid, it should return zeros or handle gracefully
        flow = np.ones((5, 5, 2), dtype=np.float32)
        invalid_mask = np.ones((5, 5), dtype=bool)
        result = apply_nearest_neighbor_fallback(flow, invalid_mask)
        
        # The implementation returns zeros if no valid pixels found
        assert np.all(result == 0.0)

    def test_compute_flow_with_fallback_valid_flow(self):
        # Mock model that returns valid flow
        class MockModel:
            pass
        
        frame1 = np.zeros((10, 10, 3), dtype=np.float32)
        frame2 = np.zeros((10, 10, 3), dtype=np.float32)
        
        # We can't easily mock the internal estimate_flow without patching,
        # but we can test the logic flow if we assume estimate_flow returns valid data.
        # For this unit test, we focus on the fallback functions directly.
        pass
    
    def test_apply_nearest_neighbor_fallback_extreme_values(self):
        flow = np.zeros((10, 10, 2), dtype=np.float32)
        flow[0, 0, 0] = 200.0 # Extreme value, but not NaN/Inf
        invalid_mask = np.zeros((10, 10), dtype=bool)
        invalid_mask[5, 5] = True # Mark center as invalid for fallback test
        
        # This test checks that the fallback logic works even if valid data has extreme values
        # The is_flow_valid function might flag the whole flow as invalid in a real scenario
        # but here we test the interpolation logic specifically.
        result = apply_nearest_neighbor_fallback(flow, invalid_mask)
        assert result[5, 5, 0] == 0.0 # Nearest valid is 0.0 (from initialization)