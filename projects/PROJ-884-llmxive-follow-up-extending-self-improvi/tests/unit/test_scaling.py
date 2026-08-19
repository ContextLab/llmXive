"""
Unit tests for the scalability analysis module.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import math

# Import the module under test
# Assuming the project root is added to sys.path or we run from code/
# We will use a relative import style compatible with the project structure
try:
    from code.analysis.scaling import (
        perform_log_log_regression, 
        determine_complexity_class, 
        analyze_scaling, 
        load_scaling_logs
    )
except ImportError:
    # Fallback for if the test runner sets up paths differently
    from analysis.scaling import (
        perform_log_log_regression, 
        determine_complexity_class, 
        analyze_scaling, 
        load_scaling_logs
    )


class TestLogLogRegression:
    def test_perfect_linear_complexity(self):
        """Test with data that perfectly fits O(n) -> slope should be 1.0"""
        # y = 2 * x
        data = [(1, 2), (2, 4), (3, 6), (4, 8), (5, 10)]
        slope, intercept, r_squared = perform_log_log_regression(data)
        
        assert math.isclose(slope, 1.0, rel_tol=1e-4)
        assert math.isclose(r_squared, 1.0, rel_tol=1e-4)

    def test_quadratic_complexity(self):
        """Test with data that fits O(n^2) -> slope should be 2.0"""
        # y = x^2
        data = [(1, 1), (2, 4), (3, 9), (4, 16), (5, 25)]
        slope, intercept, r_squared = perform_log_log_regression(data)
        
        assert math.isclose(slope, 2.0, rel_tol=1e-4)
        assert math.isclose(r_squared, 1.0, rel_tol=1e-4)

    def test_low_r_squared(self):
        """Test with noisy data resulting in low R^2"""
        # Random-ish data that doesn't fit a line well
        data = [(1, 1), (2, 10), (3, 2), (4, 20), (5, 5)]
        slope, intercept, r_squared = perform_log_log_regression(data)
        
        # Just ensure it runs and returns a valid number < 1
        assert 0.0 <= r_squared <= 1.0
        assert r_squared < 0.9  # Expecting low fit


class TestComplexityClass:
    def test_linear_class(self):
        assert determine_complexity_class(1.0, 0.95) == "O(n)"
    
    def test_quadratic_class(self):
        assert determine_complexity_class(2.0, 0.95) == "O(n^2)"
    
    def test_unknown_low_r_squared(self):
        # Even if slope is perfect, low R^2 should result in UNKNOWN
        assert determine_complexity_class(1.0, 0.5) == "UNKNOWN"
    
    def test_unknown_default_threshold(self):
        assert determine_complexity_class(1.0, 0.84) == "UNKNOWN"
    
    def test_unknown_high_threshold(self):
        assert determine_complexity_class(1.0, 0.85) == "O(n)"

    def test_constant_class(self):
        assert determine_complexity_class(0.0, 0.95) == "O(1)"
    
    def test_cubic_class(self):
        assert determine_complexity_class(3.0, 0.95) == "O(n^3)"


class TestEndToEnd:
    def test_analyze_scaling_creates_csv(self):
        """Test the full pipeline of loading, analyzing, and saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "logs.json")
            output_path = os.path.join(tmpdir, "analysis.csv")
            
            # Create mock data for O(n^2)
            mock_data = []
            for n in [10, 20, 30, 40, 50]:
                mock_data.append({"n": n, "time": n * n * 0.01})
            
            with open(input_path, "w") as f:
                json.dump(mock_data, f)
            
            results = analyze_scaling(input_path, output_path)
            
            assert os.path.exists(output_path)
            assert len(results) == 5
            
            # Check that all rows have the same complexity class (global fit)
            assert all(r["complexity_class"] == "O(n^2)" for r in results)
            assert all(r["r_squared"] > 0.99 for r in results) # Should be very high
            
            # Verify CSV content
            with open(output_path, "r") as f:
                content = f.read()
                assert "n,time,complexity_class,r_squared" in content
                assert "O(n^2)" in content

    def test_analyze_scaling_unknown_class(self):
        """Test with noisy data that results in UNKNOWN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "logs.json")
            output_path = os.path.join(tmpdir, "analysis.csv")
            
            # Noisy data
            mock_data = [
                {"n": 10, "time": 1.0},
                {"n": 20, "time": 100.0}, # Jump
                {"n": 30, "time": 2.0},
                {"n": 40, "time": 50.0},
                {"n": 50, "time": 3.0}
            ]
            
            with open(input_path, "w") as f:
                json.dump(mock_data, f)
            
            results = analyze_scaling(input_path, output_path)
            
            assert len(results) == 5
            # Should be UNKNOWN due to low R^2
            assert all(r["complexity_class"] == "UNKNOWN" for r in results)
            
            # Verify R^2 is low
            assert all(r["r_squared"] < 0.85 for r in results)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "nonexistent.json")
            output_path = os.path.join(tmpdir, "analysis.csv")
            
            with pytest.raises(FileNotFoundError):
                analyze_scaling(input_path, output_path)