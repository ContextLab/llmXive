#!/usr/bin/env python
"""
Unit tests for T043: Data Source Verification & Hashing.
"""
import json
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Import the functions to test
from code.utils.config import get_config
# We need to import from the module directly, handling the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code._00_verify_data_sources import (
    calculate_sha256_file,
    load_stream_hashes,
    save_source_hashes,
    save_verification_log,
    verify_data_sources
)

def test_calculate_sha256_file():
    """Test SHA256 calculation on a known file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    try:
        # Calculate expected hash
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        actual_hash = calculate_sha256_file(tmp_path)
        
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_load_stream_hashes_missing_file():
    """Test loading hashes when the file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir)
        hashes = load_stream_hashes(state_dir)
        assert hashes == {}

def test_load_stream_hashes_valid_file():
    """Test loading hashes from a valid YAML file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_dir = Path(tmp_dir)
        hash_file = state_dir / "artifact_hashes.yaml"
        
        test_data = {
            "source_stream_hash_imagenet": "abc123",
            "source_stream_hash_laion400m": "def456"
        }
        
        with open(hash_file, 'w') as f:
            yaml.dump(test_data, f)
        
        hashes = load_stream_hashes(state_dir)
        assert hashes == test_data

def test_save_source_hashes():
    """Test saving source hashes to JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        results_dir = Path(tmp_dir)
        test_hashes = {
            "imagenet_samples.parquet": "hash1",
            "laion_samples.parquet": "hash2"
        }
        
        save_source_hashes(results_dir, test_hashes)
        
        output_file = results_dir / "source_hashes.json"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_hashes = json.load(f)
        
        assert saved_hashes == test_hashes

def test_save_verification_log():
    """Test saving verification log entries."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        results_dir = Path(tmp_dir)
        log_entry = {
            "file": "test.parquet",
            "status": "verified",
            "file_hash": "abc",
            "stream_hash": "abc",
            "timestamp": "test"
        }
        
        save_verification_log(results_dir, log_entry)
        
        log_file = results_dir / "verification_log.json"
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data) == 1
        assert log_data[0]["file"] == "test.parquet"

def test_verify_data_sources_match():
    """Test verification when file hash matches stream hash."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_dir = Path(tmp_dir) / "raw"
        state_dir = Path(tmp_dir) / "state"
        results_dir = Path(tmp_dir) / "results"
        
        raw_dir.mkdir()
        state_dir.mkdir()
        results_dir.mkdir()
        
        # Create a test file
        test_file = raw_dir / "imagenet_samples.parquet"
        test_content = b"test content"
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        file_hash = hashlib.sha256(test_content).hexdigest()
        
        # Create stream hash file with matching hash
        hash_file = state_dir / "artifact_hashes.yaml"
        stream_data = {
            "source_stream_hash_imagenet": file_hash
        }
        with open(hash_file, 'w') as f:
            yaml.dump(stream_data, f)
        
        # Run verification
        success = verify_data_sources(raw_dir, state_dir, results_dir, ["imagenet_samples.parquet"])
        
        assert success is True
        
        # Check log
        log_file = results_dir / "verification_log.json"
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert log_data[0]["status"] == "verified"

def test_verify_data_sources_mismatch():
    """Test verification when file hash does NOT match stream hash."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_dir = Path(tmp_dir) / "raw"
        state_dir = Path(tmp_dir) / "state"
        results_dir = Path(tmp_dir) / "results"
        
        raw_dir.mkdir()
        state_dir.mkdir()
        results_dir.mkdir()
        
        # Create a test file
        test_file = raw_dir / "imagenet_samples.parquet"
        with open(test_file, 'wb') as f:
            f.write(b"test content")
        
        # Create stream hash file with DIFFERENT hash
        hash_file = state_dir / "artifact_hashes.yaml"
        stream_data = {
            "source_stream_hash_imagenet": "different_hash_value"
        }
        with open(hash_file, 'w') as f:
            yaml.dump(stream_data, f)
        
        # Run verification
        success = verify_data_sources(raw_dir, state_dir, results_dir, ["imagenet_samples.parquet"])
        
        assert success is False
        
        # Check log
        log_file = results_dir / "verification_log.json"
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert log_data[0]["status"] == "failed"

def test_verify_data_sources_missing_stream_hash():
    """Test verification when no stream hash exists (first run)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_dir = Path(tmp_dir) / "raw"
        state_dir = Path(tmp_dir) / "state"
        results_dir = Path(tmp_dir) / "results"
        
        raw_dir.mkdir()
        state_dir.mkdir()
        results_dir.mkdir()
        
        # Create a test file
        test_file = raw_dir / "imagenet_samples.parquet"
        with open(test_file, 'wb') as f:
            f.write(b"test content")
        
        # Do NOT create stream hash file
        
        # Run verification
        success = verify_data_sources(raw_dir, state_dir, results_dir, ["imagenet_samples.parquet"])
        
        assert success is True  # Should pass and store hash
        
        # Check that file hash was saved
        hash_output = results_dir / "source_hashes.json"
        with open(hash_output, 'r') as f:
            saved_hashes = json.load(f)
        
        assert "imagenet_samples.parquet" in saved_hashes