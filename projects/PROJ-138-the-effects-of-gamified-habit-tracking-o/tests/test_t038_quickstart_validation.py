"""
Unit tests for T038: Quickstart Validation logic.

These tests verify the validation logic without actually running the full pipeline,
which would be too slow for unit tests.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.scripts.run_quickstart_validation import main as validation_main

class TestQuickstartValidation:
    """Tests for the quickstart validation script logic."""

    def test_missing_quickstart_script(self, tmp_path):
        """Test that validation fails if quickstart.sh is missing."""
        # Create a temporary directory structure
        with patch('code.scripts.run_quickstart_validation.project_root', tmp_path):
            with patch('sys.exit') as mock_exit:
                # Mock subprocess to not actually run anything
                with patch('code.scripts.run_quickstart_validation.subprocess'):
                    validation_main()
                    # sys.exit should be called with 1
                    mock_exit.assert_called_once_with(1)

    def test_missing_output_file(self, tmp_path):
        """Test that validation fails if output file is missing."""
        # Create a fake quickstart.sh
        quickstart = tmp_path / "quickstart.sh"
        quickstart.write_text("#!/bin/bash\necho 'Done'\n")
        quickstart.chmod(0o755)

        # Create a fake data/processed directory but no file
        (tmp_path / "data" / "processed").mkdir(parents=True)

        with patch('code.scripts.run_quickstart_validation.project_root', tmp_path):
            with patch('sys.exit') as mock_exit:
                with patch('code.scripts.run_quickstart_validation.subprocess') as mock_sub:
                    mock_sub.run.return_value = MagicMock(returncode=0)
                    validation_main()
                    # Should exit with 1 because file is missing
                    mock_exit.assert_called_once_with(1)

    def test_successful_validation(self, tmp_path):
        """Test that validation passes when all conditions are met."""
        # Create a fake quickstart.sh
        quickstart = tmp_path / "quickstart.sh"
        quickstart.write_text("#!/bin/bash\necho 'Done'\n")
        quickstart.chmod(0o755)

        # Create the output file with valid content
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True)
        output_file = output_dir / "merged_data.csv"
        output_file.write_text("User_ID,Gamified,Adherence\n1,True,1\n2,False,0\n")

        with patch('code.scripts.run_quickstart_validation.project_root', tmp_path):
            with patch('sys.exit') as mock_exit:
                with patch('code.scripts.run_quickstart_validation.subprocess') as mock_sub:
                    mock_sub.run.return_value = MagicMock(returncode=0)
                    validation_main()
                    # Should exit with 0 (success)
                    mock_exit.assert_called_once_with(0)

    def test_empty_output_file(self, tmp_path):
        """Test that validation fails if output file is empty."""
        # Create a fake quickstart.sh
        quickstart = tmp_path / "quickstart.sh"
        quickstart.write_text("#!/bin/bash\necho 'Done'\n")
        quickstart.chmod(0o755)

        # Create an empty output file
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True)
        output_file = output_dir / "merged_data.csv"
        output_file.touch()

        with patch('code.scripts.run_quickstart_validation.project_root', tmp_path):
            with patch('sys.exit') as mock_exit:
                with patch('code.scripts.run_quickstart_validation.subprocess') as mock_sub:
                    mock_sub.run.return_value = MagicMock(returncode=0)
                    validation_main()
                    # Should exit with 1 because file is empty
                    mock_exit.assert_called_once_with(1)

    def test_timeout_handling(self, tmp_path):
        """Test that timeout is handled correctly."""
        quickstart = tmp_path / "quickstart.sh"
        quickstart.write_text("#!/bin/bash\necho 'Done'\n")
        quickstart.chmod(0o755)

        with patch('code.scripts.run_quickstart_validation.project_root', tmp_path):
            with patch('sys.exit') as mock_exit:
                with patch('code.scripts.run_quickstart_validation.subprocess') as mock_sub:
                    mock_sub.run.side_effect = subprocess.TimeoutExpired(cmd="bash", timeout=600)
                    validation_main()
                    mock_exit.assert_called_once_with(1)

    def test_execution_failure(self, tmp_path):
        """Test that execution failure is handled correctly."""
        quickstart = tmp_path / "quickstart.sh"
        quickstart.write_text("#!/bin/bash\necho 'Done'\n")
        quickstart.chmod(0o755)

        with patch('code.scripts.run_quickstart_validation.project_root', tmp_path):
            with patch('sys.exit') as mock_exit:
                with patch('code.scripts.run_quickstart_validation.subprocess') as mock_sub:
                    mock_sub.run.return_value = MagicMock(returncode=1, stderr="Error occurred")
                    validation_main()
                    mock_exit.assert_called_once_with(1)
