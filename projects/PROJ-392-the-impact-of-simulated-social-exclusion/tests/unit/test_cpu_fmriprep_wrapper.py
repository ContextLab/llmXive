"""
Unit tests for cpu_fmriprep_wrapper.py.
"""
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to add the code directory to the path to simulate the project structure
import sys
import os

# Assuming tests are run from project root
code_path = Path(__file__).parent.parent / "code" / "preprocess"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path.parent.parent))

from preprocess.cpu_fmriprep_wrapper import (
    check_docker_installed,
    build_fmriprep_command,
    run_fmriprep,
    DOCKER_IMAGE
)


class TestDockerCheck:
    @patch("subprocess.run")
    def test_docker_installed_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert check_docker_installed() is True

    @patch("subprocess.run")
    def test_docker_not_installed_error(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        assert check_docker_installed() is False


class TestCommandBuilding:
    def test_basic_command_structure(self):
        input_dir = Path("/data/input")
        output_dir = Path("/data/output")
        cmd = build_fmriprep_command(input_dir, output_dir)

        assert "docker" in cmd
        assert "run" in cmd
        assert "--rm" in cmd
        assert DOCKER_IMAGE in cmd
        assert "participant" in cmd

    def test_thread_environment_variables(self):
        input_dir = Path("/data/input")
        output_dir = Path("/data/output")
        nthreads = 8
        cmd = build_fmriprep_command(input_dir, output_dir, nthreads=nthreads)

        expected_env = f"OMP_NUM_THREADS={nthreads}"
        assert expected_env in cmd

    def test_participant_labels(self):
        input_dir = Path("/data/input")
        output_dir = Path("/data/output")
        participants = ["sub-01", "sub-02"]
        cmd = build_fmriprep_command(
            input_dir, output_dir, participant_label=participants
        )

        # Check that --participant-label appears for each
        count = cmd.count("--participant-label")
        assert count == len(participants)

    def test_skip_bids_validation(self):
        input_dir = Path("/data/input")
        output_dir = Path("/data/output")
        cmd = build_fmriprep_command(
            input_dir, output_dir, skip_bids_validation=True
        )

        assert "--skip-bids-validation" in cmd

    def test_memory_limit(self):
        input_dir = Path("/data/input")
        output_dir = Path("/data/output")
        mem_gb = 16
        cmd = build_fmriprep_command(input_dir, output_dir, mem_gb=mem_gb)

        # fMRIPrep expects MB
        expected_mb = mem_gb * 1024
        assert f"--mem-mb {expected_mb}" in " ".join(cmd)


class TestRunExecution:
    @patch("preprocess.cpu_fmriprep_wrapper.check_docker_installed")
    @patch("subprocess.run")
    def test_run_success(self, mock_run, mock_check):
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        input_dir = Path("/data/input")
        output_dir = Path("/data/output")
        result = run_fmriprep(input_dir, output_dir)

        assert result == 0
        mock_run.assert_called_once()

    @patch("preprocess.cpu_fmriprep_wrapper.check_docker_installed")
    def test_run_no_docker(self, mock_check):
        mock_check.return_value = False

        input_dir = Path("/data/input")
        output_dir = Path("/data/output")
        result = run_fmriprep(input_dir, output_dir)

        assert result == 1