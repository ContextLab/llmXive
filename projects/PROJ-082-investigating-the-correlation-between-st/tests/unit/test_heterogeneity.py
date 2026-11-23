"""
tests/unit/test_heterogeneity.py
Unit tests for I² calculation.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis.heterogeneity import calculate_i_squared, run_heterogeneity_analysis

class TestISquared:
    def test_skip_low_n(self):
        """Test that I² is skipped when N < 2."""
        r_vals = [0.1]
        se_vals = [0.05]
        result = calculate_i_squared(r_vals, se_vals)
        assert result["status"] == "skipped"
        assert "Need at least 2 studies" in result["reason"]

    def test_perfect_homogeneity(self):
        """Test I² = 0 when all effects are identical."""
        r_vals = [0.3, 0.3, 0.3, 0.3]
        se_vals = [0.05, 0.05, 0.05, 0.05]
        result = calculate_i_squared(r_vals, se_vals)
        assert result["status"] == "completed"
        assert result["i_squared"] == 0.0
        # Verify exactly two decimal places
        assert isinstance(result["i_squared"], float)

    def test_high_heterogeneity(self):
        """Test I² > 50% for highly variable data."""
        # Create data with high variance
        r_vals = [0.1, 0.9, 0.2, 0.8, 0.15, 0.85]
        se_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
        result = calculate_i_squared(r_vals, se_vals)
        assert result["status"] == "completed"
        assert result["i_squared"] > 50.0

    def test_precision_requirement(self):
        """Verify I² is reported with exactly two decimal places."""
        # Specific case to test rounding
        r_vals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        se_vals = [0.1] * 10
        result = calculate_i_squared(r_vals, se_vals)
        assert result["status"] == "completed"
        i_sq = result["i_squared"]
        # Check that it's a float with 2 decimal places
        assert isinstance(i_sq, float)
        # Verify rounding behavior
        assert round(i_sq, 2) == i_sq

    def test_negative_q_handling(self):
        """Test that negative Q (Q < df) results in I² = 0."""
        # Create data where Q might be less than df
        r_vals = [0.5, 0.5, 0.5, 0.5, 0.5]
        se_vals = [0.01, 0.01, 0.01, 0.01, 0.01]
        result = calculate_i_squared(r_vals, se_vals)
        assert result["status"] == "completed"
        assert result["i_squared"] == 0.0

class TestHeterogeneityAnalysis:
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project structure."""
        (tmp_path / "data" / "processed").mkdir(parents=True)
        (tmp_path / "data" / "derived").mkdir(parents=True)
        
        count_file = tmp_path / "data" / "processed" / "study_count.json"
        with open(count_file, "w") as f:
            json.dump({"N": 15}, f)
        
        results_file = tmp_path / "data" / "derived" / "results.json"
        studies = [
            {"r": 0.3 + i * 0.01, "se": 0.05 + i * 0.001}
            for i in range(15)
        ]
        with open(results_file, "w") as f:
            json.dump({"studies": studies}, f)
        
        return tmp_path

    def test_run_heterogeneity(self, temp_project_root, monkeypatch):
        """Test successful heterogeneity analysis run."""
        with patch("analysis.heterogeneity.get_project_root", return_value=temp_project_root):
            result = run_heterogeneity_analysis()
        
        assert result["status"] == "completed"
        assert "i_squared" in result
        assert "q_statistic" in result
        assert "degrees_of_freedom" in result
