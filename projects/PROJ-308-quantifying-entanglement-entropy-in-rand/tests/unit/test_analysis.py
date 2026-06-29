"""
Unit tests for analysis.py plotting utilities.
"""
import os
import tempfile
import numpy as np
import pytest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from analysis import (
    generate_entropy_vs_l_plot,
    ModelSelectionResult,
    select_model_aic,
    generate_toy_model_data
)

def test_plot_generation():
    """Test that generate_entropy_vs_l_plot creates a valid PNG file."""
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'entropy_vs_l.png')

        # Generate synthetic data
        l_vals = np.array([1, 2, 4, 8, 16, 32])
        s_vals = 0.3 * np.log(l_vals) + np.random.normal(0, 0.05, size=len(l_vals))

        # Generate plot
        generate_entropy_vs_l_plot(
            l_vals,
            s_vals,
            output_path,
            title="Test Entropy vs Length"
        )

        # Verify file exists and has content
        assert os.path.exists(output_path), f"Plot file not created at {output_path}"
        assert os.path.getsize(output_path) > 0, "Plot file is empty"

        # Verify it's a valid PNG by checking header
        with open(output_path, 'rb') as f:
            header = f.read(8)
            assert header[:4] == b'\x89PNG', "Not a valid PNG file"

def test_plot_with_model_fit():
    """Test plot generation with a model fit line."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'entropy_vs_l_fit.png')

        l_vals = np.array([1, 2, 4, 8, 16])
        s_vals = 0.35 * np.log(l_vals) + 0.1

        # Select model
        model_result = select_model_aic(l_vals, s_vals)

        generate_entropy_vs_l_plot(
            l_vals,
            s_vals,
            output_path,
            model_result=model_result,
            title="Entropy with Fit"
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

def test_plot_log_scale():
    """Test that log scale is applied correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'entropy_log_scale.png')

        l_vals = np.array([1, 2, 4, 8, 16])
        s_vals = np.log(l_vals) * 0.3

        generate_entropy_vs_l_plot(
            l_vals,
            s_vals,
            output_path,
            log_scale=True
        )

        assert os.path.exists(output_path)

def test_plot_without_log_scale():
    """Test plot generation without log scale."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'entropy_linear_scale.png')

        l_vals = np.array([1, 2, 4, 8, 16])
        s_vals = np.log(l_vals) * 0.3

        generate_entropy_vs_l_plot(
            l_vals,
            s_vals,
            output_path,
            log_scale=False
        )

        assert os.path.exists(output_path)

def test_plot_constant_model():
    """Test plot generation for constant model (area law)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'entropy_constant.png')

        l_vals = np.array([1, 2, 4, 8, 16])
        s_vals = np.ones_like(l_vals, dtype=float) * 0.5  # Constant entropy

        model_result = ModelSelectionResult(
            model_type='constant',
            params={'c': 0.5},
            aic_scores={'constant': 10.0, 'logarithmic': 20.0, 'linear': 30.0},
            selected_aic=10.0,
            r_squared=0.0,
            p_value=None,
            slope=None,
            intercept=None
        )

        generate_entropy_vs_l_plot(
            l_vals,
            s_vals,
            output_path,
            model_result=model_result
        )

        assert os.path.exists(output_path)

def test_plot_directory_creation():
    """Test that plot function creates output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a subdirectory path that doesn't exist yet
        output_path = os.path.join(tmpdir, 'subdir', 'plots', 'entropy.png')

        l_vals = np.array([1, 2, 4, 8])
        s_vals = np.log(l_vals) * 0.3

        generate_entropy_vs_l_plot(l_vals, s_vals, output_path)

        assert os.path.exists(output_path)
        assert os.path.isdir(os.path.dirname(output_path))

def test_toy_model_data_generation():
    """Test that toy model data generation works correctly."""
    l_vals, s_avg = generate_toy_model_data(L=10, delta=0.5, n_realizations=5, random_seed=42)

    assert len(l_vals) == 9  # L-1 bipartitions
    assert len(s_avg) == 9
    assert np.all(s_avg >= 0)  # Entropy should be non-negative
    assert np.all(l_vals > 0)  # Bipartition lengths should be positive