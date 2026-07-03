"""
Tests for data directory structure and checksum validation logic.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock the config to use temporary directories during tests
import unittest.mock as mock

from utils.data_validator import (
    ensure_data_structure,
    validate_raw_data,
    validate_processed_data,
    refresh_manifests,
    main
)
from utils.hasher import hash_file, generate_manifest


@pytest.fixture
def temp_data_root(tmp_path):
    """Create a temporary data root with raw and processed subdirectories."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Create some test files
    (raw_dir / "file1.json").write_text('{"test": 1}')
    (raw_dir / "file2.txt").write_text("sample data")
    (processed_dir / "result1.csv").write_text("a,b\n1,2")
    
    return tmp_path / "data"


def test_ensure_data_structure_creates_dirs(temp_data_root, monkeypatch):
    """Test that ensure_data_structure creates missing directories."""
    # Monkeypatch the config functions to return our temp paths
    monkeypatch.setattr("utils.data_validator.get_data_raw_dir", lambda: temp_data_root / "raw")
    monkeypatch.setattr("utils.data_validator.get_data_processed_dir", lambda: temp_data_root / "processed")
    
    # Remove checksum dirs to test creation
    if (temp_data_root / "raw" / ".checksums").exists():
        shutil.rmtree(temp_data_root / "raw" / ".checksums")
    if (temp_data_root / "processed" / ".checksums").exists():
        shutil.rmtree(temp_data_root / "processed" / ".checksums")
    
    dirs = ensure_data_structure()
    
    assert dirs['raw'].exists()
    assert dirs['processed'].exists()
    assert dirs['raw_checksums'].exists()
    assert dirs['processed_checksums'].exists()


def test_validate_raw_data_with_valid_manifest(temp_data_root, monkeypatch):
    """Test validation passes when manifest matches files."""
    monkeypatch.setattr("utils.data_validator.get_data_raw_dir", lambda: temp_data_root / "raw")
    monkeypatch.setattr("utils.data_validator.get_data_processed_dir", lambda: temp_data_root / "processed")
    
    # Generate a valid manifest first
    raw_dir = temp_data_root / "raw"
    checksums_dir = raw_dir / ".checksums"
    checksums_dir.mkdir(exist_ok=True)
    generate_manifest(raw_dir, checksums_dir)
    
    is_valid, invalid_files = validate_raw_data()
    
    assert is_valid is True
    assert len(invalid_files) == 0


def test_validate_raw_data_with_invalid_manifest(temp_data_root, monkeypatch):
    """Test validation fails when file content changes after manifest generation."""
    monkeypatch.setattr("utils.data_validator.get_data_raw_dir", lambda: temp_data_root / "raw")
    monkeypatch.setattr("utils.data_validator.get_data_processed_dir", lambda: temp_data_root / "processed")
    
    raw_dir = temp_data_root / "raw"
    checksums_dir = raw_dir / ".checksums"
    checksums_dir.mkdir(exist_ok=True)
    
    # Generate manifest
    generate_manifest(raw_dir, checksums_dir)
    
    # Modify a file
    (raw_dir / "file1.json").write_text('{"test": 999}')
    
    is_valid, invalid_files = validate_raw_data()
    
    assert is_valid is False
    assert len(invalid_files) > 0
    assert "file1.json" in invalid_files[0]


def test_validate_processed_data_with_valid_manifest(temp_data_root, monkeypatch):
    """Test validation passes for processed data."""
    monkeypatch.setattr("utils.data_validator.get_data_raw_dir", lambda: temp_data_root / "raw")
    monkeypatch.setattr("utils.data_validator.get_data_processed_dir", lambda: temp_data_root / "processed")
    
    processed_dir = temp_data_root / "processed"
    checksums_dir = processed_dir / ".checksums"
    checksums_dir.mkdir(exist_ok=True)
    generate_manifest(processed_dir, checksums_dir)
    
    is_valid, invalid_files = validate_processed_data()
    
    assert is_valid is True
    assert len(invalid_files) == 0


def test_refresh_manifests(temp_data_root, monkeypatch):
    """Test that refresh_manifests updates both manifests."""
    monkeypatch.setattr("utils.data_validator.get_data_raw_dir", lambda: temp_data_root / "raw")
    monkeypatch.setattr("utils.data_validator.get_data_processed_dir", lambda: temp_data_root / "processed")
    
    results = refresh_manifests()
    
    assert 'raw' in results
    assert 'processed' in results
    assert 'Manifest updated' in results['raw']
    assert 'Manifest updated' in results['processed']


def test_main_function_runs_without_error(temp_data_root, monkeypatch, caplog):
    """Test that main() runs and produces expected output."""
    monkeypatch.setattr("utils.data_validator.get_data_raw_dir", lambda: temp_data_root / "raw")
    monkeypatch.setattr("utils.data_validator.get_data_processed_dir", lambda: temp_data_root / "processed")
    
    # Create initial manifests
    refresh_manifests()
    
    # Run main
    main()
    
    # Check logs
    assert "All data integrity checks passed" in caplog.text or "Data integrity checks" in caplog.text