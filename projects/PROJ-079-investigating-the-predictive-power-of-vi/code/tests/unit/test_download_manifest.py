import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import hashlib

from src.download import generate_manifest_v1, fetch_viral_genomes
from src.config import DATA_RAW_PATH

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory for raw data to avoid polluting the real data folder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('src.download.DATA_RAW_PATH', tmpdir):
            yield Path(tmpdir)

def test_manifest_v1_structure(temp_raw_dir):
    """Test that generate_manifest_v1 creates the correct JSON structure."""
    accessions = ["NC_045512", "MN908947"]
    results = [
        {"accession": "NC_045512", "sequence": "ATGC", "family": "Coronaviridae"},
        {"accession": "MN908947", "sequence": "GCTA", "family": "Coronaviridae"}
    ]
    
    generate_manifest_v1(accessions, results)
    
    manifest_path = temp_raw_dir / "manifest_v1.json"
    assert manifest_path.exists(), "manifest_v1.json was not created"
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert "accessions" in manifest
    assert manifest["accessions"] == accessions
    assert manifest["source"] == "NCBI Virus"
    assert "timestamp" in manifest
    assert "version" in manifest
    assert "checksums" in manifest
    assert "data" in manifest["checksums"]
    
    # Verify checksum calculation
    data_str = json.dumps(results, sort_keys=True)
    expected_checksum = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    assert manifest["checksums"]["data"] == expected_checksum

def test_manifest_overwrites_existing(temp_raw_dir):
    """Test that generate_manifest_v1 overwrites an existing file."""
    accessions = ["NC_045512"]
    results = [{"accession": "NC_045512", "sequence": "ATGC", "family": "Coronaviridae"}]
    
    # Create initial manifest
    generate_manifest_v1(accessions, results)
    
    # Modify accessions and regenerate
    new_accessions = ["MN908947"]
    new_results = [{"accession": "MN908947", "sequence": "GCTA", "family": "Coronaviridae"}]
    generate_manifest_v1(new_accessions, new_results)
    
    manifest_path = temp_raw_dir / "manifest_v1.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert manifest["accessions"] == new_accessions
    assert len(manifest["accessions"]) == 1

def test_manifest_checksums_data(temp_raw_dir):
    """Test that checksums are consistent for the same data."""
    accessions = ["NC_045512"]
    results = [{"accession": "NC_045512", "sequence": "ATGC", "family": "Coronaviridae"}]
    
    generate_manifest_v1(accessions, results)
    
    manifest_path = temp_raw_dir / "manifest_v1.json"
    with open(manifest_path, 'r') as f:
        manifest1 = json.load(f)
    
    # Regenerate
    generate_manifest_v1(accessions, results)
    
    with open(manifest_path, 'r') as f:
        manifest2 = json.load(f)
    
    assert manifest1["checksums"]["data"] == manifest2["checksums"]["data"]

def test_manifest_empty_accessions(temp_raw_dir):
    """Test handling of empty accessions list."""
    accessions = []
    results = []
    
    generate_manifest_v1(accessions, results)
    
    manifest_path = temp_raw_dir / "manifest_v1.json"
    assert manifest_path.exists()
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert manifest["accessions"] == []
    assert manifest["fetched_count"] == 0
    assert manifest["requested_count"] == 0