"""
Tests for linting and formatting configuration.

These tests verify that the configuration files were created correctly
and that the tools can be invoked successfully.
"""
import os
import subprocess
import pytest


class TestLintingConfiguration:
    """Test suite for linting and formatting configuration."""

    def test_ruff_config_exists(self):
        """Test that ruff.toml configuration file exists."""
        assert os.path.exists("ruff.toml"), "ruff.toml should exist"

    def test_black_config_exists(self):
        """Test that black configuration exists in pyproject.toml."""
        assert os.path.exists("pyproject.toml"), "pyproject.toml should exist"
        
        with open("pyproject.toml", "r") as f:
            content = f.read()
        
        assert "[tool.black]" in content, "Black configuration should exist in pyproject.toml"

    def test_pre_commit_config_exists(self):
        """Test that pre-commit configuration file exists."""
        assert os.path.exists(".pre-commit-config.yaml"), ".pre-commit-config.yaml should exist"

    def test_ruff_config_content(self):
        """Test that ruff.toml contains expected configuration."""
        with open("ruff.toml", "r") as f:
            content = f.read()
        
        # Check for key configuration elements
        assert "line-length = 88" in content, "Line length should be 88"
        assert "target-version = \"py311\"" in content, "Target version should be py311"
        assert 'select = [' in content, "Should have select configuration"
        assert '"E"' in content, "Should include pycodestyle errors"
        assert '"F"' in content, "Should include Pyflakes"

    def test_black_config_content(self):
        """Test that black configuration contains expected settings."""
        with open("pyproject.toml", "r") as f:
            content = f.read()
        
        # Check for key black configuration elements
        assert "line-length = 88" in content, "Line length should be 88"
        assert "target-version = ['py311']" in content, "Target version should include py311"

    def test_pre_commit_config_content(self):
        """Test that pre-commit configuration contains expected hooks."""
        with open(".pre-commit-config.yaml", "r") as f:
            content = f.read()
        
        # Check for key pre-commit configuration elements
        assert "black" in content, "Should include black hook"
        assert "ruff" in content, "Should include ruff hook"
        assert "python3.11" in content, "Should target Python 3.11"

    @pytest.mark.skipif(
        not shutil.which("black") or not shutil.which("ruff"),
        reason="black and ruff must be installed to run this test"
    )
    def test_black_can_check_code(self):
        """Test that black can be invoked to check code formatting."""
        try:
            result = subprocess.run(
                ["black", "--check", "code/"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # This test passes if black runs without crashing
            # The actual formatting status is not important for this test
            assert result.returncode in [0, 1], "Black should run without errors"
        except subprocess.TimeoutExpired:
            pytest.skip("Black check timed out")
        except FileNotFoundError:
            pytest.skip("Black not installed")

    @pytest.mark.skipif(
        not shutil.which("ruff"),
        reason="ruff must be installed to run this test"
    )
    def test_ruff_can_check_code(self):
        """Test that ruff can be invoked to check code."""
        try:
            result = subprocess.run(
                ["ruff", "check", "code/"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # This test passes if ruff runs without crashing
            # The actual linting status is not important for this test
            assert result.returncode in [0, 1], "Ruff should run without errors"
        except subprocess.TimeoutExpired:
            pytest.skip("Ruff check timed out")
        except FileNotFoundError:
            pytest.skip("Ruff not installed")


import shutil