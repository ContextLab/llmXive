"""
Unit tests for download.py module.

These tests verify the manifest entry creation and basic logic.
Note: Real download tests require network access and are skipped in CI.
"""
import pytest
import os
import tempfile
from pathlib import Path
import sys
import json
import hashlib

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.download import (
    calculate_sha256,
    create_manifest_entry,
    DataManifest,
    ManifestEntry
)
from src.utils.schemas import ProvenanceInfo

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "test.fastq.gz"
    content = b"Test FASTQ content for checksum validation\n"
    file_path.write_bytes(content)
    return file_path

@pytest.fixture
def temp_manifest(tmp_path):
    """Create a temporary manifest file."""
    manifest_path = tmp_path / "test_manifest.json"
    return manifest_path

def test_calculate_sha256(temp_file):
    """Test SHA256 calculation matches expected value."""
    # Calculate expected checksum manually
    expected = hashlib.sha256(temp_file.read_bytes()).hexdigest()
    
    # Calculate using our function
    actual = calculate_sha256(temp_file)
    
    assert actual == expected
    assert len(actual) == 64  # SHA256 hex length

def test_manifest_entry_creation(temp_file, tmp_path):
    """Test that manifest entries are created correctly."""
    # Create a manifest entry
    entry = create_manifest_entry(temp_file, "ncbi_sra")
    
    # Verify fields
    assert entry.file_name == temp_file.name
    assert entry.file_path == str(temp_file)
    assert entry.source_type == "ncbi_sra"
    assert entry.source_id == temp_file.stem
    assert len(entry.checksum) == 64  # SHA256 hex length
    assert entry.file_size == temp_file.stat().st_size
    assert entry.downloaded_at is not None

def test_manifest_serialization(temp_file, tmp_path):
    """Test that manifests can be serialized and deserialized."""
    # Create an entry
    entry = create_manifest_entry(temp_file, "ncbi_sra")
    
    # Create manifest
    manifest = DataManifest(
        entries=[entry],
        created_at="2024-01-01T00:00:00",
        version="1.0",
        provenance=ProvenanceInfo(
            pipeline_version="0.1.0",
            tool="test",
            host_name="test-host"
        )
    )
    
    # Serialize to JSON
    manifest_path = tmp_path / "test_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest.model_dump(mode='json'), f)
    
    # Deserialize
    with open(manifest_path, 'r') as f:
        loaded = json.load(f)
    
    # Verify
    assert len(loaded['entries']) == 1
    assert loaded['entries'][0]['file_name'] == temp_file.name
    assert loaded['entries'][0]['source_type'] == "ncbi_sra"

def test_manifest_entry_validation():
    """Test that manifest entries validate correctly."""
    entry = create_manifest_entry(
        Path("/fake/path/test.fastq.gz"),
        "ncbi_sra"
    )
    
    # Verify required fields are present
    assert entry.file_name
    assert entry.checksum
    assert entry.source_type
    assert entry.downloaded_at

def test_checksum_consistency(temp_file):
    """Test that checksum is consistent across multiple calculations."""
    checksum1 = calculate_sha256(temp_file)
    checksum2 = calculate_sha256(temp_file)
    checksum3 = calculate_sha256(temp_file)
    
    assert checksum1 == checksum2 == checksum3

@pytest.mark.skipif(
    os.environ.get('CI') == 'true',
    reason="Skip network tests in CI"
)
def test_real_download_integration():
    """
    Test real download functionality (requires network).
    
    This test is skipped in CI environments. It should be run manually
    with a real SRA/GEO accession to verify end-to-end functionality.
    """
    pytest.skip("Network test - run manually with real accession")
