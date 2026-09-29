import os
import subprocess
import tempfile
import pytest
from pathlib import Path

class TestLintingConfig:
    """
    Tests to verify that linting and formatting tools are properly configured.
    These tests check for the existence of config files and basic tool availability.
    """
    
    def test_ruff_config_exists(self):
        """Verify .ruff.toml or pyproject.toml with ruff config exists"""
        root = Path(__file__).parent.parent.parent
        ruff_config = root / ".ruff.toml"
        pyproject = root / "pyproject.toml"
        
        assert ruff_config.exists() or pyproject.exists(), \
            "Ruff configuration file (.ruff.toml or pyproject.toml) must exist"
    
    def test_black_config_exists(self):
        """Verify black is configured (via pyproject.toml or .black)"""
        root = Path(__file__).parent.parent.parent
        pyproject = root / "pyproject.toml"
        black_config = root / ".black"
        
        # Black can be configured via pyproject.toml or default settings
        # We just verify the tool is available and config files exist
        assert pyproject.exists() or black_config.exists(), \
            "Black configuration must be present (pyproject.toml or .black)"
    
    def test_precommit_config_exists(self):
        """Verify .pre-commit-config.yaml exists"""
        root = Path(__file__).parent.parent.parent
        config = root / ".pre-commit-config.yaml"
        
        assert config.exists(), \
            "Pre-commit configuration file (.pre-commit-config.yaml) must exist"
    
    def test_ruff_is_installed(self):
        """Verify ruff is installed and runnable"""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "Ruff must be executable"
            assert "ruff" in result.stdout.lower(), "Output should mention ruff"
        except FileNotFoundError:
            pytest.fail("Ruff is not installed. Run: pip install ruff")
    
    def test_black_is_installed(self):
        """Verify black is installed and runnable"""
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "Black must be executable"
            assert "black" in result.stdout.lower(), "Output should mention black"
        except FileNotFoundError:
            pytest.fail("Black is not installed. Run: pip install black")
    
    def test_requirements_dev_includes_tools(self):
        """Verify requirements-dev.txt includes ruff and black"""
        root = Path(__file__).parent.parent.parent
        req_file = root / "requirements-dev.txt"
        
        if not req_file.exists():
            # If file doesn't exist, check main requirements
            req_file = root / "requirements.txt"
        
        assert req_file.exists(), "Requirements file must exist"
        
        content = req_file.read_text()
        assert "ruff" in content.lower(), "requirements must include ruff"
        assert "black" in content.lower(), "requirements must include black"