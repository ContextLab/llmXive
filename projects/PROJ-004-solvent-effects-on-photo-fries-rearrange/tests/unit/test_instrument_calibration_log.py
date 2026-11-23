"""Unit tests for instrument_calibration_log module."""
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import patch

import pytest

from analysis.instrument_calibration_log import (
    load_instrument_config,
    generate_calibration_log,
    write_calibration_log,
    run_calibration_log_generation
)


class TestLoadInstrumentConfig:
    def test_load_defaults_when_no_file(self):
        """Test that defaults are returned when config file is missing."""
        config = load_instrument_config("/nonexistent/path.yaml")
        assert config["model"] == "Generic Transient Absorption Spectrometer"
        assert "detector_type" in config
        assert "detection_limit_absorbance" in config
        assert config["detection_limit_absorbance"] == 1e-5

    def test_load_from_valid_file(self):
        """Test loading from a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("model: Custom Model\n")
            f.write("detector_type: InGaAs\n")
            f.write("detection_limit_absorbance: 1e-6\n")
            temp_path = f.name

        try:
            config = load_instrument_config(temp_path)
            assert config["model"] == "Custom Model"
            assert config["detector_type"] == "InGaAs"
            assert config["detection_limit_absorbance"] == 1e-6
        finally:
            os.unlink(temp_path)

    def test_merge_with_defaults(self):
        """Test that partial config merges with defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("model: Partial Model\n")
            temp_path = f.name

        try:
            config = load_instrument_config(temp_path)
            assert config["model"] == "Partial Model"
            # Should still have defaults for other fields
            assert "detector_type" in config
            assert config["detection_limit_absorbance"] == 1e-5
        finally:
            os.unlink(temp_path)


class TestGenerateCalibrationLog:
    def test_generates_required_fields(self):
        """Test that the log contains all required fields."""
        config = {
            "model": "Test Model",
            "detector_type": "Test Detector",
            "detection_limit_absorbance": 1e-5
        }
        log_data = generate_calibration_log(config)

        assert "metadata" in log_data
        assert "instrument" in log_data
        assert "calibration" in log_data
        assert "compliance" in log_data

        assert log_data["instrument"]["model"] == "Test Model"
        assert log_data["instrument"]["detector_type"] == "Test Detector"
        assert log_data["instrument"]["detection_limit_absorbance"] == 1e-5

    def test_compliance_section(self):
        """Test that compliance section is present."""
        config = {}
        log_data = generate_calibration_log(config)

        assert log_data["compliance"]["satisfied"] is True
        assert "Marie Curie" in log_data["compliance"]["reviewer"]
        assert log_data["compliance"]["requirement"] is not None


class TestWriteCalibrationLog:
    def test_writes_to_specified_path(self):
        """Test writing to a specific path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            log_data = {"test": "data"}
            write_path = write_calibration_log(log_data, output_path)

            assert write_path == output_path
            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded["test"] == "data"
        finally:
            os.unlink(output_path)

    def test_creates_directories(self):
        """Test that directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test.json")
            log_data = {"test": "data"}

            write_path = write_calibration_log(log_data, output_path)

            assert os.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded["test"] == "data"


class TestRunCalibrationLogGeneration:
    def test_end_to_end(self):
        """Test the full pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "calibration_log.json")

            log_data = run_calibration_log_generation(output_path=output_path)

            assert "instrument" in log_data
            assert os.exists(output_path)

            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded["instrument"]["model"] is not None
                assert loaded["instrument"]["detector_type"] is not None
                assert loaded["instrument"]["detection_limit_absorbance"] is not None
