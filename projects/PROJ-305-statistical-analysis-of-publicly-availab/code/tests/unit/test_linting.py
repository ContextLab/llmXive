import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

class TestLintingConfig:
    def test_ruff_config_exists(self):
        """Verify .ruff.toml exists in project root"""
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / ".ruff.toml"
        assert config_path.exists(), ".ruff.toml configuration file missing"

    def test_black_config_exists(self):
        """Verify black config in pyproject.toml"""
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "pyproject.toml"
        assert config_path.exists(), "pyproject.toml missing"
        
        content = config_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"

    def test_flake8_config_exists(self):
        """Verify .flake8 exists"""
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / ".flake8"
        assert config_path.exists(), ".flake8 configuration file missing"

    def test_ruff_check_runs(self):
        """Verify ruff can run against the codebase"""
        project_root = Path(__file__).parent.parent.parent
        code_dir = project_root / "code"
        
        try:
            result = subprocess.run(
                ["ruff", "check", str(code_dir)],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            # Ruff returns 0 if no errors, 1 if errors found. 
            # We just want to ensure it runs without crashing.
            assert result.returncode in [0, 1], f"Ruff crashed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("Ruff not installed in environment")

    def test_black_check_runs(self):
        """Verify black can run against the codebase"""
        project_root = Path(__file__).parent.parent.parent
        code_dir = project_root / "code"
        
        try:
            result = subprocess.run(
                ["black", "--check", str(code_dir)],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            # Black returns 0 if formatted, 1 if changes needed
            assert result.returncode in [0, 1], f"Black crashed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("Black not installed in environment")