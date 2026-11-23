"""
Unit tests for T004: Data Manifest Initialization.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the logic from the implementation
# We need to mock the paths since the script uses __file__ relative paths
from unittest.mock import patch, MagicMock
import hashlib

# Import the functions we want to test
# We will import the script logic by executing it or importing specific functions
# Since the script is a main entry point, we'll refactor slightly to importable functions
# or copy the logic here for testing if the original is too tightly coupled to paths.
# For this task, we assume we can import the logic if we refactor slightly or test the side effects.
# To keep it simple and compliant with "extend, don't re-author", we test the side effects
# by running the main logic in a temp directory.

from code.data_manifest_init import ensure_gitkeep, init_manifest, compute_file_hash

class TestManifestInit:
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory structure simulating data/raw."""
        temp_root = tempfile.mkdtemp()
        data_raw = Path(temp_root) / "data" / "raw"
        data_raw.mkdir(parents=True)
        yield data_raw
        shutil.rmtree(temp_root)

    def test_ensure_gitkeep_creates_file(self, temp_data_dir):
        """Test that .gitkeep is created if missing."""
        gitkeep = temp_data_dir / ".gitkeep"
        assert not gitkeep.exists()

        with patch('code.data_manifest_init.GITKEEP_PATH', gitkeep):
            ensure_gitkeep()

        assert gitkeep.exists()
        content = gitkeep.read_text()
        assert "curated experimental data" in content

    def test_ensure_gitkeep_skips_existing(self, temp_data_dir):
        """Test that .gitkeep is not overwritten if exists."""
        gitkeep = temp_data_dir / ".gitkeep"
        gitkeep.write_text("Existing content")
        original_content = gitkeep.read_text()

        with patch('code.data_manifest_init.GITKEEP_PATH', gitkeep):
            ensure_gitkeep()

        assert gitkeep.read_text() == original_content

    def test_init_manifest_creates_json(self, temp_data_dir):
        """Test that manifest.json is created."""
        manifest = temp_data_dir / "manifest.json"
        assert not manifest.exists()

        with patch('code.data_manifest_init.DATA_RAW_DIR', temp_data_dir):
            with patch('code.data_manifest_init.MANIFEST_PATH', manifest):
                init_manifest()

        assert manifest.exists()
        with open(manifest) as f:
            data = json.load(f)
        assert "version" in data
        assert "files" in data
        assert data["version"] == "1.0.0"

    def test_init_manifest_checksums_existing_files(self, temp_data_dir):
        """Test that existing files are checksummed."""
        # Create a dummy file
        dummy_file = temp_data_dir / "test.txt"
        dummy_file.write_text("Hello World")
        expected_hash = hashlib.sha256(b"Hello World").hexdigest()

        manifest = temp_data_dir / "manifest.json"
        with patch('code.data_manifest_init.DATA_RAW_DIR', temp_data_dir):
            with patch('code.data_manifest_init.MANIFEST_PATH', manifest):
                init_manifest()

        with open(manifest) as f:
            data = json.load(f)

        assert "test.txt" in data["files"]
        assert data["files"]["test.txt"]["sha256"] == expected_hash
        assert data["files"]["test.txt"]["size_bytes"] == 11

    def test_compute_file_hash(self, temp_data_dir):
        """Test hash computation."""
        test_file = temp_data_dir / "hash_test.txt"
        test_file.write_text("Test Data")
        expected = hashlib.sha256(b"Test Data").hexdigest()

        result = compute_file_hash(test_file)
        assert result == expected

    def test_compute_file_hash_missing(self, temp_data_dir):
        """Test hash computation on missing file."""
        result = compute_file_hash(temp_data_dir / "nonexistent.txt")
        assert result is None
