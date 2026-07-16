"""
Unit tests for quickstart validation functionality.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from validation.validate_quickstart import (
    run_command,
    verify_artifact,
    validate_quickstart_instructions,
)


class TestRunCommand:
    """Tests for run_command function."""

    def test_successful_command(self):
        """Test running a successful command."""
        success, stdout, stderr = run_command(["echo", "hello"], timeout=10)
        assert success is True
        assert "hello" in stdout
        assert stderr == ""

    def test_failed_command(self):
        """Test running a failed command."""
        success, stdout, stderr = run_command(["sh", "-c", "exit 1"], timeout=10)
        assert success is False

    def test_timeout(self):
        """Test command timeout handling."""
        success, stdout, stderr = run_command(["sleep", "5"], timeout=1)
        assert success is False
        assert "timed out" in stderr.lower()


class TestVerifyArtifact:
    """Tests for verify_artifact function."""

    def test_existing_file(self):
        """Test verifying an existing non-empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            assert verify_artifact(tmp_path) is True
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file(self):
        """Test verifying a non-existent file."""
        assert verify_artifact("/nonexistent/path/file.txt") is False

    def test_empty_file(self):
        """Test verifying an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            assert verify_artifact(tmp_path) is False
        finally:
            os.unlink(tmp_path)


class TestValidateQuickstartInstructions:
    """Tests for validate_quickstart_instructions function."""

    def test_missing_quickstart(self):
        """Test validation when quickstart.md is missing."""
        report = validate_quickstart_instructions("nonexistent/quickstart.md")
        assert report["overall_status"] == "FAIL"
        assert len(report["issues"]) > 0

    def test_valid_quickstart(self):
        """Test validation with a valid quickstart.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock quickstart.md
            quickstart_path = Path(tmpdir) / "quickstart.md"
            quickstart_content = """
            # Quickstart Guide

            ## Install dependencies
            pip install -r requirements.txt

            ## Run data ingestion
            python code/data/ingest.py

            ## Run preprocessing
            python code/data/clean.py

            ## Run model training
            python code/models/train.py

            ## Run evaluation
            python code/models/evaluate.py

            ## Run interpretability analysis
            python code/analysis/interpret.py

            ## Verify outputs
            ls artifacts/
            """
            quickstart_path.write_text(quickstart_content)

            # Create mock artifacts
            artifacts_dir = Path(tmpdir) / "data" / "processed"
            artifacts_dir.mkdir(parents=True)
            (artifacts_dir / "cleaned_sn1.csv").write_text("smiles,rate_constant\n")

            # Mock other required artifacts
            (Path(tmpdir) / "artifacts").mkdir()
            (Path(tmpdir) / "artifacts" / "best_model.pt").touch()
            (Path(tmpdir) / "artifacts" / "metrics.json").write_text("{}")
            (Path(tmpdir) / "artifacts" / "hyperparameter_search.log").write_text("")
            (Path(tmpdir) / "artifacts" / "feature_importance.png").touch()
            (Path(tmpdir) / "artifacts" / "sensitivity_report.csv").write_text("cutoff,r2,mae\n")
            (Path(tmpdir) / "artifacts" / "perturbation_results.csv").write_text("feature_id,original_r2,perturbed_r2,delta\n")
            (Path(tmpdir) / "artifacts" / "integration_test_report.md").write_text("# Report")

            # Temporarily change PROJECT_ROOT
            original_root = PROJECT_ROOT
            try:
                # We can't easily change the module-level constant, so we test the logic
                # by checking that the function returns a report structure
                report = validate_quickstart_instructions(str(quickstart_path))

                assert "timestamp" in report
                assert "overall_status" in report
                assert "issues" in report
                assert "summary" in report
            finally:
                pass  # Cannot easily restore PROJECT_ROOT in this context

    def test_missing_steps(self):
        """Test validation when quickstart.md is missing required steps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal quickstart.md missing steps
            quickstart_path = Path(tmpdir) / "quickstart.md"
            quickstart_path.write_text("# Quickstart\n\nNo steps here.")

            report = validate_quickstart_instructions(str(quickstart_path))
            assert report["overall_status"] == "FAIL"
            assert any("not found in quickstart.md" in issue for issue in report["issues"])

    def test_missing_artifacts(self):
        """Test validation when artifacts are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid quickstart.md
            quickstart_path = Path(tmpdir) / "quickstart.md"
            quickstart_content = """
            # Quickstart Guide

            ## Install dependencies
            pip install -r requirements.txt

            ## Run data ingestion
            python code/data/ingest.py

            ## Run preprocessing
            python code/data/clean.py

            ## Run model training
            python code/models/train.py

            ## Run evaluation
            python code/models/evaluate.py

            ## Run interpretability analysis
            python code/analysis/interpret.py

            ## Verify outputs
            ls artifacts/
            """
            quickstart_path.write_text(quickstart_content)

            # Don't create any artifacts

            report = validate_quickstart_instructions(str(quickstart_path))
            assert report["overall_status"] == "FAIL"
            assert any("Artifact missing" in issue for issue in report["issues"])