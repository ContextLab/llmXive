"""
Unit tests for data directory initialization.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from scripts.init_data_dirs import main

def test_data_dirs_created():
    """Test that data/raw and data/processed directories are created."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_dir = tmpdir_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        checksums_file = data_dir / "checksums.json"

        # Mock the script's parent path resolution by temporarily changing CWD
        original_cwd = os.getcwd()
        try:
            # Create a fake script structure in tmpdir to trick the Path resolution
            fake_script_dir = tmpdir_path / "code" / "scripts"
            fake_script_dir.mkdir(parents=True)
            fake_script_file = fake_script_dir / "init_data_dirs.py"
            fake_script_file.touch()

            os.chdir(fake_script_dir)
            main()

            # Verify directories exist
            assert data_dir.exists(), "data/ directory should exist"
            assert raw_dir.exists(), "data/raw/ directory should exist"
            assert processed_dir.exists(), "data/processed/ directory should exist"
            assert checksums_file.exists(), "data/checksums.json should exist"

            # Verify checksums.json structure
            with open(checksums_file, 'r') as f:
                checksums = json.load(f)

            assert "files" in checksums, "checksums.json must have 'files' key"
            assert "last_updated" in checksums, "checksums.json must have 'last_updated' key"
            assert isinstance(checksums["files"], dict), "'files' must be a dictionary"

        finally:
            os.chdir(original_cwd)

def test_checksums_file_persists():
    """Test that existing checksums.json is preserved and updated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_dir = tmpdir_path / "data"
        data_dir.mkdir()

        # Pre-populate checksums.json
        checksums_file = data_dir / "checksums.json"
        initial_data = {"files": {"existing.txt": "abc123"}, "last_updated": "2023-01-01"}
        with open(checksums_file, 'w') as f:
            json.dump(initial_data, f)

        # Create fake script structure
        fake_script_dir = tmpdir_path / "code" / "scripts"
        fake_script_dir.mkdir(parents=True)
        fake_script_file = fake_script_dir / "init_data_dirs.py"
        fake_script_file.touch()

        original_cwd = os.getcwd()
        try:
            os.chdir(fake_script_dir)
            main()

            # Verify existing data is preserved
            with open(checksums_file, 'r') as f:
                checksums = json.load(f)

            assert checksums["files"]["existing.txt"] == "abc123", "Existing checksums should be preserved"
            assert checksums["last_updated"] == "2023-01-01", "Existing last_updated should be preserved"

        finally:
            os.chdir(original_cwd)