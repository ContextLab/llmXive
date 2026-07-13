"""
Unit test for variance calculation across high-dependency apps.

This test verifies the `calculate_variance` function from 
`code/analysis/transfer.py` correctly computes the statistical variance 
of success rates for a specific subset of applications identified as 
having high state dependency.
"""
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from analysis.transfer import calculate_variance, identify_high_state_dependency_apps


class TestCalculateVariance:
    """Tests for the variance calculation logic in transfer.py."""

    def test_variance_calculation_basic(self):
        """Test variance calculation with a known simple dataset."""
        # Known success rates: [10, 20, 30, 40, 50]
        # Mean = 30
        # Variance (population) = ((10-30)^2 + (20-30)^2 + (30-30)^2 + (40-30)^2 + (50-30)^2) / 5
        # = (400 + 100 + 0 + 100 + 400) / 5 = 1000 / 5 = 200
        
        success_rates = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        result = calculate_variance(success_rates)
        
        assert abs(result - 200.0) < 1e-6, f"Expected 200.0, got {result}"

    def test_variance_single_value(self):
        """Variance of a single value should be 0."""
        success_rates = [42.5]
        result = calculate_variance(success_rates)
        assert result == 0.0, f"Expected 0.0 for single value, got {result}"

    def test_variance_empty_list(self):
        """Variance of an empty list should raise a ValueError."""
        success_rates = []
        try:
            calculate_variance(success_rates)
            assert False, "Expected ValueError for empty list"
        except ValueError:
            pass  # Expected

    def test_variance_identical_values(self):
        """Variance of identical values should be 0."""
        success_rates = [25.0, 25.0, 25.0, 25.0]
        result = calculate_variance(success_rates)
        assert result == 0.0, f"Expected 0.0 for identical values, got {result}"

    def test_variance_high_precision(self):
        """Test variance with floating point precision requirements."""
        # Rates: 0.1, 0.2, 0.3
        # Mean: 0.2
        # Var: ((0.1-0.2)^2 + (0.2-0.2)^2 + (0.3-0.2)^2) / 3
        # = (0.01 + 0 + 0.01) / 3 = 0.02 / 3 = 0.006666...
        success_rates = [0.1, 0.2, 0.3]
        result = calculate_variance(success_rates)
        expected = 0.02 / 3.0
        assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"

    def test_integration_with_high_dependency_filter(self):
        """
        Integration test: Filter a mock dataset for high-dependency apps
        and calculate variance on the filtered set.
        """
        # Create a temporary directory for mock data
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Mock experimental logs with success rates
            mock_logs = [
                {
                    "app_id": "app_001",
                    "state_dependency_score": 0.85,  # High
                    "success_rate": 0.90
                },
                {
                    "app_id": "app_002",
                    "state_dependency_score": 0.15,  # Low
                    "success_rate": 0.50
                },
                {
                    "app_id": "app_003",
                    "state_dependency_score": 0.92,  # High
                    "success_rate": 0.80
                },
                {
                    "app_id": "app_004",
                    "state_dependency_score": 0.88,  # High
                    "success_rate": 0.70
                },
                {
                    "app_id": "app_005",
                    "state_dependency_score": 0.20,  # Low
                    "success_rate": 0.60
                }
            ]
            
            logs_file = tmp_path / "experimental_logs.json"
            with open(logs_file, "w") as f:
                json.dump(mock_logs, f)
            
            # Mock threshold config
            config = {
                "high_dependency_threshold": 0.80
            }
            config_file = tmp_path / "config.json"
            with open(config_file, "w") as f:
                json.dump(config, f)
            
            # Load logs
            with open(logs_file, "r") as f:
                logs_data = json.load(f)
            
            # Identify high dependency apps
            high_dep_apps = identify_high_state_dependency_apps(
                logs_data, 
                threshold=0.80
            )
            
            # Extract success rates for these apps
            high_dep_rates = [app["success_rate"] for app in high_dep_apps]
            
            # Expected rates: 0.90, 0.80, 0.70
            assert len(high_dep_rates) == 3, f"Expected 3 high dependency apps, got {len(high_dep_rates)}"
            assert 0.90 in high_dep_rates
            assert 0.80 in high_dep_rates
            assert 0.70 in high_dep_rates
            
            # Calculate variance
            variance = calculate_variance(high_dep_rates)
            
            # Manual calculation:
            # Mean = (0.9 + 0.8 + 0.7) / 3 = 2.4 / 3 = 0.8
            # Var = ((0.9-0.8)^2 + (0.8-0.8)^2 + (0.7-0.8)^2) / 3
            # = (0.01 + 0 + 0.01) / 3 = 0.02 / 3 = 0.006666...
            expected_variance = 0.02 / 3.0
            
            assert abs(variance - expected_variance) < 1e-9, \
                f"Expected variance {expected_variance}, got {variance}"

    def test_variance_robustness_to_outliers(self):
        """Test that variance correctly reflects the impact of outliers."""
        # Normal distribution: 50, 50, 50
        # With outlier: 50, 50, 100
        rates_normal = [50.0, 50.0, 50.0]
        rates_outlier = [50.0, 50.0, 100.0]
        
        var_normal = calculate_variance(rates_normal)
        var_outlier = calculate_variance(rates_outlier)
        
        assert var_normal == 0.0
        assert var_outlier > var_normal, "Variance should increase with outlier"
        
        # Manual check for outlier set:
        # Mean = (50+50+100)/3 = 200/3 = 66.666...
        # Var = ((50-66.66)^2 + (50-66.66)^2 + (100-66.66)^2) / 3
        # = (277.77 + 277.77 + 1111.11) / 3 = 1666.66 / 3 = 555.555...
        expected_outlier_var = (
            (50 - 200/3)**2 + 
            (50 - 200/3)**2 + 
            (100 - 200/3)**2
        ) / 3.0
        
        assert abs(var_outlier - expected_outlier_var) < 1e-6, \
            f"Calculated variance {var_outlier} does not match expected {expected_outlier_var}"