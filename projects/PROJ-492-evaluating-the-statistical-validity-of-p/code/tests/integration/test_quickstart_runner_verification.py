"""
Integration test for Quickstart runner verification (T049b).

This test verifies that the Quickstart execution can run on the
default GitHub Actions runner environment and records it properly.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from code.src.utils.runner_environment_verifier import (
    ENVIRONMENT_RECORD_PATH,
    DEFAULT_GITHUB_ACTIONS_VCPU,
    DEFAULT_GITHUB_ACTIONS_RAM_GB,
)


class TestQuickstartRunnerVerification:
    """Integration tests for Quickstart runner verification."""

    def test_runner_verifier_script_executes(self):
        """Test that the runner verifier script executes without error."""
        script_path = Path("code/src/utils/runner_environment_verifier.py")
        assert script_path.exists(), "Runner verifier script must exist"

        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_environment_record_is_created(self):
        """Test that environment record file is created after running verifier."""
        script_path = Path("code/src/utils/runner_environment_verifier.py")

        # Run the script
        subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            timeout=60,
        )

        # Check that output file exists
        assert ENVIRONMENT_RECORD_PATH.exists(), (
            f"Environment record file must be created at {ENVIRONMENT_RECORD_PATH}"
        )

    def test_environment_record_has_required_fields(self):
        """Test that environment record contains all required fields."""
        script_path = Path("code/src/utils/runner_environment_verifier.py")

        # Run the script
        subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            timeout=60,
        )

        # Load and verify record
        with open(ENVIRONMENT_RECORD_PATH, "r") as f:
            record = json.load(f)

        required_fields = [
            "timestamp",
            "is_github_actions",
            "detected_specifications",
            "verification",
        ]
        for field in required_fields:
            assert field in record, f"Required field '{field}' missing from environment record"

        # Verify nested structure
        assert "vcpu" in record["detected_specifications"]
        assert "ram_gb" in record["detected_specifications"]
        assert "overall_match" in record["verification"]

    def test_environment_record_validates_runner_specs(self):
        """Test that environment record properly validates runner specifications."""
        script_path = Path("code/src/utils/runner_environment_verifier.py")

        # Run the script
        subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            timeout=60,
        )

        # Load and verify record
        with open(ENVIRONMENT_RECORD_PATH, "r") as f:
            record = json.load(f)

        verification = record["verification"]

        # Verify that expected values are recorded
        assert verification["expected_vcpu"] == DEFAULT_GITHUB_ACTIONS_VCPU
        assert "expected_ram_gb_min" in verification
        assert "expected_ram_gb_max" in verification

        # Verify detected values are numeric
        assert isinstance(verification["detected_vcpu"], int)
        assert isinstance(verification["detected_ram_gb"], float)

    def test_quickstart_verification_completes(self):
        """
        Test that the full Quickstart verification workflow completes.

        This simulates what would happen when running the Quickstart
        on a GitHub Actions runner.
        """
        script_path = Path("code/src/utils/runner_environment_verifier.py")

        # Run with environment variables that simulate GitHub Actions
        env = os.environ.copy()
        env["GITHUB_ACTIONS"] = "true"
        env["GITHUB_RUNNER_NAME"] = "ubuntu-latest"
        env["RUNNER_OS"] = "Linux"

        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

        # Script should complete successfully
        assert result.returncode == 0, f"Verification failed: {result.stderr}"

        # Verify environment record was updated
        with open(ENVIRONMENT_RECORD_PATH, "r") as f:
            record = json.load(f)

        assert record["is_github_actions"] is True
        assert record["runner_name"] == "ubuntu-latest"
        assert record["runner_os"] == "Linux"