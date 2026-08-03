"""
Tests for the quickstart validation script.
These tests verify that the validation logic correctly identifies
missing artifacts and handles execution failures.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validate_quickstart import (
    run_script,
    verify_artifacts,
    EXPECTED_ARTIFACTS,
    PROJECT_ROOT
)


class TestRunScript:
    def test_run_existing_script(self):
        """Test running an existing script returns True."""
        # Mock subprocess.run to simulate success
        with patch('validate_quickstart.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            result = run_script("test_script.py")
            assert result is True
            mock_run.assert_called_once()

    def test_run_missing_script(self):
        """Test running a non-existent script returns False."""
        with patch('validate_quickstart.logger') as mock_logger:
            result = run_script("non_existent_script_12345.py")
            assert result is False
            mock_logger.error.assert_called()

    def test_run_timeout(self):
        """Test handling of script timeout."""
        with patch('validate_quickstart.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=1)
            with patch('validate_quickstart.logger') as mock_logger:
                result = run_script("slow_script.py")
                assert result is False
                mock_logger.error.assert_called()


class TestVerifyArtifacts:
    def setup_method(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.data_dir = self.project_root / "data"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_all_artifacts_present(self):
        """Test verification passes when all artifacts exist."""
        # Create dummy files for all expected artifacts
        for artifact in EXPECTED_ARTIFACTS:
            full_path = self.processed_dir / Path(artifact).name
            if full_path.suffix == '.json':
                with open(full_path, 'w') as f:
                    json.dump({"test": "data"}, f)
            elif full_path.suffix == '.png':
                full_path.write_bytes(b'\x89PNG\r\n\x1a\n') # Minimal PNG header
            elif full_path.suffix == '.csv':
                full_path.write_text("col1,col2\n1,2\n")
            elif full_path.suffix == '.md':
                full_path.write_text("# Test Report\n")

        # Patch PROJECT_ROOT to use temp directory
        with patch('validate_quickstart.PROJECT_ROOT', self.project_root):
            result = verify_artifacts()
            assert result is True

    def test_missing_artifact(self):
        """Test verification fails when an artifact is missing."""
        # Create all artifacts except one
        missing_artifact = EXPECTED_ARTIFACTS[0]
        for artifact in EXPECTED_ARTIFACTS[1:]:
            full_path = self.processed_dir / Path(artifact).name
            if full_path.suffix == '.json':
                with open(full_path, 'w') as f:
                    json.dump({"test": "data"}, f)
            elif full_path.suffix == '.png':
                full_path.write_bytes(b'\x89PNG\r\n\x1a\n')
            elif full_path.suffix == '.csv':
                full_path.write_text("col1,col2\n1,2\n")
            elif full_path.suffix == '.md':
                full_path.write_text("# Test Report\n")

        with patch('validate_quickstart.PROJECT_ROOT', self.project_root):
            with patch('validate_quickstart.logger') as mock_logger:
                result = verify_artifacts()
                assert result is False
                mock_logger.error.assert_called()

    def test_empty_file(self):
        """Test verification fails when a file is empty."""
        for artifact in EXPECTED_ARTIFACTS:
            full_path = self.processed_dir / Path(artifact).name
            if full_path.suffix == '.json':
                with open(full_path, 'w') as f:
                    json.dump({"test": "data"}, f)
            elif full_path.suffix == '.png':
                full_path.write_bytes(b'') # Empty file
            elif full_path.suffix == '.csv':
                full_path.write_text("col1,col2\n1,2\n")
            elif full_path.suffix == '.md':
                full_path.write_text("# Test Report\n")

        with patch('validate_quickstart.PROJECT_ROOT', self.project_root):
            with patch('validate_quickstart.logger') as mock_logger:
                result = verify_artifacts()
                assert result is False
                mock_logger.warning.assert_called()

    def test_invalid_json(self):
        """Test verification fails when JSON is invalid."""
        for artifact in EXPECTED_ARTIFACTS:
            full_path = self.processed_dir / Path(artifact).name
            if full_path.suffix == '.json':
                full_path.write_text("not valid json {{{")
            elif full_path.suffix == '.png':
                full_path.write_bytes(b'\x89PNG\r\n\x1a\n')
            elif full_path.suffix == '.csv':
                full_path.write_text("col1,col2\n1,2\n")
            elif full_path.suffix == '.md':
                full_path.write_text("# Test Report\n")

        with patch('validate_quickstart.PROJECT_ROOT', self.project_root):
            with patch('validate_quickstart.logger') as mock_logger:
                result = verify_artifacts()
                assert result is False
                mock_logger.error.assert_called()


class TestIntegration:
    def test_expected_artifacts_list(self):
        """Ensure the expected artifacts list covers all required outputs."""
        required_outputs = [
            "config.json",
            "graph_metadata.json",
            "simulation_results.csv",
            "invariance_verification.json",
            "stability_results.json",
            "sensitivity_analysis.json",
            "correlation_results.json",
            "plot_kc_vs_p.png",
            "analysis_report.md",
        ]

        artifact_names = [Path(a).name for a in EXPECTED_ARTIFACTS]
        for req in required_outputs:
            assert req in artifact_names, f"Missing required artifact: {req}"