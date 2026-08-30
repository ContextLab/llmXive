import os
import sys
import tempfile
import tomllib
import configparser
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_linting import (
    check_file_exists,
    validate_ruff_config,
    validate_pyproject_black,
    validate_flake8,
    create_ruff_config,
    create_black_config,
    create_flake8_config,
)

class TestLintingConfigValidation:
    def test_check_file_exists_true(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            path = Path(f.name)
        try:
            assert check_file_exists(path) is True
        finally:
            os.unlink(path)

    def test_check_file_exists_false(self):
        path = Path("/nonexistent/file.txt")
        assert check_file_exists(path) is False

    def test_validate_ruff_config_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".ruff.toml"
            content = """
            line-length = 88
            [lint]
            select = ["E", "F"]
            """
            config_path.write_text(content)
            assert validate_ruff_config(config_path) is True

    def test_validate_ruff_config_invalid_toml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".ruff.toml"
            config_path.write_text("invalid toml [[[")
            assert validate_ruff_config(config_path) is False

    def test_validate_ruff_config_missing_ruff_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyproject.toml"
            content = """
            [project]
            name = "test"
            """
            config_path.write_text(content)
            assert validate_ruff_config(config_path) is False

    def test_validate_pyproject_black_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyproject.toml"
            content = """
            [tool.black]
            line-length = 88
            """
            config_path.write_text(content)
            assert validate_pyproject_black(config_path) is True

    def test_validate_pyproject_black_missing_black_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyproject.toml"
            content = """
            [project]
            name = "test"
            """
            config_path.write_text(content)
            assert validate_pyproject_black(config_path) is False

    def test_validate_flake8_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".flake8"
            content = """
            [flake8]
            max-line-length = 88
            """
            config_path.write_text(content)
            assert validate_flake8(config_path) is True

    def test_validate_flake8_missing_flake8_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "setup.cfg"
            content = """
            [metadata]
            name = test
            """
            config_path.write_text(content)
            assert validate_flake8(config_path) is False

class TestLintingConfigCreation:
    def test_create_ruff_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = create_ruff_config(project_root)
            assert config_path.exists()
            assert validate_ruff_config(config_path) is True
            content = config_path.read_text()
            assert "line-length" in content
            assert "[lint]" in content

    def test_create_black_config_creates_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = project_root / "pyproject.toml"
            config_path.write_text("[project]\nname = 'test'\n")
            
            result_path = create_black_config(project_root)
            assert result_path.exists()
            content = result_path.read_text()
            assert "[tool.black]" in content
            assert "line-length" in content

    def test_create_flake8_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = create_flake8_config(project_root)
            assert config_path.exists()
            assert validate_flake8(config_path) is True
            content = config_path.read_text()
            assert "[flake8]" in content
            assert "max-line-length" in content