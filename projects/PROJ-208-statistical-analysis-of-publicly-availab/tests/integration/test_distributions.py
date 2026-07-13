"""
Integration test for distribution fitting output format (US2).

This test verifies that the distribution analysis pipeline:
1. Produces valid ECDF plots (log-scale x-axis)
2. Generates distribution fit metrics (log-normal, Weibull)
3. Outputs results in the expected JSON schema
4. Detects extreme outliers correctly

Prerequisites:
- cleaned_issues.csv must exist in data/processed/ (from US1)
- distribution_fitting.py must be implemented (T015, T016)
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_config, get_path
from utils.validators import validate_dataset_schema, ValidationError


class TestDistributionFittingOutput:
    """Integration tests for distribution fitting output format."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.config = get_config()
        self.processed_dir = get_path("processed")
        self.figures_dir = get_path("figures")
        self.cleaned_file = self.processed_dir / "cleaned_issues.csv"
        self.metrics_file = self.processed_dir / "distribution_metrics.json"
        
        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

    def _create_mock_cleaned_data(self, n_samples: int = 1000):
        """Create a mock cleaned dataset for testing if real data doesn't exist."""
        if not self.cleaned_file.exists():
            # Generate realistic mock data for testing
            np.random.seed(42)
            
            # Simulate resolution times (log-normal distributed)
            resolution_times = np.random.lognormal(
                mean=2.5, sigma=1.2, size=n_samples
            )
            # Add some extreme outliers (>30 days = 720 hours)
            outliers = np.random.uniform(720, 2000, size=int(n_samples * 0.05))
            resolution_times = np.concatenate([resolution_times, outliers])
            
            # Create DataFrame with required columns
            data = {
                "issue_id": range(n_samples + len(outliers)),
                "repository": ["repo"] * len(resolution_times),
                "language": ["Python"] * len(resolution_times),
                "resolution_time_hours": resolution_times,
                "created_at": ["2023-01-01"] * len(resolution_times),
                "closed_at": ["2023-01-02"] * len(resolution_times),
                "is_pull_request": [False] * len(resolution_times),
                "has_labels": [True] * len(resolution_times),
                "comment_count": np.random.randint(0, 20, len(resolution_times)),
            }
            
            df = pd.DataFrame(data)
            df.to_csv(self.cleaned_file, index=False)
            return True
        return False

    def test_distribution_metrics_json_schema(self):
        """Test that distribution metrics JSON has expected schema."""
        # Ensure we have data to work with
        self._create_mock_cleaned_data()
        
        # Import the distribution fitting module
        # Note: This assumes T015 and T016 are implemented
        try:
            from analysis.distribution_fitting import (
                fit_distributions,
                generate_ecdf_plot,
                detect_outliers,
                main as distribution_main
            )
        except ImportError:
            pytest.skip(
                "Distribution fitting module not yet implemented (T015/T016)"
            )
            return

        # Run the distribution analysis
        try:
            distribution_main()
        except Exception as e:
            pytest.fail(f"Distribution analysis failed: {e}")

        # Verify output file exists
        assert self.metrics_file.exists(), (
            f"Metrics file not created: {self.metrics_file}"
        )

        # Load and validate JSON schema
        with open(self.metrics_file, "r") as f:
            metrics = json.load(f)

        # Check required top-level keys
        required_keys = [
            "log_normal_fit",
            "weibull_fit",
            "outlier_summary",
            "dataset_info",
            "fit_quality",
        ]
        for key in required_keys:
            assert key in metrics, f"Missing required key: {key}"

        # Validate log-normal fit structure
        log_normal = metrics["log_normal_fit"]
        assert "parameters" in log_normal, "Missing log-normal parameters"
        assert "ks_statistic" in log_normal, "Missing KS statistic"
        assert "p_value" in log_normal, "Missing p-value"
        assert "aic" in log_normal, "Missing AIC"
        
        params = log_normal["parameters"]
        assert "loc" in params, "Missing loc parameter"
        assert "scale" in params, "Missing scale parameter"
        assert "shape" in params, "Missing shape parameter"

        # Validate Weibull fit structure
        weibull = metrics["weibull_fit"]
        assert "parameters" in weibull, "Missing Weibull parameters"
        assert "ks_statistic" in weibull, "Missing KS statistic"
        assert "p_value" in weibull, "Missing p-value"
        assert "aic" in weibull, "Missing AIC"

        # Validate outlier summary
        outliers = metrics["outlier_summary"]
        assert "count" in outliers, "Missing outlier count"
        assert "percentage" in outliers, "Missing outlier percentage"
        assert "threshold_hours" in outliers, "Missing threshold"
        
        assert outliers["threshold_hours"] == 720, (
            "Outlier threshold should be 720 hours (30 days)"
        )

        # Validate dataset info
        dataset_info = metrics["dataset_info"]
        assert "total_issues" in dataset_info, "Missing total issues count"
        assert "mean_resolution_time" in dataset_info, "Missing mean"
        assert "median_resolution_time" in dataset_info, "Missing median"
        assert "std_resolution_time" in dataset_info, "Missing std"

        # Validate fit quality
        fit_quality = metrics["fit_quality"]
        assert "best_model" in fit_quality, "Missing best model designation"
        assert fit_quality["best_model"] in [
            "log_normal",
            "weibull",
        ], "Invalid best model"

    def test_ecdf_plot_generation(self):
        """Test that ECDF plots are generated with correct format."""
        # Ensure we have data to work with
        self._create_mock_cleaned_data()

        try:
            from analysis.distribution_fitting import generate_ecdf_plot
        except ImportError:
            pytest.skip(
                "Distribution fitting module not yet implemented (T015)"
            )
            return

        # Generate ECDF plot
        try:
            ecdf_path = generate_ecdf_plot(
                self.cleaned_file, self.figures_dir / "ecdf_resolution_times.png"
            )
        except Exception as e:
            pytest.fail(f"ECDF plot generation failed: {e}")

        # Verify plot file exists
        assert ecdf_path.exists(), f"ECDF plot not created: {ecdf_path}"
        
        # Verify file size is reasonable (> 10KB for a real plot)
        assert ecdf_path.stat().st_size > 10240, (
            "ECDF plot file too small - may be empty or corrupted"
        )

    def test_outlier_detection_accuracy(self):
        """Test that outlier detection correctly identifies >30 day issues."""
        # Create data with known outliers
        self._create_mock_cleaned_data(n_samples=500)
        
        # Load the data
        df = pd.read_csv(self.cleaned_file)
        resolution_times = df["resolution_time_hours"]
        
        # Expected outliers (>720 hours)
        expected_outliers = resolution_times[resolution_times > 720]
        expected_count = len(expected_outliers)
        
        # Run distribution analysis
        try:
            from analysis.distribution_fitting import detect_outliers
        except ImportError:
            pytest.skip(
                "Distribution fitting module not yet implemented (T017)"
            )
            return

        try:
            outliers = detect_outliers(self.cleaned_file, threshold_hours=720)
        except Exception as e:
            pytest.fail(f"Outlier detection failed: {e}")

        # Verify outlier count matches
        assert outliers["count"] == expected_count, (
            f"Expected {expected_count} outliers, got {outliers['count']}"
        )
        
        # Verify percentage calculation
        expected_percentage = (expected_count / len(resolution_times)) * 100
        assert abs(outliers["percentage"] - expected_percentage) < 0.01, (
            f"Percentage mismatch: expected {expected_percentage}, "
            f"got {outliers['percentage']}"
        )

    def test_distribution_fitting_on_real_data(self):
        """Test distribution fitting with actual cleaned data format."""
        # Ensure we have data
        self._create_mock_cleaned_data()
        
        # Load data
        df = pd.read_csv(self.cleaned_file)
        
        # Verify required column exists
        assert "resolution_time_hours" in df.columns, (
            "Missing resolution_time_hours column"
        )
        
        # Verify no negative values
        assert (df["resolution_time_hours"] >= 0).all(), (
            "Found negative resolution times"
        )
        
        # Verify we have enough data points
        assert len(df) >= 100, (
            f"Insufficient data points: {len(df)} (need >= 100)"
        )

    def test_json_serialization_completeness(self):
        """Test that all metrics can be serialized to JSON without errors."""
        # Ensure we have data
        self._create_mock_cleaned_data()
        
        # Run analysis
        try:
            from analysis.distribution_fitting import main as distribution_main
            distribution_main()
        except ImportError:
            pytest.skip("Distribution fitting module not yet implemented")
            return
        except Exception as e:
            pytest.fail(f"Distribution analysis failed: {e}")
        
        # Load metrics
        with open(self.metrics_file, "r") as f:
            metrics = json.load(f)
        
        # Convert to JSON string to ensure full serialization
        json_str = json.dumps(metrics, indent=2)
        
        # Parse back to ensure round-trip works
        reparsed = json.loads(json_str)
        
        assert reparsed == metrics, "JSON round-trip failed"
        
        # Verify no NaN or Inf values
        def check_no_nan_inf(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    check_no_nan_inf(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_no_nan_inf(v, f"{path}[{i}]")
            elif isinstance(obj, float):
                assert not np.isnan(obj), f"NaN found at {path}"
                assert not np.isinf(obj), f"Inf found at {path}"
        
        check_no_nan_inf(metrics)