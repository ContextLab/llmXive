import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from src.download import fetch_viral_genomes, _generate_manifest_v1
from src.config import DATA_RAW_PATH

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory for raw data"""
    temp_dir = tempfile.mkdtemp()
    # Mock DATA_RAW_PATH
    original = DATA_RAW_PATH
    DATA_RAW_PATH = temp_dir
    yield temp_dir
    DATA_RAW_PATH = original
    shutil.rmtree(temp_dir)

def test_manifest_v1_structure(temp_raw_dir):
    """Test that manifest_v1.json has the correct structure"""
    # Mock the API response
    mock_fasta = """>NC_001802.1 Influenza A virus segment 1
    ATGCATGCATGCATGCATGC
    >NC_001803.1 Influenza A virus segment 2
    GCGCGCGCGCGCGCGCGC
    """
    
    with patch('src.download.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_fasta
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call the function
        fetch_viral_genomes(["NC_001802", "NC_001803"])
        
        # Check manifest was created
        manifest_path = Path(temp_raw_dir) / "manifest_v1.json"
        assert manifest_path.exists(), "manifest_v1.json was not created"
        
        # Load and validate structure
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "accessions" in manifest
        assert "source" in manifest
        assert "timestamp" in manifest
        assert "version" in manifest
        assert "checksums" in manifest
        
        assert manifest["source"] == "NCBI Virus"
        assert "sha256" in manifest["checksums"]
        assert len(manifest["accessions"]) == 2

def test_manifest_overwrites_existing(temp_raw_dir):
    """Test that manifest is overwritten, not appended"""
    manifest_path = Path(temp_raw_dir) / "manifest_v1.json"
    
    # Create initial manifest
    initial_data = {"accessions": ["old"], "source": "old"}
    with open(manifest_path, 'w') as f:
        json.dump(initial_data, f)
    
    # Mock API response
    mock_fasta = """>NC_001802.1 Test
    ATGCATGCATGCATGCATGC
    """
    
    with patch('src.download.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_fasta
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        fetch_viral_genomes(["NC_001802"])
        
        # Verify manifest was overwritten
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["accessions"] == ["NC_001802"]
        assert manifest["source"] == "NCBI Virus"
        assert "old" not in str(manifest)

def test_manifest_checksums_data(temp_raw_dir):
    """Test that checksum is calculated correctly"""
    mock_fasta = """>NC_001802.1 Test
    ATGCATGCATGCATGCATGC
    """
    
    with patch('src.download.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_fasta
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        fetch_viral_genomes(["NC_001802"])
        
        manifest_path = Path(temp_raw_dir) / "manifest_v1.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Verify checksum is a valid SHA-256 hash (64 hex characters)
        checksum = manifest["checksums"]["sha256"]
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

def test_manifest_empty_accessions(temp_raw_dir):
    """Test behavior with empty accessions list"""
    mock_fasta = """>NC_001802.1 Test
    ATGCATGCATGCATGCATGC
    """
    
    with patch('src.download.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_fasta
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Should not fail with empty list
        result = fetch_viral_genomes([])
        assert result == []
        
        # Manifest should still be created (with empty accessions)
        manifest_path = Path(temp_raw_dir) / "manifest_v1.json"
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["accessions"] == []
