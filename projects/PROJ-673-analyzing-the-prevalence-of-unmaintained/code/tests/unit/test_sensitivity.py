"""
Unit tests for the sensitivity analysis module.
"""
import pytest
import json
import tempfile
from pathlib import Path
import numpy as np

from src.analysis.sensitivity import (
    calculate_unmaintained_ratio,
    calculate_correlation_with_maintenance_status,
    run_threshold_sweep,
    run_sensitivity_analysis
)

# Sample mock data for testing
MOCK_DEPENDENCIES = [
    {"name": "pkg1", "age_in_days": 100, "vulnerability_count": 5},
    {"name": "pkg2", "age_in_days": 50, "vulnerability_count": 2},
    {"name": "pkg3", "age_in_days": 400, "vulnerability_count": 10},
    {"name": "pkg4", "age_in_days": 200, "vulnerability_count": 0},
    {"name": "pkg5", "age_in_days": 10, "vulnerability_count": 1},
    {"name": "pkg6", "age_in_days": None, "vulnerability_count": 3}, # Should be skipped
]

class TestCalculateUnmaintainedRatio:
    def test_ratio_calculation(self):
        """Test basic ratio calculation."""
        # 30 days threshold: pkg1, pkg3, pkg4 are unmaintained (3/5 valid)
        ratio = calculate_unmaintained_ratio(MOCK_DEPENDENCIES, 30)
        assert ratio == 0.6  # 3 out of 5 valid entries

    def test_high_threshold(self):
        """Test with a threshold higher than any age."""
        ratio = calculate_unmaintained_ratio(MOCK_DEPENDENCIES, 500)
        assert ratio == 0.0

    def test_low_threshold(self):
        """Test with a threshold lower than any age."""
        ratio = calculate_unmaintained_ratio(MOCK_DEPENDENCIES, 5)
        # pkg1, pkg2, pkg3, pkg4 are unmaintained (4/5 valid)
        assert ratio == 0.8

    def test_empty_list(self):
        """Test with empty list."""
        ratio = calculate_unmaintained_ratio([], 30)
        assert ratio == 0.0

    def test_all_null_ages(self):
        """Test with all null ages."""
        null_deps = [{"name": "x", "age_in_days": None}]
        ratio = calculate_unmaintained_ratio(null_deps, 30)
        assert ratio == 0.0

class TestCalculateCorrelationWithMaintenanceStatus:
    def test_correlation_calculation(self):
        """Test correlation calculation on a subset."""
        # Threshold 100: only pkg3 (400 days) is unmaintained.
        # N=1 -> returns (0.0, 1.0)
        rho, p = calculate_correlation_with_maintenance_status(MOCK_DEPENDENCIES, 100)
        assert rho == 0.0
        assert p == 1.0

    def test_correlation_with_sufficient_data(self):
        """Test correlation with enough data points."""
        # Threshold 40: pkg1 (100), pkg3 (400), pkg4 (200) are unmaintained.
        # Ages: [100, 400, 200], Vulns: [5, 10, 0]
        rho, p = calculate_correlation_with_maintenance_status(MOCK_DEPENDENCIES, 40)
        assert isinstance(rho, float)
        assert isinstance(p, float)
        assert -1.0 <= rho <= 1.0
        assert 0.0 <= p <= 1.0

    def test_insufficient_data(self):
        """Test behavior when subset is too small."""
        # Threshold 450: No packages > 450
        rho, p = calculate_correlation_with_maintenance_status(MOCK_DEPENDENCIES, 450)
        assert rho == 0.0
        assert p == 1.0

class TestRunThresholdSweep:
    def test_sweep_output_structure(self):
        """Verify the structure of the sweep results."""
        results = run_threshold_sweep(MOCK_DEPENDENCIES, [30, 100])
        
        assert isinstance(results, list)
        assert len(results) == 2
        
        for res in results:
            assert "threshold_days" in res
            assert "unmaintained_ratio" in res
            assert "correlation_coefficient" in res
            assert "p_value" in res

class TestSensitivityAnalysisIntegration:
    def test_end_to_end_execution(self):
        """Test the full pipeline writing to a temp file."""
        # Create a temporary CSV file
        import pandas as pd
        df = pd.DataFrame(MOCK_DEPENDENCIES)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test_deps.csv"
            output_path = Path(tmpdir) / "test_sensitivity.json"
            
            df.to_csv(input_path, index=False)
            
            result = run_sensitivity_analysis(str(input_path), str(output_path))
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify result content
            assert "threshold_sweep" in result
            assert len(result["threshold_sweep"]) > 0
            
            # Verify JSON content matches
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
