"""
Unit tests for the quickstart_validator module.

These tests verify that the validator correctly:
1. Extracts commands from markdown files
2. Executes commands and captures results
3. Generates accurate validation reports
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from utils.quickstart_validator import (
    extract_commands_from_markdown,
    run_command,
    validate_quickstart,
    generate_report
)


class TestExtractCommands:
    """Tests for command extraction from markdown files."""

    def test_extract_single_bash_command(self, tmp_path):
        """Test extraction of a single bash command."""
        md_content = """
        # Test Quickstart

        ```bash
        echo "hello world"
        ```
        """
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        commands = extract_commands_from_markdown(md_file)

        assert len(commands) == 1
        assert commands[0]['command'] == 'echo "hello world"'
        assert commands[0]['line_number'] == 3
        assert commands[0]['block_type'] == 'shell'

    def test_extract_multiple_commands(self, tmp_path):
        """Test extraction of multiple commands from different blocks."""
        md_content = """
        # Test Quickstart

        ```bash
        cd project
        ```

        ```sh
        python main.py
        ```

        ```shell
        ls -la
        ```
        """
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        commands = extract_commands_from_markdown(md_file)

        assert len(commands) == 3
        assert commands[0]['command'] == 'cd project'
        assert commands[1]['command'] == 'python main.py'
        assert commands[2]['command'] == 'ls -la'

    def test_skip_comment_only_blocks(self, tmp_path):
        """Test that blocks with only comments are skipped."""
        md_content = """
        # Test Quickstart

        ```bash
        # This is just a comment
        ```

        ```bash
        echo "real command"
        ```
        """
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        commands = extract_commands_from_markdown(md_file)

        assert len(commands) == 1
        assert commands[0]['command'] == 'echo "real command"'

    def test_multiline_command(self, tmp_path):
        """Test extraction of multiline commands."""
        md_content = """
        # Test Quickstart

        ```bash
        pip install package1
        pip install package2
        python run.py
        ```
        """
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        commands = extract_commands_from_markdown(md_file)

        assert len(commands) == 1
        expected = "pip install package1\npip install package2\npython run.py"
        assert commands[0]['command'] == expected

    def test_empty_file(self, tmp_path):
        """Test extraction from empty file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# No commands here")

        commands = extract_commands_from_markdown(md_file)

        assert len(commands) == 0


class TestRunCommand:
    """Tests for command execution."""

    def test_successful_command(self, tmp_path):
        """Test execution of a successful command."""
        exit_code, stdout, stderr = run_command("echo 'hello'", tmp_path)

        assert exit_code == 0
        assert "hello" in stdout
        assert stderr == ""

    def test_failed_command(self, tmp_path):
        """Test execution of a failing command."""
        exit_code, stdout, stderr = run_command("exit 1", tmp_path)

        assert exit_code == 1

    def test_command_with_output(self, tmp_path):
        """Test command that produces output."""
        exit_code, stdout, stderr = run_command("pwd", tmp_path)

        assert exit_code == 0
        assert str(tmp_path) in stdout

    def test_multiline_success(self, tmp_path):
        """Test multiline command execution."""
        cmd = "echo 'line1' && echo 'line2'"
        exit_code, stdout, stderr = run_command(cmd, tmp_path)

        assert exit_code == 0
        assert "line1" in stdout
        assert "line2" in stdout


class TestValidateQuickstart:
    """Tests for the main validation function."""

    def test_nonexistent_quickstart(self, tmp_path):
        """Test validation with non-existent quickstart file."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        results = validate_quickstart(project_dir / "nonexistent.md", project_dir)

        assert results['success'] is False
        assert 'not found' in results['error']

    def test_nonexistent_project_dir(self, tmp_path):
        """Test validation with non-existent project directory."""
        quickstart_file = tmp_path / "quickstart.md"
        quickstart_file.write_text("```bash\necho test\n```")

        results = validate_quickstart(quickstart_file, tmp_path / "nonexistent")

        assert results['success'] is False
        assert 'not found' in results['error']

    def test_successful_validation(self, tmp_path):
        """Test successful validation of commands."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        md_content = """
        # Test

        ```bash
        echo "success"
        ```
        """
        quickstart_file = project_dir / "quickstart.md"
        quickstart_file.write_text(md_content)

        results = validate_quickstart(quickstart_file, project_dir)

        assert results['success'] is True
        assert results['total_commands'] == 1
        assert results['passed_commands'] == 1
        assert results['failed_commands'] == 0

    def test_failed_command_validation(self, tmp_path):
        """Test validation with a failing command."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        md_content = """
        # Test

        ```bash
        exit 1
        ```
        """
        quickstart_file = project_dir / "quickstart.md"
        quickstart_file.write_text(md_content)

        results = validate_quickstart(quickstart_file, project_dir)

        assert results['success'] is False
        assert results['failed_commands'] == 1


class TestGenerateReport:
    """Tests for report generation."""

    def test_generate_report_structure(self):
        """Test that report contains expected fields."""
        results = {
            'success': True,
            'total_commands': 1,
            'passed_commands': 1,
            'failed_commands': 0,
            'timestamp': '2024-01-01T00:00:00',
            'commands': [
                {
                    'command': 'echo test',
                    'line_number': 3,
                    'exit_code': 0,
                    'status': 'passed',
                    'stdout': '',
                    'stderr': ''
                }
            ]
        }

        report = generate_report(results)

        assert 'QUICKSTART VALIDATION REPORT' in report
        assert 'Total Commands: 1' in report
        assert 'Passed: 1' in report
        assert 'Failed: 0' in report
        assert 'Overall Status: PASSED' in report

    def test_failed_report_structure(self):
        """Test report for failed validation."""
        results = {
            'success': False,
            'total_commands': 2,
            'passed_commands': 1,
            'failed_commands': 1,
            'timestamp': '2024-01-01T00:00:00',
            'commands': [
                {
                    'command': 'echo test',
                    'line_number': 3,
                    'exit_code': 0,
                    'status': 'passed',
                    'stdout': '',
                    'stderr': ''
                },
                {
                    'command': 'exit 1',
                    'line_number': 7,
                    'exit_code': 1,
                    'status': 'failed',
                    'stdout': '',
                    'stderr': 'error'
                }
            ]
        }

        report = generate_report(results)

        assert 'Overall Status: FAILED' in report
        assert 'Failed: 1' in report

    def test_save_report_to_file(self, tmp_path):
        """Test saving report to a file."""
        results = {
            'success': True,
            'total_commands': 0,
            'passed_commands': 0,
            'failed_commands': 0,
            'timestamp': '2024-01-01T00:00:00',
            'commands': []
        }

        output_path = tmp_path / "report.txt"
        report = generate_report(results, output_path)

        assert output_path.exists()
        assert output_path.read_text() == report
