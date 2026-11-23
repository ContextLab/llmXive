import json
import os
import tempfile
from pathlib import Path
import pytest

from verify_metrics import validate_metrics, load_json_file, REQUIRED_KEYS

class TestValidateMetrics:
    """Tests for the metrics verification logic."""

    def test_valid_metrics_structure(self):
        """Test that a fully valid metrics structure passes."""
        valid_data = {
            "mae": 25.5,
            "r2": 0.85,
            "wilcoxon_p_value": 0.03,
            "sc001_status": "PASS",
            "collinearity_flags": {"flag1": True},
            "redundancy_masks": {"mol1": [True, False]},
            "power_status": "high_power",
            "attribution_results": {"atom1": 0.5},
            "narrative_summary": "Model performed well."
        }
        assert validate_metrics(valid_data) is True

    def test_valid_metrics_with_nulls(self):
        """Test that valid metrics with None values (allowed types) pass."""
        valid_data = {
            "mae": None,
            "r2": None,
            "wilcoxon_p_value": None,
            "sc001_status": "computed_ground_truth",
            "collinearity_flags": None,
            "redundancy_masks": None,
            "power_status": None,
            "attribution_results": None,
            "narrative_summary": None
        }
        assert validate_metrics(valid_data) is True

    def test_missing_key(self):
        """Test that missing a required key fails."""
        data = {
            "mae": 25.5,
            # Missing r2 and others
            "sc001_status": "PASS"
        }
        # We expect the function to log errors and return False
        # Since logging happens, we just check the return value
        assert validate_metrics(data) is False

    def test_invalid_type_for_mae(self):
        """Test that non-float/non-None mae fails."""
        data = {
            "mae": "invalid",
            "r2": 0.85,
            "wilcoxon_p_value": 0.03,
            "sc001_status": "PASS",
            "collinearity_flags": {},
            "redundancy_masks": {},
            "power_status": "high_power",
            "attribution_results": {},
            "narrative_summary": "test"
        }
        assert validate_metrics(data) is False

    def test_invalid_sc001_status_value(self):
        """Test that an invalid sc001_status string fails."""
        data = {
            "mae": 25.5,
            "r2": 0.85,
            "wilcoxon_p_value": 0.03,
            "sc001_status": "INVALID_STATUS",
            "collinearity_flags": {},
            "redundancy_masks": {},
            "power_status": "high_power",
            "attribution_results": {},
            "narrative_summary": "test"
        }
        assert validate_metrics(data) is False

    def test_all_valid_sc001_statuses(self):
        """Test that all valid sc001_status values pass type check."""
        valid_statuses = ["PASS", "FAIL", "LOW_POWER", "computed_ground_truth"]
        base_data = {
            "mae": 25.5,
            "r2": 0.85,
            "wilcoxon_p_value": 0.03,
            "collinearity_flags": {},
            "redundancy_masks": {},
            "power_status": "high_power",
            "attribution_results": {},
            "narrative_summary": "test"
        }
        for status in valid_statuses:
            data = base_data.copy()
            data["sc001_status"] = status
            assert validate_metrics(data) is True

class TestLoadJsonFile:
    """Tests for JSON file loading."""

    def test_load_existing_json(self):
        """Test loading an existing valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = Path(f.name)

        try:
            result = load_json_file(temp_path)
            assert result == {"key": "value"}
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_json(self):
        """Test loading a non-existent file returns None."""
        result = load_json_file(Path("/nonexistent/path/file.json"))
        assert result is None

    def test_load_invalid_json(self):
        """Test loading a file with invalid JSON returns None."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            result = load_json_file(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)
