"""
Unit tests for calculate_calibration_metrics.py
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from simulate.calculate_calibration_metrics import (
    calculate_metrics,
    validate_metrics,
    MAX_ABSOLUTE_RMSE,
    MAX_RMSE_DIFFERENCE
)

class TestCalculateMetrics:
    def test_calculate_metrics_basic(self):
        """Test basic metric calculation."""
        report = {
            "bkt_rmse": 0.10,
            "human_rmse": 0.12,
            "limitation_flag": False
        }
        
        metrics = calculate_metrics(report)
        
        assert metrics["bkt_rmse"] == 0.10
        assert metrics["human_rmse"] == 0.12
        assert metrics["absolute_rmse"] == 0.10
        assert abs(metrics["rmse_difference"] - 0.02) < 1e-6
        assert metrics["limitation_flag"] is False

    def test_calculate_metrics_with_synthetic_flag(self):
        """Test calculation when synthetic data flag is set."""
        report = {
            "bkt_rmse": 0.20,
            "human_rmse": 0.18,
            "limitation_flag": True
        }
        
        metrics = calculate_metrics(report)
        
        assert metrics["absolute_rmse"] == 0.20
        assert metrics["rmse_difference"] == 0.02
        assert metrics["limitation_flag"] is True

    def test_calculate_metrics_missing_fields(self):
        """Test that missing fields raise an error."""
        report = {
            "bkt_rmse": 0.10,
            # Missing human_rmse
            "limitation_flag": False
        }
        
        with pytest.raises(ValueError, match="missing required RMSE fields"):
            calculate_metrics(report)

class TestValidateMetrics:
    def test_validate_passes_within_thresholds(self):
        """Test validation passes when metrics are within thresholds."""
        metrics = {
            "absolute_rmse": 0.10,
            "rmse_difference": 0.01,
            "limitation_flag": False
        }
        
        assert validate_metrics(metrics) is True

    def test_validate_fails_absolute_rmse(self):
        """Test validation fails when absolute RMSE exceeds threshold."""
        metrics = {
            "absolute_rmse": 0.20,  # > 0.15
            "rmse_difference": 0.01,
            "limitation_flag": False
        }
        
        assert validate_metrics(metrics) is False

    def test_validate_fails_rmse_difference(self):
        """Test validation fails when RMSE difference exceeds threshold."""
        metrics = {
            "absolute_rmse": 0.10,
            "rmse_difference": 0.05,  # > 0.02
            "limitation_flag": False
        }
        
        assert validate_metrics(metrics) is False

    def test_validate_skips_for_synthetic_data(self):
        """Test that validation passes for synthetic data regardless of thresholds."""
        metrics = {
            "absolute_rmse": 0.50,  # Way above threshold
            "rmse_difference": 0.30,  # Way above threshold
            "limitation_flag": True
        }
        
        # Should return True (proceed) even though thresholds are breached
        assert validate_metrics(metrics) is True

    def test_validate_boundary_conditions(self):
        """Test validation at exact boundary values."""
        # At exact threshold - should pass
        metrics = {
            "absolute_rmse": MAX_ABSOLUTE_RMSE,
            "rmse_difference": MAX_RMSE_DIFFERENCE,
            "limitation_flag": False
        }
        assert validate_metrics(metrics) is True

        # Just above threshold - should fail
        metrics = {
            "absolute_rmse": MAX_ABSOLUTE_RMSE + 0.001,
            "rmse_difference": MAX_RMSE_DIFFERENCE,
            "limitation_flag": False
        }
        assert validate_metrics(metrics) is False

        metrics = {
            "absolute_rmse": MAX_ABSOLUTE_RMSE,
            "rmse_difference": MAX_RMSE_DIFFERENCE + 0.001,
            "limitation_flag": False
        }
        assert validate_metrics(metrics) is False