"""
Unit tests for the ACF Validator module.
"""

import pytest
import numpy as np
import os
import json
import tempfile
from pathlib import Path

# Import the module under test
# Note: The project structure uses 'src' for code, so we adjust the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analysis.acf_validator import (
    compute_lag1_autocorrelation,
    validate_configuration_metrics,
    run_acf_validation
)

class TestLag1Autocorrelation:
    """Tests for the lag-1 autocorrelation calculation."""

    def test_perfect_correlation(self):
        """Test with a series where lag-1 should be ~1.0."""
        # A series that increases linearly: high positive correlation
        values = np.arange(100, dtype=float)
        acf_val = compute_lag1_autocorrelation(values)
        # For a perfect linear trend, ACF is very close to 1
        assert acf_val > 0.95, f"Expected high correlation, got {acf_val}"

    def test_negative_correlation(self):
        """Test with a series that oscillates."""
        # Alternating +1, -1
        values = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0])
        acf_val = compute_lag1_autocorrelation(values)
        # Should be strongly negative
        assert acf_val < -0.9, f"Expected negative correlation, got {acf_val}"

    def test_random_white_noise(self):
        """Test with random noise (expected ACF ~ 0)."""
        np.random.seed(42)
        values = np.random.randn(1000)
        acf_val = compute_lag1_autocorrelation(values)
        # Should be close to 0, allowing some statistical variance
        assert abs(acf_val) < 0.15, f"Expected near-zero correlation, got {acf_val}"

    def test_constant_series(self):
        """Test with a constant series (variance is 0)."""
        values = np.ones(10)
        acf_val = compute_lag1_autocorrelation(values)
        # Variance is 0, so correlation is undefined/0
        assert acf_val == 0.0

    def test_short_series(self):
        """Test with a very short series."""
        values = np.array([1.0, 2.0])
        acf_val = compute_lag1_autocorrelation(values)
        # Perfect correlation for 2 points
        assert acf_val == 1.0

    def test_empty_series(self):
        """Test with an empty series."""
        values = np.array([])
        acf_val = compute_lag1_autocorrelation(values)
        assert acf_val == 0.0

    def test_single_element(self):
        """Test with a single element."""
        values = np.array([1.0])
        acf_val = compute_lag1_autocorrelation(values)
        assert acf_val == 0.0

class TestValidateConfigurationMetrics:
    """Tests for the metric validation function."""

    def test_valid_low_acf(self):
        """Test validation passes for low ACF."""
        # White noise should have low ACF
        np.random.seed(123)
        values = np.random.randn(500).tolist()
        result = validate_configuration_metrics("config_1", "coherence", values)
        
        assert result["valid"] is True
        assert result["metric"] == "coherence"
        assert result["config_id"] == "config_1"
        assert result["requires_adjustment"] is False
        assert result["threshold"] == 0.1

    def test_invalid_high_acf(self):
        """Test validation fails for high ACF."""
        # Create a series with high autocorrelation
        values = []
        curr = 0.0
        for _ in range(500):
            curr = 0.9 * curr + 0.1 * np.random.randn() # AR(1) process
            values.append(curr)
        
        result = validate_configuration_metrics("config_2", "diversity", values)
        
        assert result["valid"] is False
        assert result["requires_adjustment"] is True
        assert "exceeds threshold" in result["reason"]
        assert result["lag1_acf"] >= 0.1

    def test_empty_values(self):
        """Test handling of empty list."""
        result = validate_configuration_metrics("config_3", "latency", [])
        
        assert result["valid"] is False
        assert "Empty data series" in result["reason"]

    def test_nan_values(self):
        """Test handling of NaN values."""
        values = [1.0, 2.0, np.nan, 4.0]
        result = validate_configuration_metrics("config_4", "score", values)
        
        assert result["valid"] is False
        assert "NaN" in result["reason"]

    def test_inf_values(self):
        """Test handling of Inf values."""
        values = [1.0, 2.0, np.inf, 4.0]
        result = validate_configuration_metrics("config_5", "score", values)
        
        assert result["valid"] is False
        assert "Inf" in result["reason"]

class TestRunAcFValidation:
    """Integration test for the main validation runner."""

    def test_run_validation_creates_report(self):
        """Test that the runner creates a valid JSON report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup input directory
            raw_dir = Path(tmpdir) / "data" / "raw"
            raw_dir.mkdir(parents=True)
            
            # Create a mock log file with low ACF data
            log_file = raw_dir / "run_test_config.jsonl"
            with open(log_file, 'w') as f:
                # Write some random noise
                for i in range(100):
                    record = {
                        "step": i,
                        "coherence_score": float(np.random.randn()),
                        "diversity_score": float(np.random.randn())
                    }
                    f.write(json.dumps(record) + "\n")
            
            output_path = Path(tmpdir) / "data" / "processed" / "report.json"
            
            # Run validation
            report = run_acf_validation(str(raw_dir), str(output_path))
            
            # Assertions
            assert output_path.exists()
            assert report["status"] == "success"
            assert "results" in report
            assert len(report["results"]) == 2 # coherence and diversity

    def test_run_validation_no_data(self):
        """Test behavior when no raw logs exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "data" / "raw"
            raw_dir.mkdir(parents=True)
            
            output_path = Path(tmpdir) / "data" / "processed" / "report.json"
            
            report = run_acf_validation(str(raw_dir), str(output_path))
            
            assert report["status"] == "no_data"
            assert output_path.exists() # Should still create the file