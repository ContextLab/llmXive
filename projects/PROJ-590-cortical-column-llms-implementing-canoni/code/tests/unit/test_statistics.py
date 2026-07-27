"""
Unit tests for statistics module.
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.statistics import load_gradient_norms, compare_gradient_stability

class TestLoadGradientNorms:
    """Tests for load_gradient_norms function."""

    def test_load_from_list_format(self, tmp_path):
        """Test loading from JSON with list format."""
        filepath = tmp_path / "norms.json"
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        with open(filepath, 'w') as f:
            json.dump(data, f)

        result = load_gradient_norms(str(filepath))
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]

    def test_load_from_dict_format(self, tmp_path):
        """Test loading from JSON with dict format containing 'norms' key."""
        filepath = tmp_path / "norms.json"
        data = {"norms": [1.0, 2.0, 3.0], "steps": [0, 1, 2]}
        with open(filepath, 'w') as f:
            json.dump(data, f)

        result = load_gradient_norms(str(filepath))
        assert result == [1.0, 2.0, 3.0]

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        filepath = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_gradient_norms(str(filepath))

    def test_invalid_format(self, tmp_path):
        """Test that ValueError is raised for invalid JSON format."""
        filepath = tmp_path / "invalid.json"
        with open(filepath, 'w') as f:
            json.dump({"other_key": [1, 2, 3]}, f)

        with pytest.raises(ValueError):
            load_gradient_norms(str(filepath))

    def test_non_numeric_values(self, tmp_path):
        """Test that ValueError is raised for non-numeric values."""
        filepath = tmp_path / "invalid.json"
        with open(filepath, 'w') as f:
            json.dump(["a", "b", "c"], f)

        with pytest.raises(ValueError):
            load_gradient_norms(str(filepath))

class TestCompareGradientStability:
    """Tests for compare_gradient_stability function."""

    def test_ks_test_identical_distributions(self, tmp_path):
        """Test KS test with identical distributions (should have high p-value)."""
        baseline_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        microcircuit_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        baseline_path = tmp_path / "baseline.json"
        microcircuit_path = tmp_path / "microcircuit.json"
        output_path = tmp_path / "result.json"

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(microcircuit_path, 'w') as f:
            json.dump(microcircuit_data, f)

        result = compare_gradient_stability(
            str(baseline_path),
            str(microcircuit_path),
            str(output_path)
        )

        assert result["ks_statistic"] >= 0.0
        assert result["p_value"] > 0.05  # High p-value for identical distributions
        assert result["stable"] is True

        # Verify output file was created
        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        assert saved_result == result

    def test_ks_test_different_distributions(self, tmp_path):
        """Test KS test with very different distributions (should have low p-value)."""
        baseline_data = [0.1, 0.15, 0.2, 0.25, 0.3]  # Low values
        microcircuit_data = [10.0, 12.0, 14.0, 16.0, 18.0]  # High values

        baseline_path = tmp_path / "baseline.json"
        microcircuit_path = tmp_path / "microcircuit.json"
        output_path = tmp_path / "result.json"

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(microcircuit_path, 'w') as f:
            json.dump(microcircuit_data, f)

        result = compare_gradient_stability(
            str(baseline_path),
            str(microcircuit_path),
            str(output_path)
        )

        assert result["ks_statistic"] > 0.0
        assert result["p_value"] < 0.05  # Low p-value for different distributions
        assert result["stable"] is False

    def test_insufficient_data(self, tmp_path):
        """Test that ValueError is raised for insufficient data."""
        baseline_data = [0.5]  # Only one sample
        microcircuit_data = [1.0]  # Only one sample

        baseline_path = tmp_path / "baseline.json"
        microcircuit_path = tmp_path / "microcircuit.json"
        output_path = tmp_path / "result.json"

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(microcircuit_path, 'w') as f:
            json.dump(microcircuit_data, f)

        with pytest.raises(ValueError, match="Insufficient data"):
            compare_gradient_stability(
                str(baseline_path),
                str(microcircuit_path),
                str(output_path)
            )

    def test_output_directory_creation(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        baseline_data = [0.1, 0.2, 0.3]
        microcircuit_data = [0.1, 0.2, 0.3]

        baseline_path = tmp_path / "baseline.json"
        microcircuit_path = tmp_path / "microcircuit.json"
        output_dir = tmp_path / "subdir" / "results"
        output_path = output_dir / "result.json"

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(microcircuit_path, 'w') as f:
            json.dump(microcircuit_data, f)

        result = compare_gradient_stability(
            str(baseline_path),
            str(microcircuit_path),
            str(output_path)
        )

        assert output_path.exists()

    def test_schema_compliance(self, tmp_path):
        """Test that output JSON has the required schema."""
        baseline_data = [0.1, 0.2, 0.3, 0.4, 0.5]
        microcircuit_data = [0.1, 0.2, 0.3, 0.4, 0.5]

        baseline_path = tmp_path / "baseline.json"
        microcircuit_path = tmp_path / "microcircuit.json"
        output_path = tmp_path / "result.json"

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(microcircuit_path, 'w') as f:
            json.dump(microcircuit_data, f)

        result = compare_gradient_stability(
            str(baseline_path),
            str(microcircuit_path),
            str(output_path)
        )

        # Verify schema
        assert "ks_statistic" in result
        assert "p_value" in result
        assert "stable" in result
        assert isinstance(result["ks_statistic"], float)
        assert isinstance(result["p_value"], float)
        assert isinstance(result["stable"], bool)