"""
Tests for verify_data_sources.py
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import hashlib
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.verify_data_sources import (
    compute_file_sha256,
    scan_for_synthetic_markers,
    verify_download_log,
    SYNTHETIC_MARKERS,
    VALID_SOURCE_TYPES
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def temp_file_with_content(temp_dir):
    """Create a temporary file with given content."""
    def _create(content: str, filename: str = "test.txt"):
        file_path = temp_dir / filename
        file_path.write_text(content)
        return file_path
    return _create

def test_compute_file_sha256(temp_dir, temp_file_with_content):
    """Test SHA-256 computation."""
    content = "test content for hashing"
    file_path = temp_file_with_content(content)
    
    hash_result = compute_file_sha256(file_path)
    assert len(hash_result) == 64  # SHA-256 hex length
    assert isinstance(hash_result, str)
    
    # Verify it matches expected
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    assert hash_result == expected_hash

def test_compute_file_sha256_nonexistent_file(temp_dir):
    """Test SHA-256 with non-existent file."""
    file_path = temp_dir / "nonexistent.txt"
    hash_result = compute_file_sha256(file_path)
    assert hash_result == ""

def test_scan_for_synthetic_markers_found(temp_file_with_content):
    """Test detection of synthetic markers."""
    content = "This is synthetic test data with mock values"
    file_path = temp_file_with_content(content)
    
    markers = scan_for_synthetic_markers(file_path)
    assert "synthetic" in markers
    assert "mock" in markers

def test_scan_for_synthetic_markers_not_found(temp_file_with_content):
    """Test when no synthetic markers are present."""
    content = "This is real data from a verified source"
    file_path = temp_file_with_content(content)
    
    markers = scan_for_synthetic_markers(file_path)
    assert len(markers) == 0

def test_scan_for_synthetic_markers_case_insensitive(temp_file_with_content):
    """Test case-insensitive marker detection."""
    content = "This contains SYNTHETIC and MOCK in uppercase"
    file_path = temp_file_with_content(content)
    
    markers = scan_for_synthetic_markers(file_path)
    assert "synthetic" in markers
    assert "mock" in markers

def test_verify_download_log_missing_file(temp_dir):
    """Test download log verification when file is missing."""
    # Temporarily change DOWNLOAD_LOG path
    import analysis.verify_data_sources as vds
    original_path = vds.DOWNLOAD_LOG
    vds.DOWNLOAD_LOG = temp_dir / "nonexistent.log"
    
    try:
        result = verify_download_log()
        assert result["log_exists"] is False
        assert len(result["anomalies"]) > 0
    finally:
        vds.DOWNLOAD_LOG = original_path

def test_verify_download_log_with_valid_entries(temp_dir, temp_file_with_content):
    """Test download log verification with valid entries."""
    log_content = """{"timestamp": "2024-01-01", "endpoint": "pushshift", "status_code": 200, "success": true, "origin_type": "pushshift"}
    {"timestamp": "2024-01-02", "endpoint": "reddit", "status_code": 200, "success": true, "origin_type": "reddit_api"}
    """
    log_path = temp_file_with_content(log_content, "download_attempts.log")
    
    import analysis.verify_data_sources as vds
    original_path = vds.DOWNLOAD_LOG
    vds.DOWNLOAD_LOG = log_path
    
    try:
        result = verify_download_log()
        assert result["log_exists"] is True
        assert "pushshift" in result["sources_logged"]
        assert "reddit_api" in result["sources_logged"]
        assert len(result["anomalies"]) == 0
    finally:
        vds.DOWNLOAD_LOG = original_path

def test_verify_download_log_with_failed_attempts(temp_dir, temp_file_with_content):
    """Test download log verification with failed attempts."""
    log_content = """{"timestamp": "2024-01-01", "endpoint": "pushshift", "status_code": 500, "success": false, "origin_type": "pushshift"}
    """
    log_path = temp_file_with_content(log_content, "download_attempts.log")
    
    import analysis.verify_data_sources as vds
    original_path = vds.DOWNLOAD_LOG
    vds.DOWNLOAD_LOG = log_path
    
    try:
        result = verify_download_log()
        assert result["log_exists"] is True
        assert len(result["anomalies"]) > 0
        assert any("Failed download attempt" in anomaly for anomaly in result["anomalies"])
    finally:
        vds.DOWNLOAD_LOG = original_path

def test_valid_source_types():
    """Test that valid source types are defined correctly."""
    expected_types = ["pushshift", "reddit_api", "huggingface", "internet_archive", "common_crawl"]
    assert set(VALID_SOURCE_TYPES) == set(expected_types)

def test_synthetic_markers_list():
    """Test that synthetic markers list is populated."""
    assert len(SYNTHETIC_MARKERS) > 0
    assert "synthetic" in SYNTHETIC_MARKERS
    assert "mock" in SYNTHETIC_MARKERS