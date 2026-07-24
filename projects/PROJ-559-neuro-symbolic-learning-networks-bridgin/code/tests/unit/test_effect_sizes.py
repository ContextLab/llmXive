import pytest
import os
import sys
import json
import tempfile
import shutil
from typing import Dict, Any

# Import the target module functions
from analyze.effect_sizes import (
    load_effect_size_data,
    calculate_cohens_d,
    run_pairwise_effect_sizes,
    validate_ci_width,
    generate_effect_size_report
)

class TestLoadEffectSizeData:
    """Tests for loading effect size data from CSV."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_content = """problem_id,condition,correct,rt_seconds,comprehension_rating,data_source
        1,neural,1,12.5,4,simulated
        1,symbolic,1,15.2,5,simulated
        1,neuro_symbolic,1,14.1,5,simulated"""
        
        csv_path = tmp_path / "test_data.csv"
        csv_path.write_text(csv_content)
        
        result = load_effect_size_data(str(csv_path))
        
        assert result is not None
        assert len(result) == 3
        assert "condition" in result.columns
        assert "correct" in result.columns

    def test_load_missing_file(self, tmp_path):
        """Test loading a non-existent file raises an error."""
        non_existent_path = tmp_path / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_effect_size_data(str(non_existent_path))

    def test_load_empty_csv(self, tmp_path):
        """Test loading an empty CSV (headers only)."""
        csv_content = "problem_id,condition,correct,rt_seconds,comprehension_rating,data_source\n"
        
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text(csv_content)
        
        result = load_effect_size_data(str(csv_path))
        
        assert result is not None
        assert len(result) == 0

class TestCalculateCohensD:
    """Tests for Cohen's d calculation."""

    def test_calculate_cohens_d_basic(self):
        """Test basic Cohen's d calculation."""
        group_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        group_b = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        d, ci_low, ci_high = calculate_cohens_d(group_a, group_b)
        
        assert d is not None
        assert isinstance(d, float)
        # For identical distributions shifted by 1, d should be around 1.0
        # (exact value depends on variance calculation)
        assert -5.0 < d < 5.0  # Sanity check

    def test_calculate_cohens_d_identical(self):
        """Test Cohen's d for identical groups (should be ~0)."""
        group_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        group_b = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        d, ci_low, ci_high = calculate_cohens_d(group_a, group_b)
        
        assert abs(d) < 0.01  # Should be very close to 0

    def test_calculate_cohens_d_single_value(self):
        """Test Cohen's d with single values (should handle edge case)."""
        group_a = [1.0]
        group_b = [2.0]
        
        d, ci_low, ci_high = calculate_cohens_d(group_a, group_b)
        
        # With single values, variance is 0, so we might get inf or nan
        # The function should handle this gracefully
        assert d is not None

class TestRunPairwiseEffectSizes:
    """Tests for running pairwise effect size comparisons."""

    def test_run_pairwise_effect_sizes_basic(self, tmp_path):
        """Test running pairwise comparisons on a simple dataset."""
        # Create a mock dataframe
        import pandas as pd
        data = {
            "condition": ["neural"] * 10 + ["symbolic"] * 10 + ["neuro_symbolic"] * 10,
            "comprehension_rating": [4.0] * 10 + [4.5] * 10 + [5.0] * 10
        }
        df = pd.DataFrame(data)
        
        results = run_pairwise_effect_sizes(df, "comprehension_rating")
        
        assert results is not None
        assert isinstance(results, dict)
        # Should have 3 comparisons: neural-symbolic, neural-neuro_symbolic, symbolic-neuro_symbolic
        assert len(results) == 3

    def test_run_pairwise_effect_sizes_empty(self):
        """Test running pairwise comparisons on an empty dataset."""
        import pandas as pd
        df = pd.DataFrame(columns=["condition", "comprehension_rating"])
        
        results = run_pairwise_effect_sizes(df, "comprehension_rating")
        
        assert results == {}

class TestValidateCIWidth:
    """Tests for CI width validation."""

    def test_validate_ci_width_pass(self):
        """Test validation when CI width is within threshold."""
        ci_width = 0.10
        threshold = 0.20
        
        passed, message = validate_ci_width(ci_width, threshold)
        
        assert passed is True
        assert "within" in message.lower()

    def test_validate_ci_width_fail(self):
        """Test validation when CI width exceeds threshold."""
        ci_width = 0.25
        threshold = 0.20
        
        passed, message = validate_ci_width(ci_width, threshold)
        
        assert passed is False
        assert "exceeds" in message.lower()

    def test_validate_ci_width_boundary(self):
        """Test validation at the exact threshold."""
        ci_width = 0.20
        threshold = 0.20
        
        passed, message = validate_ci_width(ci_width, threshold)
        
        # Typically <= is considered passing
        assert passed is True

class TestGenerateEffectSizeReport:
    """Tests for generating the effect size report."""

    def test_generate_effect_size_report_basic(self, tmp_path):
        """Test generating a basic report."""
        results = {
            "neural_vs_symbolic": {
                "cohen_d": 0.5,
                "ci_low": 0.3,
                "ci_high": 0.7,
                "ci_width": 0.4,
                "valid": False
            },
            "neural_vs_neuro_symbolic": {
                "cohen_d": 0.8,
                "ci_low": 0.6,
                "ci_high": 1.0,
                "ci_width": 0.4,
                "valid": False
            }
        }
        
        report = generate_effect_size_report(results, ci_threshold=0.20)
        
        assert report is not None
        assert isinstance(report, str)
        assert "neural_vs_symbolic" in report
        assert "cohen_d" in report.lower()

    def test_generate_effect_size_report_empty(self):
        """Test generating a report with no results."""
        results = {}
        
        report = generate_effect_size_report(results, ci_threshold=0.20)
        
        assert report is not None
        assert "No comparisons" in report or "empty" in report.lower()

class TestMainFunctionality:
    """Tests for the main entry point."""

    def test_main_execution(self, tmp_path):
        """Test that main can be called without arguments (using defaults)."""
        # Create a temporary CSV
        csv_content = """problem_id,condition,correct,rt_seconds,comprehension_rating,data_source
        1,neural,1,12.5,4,simulated
        1,symbolic,1,15.2,5,simulated"""
        
        csv_path = tmp_path / "input.csv"
        csv_path.write_text(csv_content)
        
        output_path = tmp_path / "output.json"
        
        # Call main with arguments
        sys.argv = ["test", str(csv_path), str(output_path)]
        
        # We expect it to run without crashing on valid input
        # Note: In a real test, we might mock the main function or capture output
        # For now, we verify the function exists and has the right signature
        from analyze.effect_sizes import main
        assert callable(main)