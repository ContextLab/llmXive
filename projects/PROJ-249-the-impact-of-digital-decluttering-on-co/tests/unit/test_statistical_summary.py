"""
Unit tests for statistical summary generation (T040).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Mock the config and other dependencies for testing
import sys
from unittest.mock import patch, MagicMock

# Add code to path if not already
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from analysis.statistical_summary import aggregate_results, write_summary, load_p_values_from_json

class TestLoadPValuesFromJson:
    def test_load_valid_json(self, tmp_path):
        test_data = {"sart": 0.03, "ospan": 0.15}
        file_path = tmp_path / "test_pvalues.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        result = load_p_values_from_json(str(file_path))
        assert result == {"sart": 0.03, "ospan": 0.15}

    def test_load_empty_json(self, tmp_path):
        file_path = tmp_path / "empty.json"
        with open(file_path, 'w') as f:
            json.dump({}, f)

        result = load_p_values_from_json(str(file_path))
        assert result == {}

    def test_load_nonexistent_file(self, tmp_path):
        result = load_p_values_from_json(str(tmp_path / "nonexistent.json"))
        assert result == {}

    def test_load_invalid_json(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("not valid json")

        result = load_p_values_from_json(str(file_path))
        assert result == {}

class TestAggregateResults:
    def test_aggregate_all_sources(self, tmp_path):
        # Create mock input files
        change_data = {"sart": -2.5, "ospan": 5.0}
        change_file = tmp_path / "change.json"
        with open(change_file, 'w') as f:
            json.dump(change_data, f)

        bootstrap_data = {
            "sart": {"ci_lower": -4.0, "ci_upper": -1.0, "p_value": 0.01},
            "ospan": {"ci_lower": 2.0, "ci_upper": 8.0, "p_value": 0.005}
        }
        bootstrap_file = tmp_path / "bootstrap.json"
        with open(bootstrap_file, 'w') as f:
            json.dump(bootstrap_data, f)

        holm_data = {"sart": 0.02, "ospan": 0.01}
        holm_file = tmp_path / "holm.json"
        with open(holm_file, 'w') as f:
            json.dump(holm_data, f)

        summary = aggregate_results(
            str(change_file),
            str(bootstrap_file),
            str(holm_file)
        )

        assert "metrics" in summary
        assert "sart" in summary["metrics"]
        assert "ospan" in summary["metrics"]

        # Check SART
        sart = summary["metrics"]["sart"]
        assert sart["mean_change"] == -2.5
        assert sart["ci_95_lower"] == -4.0
        assert sart["ci_95_upper"] == -1.0
        assert sart["p_value_raw"] == 0.01
        assert sart["p_value_corrected"] == 0.02
        assert sart["significant_after_correction"] is True

        # Check OSPAN
        ospan = summary["metrics"]["ospan"]
        assert ospan["mean_change"] == 5.0
        assert ospan["ci_95_lower"] == 2.0
        assert ospan["ci_95_upper"] == 8.0
        assert ospan["p_value_raw"] == 0.005
        assert ospan["p_value_corrected"] == 0.01
        assert ospan["significant_after_correction"] is True

    def test_aggregate_partial_data(self, tmp_path):
        # Only change scores available
        change_data = {"sart": -2.5}
        change_file = tmp_path / "change.json"
        with open(change_file, 'w') as f:
            json.dump(change_data, f)

        # Empty bootstrap and holm
        bootstrap_file = tmp_path / "bootstrap.json"
        with open(bootstrap_file, 'w') as f:
            json.dump({}, f)

        holm_file = tmp_path / "holm.json"
        with open(holm_file, 'w') as f:
            json.dump({}, f)

        summary = aggregate_results(
            str(change_file),
            str(bootstrap_file),
            str(holm_file)
        )

        sart = summary["metrics"]["sart"]
        assert sart["mean_change"] == -2.5
        assert sart["ci_95_lower"] is None
        assert sart["p_value_corrected"] is None
        assert sart["significant_after_correction"] is False

class TestWriteSummary:
    def test_write_summary_creates_file(self, tmp_path):
        summary = {
            "metrics": {
                "sart": {
                    "mean_change": -2.5,
                    "ci_95_lower": -4.0,
                    "ci_95_upper": -1.0,
                    "p_value_raw": 0.01,
                    "p_value_corrected": 0.02,
                    "significant_after_correction": True
                }
            },
            "metadata": {}
        }

        output_file = tmp_path / "results" / "statistical_summary.json"
        write_summary(summary, str(output_file))

        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == summary