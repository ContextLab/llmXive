import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from config_linting import run_command, check_flake8, check_black, setup_config_files

def test_run_command_success():
    """Test running a simple command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(tmpdir)
        returncode, stdout, stderr = run_command(["echo", "hello"], cwd=cwd)
        assert returncode == 0
        assert "hello" in stdout
        assert stderr == ""

def test_run_command_failure():
    """Test running a failing command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(tmpdir)
        returncode, stdout, stderr = run_command(["false"], cwd=cwd)
        assert returncode != 0

def test_setup_config_files_creates_files():
    """Test that setup_config_files creates .flake8 and pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        setup_config_files(tmp_path)
        
        assert (tmp_path / ".flake8").exists()
        assert (tmp_path / "pyproject.toml").exists()

        # Check content exists
        flake8_content = (tmp_path / ".flake8").read_text()
        assert "max-line-length" in flake8_content

        pyproject_content = (tmp_path / "pyproject.toml").read_text()
        assert "[tool.black]" in pyproject_content

def test_check_flake8_on_empty_project():
    """Test flake8 check on a project with no code (should pass)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create empty code and tests directories
        (tmp_path / "code").mkdir()
        (tmp_path / "tests").mkdir()
        
        # Create __init__.py to make them packages
        (tmp_path / "code" / "__init__.py").touch()
        (tmp_path / "tests" / "__init__.py").touch()
        
        setup_config_files(tmp_path)
        
        success, msg = check_flake8(tmp_path)
        # flake8 should pass on empty valid packages
        assert success is True

def test_check_black_on_empty_project():
    """Test black check on a project with no code (should pass)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create empty code and tests directories
        (tmp_path / "code").mkdir()
        (tmp_path / "tests").mkdir()
        
        (tmp_path / "code" / "__init__.py").touch()
        (tmp_path / "tests" / "__init__.py").touch()
        
        setup_config_files(tmp_path)
        
        success, msg = check_black(tmp_path)
        assert success is True