"""Unit tests for asymmetry calculation (US2)."""
import numpy as np
import pytest
from metrics.asymmetry import calculate_asymmetry

def test_asymmetry_conselice():
    """Test that the A-statistic matches the Conselice (2003) definition.
    
    For a perfectly symmetric Gaussian centered in the image, A should be ~0.
    For an asymmetric shape, A should be > 0.
    """
    # Create a symmetric Gaussian centered at (10, 10) in a 20x20 image
    size = 20
    y, x = np.indices((size, size))
    center = (10, 10)
    sigma = 2.0
    gaussian = np.exp(-((x - center[0])**2 + (y - center[1])**2) / (2 * sigma**2))
    
    # Calculate asymmetry
    A, bg_corr = calculate_asymmetry(gaussian)
    
    # For a perfect symmetric Gaussian, A should be very close to 0
    # (allowing for small numerical errors)
    assert A < 0.01, f"Expected A ~ 0 for symmetric Gaussian, got {A}"
    assert bg_corr == 0.0, "Background correction should be 0.0 if not provided"
    
    # Create an asymmetric image: Gaussian + offset point
    asymmetric = gaussian.copy()
    asymmetric[5, 5] += 10.0  # Add a bright point off-center
    
    A_asym, _ = calculate_asymmetry(asymmetric)
    assert A_asym > A, f"Asymmetric image should have higher A ({A_asym}) than symmetric ({A})"
    
    # Test with explicit center
    A_explicit, _ = calculate_asymmetry(gaussian, center=center)
    assert np.isclose(A, A_explicit), "Explicit center should yield same result"
    
    # Test with background correction
    background = np.ones_like(gaussian) * 0.1
    A_corr, bg_corr_val = calculate_asymmetry(gaussian, background_image=background)
    assert isinstance(A_corr, float)
    assert isinstance(bg_corr_val, float)

def test_asymmetry_zero_flux():
    """Test behavior with zero flux image."""
    zero_image = np.zeros((10, 10))
    A, bg_corr = calculate_asymmetry(zero_image)
    assert A == 0.0
    assert bg_corr == 0.0

def test_asymmetry_non_2d():
    """Test that non-2D images raise an error."""
    with pytest.raises(ValueError):
        calculate_asymmetry(np.zeros((10, 10, 10)))