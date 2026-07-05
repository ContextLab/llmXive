"""
Unit tests for statistical_tests.py
Verifies Wilcoxon Signed-Rank test implementation with known mock data.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

# Import the function to test
from code.statistical_tests import wilcoxon_signed_rank_test, run_statistical_analysis, load_metrics

class TestWilcoxonSignedRank:
    """Tests for the Wilcoxon Signed-Rank test implementation."""

    def test_wilcoxon_identical_groups(self):
        """Test that identical groups return p-value of 1.0 (or very close)."""
        group_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        group_b = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        result = wilcoxon_signed_rank_test(group_a, group_b, "test_metric")
        
        assert result["status"] == "passed"
        assert result["p_value"] == pytest.approx(1.0, abs=1e-6)
        assert result["metric"] == "test_metric"

    def test_wilcoxon_different_groups(self):
        """Test with groups that should show a significant difference."""
        # Group A: Low values
        group_a = [1.0, 1.5, 2.0, 2.5, 3.0]
        # Group B: High values
        group_b = [10.0, 11.0, 12.0, 13.0, 14.0]
        
        result = wilcoxon_signed_rank_test(group_a, group_b, "test_metric")
        
        assert result["status"] == "passed"
        assert result["p_value"] < 0.05  # Should be significant
        assert result["n_samples"] == 5

    def test_wilcoxon_empty_data(self):
        """Test handling of empty data."""
        result = wilcoxon_signed_rank_test([], [], "test_metric")
        assert result["status"] == "skipped"
        assert result["reason"] == "Empty data"

    def test_wilcoxon_mismatched_sizes(self):
        """Test handling of mismatched group sizes."""
        with pytest.raises(ValueError):
            wilcoxon_signed_rank_test([1, 2], [1], "test_metric")

    def test_wilcoxon_with_nan(self):
        """Test handling of NaN values (should be filtered or handled)."""
        # Our implementation filters out pairs with NaN
        group_a = [1.0, 2.0, float('nan'), 4.0]
        group_b = [1.0, 2.0, 3.0, 4.0]
        
        result = wilcoxon_signed_rank_test(group_a, group_b, "test_metric")
        
        # Should skip the NaN pair and run on the rest
        assert result["status"] in ["passed", "skipped"]
        if result["status"] == "passed":
            assert result["n_samples"] == 3

class TestRunStatisticalAnalysis:
    """Tests for the main analysis runner."""

    def test_run_analysis_creates_output(self):
        """Test that run_statistical_analysis creates a valid output file."""
        # Create temporary metrics file
        mock_data = [
            {
                "task_id": "test_1",
                "baseline_cyclomatic_complexity": 2.0,
                "generated_cyclomatic_complexity": 3.0,
                "baseline_halstead_volume": 10.0,
                "generated_halstead_volume": 12.0,
                "baseline_branch_coverage_pct": 80.0,
                "generated_branch_coverage_pct": 75.0
            },
            {
                "task_id": "test_2",
                "baseline_cyclomatic_complexity": 5.0,
                "generated_cyclomatic_complexity": 6.0,
                "baseline_halstead_volume": 20.0,
                "generated_halstead_volume": 22.0,
                "baseline_branch_coverage_pct": 90.0,
                "generated_branch_coverage_pct": 85.0
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_data, f)
            input_path = f.name

        output_path = input_path.replace('.json', '_results.json')

        try:
            result = run_statistical_analysis(input_path, output_path)
            
            assert "wilcoxon_tests" in result
            assert "cyclomatic_complexity" in result["wilcoxon_tests"]
            assert "halstead_volume" in result["wilcoxon_tests"]
            assert "branch_coverage_pct" in result["wilcoxon_tests"]
            
            # Verify file was written
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
                assert saved_data["sample_count"] == 2
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_run_analysis_missing_file(self):
        """Test handling of missing input file."""
        result = run_statistical_analysis("nonexistent.json")
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()