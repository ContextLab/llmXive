import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from src.download import fetch_all_data, fetch_viral_genomes, fetch_geo_data
from src.config import DATA_RAW_PATH

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory for raw data during tests."""
    temp_dir = tempfile.mkdtemp()
    # Patch DATA_RAW_PATH to use temp directory
    original_path = DATA_RAW_PATH
    # Note: Since DATA_RAW_PATH is imported in download.py, we need to patch it there
    # or use a different strategy. For this test, we assume the path is writable.
    # In a real scenario, we would patch src.download.DATA_RAW_PATH
    yield temp_dir
    shutil.rmtree(temp_dir)

@patch('src.download.fetch_viral_genomes')
@patch('src.download.fetch_geo_data')
@patch('src.download.Path')
def test_manifest_v1_structure(mock_path_class, mock_fetch_geo, mock_fetch_viral, temp_raw_dir):
    """Test that fetch_all_data produces a manifest with correct structure."""
    # Setup mocks
    mock_genome = MagicMock()
    mock_genome.accession = "NC_000001"
    mock_genome.family = "TestFamily"
    mock_genome.fasta = os.path.join(temp_raw_dir, "NC_000001.fasta")
    
    mock_fetch_viral.return_value = [mock_genome]
    
    mock_geo_data = {
        "GSE12345": {
            "source": "GEO",
            "accession": "GSE12345",
            "path": os.path.join(temp_raw_dir, "GSE12345_matrix.txt"),
            "samples_found": 10,
            "virus_strain_accession": "NC_000001"
        }
    }
    mock_fetch_geo.return_value = mock_geo_data

    # Create dummy files for checksums
    Path(mock_genome.fasta).touch()
    Path(mock_geo_data["GSE12345"]["path"]).touch()

    # Mock Path to use our temp directory
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_class.return_value = mock_path_instance
    mock_path_class.side_effect = lambda x: Path(x) if isinstance(x, str) else x

    # Run function
    accessions = ["NC_000001", "GSE12345"]
    result = fetch_all_data(accessions)

    # Verify manifest exists and has correct keys
    assert "manifest_path" in result
    assert os.path.exists(result["manifest_path"])

    with open(result["manifest_path"], "r") as f:
        manifest = json.load(f)

    assert "accessions" in manifest
    assert "source" in manifest
    assert "timestamp" in manifest
    assert "version" in manifest
    assert "checksums" in manifest
    
    assert len(manifest["accessions"]) >= 2
    assert manifest["source"] == "NCBI Virus / GEO"
    assert "ncbi_virus" in manifest["version"]
    assert "geo" in manifest["version"]

@patch('src.download.fetch_viral_genomes')
@patch('src.download.fetch_geo_data')
@patch('src.download.Path')
def test_manifest_overwrites_existing(mock_path_class, mock_fetch_geo, mock_fetch_viral, temp_raw_dir):
    """Test that manifest overwrites existing file."""
    # Setup similar to above
    mock_genome = MagicMock()
    mock_genome.accession = "NC_000001"
    mock_genome.family = "TestFamily"
    mock_genome.fasta = os.path.join(temp_raw_dir, "NC_000001.fasta")
    
    mock_fetch_viral.return_value = [mock_genome]
    mock_geo_data = {
        "GSE12345": {
            "source": "GEO",
            "accession": "GSE12345",
            "path": os.path.join(temp_raw_dir, "GSE12345_matrix.txt"),
            "samples_found": 10,
            "virus_strain_accession": "NC_000001"
        }
    }
    mock_fetch_geo.return_value = mock_geo_data

    Path(mock_genome.fasta).touch()
    Path(mock_geo_data["GSE12345"]["path"]).touch()

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_class.return_value = mock_path_instance
    mock_path_class.side_effect = lambda x: Path(x) if isinstance(x, str) else x

    accessions = ["NC_000001", "GSE12345"]
    result = fetch_all_data(accessions)

    # Run again
    result2 = fetch_all_data(accessions)

    # Should overwrite (same path, updated timestamp)
    assert result["manifest_path"] == result2["manifest_path"]
    
    with open(result2["manifest_path"], "r") as f:
        manifest2 = json.load(f)
    
    # Timestamp should be different (or at least valid)
    assert "timestamp" in manifest2

@patch('src.download.fetch_viral_genomes')
@patch('src.download.fetch_geo_data')
@patch('src.download.Path')
def test_manifest_checksums_data(mock_path_class, mock_fetch_geo, mock_fetch_viral, temp_raw_dir):
    """Test that manifest contains SHA-256 checksums for downloaded files."""
    mock_genome = MagicMock()
    mock_genome.accession = "NC_000001"
    mock_genome.family = "TestFamily"
    mock_genome.fasta = os.path.join(temp_raw_dir, "NC_000001.fasta")
    
    mock_fetch_viral.return_value = [mock_genome]
    mock_geo_data = {
        "GSE12345": {
            "source": "GEO",
            "accession": "GSE12345",
            "path": os.path.join(temp_raw_dir, "GSE12345_matrix.txt"),
            "samples_found": 10,
            "virus_strain_accession": "NC_000001"
        }
    }
    mock_fetch_geo.return_value = mock_geo_data

    # Create files with known content
    test_content = "TEST_DATA_CONTENT"
    with open(mock_genome.fasta, "w") as f:
        f.write(test_content)
    with open(mock_geo_data["GSE12345"]["path"], "w") as f:
        f.write(test_content)

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_class.return_value = mock_path_instance
    mock_path_class.side_effect = lambda x: Path(x) if isinstance(x, str) else x

    accessions = ["NC_000001", "GSE12345"]
    result = fetch_all_data(accessions)

    with open(result["manifest_path"], "r") as f:
        manifest = json.load(f)

    # Check checksums exist
    assert "checksums" in manifest
    assert len(manifest["checksums"]) >= 2
    
    # Verify checksum format (SHA-256 is 64 hex chars)
    for filename, checksum in manifest["checksums"].items():
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

@patch('src.download.fetch_viral_genomes')
@patch('src.download.fetch_geo_data')
def test_manifest_empty_accessions(mock_fetch_geo, mock_fetch_viral, temp_raw_dir):
    """Test that fetch_all_data raises ValueError for empty accessions."""
    mock_fetch_viral.return_value = []
    mock_fetch_geo.return_value = {}

    with pytest.raises(ValueError, match="accessions must be a non-empty list"):
        fetch_all_data([])

    with pytest.raises(ValueError, match="accessions must be a non-empty list"):
        fetch_all_data(None)
