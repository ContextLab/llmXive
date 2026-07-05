"""
Unit tests for T095b: Docker & venv verification logic.
Tests the helper functions in docs/verify_docker_venv.py.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Import the functions to test
import sys
sys.path.insert(0, "code")
from docs.verify_docker_venv import check_dockerfile, check_requirements_txt, test_venv_isolation


class TestDockerfileCheck:
    def test_dockerfile_missing(self, tmp_path):
        """Test when Dockerfile does not exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = check_dockerfile()
            assert result is False

    def test_dockerfile_empty(self, tmp_path):
        """Test when Dockerfile exists but is empty."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("")
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=""):
                result = check_dockerfile()
                assert result is False

    def test_dockerfile_valid(self, tmp_path):
        """Test when Dockerfile contains required command."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nRUN pip install -r requirements.txt")
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=dockerfile.read_text()):
                result = check_dockerfile()
                assert result is True


class TestRequirementsTxtCheck:
    def test_requirements_missing(self, tmp_path):
        """Test when requirements.txt does not exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = check_requirements_txt()
            assert result is False

    def test_requirements_empty(self, tmp_path):
        """Test when requirements.txt exists but is empty."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("")
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=""):
                result = check_requirements_txt()
                assert result is False

    def test_requirements_valid(self, tmp_path):
        """Test when requirements.txt has content."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy\npandas")
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="numpy\npandas"):
                result = check_requirements_txt()
                assert result is True


class TestVenvIsolation:
    def test_venv_creation_success(self, tmp_path):
        """Test successful venv creation and install."""
        # Mock subprocess to avoid actual venv creation in tests
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("os.name", "posix"):
                with patch("pathlib.Path.exists", return_value=True):
                    result = test_venv_isolation()
                    # Should succeed if subprocess calls are mocked
                    assert result is True

    def test_venv_install_failure(self, tmp_path):
        """Test when pip install fails."""
        with patch("subprocess.run") as mock_run:
            # First call (venv) succeeds, second (pip) fails
            mock_run.side_effect = [
                MagicMock(returncode=0),
                subprocess.CalledProcessError(1, "pip", b"Error installing"),
            ]
            with patch("os.name", "posix"):
                with patch("pathlib.Path.exists", return_value=True):
                    result = test_venv_isolation()
                    assert result is False