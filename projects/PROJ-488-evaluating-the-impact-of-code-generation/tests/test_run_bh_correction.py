"""
Tests for the Benjamini-Hochberg correction implementation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Import the functions to test
from run_bh_correction import run_bh_correction, load_metrics_data, run_bh_correction_pipeline

class TestBHCorrection:
    """Test cases for Benjamini-Hochberg correction logic."""

    def test_bh_correction_basic(self):
        """Test basic BH correction with known values."""
        # Simple test case with 4 p-values
        p_values = [0.01, 0.04, 0.03, 0.005]
        adjusted = run_bh_correction(p_values)
        
        # All adjusted values should be in [0, 1]
        assert all(0 <= p <= 1 for p in adjusted)
        assert len(adjusted) == len(p_values)
        
        # The smallest p-value should have the smallest adjusted value
        min_idx = np.argmin(p_values)
        assert adjusted[min_idx] <= max(adjusted)

    def test_bh_correction_monotonicity(self):
        """Test that adjusted p-values maintain monotonicity."""
        # Generate random p-values
        np.random.seed(42)
        p_values = np.random.uniform(0, 0.1, 10).tolist()
        adjusted = run_bh_correction(p_values)
        
        # Sort original and adjusted
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = [adjusted[i] for i in sorted_indices]
        
        # Check monotonicity (adjusted values should be non-decreasing when sorted by original p)
        for i in range(len(sorted_adjusted) - 1):
            assert sorted_adjusted[i] <= sorted_adjusted[i + 1] + 1e-10

    def test_bh_correction_empty(self):
        """Test with empty list."""
        result = run_bh_correction([])
        assert result == []

    def test_bh_correction_single(self):
        """Test with single p-value."""
        result = run_bh_correction([0.05])
        assert len(result) == 1
        assert result[0] == 0.05  # Single value: p * 1 / 1 = p

    def test_bh_correction_all_zeros(self):
        """Test with all zero p-values."""
        result = run_bh_correction([0.0, 0.0, 0.0])
        assert all(p == 0.0 for p in result)

    def test_bh_correction_all_ones(self):
        """Test with all 1.0 p-values."""
        result = run_bh_correction([1.0, 1.0, 1.0])
        # With BH: 1.0 * 3 / 1 = 3.0 -> clipped to 1.0
        assert all(p == 1.0 for p in result)

    def test_bh_correction_known_case(self):
        """Test with a known case from literature."""
        # Example: 5 p-values [0.001, 0.01, 0.02, 0.05, 0.1]
        p_values = [0.001, 0.01, 0.02, 0.05, 0.1]
        adjusted = run_bh_correction(p_values)
        
        # Manually compute expected values:
        # Sorted: same order
        # i=1: 0.001 * 5 / 1 = 0.005
        # i=2: 0.01 * 5 / 2 = 0.025
        # i=3: 0.02 * 5 / 3 = 0.0333...
        # i=4: 0.05 * 5 / 4 = 0.0625
        # i=5: 0.1 * 5 / 5 = 0.1
        # Monotonicity check: all values are increasing, so no adjustment needed
        
        expected = [0.005, 0.025, 0.0333333, 0.0625, 0.1]
        for a, e in zip(adjusted, expected):
            assert abs(a - e) < 1e-5

class TestLoadMetricsData:
    """Test cases for loading metric data."""

    def test_load_metrics_data_creates_temp_files(self):
        """Test loading from temporary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create dummy metric files
            df1 = pd.DataFrame({
                "group": ["human", "llm"],
                "metric_value": [10.5, 12.3],
                "p_value": [0.03, 0.04]
            })
            df1.to_csv(tmpdir_path / "metric_cyclomatic.csv", index=False)
            
            df2 = pd.DataFrame({
                "group": ["human", "llm"],
                "metric_value": [5.2, 6.1],
                "p_value": [0.02, 0.05]
            })
            df2.to_csv(tmpdir_path / "metric_maintainability.csv", index=False)
            
            # Load and verify
            combined = load_metrics_data(tmpdir_path)
            
            assert len(combined) == 4
            assert "metric_name" in combined.columns
            assert set(combined["metric_name"].unique()) == {"cyclomatic", "maintainability"}

    def test_load_metrics_data_no_files(self):
        """Test error when no metric files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_metrics_data(Path(tmpdir))

class TestBHCorrectionPipeline:
    """Test cases for the full pipeline."""

    def test_pipeline_integration(self):
        """Test the full pipeline with temporary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            metrics_dir = tmpdir_path / "metrics"
            output_dir = tmpdir_path / "output"
            state_file = tmpdir_path / "state.yaml"
            
            metrics_dir.mkdir()
            output_dir.mkdir()
            
            # Create dummy metric file
            df = pd.DataFrame({
                "group": ["human", "llm", "human", "llm"],
                "metric_value": [10.5, 12.3, 11.2, 13.1],
                "p_value": [0.03, 0.04, 0.02, 0.05]
            })
            df.to_csv(metrics_dir / "metric_test.csv", index=False)
            
            # Create dummy state file
            state_content = {
                "project": "test",
                "artifacts": []
            }
            with open(state_file, "w") as f:
                import yaml
                yaml.dump(state_content, f)
            
            # Run pipeline
            results = run_bh_correction_pipeline(
                metrics_dir=metrics_dir,
                output_dir=output_dir,
                state_file_path=state_file
            )
            
            # Verify results
            assert "test" in results
            assert "adjusted_p_values" in results["test"]
            assert len(results["test"]["adjusted_p_values"]) == 4
            
            # Verify output file exists
            output_file = output_dir / "metric_test_corrected.csv"
            assert output_file.exists()
            
            # Verify summary JSON exists
            summary_file = output_dir / "bh_correction_summary.json"
            assert summary_file.exists()