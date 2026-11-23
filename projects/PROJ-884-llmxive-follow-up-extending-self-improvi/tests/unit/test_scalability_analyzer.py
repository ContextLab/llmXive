"""
Unit tests for the Scalability Analyzer.

Task: T029b - Implement Scalability Analysis
"""
import pytest
import json
import math
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.scalability_analyzer import (
    load_scaling_logs,
    determine_complexity_class,
    perform_log_log_regression,
    save_results_csv,
    analyze_scaling,
    ScalingResult
)

class TestLoadScalingLogs:
    def test_load_valid_logs(self, tmp_path):
        """Test loading valid scaling logs."""
        data = [
            {"n": 10, "elapsed_seconds": 1.0},
            {"n": 20, "elapsed_seconds": 4.0}
        ]
        
        input_file = tmp_path / "scaling_raw_logs.json"
        input_file.write_text(json.dumps(data))
        
        result = load_scaling_logs(str(input_file))
        
        assert len(result) == 2
        assert result[0]["n"] == 10
        assert result[1]["n"] == 20

    def test_load_nonexistent_file(self):
        """Test loading from a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_scaling_logs("/nonexistent/path/file.json")

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises JSONDecodeError."""
        input_file = tmp_path / "invalid.json"
        input_file.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_scaling_logs(str(input_file))

    def test_load_non_list_json(self, tmp_path):
        """Test loading non-list JSON raises ValueError."""
        input_file = tmp_path / "not_list.json"
        input_file.write_text('{"key": "value"}')
        
        with pytest.raises(ValueError):
            load_scaling_logs(str(input_file))

class TestDetermineComplexityClass:
    def test_linear_complexity(self):
        """Test detection of O(n) complexity."""
        result = determine_complexity_class(1.0, 0.95)
        assert result == "O(n)"

    def test_quadratic_complexity(self):
        """Test detection of O(n^2) complexity."""
        result = determine_complexity_class(2.0, 0.95)
        assert result == "O(n^2)"

    def test_cubic_complexity(self):
        """Test detection of O(n^3) complexity."""
        result = determine_complexity_class(3.0, 0.95)
        assert result == "O(n^3)"

    def test_low_r_squared(self):
        """Test that low R-squared returns Unknown."""
        result = determine_complexity_class(1.5, 0.5)
        assert result == "Unknown"

    def test_constant_complexity(self):
        """Test detection of O(1) complexity."""
        result = determine_complexity_class(0.05, 0.95)
        assert result == "O(1)"

class TestPerformLogLogRegression:
    def test_perfect_linear_relationship(self):
        """Test regression with perfect linear relationship in log-log space."""
        # O(n) -> log(t) = log(n) + constant
        data = [
            {"n": 10, "elapsed_seconds": 1.0},
            {"n": 20, "elapsed_seconds": 2.0},
            {"n": 40, "elapsed_seconds": 4.0},
            {"n": 80, "elapsed_seconds": 8.0}
        ]
        
        slope, intercept, r_squared = perform_log_log_regression(data)
        
        assert abs(slope - 1.0) < 0.01
        assert r_squared > 0.99

    def test_quadratic_relationship(self):
        """Test regression with quadratic relationship."""
        # O(n^2) -> log(t) = 2*log(n) + constant
        data = [
            {"n": 10, "elapsed_seconds": 1.0},
            {"n": 20, "elapsed_seconds": 4.0},
            {"n": 40, "elapsed_seconds": 16.0},
            {"n": 80, "elapsed_seconds": 64.0}
        ]
        
        slope, intercept, r_squared = perform_log_log_regression(data)
        
        assert abs(slope - 2.0) < 0.01
        assert r_squared > 0.99

    def test_insufficient_data_points(self):
        """Test that less than 2 points raises ValueError."""
        data = [{"n": 10, "elapsed_seconds": 1.0}]
        
        with pytest.raises(ValueError):
            perform_log_log_regression(data)

    def test_empty_data(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError):
            perform_log_log_regression([])

    def test_handles_invalid_values(self, caplog):
        """Test that invalid values are skipped with warnings."""
        data = [
            {"n": 10, "elapsed_seconds": 1.0},
            {"n": 0, "elapsed_seconds": 2.0},  # Invalid
            {"n": 20, "elapsed_seconds": -1.0},  # Invalid
            {"n": 40, "elapsed_seconds": 4.0}
        ]
        
        slope, intercept, r_squared = perform_log_log_regression(data)
        
        # Should still work with valid points
        assert abs(slope - 1.0) < 0.1
        assert "Skipping entry" in caplog.text

