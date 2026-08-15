import pytest
import pandas as pd
from descriptors import compute_range_uncertainty, compute_valence_electron_concentration, compute_mean_atomic_radius, compute_electronegativity_std, compute_cation_size_variance

def test_compute_range_uncertainty_single_value():
    """Test range uncertainty for a single value."""
    result = compute_range_uncertainty("15")
    assert result == 0.0

def test_compute_range_uncertainty_range():
    """Test range uncertainty for a range string."""
    result = compute_range_uncertainty("10-20")
    assert result == 10.0

def test_compute_range_uncertainty_invalid():
    """Test range uncertainty for invalid input."""
    result = compute_range_uncertainty("invalid")
    assert result is None

def test_compute_valence_electron_concentration():
    """Test VEC computation."""
    result = compute_valence_electron_concentration("Al2O3")
    assert result is not None
    assert result > 0

def test_compute_mean_atomic_radius():
    """Test mean atomic radius computation."""
    result = compute_mean_atomic_radius("Al2O3")
    assert result is not None
    assert result > 0

def test_compute_electronegativity_std():
    """Test electronegativity std computation."""
    result = compute_electronegativity_std("Al2O3")
    assert result is not None
    assert result >= 0

def test_compute_cation_size_variance():
    """Test cation size variance computation."""
    result = compute_cation_size_variance("Al2O3")
    assert result is not None
    assert result >= 0