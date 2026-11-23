import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.archive_artifacts import (
    create_archive_structure,
    collect_files,
    copy_to_archive,
    generate_archive_manifest,
    main
)
from src.utils.config import get_project_root

class TestArchiveArtifacts:
    @patch('src.evaluation.archive_artifacts.get_project_root')
    def test_create_archive_structure(self, mock_get_root):
        """Test that the archive directory structure is created correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_get_root.return_value = Path(tmp_dir)
            archive_root = Path(tmp_dir) / "archive"
            
            result_path = create_archive_structure(archive_root)
            
            assert result_path.exists()
            assert (result_path / "data").exists()
            assert (result_path / "artifacts").exists()
            assert (result_path / "reports").exists()
            assert (result_path / "logs").exists()
            assert (result_path / "metadata").exists()
            
            # Verify timestamp format (basic check)
            assert len(result_path.name) == 15 # YYYYMMDD_HHMMSS

    def test_collect_files_empty(self):
        """Test collection when source directories are empty/missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = Path(tmp_dir) / "archive"
            manifest = collect_files(archive_path)
            
            assert isinstance(manifest, dict)
            assert "data" in manifest
            assert len(manifest["data"]) == 0

    @patch('src.evaluation.archive_artifacts.get_project_root')
    def test_copy_to_archive(self, mock_get_root):
        """Test copying files to the archive."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            mock_get_root.return_value = project_root
            
            # Create dummy source file
            data_dir = project_root / "data"
            data_dir.mkdir()
            dummy_file = data_dir / "test.json"
            dummy_file.write_text('{"key": "value"}')
            
            archive_version = project_root / "archive" / "test_archive"
            archive_version.mkdir(parents=True)
            
            manifest = {
                "data": ["data/test.json"],
                "artifacts": [],
                "reports": [],
                "logs": [],
                "metadata": []
            }
            
            count = copy_to_archive(archive_version, manifest)
            
            assert count == 1
            assert (archive_version / "data" / "test.json").exists()

    @patch('src.evaluation.archive_artifacts.get_project_root')
    def test_generate_archive_manifest(self, mock_get_root):
        """Test manifest generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            mock_get_root.return_value = project_root
            
            archive_version = project_root / "archive" / "test"
            archive_version.mkdir(parents=True)
            metadata_dir = archive_version / "metadata"
            metadata_dir.mkdir()
            
            manifest_data = {
                "data": ["data/test.json"],
                "artifacts": [],
                "reports": [],
                "logs": [],
                "metadata": []
            }
            
            result_path = generate_archive_manifest(archive_version, manifest_data, 1)
            
            assert result_path.exists()
            with open(result_path) as f:
                data = json.load(f)
            
            assert data["total_files_copied"] == 1
            assert "created_at" in data
            assert "contents" in data

    @patch('src.evaluation.archive_artifacts.get_project_root')
    @patch('src.evaluation.archive_artifacts.create_archive_structure')
    @patch('src.evaluation.archive_artifacts.collect_files')
    @patch('src.evaluation.archive_artifacts.copy_to_archive')
    @patch('src.evaluation.archive_artifacts.generate_archive_manifest')
    @patch('src.evaluation.archive_artifacts.tarfile.open')
    def test_main_success(self, mock_tar_open, mock_gen_manifest, mock_copy, mock_collect, mock_create, mock_get_root):
        """Test the main function execution flow."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            mock_get_root.return_value = project_root
            
            mock_create.return_value = project_root / "archive" / "20230101_120000"
            mock_collect.return_value = {"data": [], "artifacts": [], "reports": [], "logs": [], "metadata": []}
            mock_copy.return_value = 0
            mock_gen_manifest.return_value = project_root / "archive" / "manifest.json"
            
            # Mock tarfile context manager
            mock_tar = MagicMock()
            mock_tar_open.return_value.__enter__ = MagicMock(return_value=mock_tar)
            mock_tar_open.return_value.__exit__ = MagicMock(return_value=False)
            
            exit_code = main()
            
            assert exit_code == 0
            mock_create.assert_called_once()
            mock_collect.assert_called_once()
            mock_copy.assert_called_once()
            mock_gen_manifest.assert_called_once()
            mock_tar_open.assert_called()