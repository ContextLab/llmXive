import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.metrics import calculate_resonant_surface_density, detect_outliers, validate_metric_ranges

def test_calculate_resonant_surface_density_with_rational_surfaces():
    """
    Test that the function correctly identifies rational surfaces.
    We create a q-profile that definitely crosses rational values like 1.5 (3/2) and 2.0 (2/1).
    """
    # Create a profile where q goes from 1.4 to 2.1
    # This should cross 1.5 (3/2) and 2.0 (2/1)
    rho = np.linspace(0.1, 0.9, 100)
    q = 1.4 + (2.1 - 1.4) * (rho - 0.1) / (0.9 - 0.1)  # Linear interpolation

    density = calculate_resonant_surface_density(q, rho)

    # We expect at least 2 rational surfaces (1.5 and 2.0)
    # The density is count / rho_range. rho_range = 0.8
    # So density should be at least 2 / 0.8 = 2.5
    assert density >= 2.5, f"Expected density >= 2.5, got {density}"
    assert density > 0, "Density should be positive when rational surfaces are found."

def test_calculate_resonant_surface_density_no_rational():
    """
    Test that the function returns 0 when no rational surfaces are found.
    We create a q-profile that stays between 1.01 and 1.09 (avoiding 1.0 and 1.1).
    """
    rho = np.linspace(0.1, 0.9, 100)
    q = 1.01 + 0.08 * (rho - 0.1) / (0.9 - 0.1)  # Range [1.01, 1.09]

    density = calculate_resonant_surface_density(q, rho)

    # No rational m/n should be in [1.01, 1.09] with default bounds (1/1=1, 2/1=2, 3/2=1.5...)
    # The closest is 1.0 (1/1) but our range starts at 1.01.
    # So density should be 0.
    assert density == 0.0, f"Expected density 0.0, got {density}"

def test_calculate_resonant_surface_density_empty():
    """Test behavior with empty arrays."""
    density = calculate_resonant_surface_density(np.array([]), np.array([]))
    assert density == 0.0

def test_calculate_resonant_surface_density_nan_handling():
    """Test that NaN values are handled correctly."""
    rho = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    q = np.array([1.5, np.nan, 2.0, 1.0, 1.5])

    density = calculate_resonant_surface_density(q, rho)

    # Should ignore the NaN and find 1.5, 2.0, 1.0
    # rho_range = 0.4
    # Count = 3 (1.0, 1.5, 2.0)
    # Density = 3 / 0.4 = 7.5
    assert density > 0

def test_detect_outliers():
    """Test outlier detection logic."""
    df = pd.DataFrame({
        'discharge_id': [1, 2, 3],
        'island_width': [0.1, 0.5, 1.5],
        'minor_radius': [0.5, 0.5, 0.5]
    })

    result = detect_outliers(df)

    assert 'is_outlier' in result.columns
    assert result.loc[0, 'is_outlier'] == False
    assert result.loc[1, 'is_outlier'] == False
    assert result.loc[2, 'is_outlier'] == True

def test_validate_metric_ranges_valid():
    """Test validation with valid data."""
    df = pd.DataFrame({
        'resonant_surface_density': [1.5, 2.0, 3.0],
        'island_width': [0.1, 0.2, 0.3],
        'minor_radius': [0.5, 0.5, 0.5]
    })

    is_valid, errors = validate_metric_ranges(df)
    assert is_valid
    assert len(errors) == 0

def test_validate_metric_ranges_invalid():
    """Test validation with invalid data (negative values, NaN)."""
    df = pd.DataFrame({
        'resonant_surface_density': [-1.0, 2.0, np.nan],
        'island_width': [0.1, 0.2, 0.3],
        'minor_radius': [0.5, 0.5, 0.5]
    })

    is_valid, errors = validate_metric_ranges(df)
    assert not is_valid
    assert len(errors) > 0
