"""
Unit tests for the checksums utility module.
"""
import os
import tempfile
from pathlib import Path
import yaml

import pytest

from code.utils.checksums import (
    calculate_sha256,
    generate_checksums_for_directory,
    update_project_state_manifest,
    verify_checksums
)


def test_calculate_sha256_single_file():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        # Expected hash for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        actual_hash = calculate_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)


def test_calculate_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/file.txt")


def test_calculate_sha256_directory():
    """Test that IsADirectoryError is raised for directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            calculate_sha256(tmpdir)


def test_generate_checksums_for_directory():
    """Test batch checksum generation for a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.json"
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"

        file1.write_text("content1")
        file2.write_text("content2")
        file3.write_text("content3")

        checksums = generate_checksums_for_directory(tmpdir, recursive=True)

        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.json" in checksums
        assert "subdir/file3.txt" in checksums


def test_generate_checksums_filter_extensions():
    """Test filtering by file extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.json"
        
        file1.write_text("content1")
        file2.write_text("content2")

        checksums = generate_checksums_for_directory(tmpdir, extensions=[".json"])

        assert len(checksums) == 1
        assert "file2.json" in checksums
        assert "file1.txt" not in checksums


def test_verify_checksums():
    """Test verification of files against expected checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("test data")

        # Calculate correct hash
        correct_hash = calculate_sha256(file1)
        
        # Calculate incorrect hash (different string)
        incorrect_hash = calculate_sha256(tempfile.NamedTemporaryFile(mode="w", delete=False).name)
        # Force a different hash
        incorrect_hash = "0" * 64

        checksums = {
            "file1.txt": correct_hash,
            "missing.txt": correct_hash, # Should be False
            "file1.txt_wrong": incorrect_hash # Should be False
        }

        results = verify_checksums(tmpdir, checksums)

        assert results["file1.txt"] is True
        assert results["missing.txt"] is False
        assert results["file1.txt_wrong"] is False


def test_update_project_state_manifest(tmp_path):
    """Test updating the project state YAML with checksums."""
    # Setup project structure
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    test_file = data_dir / "test.csv"
    test_file.write_text("col1,col2\n1,2")

    state_file = tmp_path / "state" / "projects" / "PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml"
    state_file.parent.mkdir(parents=True)
    
    # Initialize state file
    initial_state = {
        "project_id": "PROJ-672",
        "status": "in_progress",
        "data_checksums": {}
    }
    with open(state_file, "w") as f:
        yaml.dump(initial_state, f)

    # Run update
    state = update_project_state_manifest(
        tmp_path,
        state_file_name=str(state_file.relative_to(tmp_path)),
        data_dirs=["data/raw"]
    )

    # Verify state was updated
    assert "data_checksums" in state
    assert "data/raw" in state["data_checksums"]
    assert "test.csv" in state["data_checksums"]["data/raw"]
    assert "last_checksum_update" in state

    # Verify file on disk
    with open(state_file, "r") as f:
        saved_state = yaml.safe_load(f)
    
    assert saved_state["data_checksums"]["data/raw"]["test.csv"] == state["data_checksums"]["data/raw"]["test.csv"]