class TestSaveResultsCsv:
    def test_save_results(self, tmp_path):
        """Test saving results to CSV."""
        results = [
            ScalingResult(n=10, time=1.0, complexity_class="O(n)", r_squared=0.95, status="PASS"),
            ScalingResult(n=20, time=2.0, complexity_class="O(n)", r_squared=0.95, status="PASS")
        ]
        
        output_file = tmp_path / "scaling_analysis.csv"
        save_results_csv(results, str(output_file))
        
        assert output_file.exists()
        
        # Read and verify contents
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3  # Header + 2 data rows
        assert "n,time,complexity_class,r_squared,status" in lines[0]

class TestAnalyzeScaling:
    def test_full_analysis(self, tmp_path):
        """Test complete scalability analysis."""
        # Create input data
        data = [
            {"n": 10, "elapsed_seconds": 1.0, "mode": "symbolic", "count": 5,
             "start_time": 0, "end_time": 1, "success_rate": 0.8,
             "total_successes": 4, "total_attempts": 5, "avg_wall_clock": 0.2,
             "total_energy_joules": 10.0, "population_stats": {}, "status": "SUCCESS"},
            {"n": 20, "elapsed_seconds": 4.0, "mode": "symbolic", "count": 5,
             "start_time": 0, "end_time": 4, "success_rate": 0.8,
             "total_successes": 4, "total_attempts": 5, "avg_wall_clock": 0.8,
             "total_energy_joules": 40.0, "population_stats": {}, "status": "SUCCESS"},
            {"n": 40, "elapsed_seconds": 16.0, "mode": "symbolic", "count": 5,
             "start_time": 0, "end_time": 16, "success_rate": 0.8,
             "total_successes": 4, "total_attempts": 5, "avg_wall_clock": 3.2,
             "total_energy_joules": 160.0, "population_stats": {}, "status": "SUCCESS"}
        ]
        
        input_file = tmp_path / "scaling_raw_logs.json"
        input_file.write_text(json.dumps(data))
        
        output_file = tmp_path / "scaling_analysis.csv"
        
        results = analyze_scaling(str(input_file), str(output_file))
        
        assert len(results) == 3
        assert output_file.exists()
        
        # Check that results have correct structure
        for result in results:
            assert result.n in [10, 20, 40]
            assert result.complexity_class in ["O(n^2)", "O(n^1.99)", "O(n^2.00)"]
            assert result.status == "PASS"
            assert result.r_squared > 0.99

    def test_low_r_squared_status(self, tmp_path):
        """Test that low R-squared results in INCONCLUSIVE status."""
        # Create data with poor fit
        data = [
            {"n": 10, "elapsed_seconds": 1.0},
            {"n": 20, "elapsed_seconds": 100.0},  # Outlier
            {"n": 40, "elapsed_seconds": 1.0}
        ]
        
        input_file = tmp_path / "scaling_raw_logs.json"
        input_file.write_text(json.dumps(data))
        
        output_file = tmp_path / "scaling_analysis.csv"
        
        results = analyze_scaling(str(input_file), str(output_file))
        
        # Should be INCONCLUSIVE due to low R-squared
        for result in results:
            assert result.status == "INCONCLUSIVE"
            assert result.r_squared < 0.85