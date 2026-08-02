"""
Integration test for finite-size scaling fit logic (T013a).
Verifies that fit_scaling_curve works on synthetic data and handles edge cases.
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np

import pytest

from code.finite_size_scaling import (
    saturation_model,
    fit_scaling_curve,
    run_scaling_analysis,
    load_raw_pr_data
)

def test_saturation_model():
    """Test the saturation model function."""
    L = np.array([100, 200, 400, 800, 1600])
    PR_inf = 100.0
    xi = 200.0
    expected = PR_inf * (1.0 - np.exp(-L / xi))
    result = saturation_model(L, PR_inf, xi)
    np.testing.assert_array_almost_equal(result, expected, decimal=5)

def test_fit_scaling_curve_success():
    """Test successful fit on synthetic data."""
    L = np.array([100, 200, 400, 800, 1600])
    PR_inf_true = 100.0
    xi_true = 200.0
    PR_true = saturation_model(L, PR_inf_true, xi_true)
    # Add small noise
    PR_noisy = PR_true + np.random.normal(0, 0.5, size=L.shape)

    params, r_squared, success = fit_scaling_curve(L, PR_noisy)

    assert success is True
    assert params is not None
    assert r_squared is not None
    assert r_squared > 0.95

    PR_inf_fit, xi_fit = params
    # Allow 20% tolerance
    assert abs(PR_inf_fit - PR_inf_true) / PR_inf_true < 0.2
    assert abs(xi_fit - xi_true) / xi_true < 0.2

def test_fit_scaling_curve_low_r2():
    """Test that fit with low R^2 returns success=False."""
    # Use data that doesn't fit the model
    L = np.array([100, 200, 400])
    PR = np.array([10.0, 20.0, 15.0])  # Non-monotonic, won't fit well

    params, r_squared, success = fit_scaling_curve(L, PR)

    # Should fail due to low R^2
    assert success is False
    if r_squared is not None:
        assert r_squared < 0.95

def test_run_scaling_analysis():
    """Test the full scaling analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / 'pr_raw_multiL.json'
        output_path = Path(tmpdir) / 'pr_scaling_raw.json'
        warnings_path = Path(tmpdir) / 'warnings.json'

        # Create synthetic input data
        data = []
        for W in [1.0, 2.0]:
            for L in [100, 200, 400, 800]:
                # Generate PR values that follow the model with noise
                PR_inf = 50.0 if W == 1.0 else 30.0
                xi = 150.0 if W == 1.0 else 100.0
                PR_mean = saturation_model(np.array([L]), PR_inf, xi)[0]
                for _ in range(5):  # 5 realizations
                    pr_val = PR_mean + np.random.normal(0, 1.0)
                    data.append({
                        'W': W,
                        'L': L,
                        'realization_index': len(data),
                        'energy': 0.0,
                        'pr': float(pr_val)
                    })

        with open(input_path, 'w') as f:
            json.dump(data, f)

        run_scaling_analysis(str(input_path), str(output_path), str(warnings_path))

        # Check output file exists and has correct schema
        assert output_path.exists()
        with open(output_path, 'r') as f:
            results = json.load(f)

        assert isinstance(results, list)
        assert len(results) == 2  # Two W values

        for res in results:
            assert 'disorder_width' in res
            assert 'xi' in res
            assert 'uncertainty' in res
            assert 'r_squared' in res
            assert res['r_squared'] >= 0.95  # Only successful fits

        # Check warnings file exists
        assert warnings_path.exists()
        with open(warnings_path, 'r') as f:
            warnings_data = json.load(f)
        assert isinstance(warnings_data, list)