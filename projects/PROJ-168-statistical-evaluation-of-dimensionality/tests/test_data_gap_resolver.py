import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_gap_resolver import DataGapResolver, DatasetStatus

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "data" / "raw"
        results_dir = Path(tmpdir) / "results"
        raw_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        yield {
            "raw": raw_dir,
            "results": results_dir,
            "tmp": Path(tmpdir)
        }

def test_dataset_status_to_dict():
    """Test DatasetStatus serialization."""
    status = DatasetStatus(
        accession="GSE123",
        status="found",
        details="Test details",
        file_path="/path/to/file.csv"
    )
    result = status.to_dict()
    assert result["accession"] == "GSE123"
    assert result["status"] == "found"
    assert result["details"] == "Test details"
    assert result["file_path"] == "/path/to/file.csv"

def test_resolve_all_generates_report(temp_dirs):
    """Test that resolve_all creates the report file."""
    resolver = DataGapResolver(raw_data_dir=str(temp_dirs["raw"]))
    resolver.results_dir = temp_dirs["results"]
    
    # Mock the resolve_single method to return known statuses
    mock_statuses = [
        DatasetStatus("GSE131907", "found", "Test found", "file1.csv"),
        DatasetStatus("GSE111322", "missing", "Test missing"),
        DatasetStatus("GSE150728", "found", "Test found", "file2.csv")
    ]
    
    with patch.object(resolver, 'resolve_single', side_effect=mock_statuses):
        report = resolver.resolve_all()
    
    # Check report structure
    assert "datasets" in report
    assert "summary" in report
    assert report["summary"]["final_status"] == "Full"
    assert report["summary"]["found"] == 2
    assert report["summary"]["missing"] == 1
    
    # Check file was written
    report_path = temp_dirs["results"] / "data_gap_report.json"
    assert report_path.exists()
    
    with open(report_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["summary"]["final_status"] == "Full"

def test_resolve_all_case_study_mode(temp_dirs):
    """Test Case-Study mode when only 1 dataset is found."""
    resolver = DataGapResolver(raw_data_dir=str(temp_dirs["raw"]))
    resolver.results_dir = temp_dirs["results"]
    
    mock_statuses = [
        DatasetStatus("GSE131907", "found", "Test found", "file1.csv"),
        DatasetStatus("GSE111322", "missing", "Test missing"),
        DatasetStatus("GSE150728", "missing", "Test missing")
    ]
    
    with patch.object(resolver, 'resolve_single', side_effect=mock_statuses):
        report = resolver.resolve_all()
    
    assert report["summary"]["final_status"] == "Case-Study"
    assert report["summary"]["found"] == 1

def test_resolve_all_aborted_mode(temp_dirs):
    """Test Aborted mode when no datasets are found."""
    resolver = DataGapResolver(raw_data_dir=str(temp_dirs["raw"]))
    resolver.results_dir = temp_dirs["results"]
    
    mock_statuses = [
        DatasetStatus("GSE131907", "missing", "Test missing"),
        DatasetStatus("GSE111322", "missing", "Test missing"),
        DatasetStatus("GSE150728", "missing", "Test missing")
    ]
    
    with patch.object(resolver, 'resolve_single', side_effect=mock_statuses):
        report = resolver.resolve_all()
    
    assert report["summary"]["final_status"] == "Aborted"
    assert report["summary"]["found"] == 0

def test_validate_raw_count_content_csv(temp_dirs):
    """Test validation of CSV count matrix."""
    csv_content = """GeneID,Sample1,Sample2,Sample3
    GeneA,10,20,30
    GeneB,5,15,25
    GeneC,0,5,10
    """
    csv_file = temp_dirs["raw"] / "test_counts.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    resolver = DataGapResolver(raw_data_dir=str(temp_dirs["raw"]))
    assert resolver._validate_raw_count_content(csv_file) is True

def test_validate_raw_count_content_invalid_csv(temp_dirs):
    """Test validation rejects non-numeric CSV."""
    csv_content = """GeneID,Sample1,Sample2
    GeneA,abc,def
    GeneB,1,2
    """
    csv_file = temp_dirs["raw"] / "invalid_counts.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    resolver = DataGapResolver(raw_data_dir=str(temp_dirs["raw"]))
    # This should fail because the first data line has non-numeric values
    # after the gene ID
    assert resolver._validate_raw_count_content(csv_file) is False

def test_validate_raw_count_content_mtx(temp_dirs):
    """Test validation of MTX matrix file."""
    mtx_content = """%%MatrixMarket matrix coordinate real general
    100 100 500
    1 1 10.5
    2 2 20.0
    """
    mtx_file = temp_dirs["raw"] / "test_matrix.mtx"
    with open(mtx_file, 'w') as f:
        f.write(mtx_content)
    
    resolver = DataGapResolver(raw_data_dir=str(temp_dirs["raw"]))
    assert resolver._validate_raw_count_content(mtx_file) is True

def test_validate_raw_count_content_empty_file(temp_dirs):
    """Test validation rejects empty files."""
    empty_file = temp_dirs["raw"] / "empty.csv"
    empty_file.touch()
    
    resolver = DataGapResolver(raw_data_dir=str(temp_dirs["raw"]))
    assert resolver._validate_raw_count_content(empty_file) is False