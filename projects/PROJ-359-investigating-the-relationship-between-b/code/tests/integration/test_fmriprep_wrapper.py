"""
Integration test for fMRIPrep Docker wrapper (T018).

This test verifies that the Docker command is constructed correctly
and that the wrapper handles execution errors (like Docker not found) gracefully.
It does NOT run actual fMRIPrep on real data (too slow/heavy for unit tests).
"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest import TestCase, mock

# Import the module under test
from src.fmriprep_wrapper import build_fmriprep_command, execute_fmriprep, DOCKER_MEMORY_LIMIT, DOCKER_NPROCS


class TestFMRIPrepWrapper(TestCase):
    """Tests for the fMRIPrep execution wrapper."""

    def test_command_construction_memory_limits(self):
        """Verify that the Docker command includes correct memory constraints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            cmd = build_fmriprep_command(
                subject_id="sub-01",
                input_dir=input_dir,
                output_dir=output_dir,
            )

            # Check for required flags
            cmd_str = " ".join(cmd)
            
            self.assertIn("--memory", cmd_str)
            self.assertIn("5g", cmd_str)
            self.assertIn("--mem_mb", cmd_str)
            self.assertIn("4500", cmd_str)
            self.assertIn("--nprocs", cmd_str)
            self.assertIn("1", cmd_str)
            self.assertIn("poldracklab/fmriprep:23.1.3", cmd_str)

    def test_command_construction_subject_label(self):
        """Verify that the participant label is correctly passed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            cmd = build_fmriprep_command(
                subject_id="sub-042",
                input_dir=input_dir,
                output_dir=output_dir,
            )

            self.assertIn("--participant-label", cmd)
            self.assertIn("sub-042", cmd)

    @mock.patch("src.fmriprep_wrapper.subprocess.run")
    @mock.patch("src.fmriprep_wrapper.log_event")
    @mock.patch("src.fmriprep_wrapper.write_json_log")
    def test_execute_fmriprep_docker_not_found(self, mock_write, mock_log, mock_run):
        """Test behavior when Docker is not installed."""
        mock_run.side_effect = FileNotFoundError("Docker not found")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            log_dir = Path(tmpdir) / "logs"
            input_dir.mkdir()
            output_dir.mkdir()
            log_dir.mkdir()

            result = execute_fmriprep(
                subject_id="sub-01",
                input_dir=input_dir,
                output_dir=output_dir,
                log_dir=log_dir,
            )

            self.assertEqual(result["status"], "docker_not_found")
            self.assertEqual(result["return_code"], -2)
            # Verify log was called with FATAL error
            log_calls = [call[0][0] for call in mock_log.call_args_list]
            self.assertTrue(any("Docker executable not found" in str(c) for c in log_calls))

    @mock.patch("src.fmriprep_wrapper.subprocess.run")
    @mock.patch("src.fmriprep_wrapper.log_event")
    @mock.patch("src.fmriprep_wrapper.write_json_log")
    def test_execute_fmriprep_success(self, mock_write, mock_log, mock_run):
        """Test successful execution simulation."""
        # Mock a successful process
        mock_process = mock.MagicMock()
        mock_process.returncode = 0
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            log_dir = Path(tmpdir) / "logs"
            input_dir.mkdir()
            output_dir.mkdir()
            log_dir.mkdir()

            result = execute_fmriprep(
                subject_id="sub-01",
                input_dir=input_dir,
                output_dir=output_dir,
                log_dir=log_dir,
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["return_code"], 0)

    @mock.patch("src.fmriprep_wrapper.subprocess.run")
    @mock.patch("src.fmriprep_wrapper.log_event")
    @mock.patch("src.fmriprep_wrapper.write_json_log")
    def test_execute_fmriprep_timeout(self, mock_write, mock_log, mock_run):
        """Test behavior when fMRIPrep times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["docker", "run"], timeout=7200)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            log_dir = Path(tmpdir) / "logs"
            input_dir.mkdir()
            output_dir.mkdir()
            log_dir.mkdir()

            result = execute_fmriprep(
                subject_id="sub-01",
                input_dir=input_dir,
                output_dir=output_dir,
                log_dir=log_dir,
            )

            self.assertEqual(result["status"], "timeout")
            self.assertEqual(result["return_code"], -1)