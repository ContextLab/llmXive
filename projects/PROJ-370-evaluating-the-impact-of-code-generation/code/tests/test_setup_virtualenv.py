import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import based on project structure
sys.path.insert(0, str(Path(__file__).parent.parent))
from code.setup_virtualenv import check_requirements_exists, create_venv, get_venv_python, install_dependencies

class TestSetupVirtualenv:
    def test_check_requirements_exists_found(self, tmp_path):
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("pytest\n")
        assert check_requirements_exists(str(req_file)) is True

    def test_check_requirements_exists_missing(self, tmp_path):
        assert check_requirements_exists(str(tmp_path / "nonexistent.txt")) is False

    def test_create_venv_creates_directory(self, tmp_path):
        venv_path = tmp_path / "test_venv"
        success = create_venv(str(venv_path))
        assert success is True
        assert venv_path.exists()
        # Check for standard venv structure (platform agnostic check for bin/Scripts)
        bin_dir = venv_path / "bin"
        if not bin_dir.exists():
            bin_dir = venv_path / "Scripts"
        assert bin_dir.exists()

    def test_get_venv_python(self, tmp_path):
        venv_path = tmp_path / "test_venv2"
        create_venv(str(venv_path))
        python_path = get_venv_python(str(venv_path))
        assert python_path is not None
        assert Path(python_path).exists()

    def test_install_dependencies_fails_without_req(self, tmp_path):
        venv_path = tmp_path / "bad_venv"
        create_venv(str(venv_path))
        # Point to non-existent requirements
        result = install_dependencies(str(venv_path), "nonexistent_req.txt")
        assert result is False