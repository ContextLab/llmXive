"""
Unit tests for the Hysteresis Controller (T032).
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to ensure the code directory is in the path for imports
# In a real test run, this is handled by the test runner setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from hysteresis_controller import (
    load_model_validation_status,
    determine_tier,
    generate_hysteresis_config,
    BASELINE_THRESHOLD,
    HYSTERESIS_BAND,
    MODEL_VALIDATION_STATUS_FILE,
    CONFIG_FILE
)


class TestLoadModelValidationStatus:
    """Tests for load_model_validation_status function."""

    def test_file_missing_raises_error(self, tmp_path, monkeypatch):
        """Should raise FileNotFoundError if validation file is missing."""
        monkeypatch.setattr("hysteresis_controller.MODEL_VALIDATION_STATUS_FILE", tmp_path / "nonexistent.json")

        with pytest.raises(FileNotFoundError, match="Model validation status file not found"):
            load_model_validation_status()

    def test_validation_fails_raises_error(self, tmp_path, monkeypatch):
        """Should raise ValueError if Pearson r < 0.6."""
        status_file = tmp_path / "model_validation_status.json"
        status_file.write_text(json.dumps({"pearson_r": 0.5}))
        monkeypatch.setattr("hysteresis_controller.MODEL_VALIDATION_STATUS_FILE", status_file)

        with pytest.raises(ValueError, match="Model validation failed"):
            load_model_validation_status()

    def test_validation_passes_returns_status(self, tmp_path, monkeypatch):
        """Should return status dict if Pearson r >= 0.6."""
        status_file = tmp_path / "model_validation_status.json"
        status_file.write_text(json.dumps({"pearson_r": 0.75, "model_path": "test.pkl"}))
        monkeypatch.setattr("hysteresis_controller.MODEL_VALIDATION_STATUS_FILE", status_file)

        result = load_model_validation_status()
        assert result["pearson_r"] == 0.75


class TestDetermineTier:
    """Tests for determine_tier function."""

    def test_moderate_to_simple_on_high_load(self):
        """Should switch to simple if load is high."""
        # Assuming high load is > threshold (0.05)
        # Normalized load 0.9 (90) > 0.05
        result = determine_tier(90.0, "moderate")
        assert result == "simple"

    def test_moderate_to_complex_on_low_load(self):
        """Should switch to complex if load is low."""
        # Assuming low load is < (1 - threshold)
        # Normalized load 0.0 (0) < 0.95
        result = determine_tier(0.0, "moderate")
        assert result == "complex"

    def test_stay_moderate_on_boundary(self):
        """Should stay moderate if load is within band."""
        # Load 0.05 exactly might be edge, but let's test a safe middle
        # Normalized 0.5 (50) is not > 0.05 and not < 0.95
        result = determine_tier(50.0, "moderate")
        assert result == "moderate"

    def test_simple_to_moderate_on_recovery(self):
        """Should switch to moderate if load drops from simple state."""
        # From simple, need load < 0.95 to go to moderate
        result = determine_tier(0.0, "simple")
        assert result == "moderate"

    def test_complex_to_moderate_on_increase(self):
        """Should switch to moderate if load rises from complex state."""
        # From complex, need load > 0.05 to go to moderate
        result = determine_tier(90.0, "complex")
        assert result == "moderate"


class TestGenerateHysteresisConfig:
    """Tests for generate_hysteresis_config function."""

    @patch("hysteresis_controller.load_model_validation_status")
    def test_generates_config_on_valid_model(self, mock_load_status, tmp_path, monkeypatch):
        """Should generate config file if model is valid."""
        mock_load_status.return_value = {"pearson_r": 0.8}

        # Mock output directory
        output_dir = tmp_path / "data" / "simulation_results"
        output_dir.mkdir(parents=True)
        config_file = output_dir / "hysteresis_config.json"

        monkeypatch.setattr("hysteresis_controller.OUTPUT_DIR", output_dir)
        monkeypatch.setattr("hysteresis_controller.CONFIG_FILE", config_file)

        result = generate_hysteresis_config()

        assert result["baseline_threshold"] == BASELINE_THRESHOLD
        assert result["hysteresis_band"] == HYSTERESIS_BAND
        assert config_file.exists()

        with open(config_file, 'r') as f:
            saved_config = json.load(f)
            assert saved_config["baseline_threshold"] == 0.05

    @patch("hysteresis_controller.load_model_validation_status")
    def test_raises_on_invalid_model(self, mock_load_status, tmp_path, monkeypatch):
        """Should raise error if model validation fails."""
        mock_load_status.side_effect = ValueError("Model validation failed")

        with pytest.raises(ValueError, match="Model validation failed"):
            generate_hysteresis_config()
