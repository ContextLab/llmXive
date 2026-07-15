"""
Tests for Task T029: Cliff's delta analysis module.
"""

import pytest
import os
import sys
import json
import math
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from cliffs_delta_analysis import (
    load_metric_values,
    compute_cliffs_delta_for_all_metrics,
    write_results_to_file,
    get_effect_size_magnitude
)

# Import the statistical functions directly
from statistical_analysis import compute_cliffs_delta, get_effect_size_magnitude as get_mag


class TestCliffsDeltaMagnitude:
    """Test magnitude classification of Cliff's delta values."""

    def test_negligible_effect(self):
        """Test that small values are classified as negligible."""
        assert get_mag(0.05) == "negligible"
        assert get_mag(-0.05) == "negligible"
        assert get_mag(0.14) == "negligible"
        assert get_mag(-0.14) == "negligible"

    def test_small_effect(self):
        """Test that small effect sizes are classified correctly."""
        assert get_mag(0.15) == "small"
        assert get_mag(-0.15) == "small"
        assert get_mag(0.32) == "small"
        assert get_mag(-0.32) == "small"

    def test_medium_effect(self):
        """Test that medium effect sizes are classified correctly."""
        assert get_mag(0.33) == "medium"
        assert get_mag(-0.33) == "medium"
        assert get_mag(0.47) == "medium"
        assert get_mag(-0.47) == "medium"

    def test_large_effect(self):
        """Test that large effect sizes are classified correctly."""
        assert get_mag(0.48) == "large"
        assert get_mag(-0.48) == "large"
        assert get_mag(0.9) == "large"
        assert get_mag(-0.9) == "large"


class TestCliffsDeltaComputation:
    """Test Cliff's delta computation."""

    def test_identical_distributions(self):
        """Test that identical distributions yield delta close to 0."""
        data = [1, 2, 3, 4, 5]
        delta = compute_cliffs_delta(data, data)
        assert abs(delta) < 0.01  # Should be very close to 0

    def test_opposite_distributions(self):
        """Test that well-separated distributions yield large delta."""
        # All values in group A are less than all values in group B
        group_a = [1, 2, 3]
        group_b = [10, 11, 12]
        delta = compute_cliffs_delta(group_a, group_b)
        assert delta > 0.8  # Should be large positive

    def test_reversed_opposite(self):
        """Test reversed order yields negative delta."""
        group_a = [10, 11, 12]
        group_b = [1, 2, 3]
        delta = compute_cliffs_delta(group_a, group_b)
        assert delta < -0.8  # Should be large negative


class TestLoadMetricValues:
    """Test loading metric values from CSV files."""

    @pytest.fixture
    def temp_csv(self, tmp_path):
        """Create a temporary CSV file for testing."""
        csv_file = tmp_path / "test_metric.csv"
        csv_file.write_text(
            "snippet_id,group,value\n"
            "1,human,10.5\n"
            "2,human,12.3\n"
            "3,llm,15.2\n"
            "4,llm,14.8\n"
        )
        return csv_file

    def test_load_valid_csv(self, temp_csv):
        """Test loading values from a valid CSV file."""
        human, llm = load_metric_values(temp_csv, "value")
        assert len(human) == 2
        assert len(llm) == 2
        assert human == [10.5, 12.3]
        assert llm == [15.2, 14.8]

    def test_load_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        missing_file = tmp_path / "nonexistent.csv"
        with pytest.raises(FileNotFoundError):
            load_metric_values(missing_file, "value")


class TestWriteResults:
    """Test writing results to file."""

    def test_write_json_results(self, tmp_path):
        """Test writing results to a JSON file."""
        results = {
            "metric1": {"cliffs_delta": 0.5, "magnitude": "large"},
            "metric2": {"cliffs_delta": 0.2, "magnitude": "small"}
        }
        output_file = tmp_path / "results.json"

        write_results_to_file(results, output_file)

        assert output_file.exists()
        with open(output_file) as f:
            loaded = json.load(f)
        assert loaded == results

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        results = {"test": {"cliffs_delta": 0.1, "magnitude": "negligible"}}
        output_file = tmp_path / "subdir" / "nested" / "results.json"

        write_results_to_file(results, output_file)

        assert output_file.exists()


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_compute_cliffs_delta_for_all_metrics_no_files(self, tmp_path):
        """Test behavior when no metric files exist."""
        with patch('cliffs_delta_analysis.METRICS_DIR', tmp_path):
            results = compute_cliffs_delta_for_all_metrics()
            assert results == {}

    def test_compute_with_mocked_metrics(self, tmp_path):
        """Test computation with mocked metric data."""
        # Create mock metric files
        metrics_dir = tmp_path / "metrics"
        metrics_dir.mkdir()

        (metrics_dir / "complexity.csv").write_text(
            "snippet_id,group,value\n"
            "1,human,5.0\n"
            "2,human,6.0\n"
            "3,llm,8.0\n"
            "4,llm,9.0\n"
        )

        with patch('cliffs_delta_analysis.METRICS_DIR', metrics_dir):
            with patch('cliffs_delta_analysis.RESULTS_DIR', tmp_path / "results"):
                with patch('cliffs_delta_analysis.STATE_FILE', tmp_path / "state.yaml"):
                    results = compute_cliffs_delta_for_all_metrics()

        assert "complexity" in results
        assert "cliffs_delta" in results["complexity"]
        assert "magnitude" in results["complexity"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])