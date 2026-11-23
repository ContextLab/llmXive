"""
Unit tests for the NaN Propagation Guard (T043).
"""
import pytest
import numpy as np
import healpy as hp
import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from gap_filling.NaN_guard import scan_for_nans, apply_nan_guard_wrapper, NaNPropagationError
from gap_filling.harmonic_interp import harmonic_interpolate

class TestNaNGuard:
    """Tests for the NaN guard functionality."""

    def test_scan_for_nans_clean_map(self):
        """Test that a clean map passes the NaN check."""
        nside = 32
        npix = hp.nside2npix(nside)
        clean_map = np.random.randn(npix)
        
        result = scan_for_nans(clean_map, "test_id", "test_algo", raise_on_failure=False)
        assert result is True

    def test_scan_for_nans_map_with_nans(self):
        """Test that a map with NaNs fails the NaN check."""
        nside = 32
        npix = hp.nside2npix(nside)
        map_with_nans = np.random.randn(npix)
        map_with_nans[10] = np.nan
        map_with_nans[20] = np.nan
        
        result = scan_for_nans(map_with_nans, "test_id", "test_algo", raise_on_failure=False)
        assert result is False

    def test_scan_for_nans_raises_exception(self):
        """Test that a map with NaNs raises NaNPropagationError when raise_on_failure=True."""
        nside = 32
        npix = hp.nside2npix(nside)
        map_with_nans = np.random.randn(npix)
        map_with_nans[10] = np.nan
        
        with pytest.raises(NaNPropagationError) as exc_info:
            scan_for_nans(map_with_nans, "test_123", "harmonic_interp", raise_on_failure=True)
        
        assert "test_123" in str(exc_info.value)
        assert "harmonic_interp" in str(exc_info.value)
        assert "1" in str(exc_info.value) # Count of NaNs

    def test_apply_nan_guard_wrapper_clean(self):
        """Test that the wrapper works correctly for clean outputs."""
        nside = 32
        npix = hp.nside2npix(nside)
        test_map = np.random.randn(npix)
        test_mask = np.zeros(npix, dtype=bool) # No gaps
        
        # This should succeed
        result = apply_nan_guard_wrapper(
            harmonic_interpolate,
            test_map,
            test_mask,
            "clean_test",
            "harmonic",
            lmax=50
        )
        
        assert result is not None
        assert not np.any(np.isnan(result))

    def test_apply_nan_guard_wrapper_fails_with_nans(self):
        """Test that the wrapper raises an error if the function produces NaNs."""
        nside = 32
        npix = hp.nside2npix(nside)
        
        # Create a function that produces NaNs
        def bad_function(map, mask, *args, **kwargs):
            out = map.copy()
            out[5] = np.nan
            return out
        
        test_map = np.random.randn(npix)
        test_mask = np.zeros(npix, dtype=bool)
        
        with pytest.raises(NaNPropagationError) as exc_info:
            apply_nan_guard_wrapper(
                bad_function,
                test_map,
                test_mask,
                "bad_test",
                "bad_algo"
            )
        
        assert "bad_test" in str(exc_info.value)
        assert "bad_algo" in str(exc_info.value)
        assert "1" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])