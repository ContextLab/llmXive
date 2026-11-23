"""
Unit tests for the baseline validation module (T029).
"""
import pytest
import numpy as np
import sys
from pathlib import Path
import json
import tempfile
import os

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.synthesis.validation import run_baseline_check, write_baseline_status, ValidationError


class TestBaselineValidation:
    """Tests for the baseline validation functionality."""

    def test_baseline_check_h05_returns_pass(self):
        """Test that H=0.5 baseline check passes (CI contains alpha)."""
        result = run_baseline_check(
            num_trials=100,  # Small number for testing
            series_length=500,
            hurst=0.5,
            alpha=0.05,
            seed=42
        )
        
        assert "status" in result
        assert "rejection_rate" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert "num_rejections" in result
        
        # The CI should contain alpha (0.05) for H=0.5
        # Note: With small sample size, this might occasionally fail due to randomness
        # but with 100 trials it should generally pass
        assert result["ci_lower"] <= 0.05 <= result["ci_upper"], \
            f"CI [{result['ci_lower']}, {result['ci_upper']}] does not contain 0.05"

    def test_baseline_check_wrong_hurst_raises_error(self):
        """Test that baseline check raises error for H != 0.5."""
        with pytest.raises(ValidationError) as exc_info:
            run_baseline_check(
                num_trials=10,
                series_length=100,
                hurst=0.7,  # Wrong H value
                alpha=0.05,
                seed=42
            )
        assert "H=0.5" in str(exc_info.value)

    def test_write_baseline_status_creates_file(self):
        """Test that write_baseline_status creates a valid JSON file."""
        result = {
            "status": "PASS",
            "rejection_rate": 0.05,
            "ci_lower": 0.03,
            "ci_upper": 0.07,
            "num_rejections": 5,
            "num_trials": 100,
            "alpha": 0.05,
            "hurst": 0.5,
            "series_length": 1000
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_baseline.json")
            write_baseline_status(result, output_path)
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify content
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["status"] == "PASS"
            assert abs(loaded["rejection_rate"] - 0.05) < 0.001

    def test_baseline_check_rejection_rate_bounds(self):
        """Test that rejection rate is between 0 and 1."""
        result = run_baseline_check(
            num_trials=50,
            series_length=200,
            hurst=0.5,
            alpha=0.05,
            seed=123
        )
        
        assert 0.0 <= result["rejection_rate"] <= 1.0
        assert result["num_rejections"] >= 0
        assert result["num_rejections"] <= result["num_trials"]

    def test_ci_bounds_valid(self):
        """Test that CI bounds are valid probabilities."""
        result = run_baseline_check(
            num_trials=50,
            series_length=200,
            hurst=0.5,
            alpha=0.05,
            seed=456
        )
        
        assert 0.0 <= result["ci_lower"] <= 1.0
        assert 0.0 <= result["ci_upper"] <= 1.0
        assert result["ci_lower"] <= result["ci_upper"]

    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with the same seed."""
        result1 = run_baseline_check(
            num_trials=50,
            series_length=200,
            hurst=0.5,
            alpha=0.05,
            seed=999
        )
        
        result2 = run_baseline_check(
            num_trials=50,
            series_length=200,
            hurst=0.5,
            alpha=0.05,
            seed=999
        )
        
        # Results should be identical with same seed
        assert result1["num_rejections"] == result2["num_rejections"]
        assert result1["rejection_rate"] == result2["rejection_rate"]