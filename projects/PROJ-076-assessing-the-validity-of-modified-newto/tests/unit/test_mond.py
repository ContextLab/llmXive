"""
Unit tests for the MOND 'simple' model implementation.
"""
import numpy as np
import pytest
from code.models.mond import mond_simple, A0

def test_mond_simple_basic():
    """Test basic functionality of mond_simple."""
    r = np.array([1.0, 5.0, 10.0, 50.0])  # kpc
    ml = 1.0
    v_scale = 100.0  # km/s

    v_pred = mond_simple(r, ml, v_scale)

    # Check that output is an array of the same shape
    assert isinstance(v_pred, np.ndarray)
    assert v_pred.shape == r.shape

    # Check that velocities are positive
    assert np.all(v_pred >= 0)

def test_mond_simple_mdl_dependency():
    """Test that velocity increases with M/L ratio."""
    r = np.array([10.0])  # kpc
    v_scale = 100.0  # km/s

    v_ml1 = mond_simple(r, 1.0, v_scale)[0]
    v_ml2 = mond_simple(r, 2.0, v_scale)[0]

    # Higher M/L should yield higher velocity
    assert v_ml2 > v_ml1

def test_mond_simple_mond_limit():
    """
    Test the deep MOND limit behavior.
    In deep MOND (a_N << a_0), v^4 = G * M * a_0.
    So v should be constant (flat rotation curve) for large r.
    """
    # Use large r to approach deep MOND limit
    r = np.array([10.0, 50.0, 100.0, 200.0])  # kpc
    ml = 1.0
    v_scale = 100.0  # km/s

    v_pred = mond_simple(r, ml, v_scale)

    # In the deep MOND limit, the rotation curve should be relatively flat
    # compared to the Newtonian decline.
    # v_Newtonian ~ 1/sqrt(r). v_MOND ~ constant.
    # Check that the variation is small compared to Newtonian expectation
    # or simply that it doesn't drop as fast as 1/sqrt(r).
    # For a simple check, ensure the last value is not drastically smaller than the first.
    # A strict flatness check is hard without specific G, M values, but we check monotonicity
    # or slow decline.
    # Let's check that v_pred[-1] is not significantly less than v_pred[0]
    # relative to the Newtonian drop.
    # Newtonian drop factor: sqrt(10/200) = sqrt(0.05) = 0.22.
    # MOND should be much flatter.
    ratio = v_pred[-1] / v_pred[0]
    # In deep MOND, ratio should be close to 1.
    # With our parameters, let's just ensure it's > 0.5 (arbitrary sanity check).
    assert ratio > 0.5

def test_mond_simple_newtonian_limit():
    """
    Test the Newtonian limit behavior.
    In Newtonian limit (a_N >> a_0), a ~ a_N.
    v^2 ~ v_N^2.
    """
    # Use small r to approach Newtonian limit
    r = np.array([0.1, 0.5, 1.0])  # kpc
    ml = 1.0
    v_scale = 200.0  # High velocity scale to ensure a_N >> a_0

    v_pred = mond_simple(r, ml, v_scale)

    # In Newtonian limit, v should follow v_scale * sqrt(ML) roughly
    # Check that v_pred is close to v_scale * sqrt(ML)
    # v_N = v_scale * sqrt(ML)
    v_expected = v_scale * np.sqrt(ml)

    # Allow some deviation due to the transition region
    # The formula is a = a_N/2 + sqrt(...)
    # If a_0 is negligible, a = a_N/2 + a_N/2 = a_N.
    # So v^2 = a*r = a_N*r = v_N^2.
    # So v should be v_N.
    # Check that v_pred is close to v_expected
    assert np.allclose(v_pred, v_expected, rtol=0.1)

def test_mond_simple_zero_radius():
    """Test handling of zero or near-zero radius."""
    r = np.array([0.0, 1e-10, 1e-9])
    ml = 1.0
    v_scale = 100.0

    # Should not raise an error
    v_pred = mond_simple(r, ml, v_scale)

    # Velocities should be finite
    assert np.all(np.isfinite(v_pred))
    # Velocities should be non-negative
    assert np.all(v_pred >= 0)

def test_mond_simple_vectorization():
    """Test that the function handles vector inputs correctly."""
    r = np.linspace(1, 100, 50)
    ml = 1.0
    v_scale = 100.0

    v_pred = mond_simple(r, ml, v_scale)

    assert len(v_pred) == 50
    assert np.all(np.isfinite(v_pred))
    assert np.all(v_pred >= 0)