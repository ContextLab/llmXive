import pytest
import numpy as np
import torch
from unittest.mock import patch
from models.flow_coherence import FlowCoherenceModule, FlowCoherenceResult

class TestInvalidFlowHandling:
    """
    Test T021a: Invalid flow handling (NaN/Infinity fallback to identity warp).
    """

    def test_identity_warp_invalid_vectors(self):
        """
        Verify that NaN/Infinity vectors in flow field trigger identity warp
        and set invalid_flow flag.
        """
        module = FlowCoherenceModule()
        
        # Create a flow field with NaN values
        h, w = 64, 64
        flow_with_nan = np.zeros((h, w, 2), dtype=np.float32)
        flow_with_nan[10:20, 10:20, 0] = np.nan
        
        # Create dummy latents
        latents = torch.randn(1, 4, h, w)
        
        # Call the warp function
        warped_latents = module._warp_latents(latents, flow_with_nan)
        
        # Verify that the output matches input (identity warp)
        assert torch.allclose(warped_latents, latents), "Identity warp should return original latents"
        
        # Verify invalid flow was detected and counted
        assert module.invalid_flow_count == 1, "Invalid flow count should be incremented"

    def test_identity_warp_infinity_vectors(self):
        """
        Verify that Infinity vectors in flow field trigger identity warp.
        """
        module = FlowCoherenceModule()
        
        # Create a flow field with Infinity values
        h, w = 64, 64
        flow_with_inf = np.zeros((h, w, 2), dtype=np.float32)
        flow_with_inf[30:40, 30:40, 1] = np.inf
        
        # Create dummy latents
        latents = torch.randn(1, 4, h, w)
        
        # Call the warp function
        warped_latents = module._warp_latents(latents, flow_with_inf)
        
        # Verify that the output matches input (identity warp)
        assert torch.allclose(warped_latents, latents), "Identity warp should return original latents"
        
        # Verify invalid flow was detected
        assert module.invalid_flow_count == 1, "Invalid flow count should be incremented for Inf"

    def test_valid_flow_no_fallback(self):
        """
        Verify that valid flow fields do not trigger identity warp.
        """
        module = FlowCoherenceModule()
        
        # Create a valid flow field (no NaN/Inf)
        h, w = 64, 64
        valid_flow = np.random.randn(h, w, 2).astype(np.float32) * 0.1
        
        # Create dummy latents
        latents = torch.randn(1, 4, h, w)
        
        # Call the warp function
        warped_latents = module._warp_latents(latents, valid_flow)
        
        # Verify that the output is NOT identical to input (actual warping occurred)
        # Note: We don't check exact values due to interpolation, just that it's different
        assert not torch.allclose(warped_latents, latents), "Valid flow should result in actual warping"
        
        # Verify invalid flow count is unchanged
        assert module.invalid_flow_count == 0, "Valid flow should not increment invalid count"

    def test_mixed_valid_invalid_flow(self):
        """
        Verify behavior when processing multiple frames with mixed valid/invalid flow.
        """
        module = FlowCoherenceModule()
        
        h, w = 64, 64
        latents = torch.randn(1, 4, h, w)
        
        # First frame: valid
        valid_flow = np.random.randn(h, w, 2).astype(np.float32) * 0.1
        warped1 = module._warp_latents(latents, valid_flow)
        assert module.invalid_flow_count == 0
        
        # Second frame: invalid (NaN)
        invalid_flow = np.zeros((h, w, 2), dtype=np.float32)
        invalid_flow[5:10, 5:10, 0] = np.nan
        warped2 = module._warp_latents(latents, invalid_flow)
        assert module.invalid_flow_count == 1
        assert torch.allclose(warped2, latents), "Invalid frame should use identity warp"
        
        # Third frame: valid again
        valid_flow2 = np.random.randn(h, w, 2).astype(np.float32) * 0.1
        warped3 = module._warp_latents(latents, valid_flow2)
        assert module.invalid_flow_count == 1, "Count should not increment for valid frames"
        assert not torch.allclose(warped3, latents), "Valid frame should be warped"

    def test_handle_invalid_flow_returns_cleaned(self):
        """
        Verify _handle_invalid_flow returns a cleaned flow field and correct flag.
        """
        module = FlowCoherenceModule()
        
        # Flow with NaN
        flow_nan = np.zeros((64, 64, 2), dtype=np.float32)
        flow_nan[10, 10, 0] = np.nan
        
        cleaned_flow, is_invalid = module._handle_invalid_flow(flow_nan)
        
        assert is_invalid is True, "Should flag invalid flow"
        assert np.allclose(cleaned_flow, 0.0), "Cleaned flow should be zero (identity)"
        assert cleaned_flow.shape == (64, 64, 2), "Shape should be preserved"

    def test_handle_invalid_flow_valid_unchanged(self):
        """
        Verify valid flow is returned unchanged.
        """
        module = FlowCoherenceModule()
        
        valid_flow = np.random.randn(64, 64, 2).astype(np.float32) * 0.1
        original_flow = valid_flow.copy()
        
        cleaned_flow, is_invalid = module._handle_invalid_flow(valid_flow)
        
        assert is_invalid is False, "Should not flag valid flow"
        assert np.allclose(cleaned_flow, original_flow), "Valid flow should be unchanged"