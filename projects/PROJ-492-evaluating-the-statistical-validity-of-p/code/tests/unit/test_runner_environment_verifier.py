"""
Unit tests for runner environment verifier (T049b).

Tests verify that the runner environment detection and recording
functions work correctly.
"""
import json
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.src.utils.runner_environment_verifier import (
    detect_github_actions_environment,
    get_runner_name,
    get_runner_os,
    get_platform_info,
    verify_runner_specifications,
    record_runner_environment,
    write_environment_record,
    DEFAULT_GITHUB_ACTIONS_VCPU,
    DEFAULT_GITHUB_ACTIONS_RAM_GB,
)
from code.src.utils.logger import get_default_logger, AuditLogger


class TestRunnerEnvironmentDetection:
    """Tests for runner environment detection functions."""

    def test_detect_github_actions_environment_true(self):
        """Test detection when GITHUB_ACTIONS is set to true."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert detect_github_actions_environment() is True

    def test_detect_github_actions_environment_false(self):
        """Test detection when GITHUB_ACTIONS is not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert detect_github_actions_environment() is False

    def test_get_runner_name(self):
        """Test getting runner name from environment."""
        with patch.dict(os.environ, {"GITHUB_RUNNER_NAME": "ubuntu-latest"}):
            assert get_runner_name() == "ubuntu-latest"

    def test_get_runner_name_not_set(self):
        """Test getting runner name when not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_runner_name() is None

    def test_get_runner_os(self):
        """Test getting runner OS from environment."""
        with patch.dict(os.environ, {"RUNNER_OS": "Linux"}):
            assert get_runner_os() == "Linux"

    def test_get_runner_os_not_set(self):
        """Test getting runner OS when not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_runner_os() is None

    def test_get_platform_info(self):
        """Test getting platform information."""
        info = get_platform_info()
        assert "system" in info
        assert "machine" in info
        assert info["system"] == platform.system()


class TestVerification:
    """Tests for runner specification verification."""

    def test_verify_runner_specifications_exact_match(self):
        """Test verification with exact match to defaults."""
        result = verify_runner_specifications(
            detected_vcpu=DEFAULT_GITHUB_ACTIONS_VCPU,
            detected_ram_gb=DEFAULT_GITHUB_ACTIONS_RAM_GB,
        )
        assert result["vcpu_match"] is True
        assert result["ram_match"] is True
        assert result["overall_match"] is True

    def test_verify_runner_specifications_vcpu_mismatch(self):
        """Test verification with vCPU mismatch."""
        result = verify_runner_specifications(
            detected_vcpu=4,
            detected_ram_gb=DEFAULT_GITHUB_ACTIONS_RAM_GB,
        )
        assert result["vcpu_match"] is False
        assert result["overall_match"] is False

    def test_verify_runner_specifications_ram_within_tolerance(self):
        """Test verification with RAM within tolerance."""
        result = verify_runner_specifications(
            detected_vcpu=DEFAULT_GITHUB_ACTIONS_VCPU,
            detected_ram_gb=DEFAULT_GITHUB_ACTIONS_RAM_GB + 0.5,
        )
        assert result["ram_match"] is True
        assert result["overall_match"] is True

    def test_verify_runner_specifications_ram_outside_tolerance(self):
        """Test verification with RAM outside tolerance."""
        result = verify_runner_specifications(
            detected_vcpu=DEFAULT_GITHUB_ACTIONS_VCPU,
            detected_ram_gb=10.0,  # Well outside tolerance
        )
        assert result["ram_match"] is False
        assert result["overall_match"] is False


class TestEnvironmentRecording:
    """Tests for environment recording functionality."""

    def test_write_environment_record(self):
        """Test writing environment record to JSON file."""
        record = {
            "timestamp": "2024-01-01T00:00:00Z",
            "is_github_actions": True,
            "runner_name": "ubuntu-latest",
            "detected_specifications": {
                "vcpu": 2,
                "ram_gb": 7.0,
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
          output_path = Path(tmpdir) / "test_env.json"
          write_environment_record(record, output_path)

          assert output_path.exists()
          with open(output_path, "r") as f:
              loaded = json.load(f)
          assert loaded["is_github_actions"] is True
          assert loaded["detected_specifications"]["vcpu"] == 2

    def test_record_runner_environment_structure(self):
        """Test that environment record has expected structure."""
        logger = get_default_logger(__name__)

        with patch("code.src.utils.runner_environment_verifier.get_cpu_cores", return_value=2):
            with patch("code.src.utils.runner_environment_verifier.get_memory_usage_gb", return_value=7.0):
                record = record_runner_environment(logger)

                assert "timestamp" in record
                assert "is_github_actions" in record
                assert "detected_specifications" in record
                assert "verification" in record
                assert "vcpu" in record["detected_specifications"]
                assert "ram_gb" in record["detected_specifications"]
