"""
Unit tests for linting configuration generation.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys_path = str(project_root)
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from code.utils.lint_config import generate_ruff_config, generate_black_config


class TestLintConfigGeneration:
    """Tests for configuration generation functions."""

    def test_ruff_config_contains_required_sections(self):
        """Verify Ruff config includes essential sections."""
        config = generate_ruff_config()
        
        assert "[tool.ruff]" in config
        assert "line-length" in config
        assert "target-version" in config
        assert "[tool.ruff.lint]" in config
        assert "select" in config
        assert "[tool.ruff.format]" in config

    def test_ruff_config_line_length(self):
        """Verify Ruff uses 88 character line length."""
        config = generate_ruff_config()
        assert "line-length = 88" in config

    def test_ruff_config_target_version(self):
        """Verify Ruff targets Python 3.11."""
        config = generate_ruff_config()
        assert "py311" in config

    def test_black_config_contains_required_sections(self):
        """Verify Black config includes essential sections."""
        config = generate_black_config()
        
        assert "[tool.black]" in config
        assert "line-length" in config
        assert "target-version" in config

    def test_black_config_line_length(self):
        """Verify Black uses 88 character line length."""
        config = generate_black_config()
        assert "line-length = 88" in config

    def test_black_config_target_version(self):
        """Verify Black targets Python 3.11."""
        config = generate_black_config()
        assert "'py311'" in config

    def test_configs_are_valid_toml_syntax(self):
        """Verify generated configs are valid TOML syntax."""
        try:
            import tomllib
        except ImportError:
            # Python < 3.11 fallback
            import tomli as tomllib
        
        ruff_config = generate_ruff_config()
        black_config = generate_black_config()
        
        # These should not raise
        tomllib.loads(ruff_config)
        tomllib.loads(black_config)

    def test_configs_can_be_merged(self):
        """Verify Ruff and Black configs can be merged into one file."""
        ruff = generate_ruff_config()
        black = generate_black_config()
        
        merged = ruff + "\n" + black
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        # Should parse without error
        parsed = tomllib.loads(merged)
        
        assert "tool" in parsed
        assert "ruff" in parsed["tool"]
        assert "black" in parsed["tool"]