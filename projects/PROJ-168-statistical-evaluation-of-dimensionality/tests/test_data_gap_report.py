import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_gap_resolver import DatasetStatus, DataGapResolver
from config import Config

@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config with temporary directories"""
    config = MagicMock(spec=Config)
    config.data_dir = tmp_path / "data"
    config.results_dir = tmp_path / "results"
    config.dataset_accessions = ["GSE131907", "GSE111322", "GSE150728"]
    
    # Create necessary directories
    (config.data_dir / "raw").mkdir(parents=True, exist_ok=True)
    config.results_dir.mkdir(parents=True, exist_ok=True)
    
    return config

@pytest.fixture
def mock_file(tmp_path):
    """Create a mock data file for testing found datasets"""
    file_path = tmp_path / "data" / "raw" / "GSE131907_counts.h5ad"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("mock data content")
    return file_path

def test_dataset_status_to_dict():
    """Test that DatasetStatus serializes correctly"""
    status = DatasetStatus(
        accession="GSE131907",
        found=True,
        path="/path/to/file.h5ad",
        checksum="abc123",
        reason="File found"
    )
    
    result = status.to_dict()
    assert result["accession"] == "GSE131907"
    assert result["found"] is True
    assert result["path"] == "/path/to/file.h5ad"
    assert result["checksum"] == "abc123"
    assert result["reason"] == "File found"

def test_data_gap_resolver_found(mock_config, mock_file):
    """Test resolver when a dataset is found"""
    resolver = DataGapResolver(mock_config)
    report = resolver.resolve_all()
    
    # Should find 1 dataset (GSE131907)
    assert report["datasets_found"] == 1
    assert report["total_datasets_checked"] == 3
    assert report["final_status"] == "Case-Study"  # Only 1 found
    
    # Verify report file was created
    report_path = mock_config.results_dir / "data_gap_report.json"
    assert report_path.exists()
    
    # Verify JSON content
    with open(report_path) as f:
        json_content = json.load(f)
    assert json_content["final_status"] == "Case-Study"
    assert len(json_content["dataset_details"]) == 3

def test_data_gap_resolver_all_found(mock_config, tmp_path):
    """Test resolver when all datasets are found"""
    # Create mock files for all datasets
    for accession in mock_config.dataset_accessions:
        file_path = tmp_path / "data" / "raw" / f"{accession}_counts.h5ad"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("mock data")
    
    resolver = DataGapResolver(mock_config)
    report = resolver.resolve_all()
    
    assert report["datasets_found"] == 3
    assert report["final_status"] == "Full"

def test_data_gap_resolver_none_found(mock_config):
    """Test resolver when no datasets are found"""
    resolver = DataGapResolver(mock_config)
    report = resolver.resolve_all()
    
    assert report["datasets_found"] == 0
    assert report["final_status"] == "Aborted"
    assert "No datasets found" in report["status_reason"]

def test_checksum_validation(mock_config, mock_file):
    """Test that checksums are calculated for found files"""
    resolver = DataGapResolver(mock_config)
    
    # Check the specific dataset
    status = resolver.check_dataset("GSE131907")
    
    assert status.found is True
    assert status.checksum is not None
    assert len(status.checksum) == 64  # SHA256 hex length