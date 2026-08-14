"""
Unit tests for Quickstart Validation logic.
These tests verify the helper functions in quickstart_validation.py.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to import the functions from the script
# Since the script has a main block, we import directly
import sys
from code import quickstart_validation

class TestVerifyArtifacts:
    def test_all_exist(self, tmp_path):
        """Test when all artifacts exist."""
        # Create dummy files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()

        artifacts = {
            "file1.txt": "desc1",
            "file2.txt": "desc2"
        }

        # Adjust paths to be relative to tmp_path for the test
        # We mock the project_root behavior or adapt the function
        # For simplicity, we test the logic by passing absolute paths as if they were relative
        # But the function expects relative to project_root.
        # Let's mock the Path resolution.
        with patch.object(quickstart_validation, 'project_root', tmp_path):
            exists, missing = quickstart_validation.verify_artifacts(artifacts)

        assert exists is True
        assert missing == []

    def test_some_missing(self, tmp_path):
        """Test when some artifacts are missing."""
        (tmp_path / "file1.txt").touch()

        artifacts = {
            "file1.txt": "desc1",
            "file2.txt": "desc2"
        }

        with patch.object(quickstart_validation, 'project_root', tmp_path):
            exists, missing = quickstart_validation.verify_artifacts(artifacts)

        assert exists is False
        assert "file2.txt" in missing

class TestValidateMetricsContent:
    def test_valid_json_with_keys(self, tmp_path):
        """Test a valid JSON file with expected keys."""
        file_path = tmp_path / "metrics.json"
        data = {
            "train_r2": 0.85,
            "val_r2": 0.82,
            "train_mae": 0.1,
            "val_mae": 0.12,
            "predictive_power": True
        }
        file_path.write_text(json.dumps(data))

        # Mock project_root
        with patch.object(quickstart_validation, 'project_root', tmp_path):
            result = quickstart_validation.validate_metrics_content("metrics.json")

        assert result is True

    def test_invalid_json(self, tmp_path):
        """Test a file with invalid JSON."""
        file_path = tmp_path / "bad.json"
        file_path.write_text("{ invalid json }")

        with patch.object(quickstart_validation, 'project_root', tmp_path):
            result = quickstart_validation.validate_metrics_content("bad.json")

        assert result is False

    def test_empty_dict(self, tmp_path):
        """Test an empty JSON object."""
        file_path = tmp_path / "empty.json"
        file_path.write_text("{}")

        with patch.object(quickstart_validation, 'project_root', tmp_path):
            result = quickstart_validation.validate_metrics_content("empty.json")

        assert result is False

    def test_missing_keys_warning(self, tmp_path):
        """Test that missing keys in model_metrics.json triggers a warning but returns True."""
        file_path = tmp_path / "metrics.json"
        # Missing 'predictive_power'
        data = {
            "train_r2": 0.85,
            "val_r2": 0.82
        }
        file_path.write_text(json.dumps(data))

        with patch.object(quickstart_validation, 'project_root', tmp_path):
            result = quickstart_validation.validate_metrics_content("metrics.json")

        # It should return True because it's valid JSON and a dict, even if keys are missing
        # The function logs a warning but doesn't fail on missing keys
        assert result is True
