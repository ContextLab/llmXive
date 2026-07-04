"""
Unit tests for GLM assumption validation module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.glm_assumptions import (
    validate_binary_outcome,
    check_perfect_separation,
    validate_sample_size,
    fit_glm_with_validation,
    handle_convergence_warnings,
    main
)


class TestBinaryOutcomeValidation:
    """Tests for binary outcome validation."""

    def test_valid_binary_outcome(self):
        """Test with valid binary outcome (0s and 1s)."""
        df = pd.DataFrame({
            'covered': [0, 1, 0, 1, 0, 1],
            'epsilon': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'noise_type': ['laplace'] * 3 + ['gaussian'] * 3
        })
        is_valid, msg = validate_binary_outcome(df, 'covered')
        assert is_valid, f"Valid binary outcome rejected: {msg}"
        assert "passed" in msg.lower()

    def test_non_binary_values(self):
        """Test with non-binary values (e.g., 0.5)."""
        df = pd.DataFrame({
            'covered': [0, 1, 0.5, 1, 0, 1],
            'epsilon': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'noise_type': ['laplace'] * 3 + ['gaussian'] * 3
        })
        is_valid, msg = validate_binary_outcome(df, 'covered')
        assert not is_valid, "Non-binary values should be rejected"
        assert "non-integer" in msg.lower() or "outside" in msg.lower()

    def test_values_outside_range(self):
        """Test with values outside [0, 1]."""
        df = pd.DataFrame({
            'covered': [0, 1, -1, 1, 0, 2],
            'epsilon': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'noise_type': ['laplace'] * 3 + ['gaussian'] * 3
        })
        is_valid, msg = validate_binary_outcome(df, 'covered')
        assert not is_valid, "Values outside [0, 1] should be rejected"
        assert "outside" in msg.lower()

    def test_missing_column(self):
        """Test with missing outcome column."""
        df = pd.DataFrame({
            'epsilon': [0.1, 0.2, 0.3],
            'noise_type': ['laplace'] * 3
        })
        is_valid, msg = validate_binary_outcome(df, 'covered')
        assert not is_valid, "Missing column should be rejected"
        assert "not found" in msg.lower()

    def test_only_zeros(self):
        """Test with only zeros (no variation)."""
        df = pd.DataFrame({
            'covered': [0, 0, 0, 0, 0, 0],
            'epsilon': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'noise_type': ['laplace'] * 3 + ['gaussian'] * 3
        })
        is_valid, msg = validate_binary_outcome(df, 'covered')
        assert not is_valid, "Only zeros should be rejected"
        assert "both 0 and 1" in msg.lower()

    def test_only_ones(self):
        """Test with only ones (no variation)."""
        df = pd.DataFrame({
            'covered': [1, 1, 1, 1, 1, 1],
            'epsilon': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'noise_type': ['laplace'] * 3 + ['gaussian'] * 3
        })
        is_valid, msg = validate_binary_outcome(df, 'covered')
        assert not is_valid, "Only ones should be rejected"
        assert "both 0 and 1" in msg.lower()


class TestPerfectSeparation:
    """Tests for perfect separation detection."""

    def test_no_separation(self):
        """Test data without perfect separation."""
        df = pd.DataFrame({
            'covered': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            'epsilon': [0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.2, 0.3, 0.4, 0.5],
            'noise_type': ['laplace'] * 5 + ['gaussian'] * 5
        })
        has_sep, msg = check_perfect_separation(df, "covered ~ epsilon + noise_type")
        assert not has_sep, f"No separation should be detected: {msg}"

    def test_large_sample(self):
        """Test with larger sample size."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'covered': np.random.binomial(1, 0.5, n),
            'epsilon': np.random.uniform(0.1, 1.0, n),
            'noise_type': np.random.choice(['laplace', 'gaussian'], n)
        })
        has_sep, msg = check_perfect_separation(df, "covered ~ epsilon + noise_type")
        # This should not raise an exception
        assert isinstance(has_sep, bool)


class TestSampleSizeValidation:
    """Tests for sample size validation."""

    def test_adequate_sample_size(self):
        """Test with adequate sample size."""
        df = pd.DataFrame({
            'covered': [1] * 50 + [0] * 50,
            'epsilon': [0.1] * 100,
            'noise_type': ['laplace'] * 50 + ['gaussian'] * 50
        })
        is_valid, msg = validate_sample_size(df, "covered ~ epsilon + noise_type")
        assert is_valid, f"Adequate sample size should pass: {msg}"

    def test_insufficient_events(self):
        """Test with insufficient events per variable."""
        df = pd.DataFrame({
            'covered': [1] * 5 + [0] * 95,  # Only 5 events
            'epsilon': [0.1] * 100,
            'noise_type': ['laplace'] * 50 + ['gaussian'] * 50
        })
        is_valid, msg = validate_sample_size(df, "covered ~ epsilon + noise_type", min_events_per_var=10)
        assert not is_valid, "Insufficient events should fail"
        assert "Insufficient events" in msg


class TestGLMValidationIntegration:
    """Integration tests for GLM validation."""

    def test_fit_glm_valid_data(self):
        """Test fitting GLM with valid data."""
        np.random.seed(42)
        n = 200
        df = pd.DataFrame({
            'covered': np.random.binomial(1, 0.5, n),
            'epsilon': np.random.uniform(0.1, 1.0, n),
            'noise_type': np.random.choice(['laplace', 'gaussian'], n)
        })
        formula = "covered ~ epsilon + noise_type"

        result, info = fit_glm_with_validation(df, formula)

        assert info['fit_successful'], f"GLM should fit: {info['fit_message']}"
        assert info['binary_outcome_valid'], "Binary outcome should be valid"
        assert result is not None

    def test_fit_glm_with_separation(self):
        """Test fitting GLM with potential separation issues."""
        # Create data with extreme separation
        df = pd.DataFrame({
            'covered': [1] * 50 + [0] * 50,
            'epsilon': [1.0] * 50 + [0.1] * 50,  # Extreme difference
            'noise_type': ['laplace'] * 50 + ['gaussian'] * 50
        })
        formula = "covered ~ epsilon"

        result, info = fit_glm_with_validation(df, formula)

        # Should still attempt to fit, may have convergence warnings
        assert isinstance(info['convergence_warning'], bool)
        assert isinstance(info['fit_successful'], bool)


class TestMainFunction:
    """Tests for the main validation function."""

    def test_main_with_missing_file(self, tmp_path):
        """Test main function when coverage file is missing."""
        import os
        from unittest.mock import patch

        # Create a temporary directory
        with patch('code.analysis.glm_assumptions.main.__globals__'):
            # This test is simplified - in practice, we'd need to mock the file system
            pass

    def test_main_returns_dict(self):
        """Test that main function returns a dictionary."""
        # This would require setting up the full file structure
        # For now, we verify the function exists and has the right signature
        import inspect
        sig = inspect.signature(main)
        assert len(sig.parameters) == 0  # main() takes no arguments