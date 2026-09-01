"""
Tests for the project structure creation utility.
"""
import os
import tempfile
from pathlib import Path
import pytest
from create_project_structure import create_structure

class TestCreateProjectStructure:
    """Tests for the create_structure function."""

    def test_creates_project_root(self):
        """Test that the project root directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            project_root = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
            assert project_root.exists()
            assert project_root.is_dir()

    def test_creates_data_raw(self):
        """Test that the data/raw directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            data_raw = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a" / "data" / "raw"
            assert data_raw.exists()
            assert data_raw.is_dir()

    def test_creates_data_processed(self):
        """Test that the data/processed directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            data_processed = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a" / "data" / "processed"
            assert data_processed.exists()
            assert data_processed.is_dir()

    def test_creates_code(self):
        """Test that the code directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            code_dir = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a" / "code"
            assert code_dir.exists()
            assert code_dir.is_dir()

    def test_creates_tests(self):
        """Test that the tests directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            tests_dir = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a" / "tests"
            assert tests_dir.exists()
            assert tests_dir.is_dir()

    def test_creates_artifacts_checkpoints(self):
        """Test that the artifacts/checkpoints directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            artifacts_checkpoints = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a" / "artifacts" / "checkpoints"
            assert artifacts_checkpoints.exists()
            assert artifacts_checkpoints.is_dir()

    def test_creates_artifacts_reports(self):
        """Test that the artifacts/reports directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            artifacts_reports = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a" / "artifacts" / "reports"
            assert artifacts_reports.exists()
            assert artifacts_reports.is_dir()

    def test_idempotent(self):
        """Test that calling create_structure twice does not raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            create_structure(tmpdir)  # Should not raise
            project_root = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
            assert project_root.exists()

    def test_creates_all_required_directories(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            project_root = Path(tmpdir) / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
            
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "artifacts/checkpoints",
                "artifacts/reports",
            ]
            
            for dir_path in required_dirs:
                full_path = project_root / dir_path
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"