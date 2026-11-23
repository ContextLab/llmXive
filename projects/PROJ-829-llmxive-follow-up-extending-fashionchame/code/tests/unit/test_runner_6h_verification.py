"""
Unit tests for Task T041: Verify runner execution time.

These tests verify the logic of the verification script and the timeout handling
without necessarily running the full 6-hour benchmark (which would be too slow for CI).
Instead, they mock the heavy lifting to ensure the timing logic and failure paths work.
"""
import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.verify_runner_6h_cpu import main, MAX_WALL_CLOCK_SECONDS


class TestRunnerVerificationLogic:
    """Tests for the verification script logic."""

    @patch("scripts.verify_runner_6h_cpu.load_filtered_manifest")
    @patch("scripts.verify_runner_6h_cpu.run_text_adapter_pipeline_with_bottleneck_analysis")
    @patch("scripts.verify_runner_6h_cpu.ensure_cpu_only_execution")
    def test_verification_passes_under_limit(
        self, mock_cpu, mock_run, mock_load_manifest, tmp_path
    ):
        """Verify that the script reports PASS when execution is fast."""
        # Setup mocks
        mock_samples = [{"id": 1, "feature": "color"}]
        mock_load_manifest.return_value = mock_samples
        mock_run.return_value = None  # Success

        # Mock argparse to avoid sys.argv issues in test
        with patch("scripts.verify_runner_6h_cpu.argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = MagicMock(
                manifest=str(tmp_path / "manifest.json"),
                output=str(tmp_path / "report.json")
            )
            
            # Create dummy manifest
            manifest_file = tmp_path / "manifest.json"
            manifest_file.write_text(json.dumps(mock_samples))

            # Run main
            result = main()

            # Assertions
            assert result == 0
            mock_cpu.assert_called_once()
            mock_run.assert_called_once()
            
            # Check report was written
            report_file = tmp_path / "report.json"
            assert report_file.exists()
            with open(report_file) as f:
                report = json.load(f)
            
            assert report["status"] == "PASSED"
            assert report["elapsed_seconds"] >= 0
            assert report["limit_seconds"] == MAX_WALL_CLOCK_SECONDS

    @patch("scripts.verify_runner_6h_cpu.load_filtered_manifest")
    @patch("scripts.verify_runner_6h_cpu.run_text_adapter_pipeline_with_bottleneck_analysis")
    @patch("scripts.verify_runner_6h_cpu.ensure_cpu_only_execution")
    def test_verification_fails_over_limit(
        self, mock_cpu, mock_run, mock_load_manifest, tmp_path
    ):
        """Verify that the script reports FAIL when execution times out."""
        # Setup mocks
        mock_samples = [{"id": 1}]
        mock_load_manifest.return_value = mock_samples
        
        # Simulate a timeout error from the runner
        def timeout_side_effect(*args, **kwargs):
            raise RuntimeError("TIMEOUT: Execution exceeded 6-hour limit.")
        
        mock_run.side_effect = timeout_side_effect

        with patch("scripts.verify_runner_6h_cpu.argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = MagicMock(
                manifest=str(tmp_path / "manifest.json"),
                output=str(tmp_path / "report.json")
            )
            
            manifest_file = tmp_path / "manifest.json"
            manifest_file.write_text(json.dumps(mock_samples))

            # Expect RuntimeError to propagate or be handled
            # The script catches the specific timeout error and writes a FAIL report
            # then re-raises.
            with pytest.raises(RuntimeError, match="TIMEOUT"):
                main()

            # Verify report was written with FAIL status before raising
            report_file = tmp_path / "report.json"
            assert report_file.exists()
            with open(report_file) as f:
                report = json.load(f)
            
            assert report["status"] == "FAILED"
            assert "exceeded 6-hour" in report["message"].lower()

    def test_missing_manifest_raises_error(self, tmp_path):
        """Verify that missing manifest triggers FileNotFoundError."""
        with patch("scripts.verify_runner_6h_cpu.argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = MagicMock(
                manifest=str(tmp_path / "nonexistent.json"),
                output=str(tmp_path / "report.json")
            )

            with pytest.raises(FileNotFoundError, match="Manifest file not found"):
                main()

    def test_empty_manifest_raises_error(self, tmp_path):
        """Verify that empty manifest triggers ValueError."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps([]))

        with patch("scripts.verify_runner_6h_cpu.load_filtered_manifest") as mock_load:
            mock_load.return_value = []
            
            with patch("scripts.verify_runner_6h_cpu.argparse.ArgumentParser.parse_args") as mock_parse:
                mock_parse.return_value = MagicMock(
                    manifest=str(manifest_file),
                    output=str(tmp_path / "report.json")
                )

                with pytest.raises(ValueError, match="Manifest is empty"):
                    main()