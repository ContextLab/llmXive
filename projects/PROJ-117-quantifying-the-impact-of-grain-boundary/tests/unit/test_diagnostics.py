"""
Unit tests for diagnostics.py (T018).
Tests Mutual Information calculation and collinearity diagnostic logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from diagnostics import (
    calculate_sigma_from_misorientation,
    compute_mutual_information,
    run_collinearity_diagnostic,
)
from utils import setup_logging

logger = setup_logging("test_diagnostics")


class TestCalculateSigmaFromMisorientation:
    """Tests for sigma value calculation logic."""

    def test_sigma_calculation_returns_float(self):
        """Ensure the function returns a numeric value for valid input."""
        # Mock misorientation angle (degrees)
        angle = 36.87  # Common CSL angle
        result = calculate_sigma_from_misorientation(angle)
        assert isinstance(result, (int, float, np.floating))
        assert result > 0

    def test_sigma_calculation_handles_nan(self):
        """Ensure NaN input returns NaN."""
        result = calculate_sigma_from_misorientation(np.nan)
        assert np.isnan(result)


class TestComputeMutualInformation:
    """Tests for Mutual Information calculation."""

    def test_mi_calculation_positive(self):
        """MI should be positive for correlated variables."""
        # Create synthetic but deterministic data
        np.random.seed(42)
        n_samples = 1000
        x = np.random.rand(n_samples)
        y = x + 0.1 * np.random.rand(n_samples)  # Correlated

        mi_score = compute_mutual_information(x, y)
        assert mi_score > 0

    def test_mi_calculation_independent(self):
        """MI should be near zero for independent variables."""
        np.random.seed(42)
        n_samples = 1000
        x = np.random.rand(n_samples)
        y = np.random.rand(n_samples)  # Independent

        mi_score = compute_mutual_information(x, y)
        # Allow small tolerance due to estimation noise
        assert mi_score < 0.5

    def test_mi_calculation_empty_input(self):
        """MI should handle empty arrays gracefully (return 0 or NaN)."""
        x = np.array([])
        y = np.array([])
        mi_score = compute_mutual_information(x, y)
        assert mi_score == 0.0 or np.isnan(mi_score)


class TestRunCollinearityDiagnostic:
    """Tests for the full collinearity diagnostic pipeline."""

    def test_run_diagnostic_creates_report(self):
        """Verify that run_collinearity_diagnostic creates a valid JSON report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "collinearity_diagnostic.json"
            
            # Create mock data
            data = pd.DataFrame({
                "misorientation_angle": np.random.rand(100) * 180,
                "sigma_value": np.random.randint(1, 10, 100).astype(float),
                "other_feature": np.random.rand(100)
            })
            
            # Mock the file loading to avoid dependency on T011 output
            with patch("diagnostics.load_parsed_data", return_value=data):
                result = run_collinearity_diagnostic(output_path)

            assert result is not None
            assert "status" in result
            assert "mi_score" in result
            assert "interpretation" in result
            
            # Verify file was written
            assert output_path.exists()
            with open(output_path, "r") as f:
                saved_data = json.load(f)
                assert saved_data["status"] == "success"

    def test_run_diagnostic_no_valid_sigma(self):
        """Verify diagnostic handles case with no valid Sigma values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "collinearity_diagnostic.json"
            
            # Create data with NaN Sigma values
            data = pd.DataFrame({
                "misorientation_angle": np.random.rand(100) * 180,
                "sigma_value": [np.nan] * 100,
                "other_feature": np.random.rand(100)
            })
            
            with patch("diagnostics.load_parsed_data", return_value=data):
                result = run_collinearity_diagnostic(output_path)

            assert result["status"] == "unavailable"
            assert "No valid Σ values" in result["message"]
            
            # Verify file content
            with open(output_path, "r") as f:
                saved_data = json.load(f)
                assert saved_data["status"] == "unavailable"

    def test_run_diagnostic_high_mi_threshold(self):
        """Verify interpretation logic for high MI scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "collinearity_diagnostic.json"
            
            # Create highly correlated data
            data = pd.DataFrame({
                "misorientation_angle": np.random.rand(100),
                "sigma_value": np.random.rand(100) * 100, # Artificially high correlation for test
                "other_feature": np.random.rand(100)
            })
            
            # Mock MI to return a high value to test threshold logic
            with patch("diagnostics.load_parsed_data", return_value=data):
                with patch("diagnostics.compute_mutual_information", return_value=0.85):
                    result = run_collinearity_diagnostic(output_path)

            assert result["mi_score"] > 0.8
            assert "strong dependency" in result["interpretation"].lower()

    def test_run_diagnostic_low_mi_threshold(self):
        """Verify interpretation logic for low MI scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "collinearity_diagnostic.json"
            
            data = pd.DataFrame({
                "misorientation_angle": np.random.rand(100),
                "sigma_value": np.random.rand(100),
                "other_feature": np.random.rand(100)
            })
            
            with patch("diagnostics.load_parsed_data", return_value=data):
                with patch("diagnostics.compute_mutual_information", return_value=0.1):
                    result = run_collinearity_diagnostic(output_path)

            assert result["mi_score"] < 0.8
            assert "weak" in result["interpretation"].lower() or "low" in result["interpretation"].lower()