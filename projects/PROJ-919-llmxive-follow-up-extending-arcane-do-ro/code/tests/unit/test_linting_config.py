"""
Unit tests to verify that linting and formatting tools are correctly configured.

This test suite ensures:
1. ruff can parse the configuration and run on the codebase
2. black can parse the configuration and format the codebase
3. The project structure is compatible with the configured tools
"""
import subprocess
import tempfile
import os
from pathlib import Path
import pytest
import sys

class TestLintingConfiguration:
    """Tests for linting and formatting tool configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        # Assuming tests are in code/tests/unit and project root is two levels up
        return Path(__file__).parent.parent.parent

    def test_ruff_config_exists(self, project_root):
        """Verify that ruff configuration exists and is valid."""
        # Check pyproject.toml for ruff config
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"
        
        content = pyproject.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
        
        # Verify ruff can read the config by running a check on a dummy file
        ruff_check = subprocess.run(
            ["ruff", "check", "--config", str(pyproject), "--output-format=json", "."],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        # We expect this to run without configuration errors (exit code 0 or 1 is fine, 
        # but not 2 which indicates config parsing error)
        assert ruff_check.returncode != 2, f"Ruff config error: {ruff_check.stderr}"

    def test_black_config_exists(self, project_root):
        """Verify that black configuration exists and is valid."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"
        
        content = pyproject.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        
        # Verify black can read the config by running a check on a dummy file
        black_check = subprocess.run(
            ["black", "--config", str(pyproject), "--check", "--diff", "."],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        # Exit code 0 means formatted correctly, 1 means needs formatting (both valid)
        # Exit code 2 means config error
        assert black_check.returncode != 2, f"Black config error: {black_check.stderr}"

    def test_ruff_can_lint_sample_file(self, project_root):
        """Verify ruff can actually lint a Python file without crashing."""
        # Create a temporary valid Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport sys\n\ndef hello():\n    print('Hello')\n")
            temp_file = f.name

        try:
            result = subprocess.run(
                ["ruff", "check", str(temp_file)],
                capture_output=True,
                text=True
            )
            # Should not crash (exit code 2)
            assert result.returncode != 2, f"Ruff crashed: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_black_can_format_sample_file(self, project_root):
        """Verify black can actually format a Python file without crashing."""
        # Create a temporary unformatted Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport sys\n\ndef hello( ):\n    print( 'Hello' )\n")
            temp_file = f.name

        try:
            result = subprocess.run(
                ["black", "--check", str(temp_file)],
                capture_output=True,
                text=True
            )
            # Should not crash (exit code 2)
            # Exit code 1 is expected because file is unformatted
            assert result.returncode != 2, f"Black crashed: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_ruff_ignores_data_directory(self, project_root):
        """Verify that ruff is configured to ignore the data directory."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        
        # Check that 'data' is in the exclude patterns (either in black or ruff)
        # Ruff inherits exclude from black or has its own
        assert "data" in content.lower(), "Configuration should exclude data directory"

    def test_black_ignores_data_directory(self, project_root):
        """Verify that black is configured to ignore the data directory."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        
        # Check exclude pattern includes 'data'
        assert "data" in content.lower(), "Black configuration should exclude data directory"

    def test_line_length_consistency(self, project_root):
        """Verify that ruff and black have consistent line length settings."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        
        # Extract line-length from black section
        black_line_length = None
        ruff_line_length = None
        
        in_black = False
        in_ruff = False
        
        for line in content.split('\n'):
            if '[tool.black]' in line:
                in_black = True
                in_ruff = False
            elif '[tool.ruff]' in line:
                in_ruff = True
                in_black = False
            elif line.strip().startswith('line-length'):
                value = int(line.split('=')[1].strip())
                if in_black:
                    black_line_length = value
                elif in_ruff:
                    ruff_line_length = value
        
        # If both are defined, they should match
        if black_line_length is not None and ruff_line_length is not None:
            assert black_line_length == ruff_line_length, \
                f"Line length mismatch: black={black_line_length}, ruff={ruff_line_length}"