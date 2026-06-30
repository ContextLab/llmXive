"""
Unit tests for the Artifact Archiver module.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

from src.utils.artifact_archiver import (
    should_skip_path,
    scan_directory_for_files,
    compute_artifact_hashes,
    update_artifact_hashes_file,
    archive_artifacts,
    EXCLUDED_DIRS
)
from src.utils.checksum_utils import compute_file_sha256


class TestArtifactArchiver:
    """Tests for the artifact archiver functionality."""

    @pytest.fixture
    def temp_project_structure(self, tmp_path):
        """Create a temporary project structure for testing."""
        # Create directory structure
        dirs = [
            "data",
            "state",
            "src",
            "src/utils",
            "src/models",
            "__pycache__",
            "data/processed",
            "src/benchmark"
        ]
        
        for d in dirs:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        
        # Create some test files
        test_files = {
            "data/dataset.csv": "id,value\n1,10\n2,20",
            "state/config.yaml": "key: value",
            "src/main.py": "print('hello')",
            "src/utils/helper.py": "def helper(): pass",
            "src/models/model.py": "class Model: pass",
            "data/processed/clean.csv": "clean,data",
            "__pycache__/cache.pyc": "fake cache",
            "src/benchmark/run.py": "def run(): pass"
        }
        
        for file_path, content in test_files.items():
            full_path = tmp_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        return tmp_path

    def test_should_skip_path_pycache(self, temp_project_structure):
        """Test that __pycache__ directories are skipped."""
        base = temp_project_structure
        path = base / "__pycache__" / "file.pyc"
        
        assert should_skip_path(path, base) is True

    def test_should_skip_path_regular_file(self, temp_project_structure):
        """Test that regular files are not skipped."""
        base = temp_project_structure
        path = base / "src" / "main.py"
        
        assert should_skip_path(path, base) is False

    def test_should_skip_path_nested_pycache(self, temp_project_structure):
        """Test that nested __pycache__ directories are skipped."""
        base = temp_project_structure
        path = base / "src" / "__pycache__" / "module.pyc"
        
        assert should_skip_path(path, base) is True

    def test_scan_directory_for_files(self, temp_project_structure):
        """Test scanning for files in directories."""
        base = temp_project_structure
        target_dirs = ["data", "src"]
        
        files = scan_directory_for_files(base, target_dirs, base)
        
        # Should find files in data and src, but not __pycache__
        file_paths = [str(f.relative_to(base)) for f in files]
        
        assert "data/dataset.csv" in file_paths
        assert "data/processed/clean.csv" in file_paths
        assert "src/main.py" in file_paths
        assert "src/utils/helper.py" in file_paths
        assert "src/models/model.py" in file_paths
        assert "src/benchmark/run.py" in file_paths
        
        # Should NOT find pycache files
        pycache_files = [f for f in file_paths if "__pycache__" in f]
        assert len(pycache_files) == 0

    def test_scan_directory_nonexistent(self, temp_project_structure):
        """Test scanning when a directory doesn't exist."""
        base = temp_project_structure
        target_dirs = ["nonexistent_dir"]
        
        files = scan_directory_for_files(base, target_dirs, base)
        
        assert files == []

    def test_compute_file_sha256_exists(self, temp_project_structure):
        """Test that compute_file_sha256 works correctly."""
        file_path = temp_project_structure / "src" / "main.py"
        
        hash_val = compute_file_sha256(file_path)
        
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in hash_val)

    def test_compute_artifact_hashes(self, temp_project_structure):
        """Test computing hashes for all artifacts."""
        hashes = compute_artifact_hashes(temp_project_structure, ["data", "src"])
        
        assert isinstance(hashes, dict)
        assert len(hashes) > 0
        
        # Check specific files
        assert "src/main.py" in hashes
        assert "data/dataset.csv" in hashes
        
        # Check hash format
        for path, hash_val in hashes.items():
            assert isinstance(hash_val, str)
            assert len(hash_val) == 64

    def test_update_artifact_hashes_file(self, temp_project_structure):
        """Test updating the artifact hashes file."""
        new_hashes = {
            "src/main.py": "abc123...",
            "data/dataset.csv": "def456..."
        }
        
        output_file = update_artifact_hashes_file(
            new_hashes, 
            temp_project_structure,
            "state/test_artifact_hashes.yaml"
        )
        
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "artifacts" in data
        assert data["artifacts"]["src/main.py"] == "abc123..."
        assert "updated_at" in data

    def test_archive_artifacts_full_flow(self, temp_project_structure, caplog):
        """Test the full archiving flow."""
        result = archive_artifacts(
            temp_project_structure,
            ["data", "src"],
            "state/final_hashes.yaml"
        )
        
        assert result["status"] == "success"
        assert result["files_archived"] > 0
        assert "output_file" in result
        
        # Verify file was created
        output_path = temp_project_structure / "state/final_hashes.yaml"
        assert output_path.exists()
        
        # Verify content structure
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "artifacts" in data
        assert "updated_at" in data
        assert data["artifacts"]["src/main.py"] is not None

    def test_archive_artifacts_empty_directory(self, tmp_path):
        """Test archiving when target directories are empty."""
        # Create empty structure
        (tmp_path / "data").mkdir()
        
        result = archive_artifacts(tmp_path, ["data"])
        
        # Should handle gracefully
        assert result["status"] in ["success", "warning"]
        assert result["files_archived"] == 0

    def test_archive_artifacts_missing_directory(self, temp_project_structure):
        """Test archiving when some directories don't exist."""
        result = archive_artifacts(
            temp_project_structure,
            ["data", "nonexistent_dir"]
        )
        
        # Should still succeed for existing dirs
        assert result["status"] == "success"
        assert result["files_archived"] > 0
