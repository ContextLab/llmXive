"""
Tests for the Lint Runner module.

These tests verify that the lint_runner module correctly:
1. Creates missing configuration files
2. Runs Black and Ruff (mocked)
3. Generates compliance reports
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.lint_runner import (
    get_project_root,
    ensure_linting_configs,
    run_black,
    run_ruff,
    generate_compliance_report,
    main
)


class TestLintRunnerConfig:
    """Tests for configuration file creation."""

    def test_ensure_ruff_config_created(self, tmp_path):
        """Test that .ruff.toml is created if missing."""
        ruff_config = tmp_path / ".ruff.toml"
        assert not ruff_config.exists()
        
        ensure_linting_configs(tmp_path)
        
        assert ruff_config.exists()
        content = ruff_config.read_text()
        assert "select" in content
        assert "E" in content
        assert "F" in content
        assert "W" in content
        assert "I" in content

    def test_ensure_pyproject_black_section(self, tmp_path):
        """Test that pyproject.toml gets [tool.black] if missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("# existing content\n")
        
        ensure_linting_configs(tmp_path)
        
        content = pyproject.read_text()
        assert "[tool.black]" in content
        assert "line-length" in content

    def test_ensure_ruff_config_exists_no_overwrite(self, tmp_path):
        """Test that existing .ruff.toml is not overwritten."""
        ruff_config = tmp_path / ".ruff.toml"
        original_content = "# custom config\n"
        ruff_config.write_text(original_content)
        
        ensure_linting_configs(tmp_path)
        
        assert ruff_config.read_text() == original_content


class TestLintRunnerExecution:
    """Tests for linting execution (mocked)."""

    @patch('code.lint_runner.subprocess.run')
    def test_run_black_success(self, mock_run, tmp_path):
        """Test successful Black run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All done!",
            stderr=""
        )
        
        success, stdout, stderr = run_black(tmp_path, dry_run=True)
        
        assert success is True
        assert "All done!" in stdout
        mock_run.assert_called_once()

    @patch('code.lint_runner.subprocess.run')
    def test_run_black_failure(self, mock_run, tmp_path):
        """Test failed Black run (formatting needed)."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="would reformat file.py",
            stderr=""
        )
        
        success, stdout, stderr = run_black(tmp_path, dry_run=True)
        
        assert success is False
        assert "would reformat" in stdout

    @patch('code.lint_runner.subprocess.run')
    def test_run_ruff_success(self, mock_run, tmp_path):
        """Test successful Ruff run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All checks passed!",
            stderr=""
        )
        
        success, stdout, stderr = run_ruff(tmp_path, fix=False)
        
        assert success is True
        assert "All checks passed" in stdout

    @patch('code.lint_runner.subprocess.run')
    def test_run_ruff_failure(self, mock_run, tmp_path):
        """Test failed Ruff run (issues found)."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="F401 unused import",
            stderr=""
        )
        
        success, stdout, stderr = run_ruff(tmp_path, fix=False)
        
        assert success is False
        assert "F401" in stdout


class TestLintRunnerReport:
    """Tests for compliance report generation."""

    def test_generate_compliance_report(self, tmp_path):
        """Test that compliance report is generated correctly."""
        results_dir = tmp_path / "results" / "validation"
        results_dir.mkdir(parents=True)
        
        # Temporarily override project root for the test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            report_path = generate_compliance_report(
                tmp_path,
                black_success=True,
                black_stdout="All done!",
                black_stderr="",
                ruff_success=True,
                ruff_stdout="All checks passed!",
                ruff_stderr=""
            )
            
            assert report_path.exists()
            
            with open(report_path) as f:
                report = json.load(f)
            
            assert report["task_id"] == "T041"
            assert report["overall_passed"] is True
            assert report["linting"]["black"]["passed"] is True
            assert report["linting"]["ruff"]["passed"] is True
        finally:
            os.chdir(original_cwd)

    def test_generate_compliance_report_failure(self, tmp_path):
        """Test report generation when checks fail."""
        results_dir = tmp_path / "results" / "validation"
        results_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            report_path = generate_compliance_report(
                tmp_path,
                black_success=False,
                black_stdout="would reformat",
                black_stderr="",
                ruff_success=True,
                ruff_stdout="All checks passed!",
                ruff_stderr=""
            )
            
            with open(report_path) as f:
                report = json.load(f)
            
            assert report["overall_passed"] is False
            assert report["linting"]["black"]["passed"] is False
        finally:
            os.chdir(original_cwd)


class TestMainExecution:
    """Tests for the main entry point."""

    @patch('code.lint_runner.run_black')
    @patch('code.lint_runner.run_ruff')
    @patch('code.lint_runner.ensure_linting_configs')
    @patch('code.lint_runner.generate_compliance_report')
    @patch('code.lint_runner.get_project_root')
    def test_main_success(
        self,
        mock_root,
        mock_report,
        mock_ensure,
        mock_ruff,
        mock_black
    ):
        """Test main function with successful linting."""
        mock_root.return_value = Path("/fake/project")
        mock_ensure.return_value = (Path("/fake/.ruff.toml"), Path("/fake/pyproject.toml"))
        mock_black.return_value = (True, "All done!", "")
        mock_ruff.return_value = (True, "All checks passed!", "")
        mock_report.return_value = Path("/fake/report.json")
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)

    @patch('code.lint_runner.run_black')
    @patch('code.lint_runner.run_ruff')
    @patch('code.lint_runner.ensure_linting_configs')
    @patch('code.lint_runner.generate_compliance_report')
    @patch('code.lint_runner.get_project_root')
    def test_main_failure(
        self,
        mock_root,
        mock_report,
        mock_ensure,
        mock_ruff,
        mock_black
    ):
        """Test main function with failed linting."""
        mock_root.return_value = Path("/fake/project")
        mock_ensure.return_value = (Path("/fake/.ruff.toml"), Path("/fake/pyproject.toml"))
        mock_black.return_value = (False, "would reformat", "")
        mock_ruff.return_value = (False, "F401", "")
        mock_report.return_value = Path("/fake/report.json")
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)