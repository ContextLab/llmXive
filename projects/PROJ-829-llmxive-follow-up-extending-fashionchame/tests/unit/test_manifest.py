"""
Unit tests for the manifest generator (code/src/pipeline/manifest.py).
Tests content hashing, file inclusion logic, and manifest generation.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from src.pipeline.manifest import (
    calculate_file_hash,
    should_include_file,
    generate_manifest,
    write_manifest,
    main
)


class TestCalculateFileHash:
    """Tests for the calculate_file_hash function."""

    def test_hash_consistency(self, tmp_path):
        """Hash should be consistent for the same file content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        hash1 = calculate_file_hash(test_file)
        hash2 = calculate_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_hash_changes_with_content(self, tmp_path):
        """Hash should change when content changes."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Content A")
        hash1 = calculate_file_hash(test_file)
        
        test_file.write_bytes(b"Content B")
        hash2 = calculate_file_hash(test_file)
        
        assert hash1 != hash2

    def test_large_file_handling(self, tmp_path):
        """Should handle large files by reading in chunks."""
        test_file = tmp_path / "large.txt"
        # Create a file larger than the default chunk size (8KB)
        content = b"x" * (100 * 1024)  # 100KB
        test_file.write_bytes(content)
        
        # Should not raise an exception
        hash_value = calculate_file_hash(test_file)
        assert len(hash_value) == 64

    def test_file_not_found(self, tmp_path):
        """Should raise RuntimeError for non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(RuntimeError):
            calculate_file_hash(non_existent)


class TestShouldIncludeFile:
    """Tests for the should_include_file function."""

    def test_include_py_in_code_dir(self, tmp_path):
        """Should include .py files in code directory."""
        test_file = tmp_path / "code" / "script.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        assert should_include_file(test_file) is True

    def test_include_yaml_in_code_dir(self, tmp_path):
        """Should include .yaml files in code directory."""
        test_file = tmp_path / "code" / "config.yaml"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        assert should_include_file(test_file) is True

    def test_exclude_pyc(self, tmp_path):
        """Should exclude .pyc files."""
        test_file = tmp_path / "code" / "script.pyc"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        assert should_include_file(test_file) is False

    def test_include_csv_in_data_dir(self, tmp_path):
        """Should include .csv files in data directory."""
        test_file = tmp_path / "data" / "processed" / "data.csv"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        assert should_include_file(test_file) is True

    def test_include_json_in_tests_dir(self, tmp_path):
        """Should include .json files in tests directory."""
        test_file = tmp_path / "tests" / "fixtures" / "config.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        assert should_include_file(test_file) is True

    def test_exclude_pth_in_data_dir(self, tmp_path):
        """Should include .pth files in data directory."""
        test_file = tmp_path / "data" / "models" / "model.pth"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        assert should_include_file(test_file) is True

    def test_exclude_non_relevant_extension(self, tmp_path):
        """Should exclude files with non-relevant extensions."""
        test_file = tmp_path / "data" / "readme.xyz"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        assert should_include_file(test_file) is False


class TestGenerateManifest:
    """Tests for the generate_manifest function."""

    def test_manifest_structure(self, tmp_path):
        """Manifest should have required keys."""
        # Create some test files
        (tmp_path / "code").mkdir()
        (tmp_path / "code" / "test.py").write_text("print('hello')")
        
        manifest = generate_manifest(tmp_path)
        
        assert 'version' in manifest
        assert 'artifacts' in manifest
        assert 'total_artifacts' in manifest
        assert 'project_root' in manifest

    def test_manifest_contains_artifact_info(self, tmp_path):
        """Each artifact should have path, hash, algorithm, and size."""
        (tmp_path / "code").mkdir()
        test_file = tmp_path / "code" / "test.py"
        test_file.write_text("print('hello')")
        
        manifest = generate_manifest(tmp_path)
        
        assert len(manifest['artifacts']) >= 1
        artifact = manifest['artifacts'][0]
        
        assert 'path' in artifact
        assert 'hash' in artifact
        assert 'algorithm' in artifact
        assert 'size_bytes' in artifact
        assert artifact['algorithm'] == 'sha256'

    def test_manifest_excludes_non_target_dirs(self, tmp_path):
        """Should only include files from target directories."""
        # Create a file outside target dirs
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "test.py").write_text("print('hello')")
        
        # Create a file in target dir
        (tmp_path / "code").mkdir()
        (tmp_path / "code" / "test.py").write_text("print('hello')")
        
        manifest = generate_manifest(tmp_path)
        
        # Should only have the one in 'code'
        artifact_paths = [a['path'] for a in manifest['artifacts']]
        assert any('code/test.py' in p for p in artifact_paths)
        assert not any('other/test.py' in p for p in artifact_paths)

    def test_empty_directory(self, tmp_path):
        """Should handle empty directories gracefully."""
        manifest = generate_manifest(tmp_path)
        
        assert manifest['artifacts'] == []
        assert manifest['total_artifacts'] == 0


class TestWriteManifest:
    """Tests for the write_manifest function."""

    def test_writes_valid_json(self, tmp_path):
        """Should write a valid JSON file."""
        manifest = {
            'version': '1.0',
            'artifacts': [],
            'total_artifacts': 0,
            'project_root': str(tmp_path)
        }
        output_path = tmp_path / "output" / "manifest.json"
        
        write_manifest(manifest, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['version'] == '1.0'

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        manifest = {'version': '1.0', 'artifacts': [], 'total_artifacts': 0}
        output_path = tmp_path / "deep" / "nested" / "dir" / "manifest.json"
        
        write_manifest(manifest, output_path)
        
        assert output_path.exists()

    def test_adds_timestamp(self, tmp_path):
        """Should add timestamp if not present."""
        manifest = {
            'version': '1.0',
            'artifacts': [],
            'total_artifacts': 0
        }
        output_path = tmp_path / "manifest.json"
        
        write_manifest(manifest, output_path)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert 'generated_at' in loaded
        assert loaded['generated_at'] is not None


class TestMain:
    """Tests for the main function."""

    def test_main_creates_manifest_file(self, tmp_path, monkeypatch):
        """Main should create manifest.json in data/processed/."""
        # Set up project structure
        (tmp_path / "code").mkdir()
        (tmp_path / "code" / "test.py").write_text("print('hello')")
        
        # Monkeypatch cwd
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
        
        # Run main
        result = main()
        
        # Check output
        output_path = tmp_path / "data" / "processed" / "manifest.json"
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest['total_artifacts'] >= 1