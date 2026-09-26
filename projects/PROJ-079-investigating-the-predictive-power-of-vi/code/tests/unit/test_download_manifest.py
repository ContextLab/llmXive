import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from src.download import generate_manifest
from src.config import DATA_RAW_PATH, ARTIFACTS_PATH

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory for raw data files."""
    temp_dir = tempfile.mkdtemp()
    # Create mock FASTA files for NCBI accessions
    for acc in ['NC_001', 'NC_002', 'NC_003']:
        fasta_path = Path(temp_dir) / f"{acc}.fasta"
        fasta_path.write_text(f">Sequence for {acc}\nATCGATCGATCG")
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_artifacts_dir():
    """Create a temporary directory for artifacts."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_manifest_v1_structure(temp_raw_dir, temp_artifacts_dir):
    """Test that generate_manifest creates a valid manifest structure."""
    with patch('src.download.DATA_RAW_PATH', temp_raw_dir), \
         patch('src.download.ARTIFACTS_PATH', temp_artifacts_dir):
        
        accessions = ['NC_001', 'NC_002']
        geo_accessions = ['GSE001', 'GSE002']
        
        # Create mock GEO files
        for geo_acc in geo_accessions:
            geo_path = Path(temp_raw_dir) / f"{geo_acc}_matrix.txt"
            geo_path.write_text("Mock GEO data")
        
        generate_manifest(accessions, geo_accessions)
        
        manifest_path = Path(temp_artifacts_dir) / "manifest.json"
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Check required keys
        assert "accessions" in manifest
        assert "source" in manifest
        assert "timestamp" in manifest
        assert "version" in manifest
        assert "checksums" in manifest
        assert "validation" in manifest
        
        # Check validation structure
        assert "virus_strain_link_check" in manifest["validation"]
        assert "ortholog_mapping_check" in manifest["validation"]

def test_manifest_overwrites_existing(temp_raw_dir, temp_artifacts_dir):
    """Test that generate_manifest overwrites existing manifest."""
    with patch('src.download.DATA_RAW_PATH', temp_raw_dir), \
         patch('src.download.ARTIFACTS_PATH', temp_artifacts_dir):
        
        # Create initial manifest
        manifest_path = Path(temp_artifacts_dir) / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump({"old": "data"}, f)
        
        accessions = ['NC_001']
        geo_accessions = ['GSE001']
        
        # Create mock files
        (Path(temp_raw_dir) / "NC_001.fasta").write_text("ATCG")
        (Path(temp_raw_dir) / "GSE001_matrix.txt").write_text("data")
        
        generate_manifest(accessions, geo_accessions)
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "old" not in manifest
        assert "accessions" in manifest

def test_manifest_checksums_data(temp_raw_dir, temp_artifacts_dir):
    """Test that manifest contains correct checksums."""
    with patch('src.download.DATA_RAW_PATH', temp_raw_dir), \
         patch('src.download.ARTIFACTS_PATH', temp_artifacts_dir):
        
        accessions = ['NC_001']
        geo_accessions = ['GSE001']
        
        # Create mock files with known content
        fasta_path = Path(temp_raw_dir) / "NC_001.fasta"
        fasta_path.write_text("ATCG")
        
        geo_path = Path(temp_raw_dir) / "GSE001_matrix.txt"
        geo_path.write_text("GEO_DATA")
        
        generate_manifest(accessions, geo_accessions)
        
        manifest_path = Path(temp_artifacts_dir) / "manifest.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Check checksums exist
        assert "NC_001" in manifest["checksums"]
        assert "GSE001" in manifest["checksums"]
        
        # Verify checksum format
        assert manifest["checksums"]["NC_001"]["algorithm"] == "sha256"
        assert len(manifest["checksums"]["NC_001"]["value"]) == 64  # SHA-256 hex length
        assert "file" in manifest["checksums"]["NC_001"]

def test_manifest_empty_accessions(temp_raw_dir, temp_artifacts_dir):
    """Test manifest generation with empty accessions lists."""
    with patch('src.download.DATA_RAW_PATH', temp_raw_dir), \
         patch('src.download.ARTIFACTS_PATH', temp_artifacts_dir):
        
        generate_manifest([], [])
        
        manifest_path = Path(temp_artifacts_dir) / "manifest.json"
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["accessions"] == []
        assert manifest["source"] == []
        assert manifest["checksums"] == {}

def test_manifest_fr014_aborts_on_high_missing_ratio(temp_raw_dir, temp_artifacts_dir):
    """Test FR-014: Abort if >10% of samples lack virus_strain_accession link."""
    with patch('src.download.DATA_RAW_PATH', temp_raw_dir), \
         patch('src.download.ARTIFACTS_PATH', temp_artifacts_dir):
        
        # Create mock GEO files
        geo_accessions = ['GSE001', 'GSE002', 'GSE003', 'GSE004', 'GSE005']
        for geo_acc in geo_accessions:
            geo_path = Path(temp_raw_dir) / f"{geo_acc}_matrix.txt"
            geo_path.write_text("Mock data")
        
        # Mock the validation logic to simulate high failure rate
        with patch('src.download._check_virus_strain_link', return_value=False):
            with pytest.raises(RuntimeError) as exc_info:
                generate_manifest([], geo_accessions)
            
            assert "FR-014" in str(exc_info.value)
            assert "virus_strain_accession" in str(exc_info.value)

def test_manifest_fr013_excludes_missing_files(temp_raw_dir, temp_artifacts_dir):
    """Test FR-013: Exclude missing files but continue with remaining data."""
    with patch('src.download.DATA_RAW_PATH', temp_raw_dir), \
         patch('src.download.ARTIFACTS_PATH', temp_artifacts_dir):
        
        # Create only some of the expected files
        accessions = ['NC_001', 'NC_002', 'NC_003']
        geo_accessions = ['GSE001', 'GSE002']
        
        # Only create NC_001 and GSE001
        (Path(temp_raw_dir) / "NC_001.fasta").write_text("ATCG")
        (Path(temp_raw_dir) / "GSE001_matrix.txt").write_text("data")
        
        # Should not raise, but log warnings
        generate_manifest(accessions, geo_accessions)
        
        manifest_path = Path(temp_artifacts_dir) / "manifest.json"
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Only valid files should be in manifest
        assert "NC_001" in manifest["accessions"]
        assert "NC_002" not in manifest["accessions"]
        assert "NC_003" not in manifest["accessions"]
        assert "GSE001" in manifest["accessions"]
        assert "GSE002" not in manifest["accessions"]