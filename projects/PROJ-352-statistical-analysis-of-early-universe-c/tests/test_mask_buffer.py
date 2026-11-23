import pytest
import numpy as np
import healpy as hp
from pathlib import Path
import tempfile
import json

# Import functions from mask module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from mask import apply_buffer_zone, load_mask, apply_mask, apply_schmalzing_gorski_correction
from config import get_config

class TestBufferZone:
    """Test the 2-pixel buffer zone application for mask verification."""
    
    def test_buffer_zone_reduces_valid_pixels(self):
        """Test that applying a buffer zone reduces the number of valid pixels."""
        # Create a simple test mask (all valid)
        nside = 32
        npix = hp.nside2npix(nside)
        mask = np.ones(npix)
        
        # Apply a small masked region
        mask[100:110] = 0
        
        # Apply buffer zone
        buffered_mask, additional_masked = apply_buffer_zone(mask, nside, buffer_pixels=2)
        
        # Verify that additional pixels were masked
        assert additional_masked > 0
        assert np.sum(buffered_mask == 1) < np.sum(mask == 1)
    
    def test_buffer_zone_consistency(self):
        """Test that buffer zone application is deterministic."""
        nside = 32
        npix = hp.nside2npix(nside)
        mask = np.ones(npix)
        mask[100:110] = 0
        
        # Apply buffer zone twice
        buffered_mask1, _ = apply_buffer_zone(mask, nside, buffer_pixels=2)
        buffered_mask2, _ = apply_buffer_zone(mask, nside, buffer_pixels=2)
        
        # Results should be identical
        assert np.array_equal(buffered_mask1, buffered_mask2)
    
    def test_buffer_zone_with_real_mask(self):
        """Test buffer zone application with a real mask file if available."""
        config = get_config()
        mask_path = config.data_raw_dir / "u73_mask.fits"
        
        if mask_path.exists():
            mask = load_mask(mask_path)
            nside = hp.npix2nside(len(mask))
            
            buffered_mask, additional_masked = apply_buffer_zone(mask, nside, buffer_pixels=2)
            
            # Verify buffer zone was applied
            assert additional_masked > 0
            assert np.sum(buffered_mask == 1) < np.sum(mask == 1)
        else:
            pytest.skip("Real mask file not available")

class TestMaskVerification:
    """Test the verification comparison between analytical and buffer methods."""
    
    def test_verification_log_creation(self):
        """Test that verification log is created with expected content."""
        # This test would require the full pipeline to run
        # For now, we test the individual components
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])