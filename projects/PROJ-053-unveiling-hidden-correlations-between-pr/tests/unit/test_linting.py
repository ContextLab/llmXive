"""
Unit tests for T046 linting runner.
"""
import os
import tempfile
from pathlib import Path
import pytest

from lint_runner import run_linting


class TestLintingRunner:
    """Tests for the linting runner."""

    def test_report_file_created(self, tmp_path):
        """Test that the linting report file is created."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            code_dir = tmpdir / "code"
            results_dir = tmpdir / "results"
            code_dir.mkdir()
            results_dir.mkdir()

            # Create a simple Python file with a linting issue
            test_file = code_dir / "test_module.py"
            test_file.write_text("x=1\n")  # Missing whitespace around operator

            # Mock the config functions
            import config
            original_get_project_root = config.get_project_root
            original_get_results_dir = config.get_results_dir

            config.get_project_root = lambda: tmpdir
            config.get_results_dir = lambda: results_dir

            try:
                run_linting()

                # Check that report file was created
                report_path = results_dir / "linting_report.txt"
                assert report_path.exists(), "Linting report file should be created"

                # Check that report contains the linting issue
                content = report_path.read_text()
                assert "test_module.py" in content, "Report should mention the test file"
            finally:
                # Restore original functions
                config.get_project_root = original_get_project_root
                config.get_results_dir = original_get_results_dir

    def test_valid_code_no_issues(self, tmp_path):
        """Test that valid code produces no linting issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            code_dir = tmpdir / "code"
            results_dir = tmpdir / "results"
            code_dir.mkdir()
            results_dir.mkdir()

            # Create a valid Python file
            test_file = code_dir / "valid_module.py"
            test_file.write_text("x = 1  # Valid code\n")

            import config
            original_get_project_root = config.get_project_root
            original_get_results_dir = config.get_results_dir

            config.get_project_root = lambda: tmpdir
            config.get_results_dir = lambda: results_dir

            try:
                return_code = run_linting()

                report_path = results_dir / "linting_report.txt"
                content = report_path.read_text()

                # Valid code should not produce issues (except possibly about the test file itself)
                # The report should be mostly empty or just have headers
                assert "valid_module.py" not in content or "E" not in content.split("valid_module.py")[1][:50]
            finally:
                config.get_project_root = original_get_project_root
                config.get_results_dir = original_get_results_dir