import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

from verify_data_integrity import verify_data_integrity
from run_fabrication_audit import run_fabrication_audit

@pytest.fixture
def temp_project_dir():
    """Create a temporary project structure for testing."""
    base = tempfile.mkdtemp()
    project_root = Path(base)
    
    # Create necessary directories
    (project_root / "data" / "raw").mkdir(parents=True)
    (project_root / "data" / "processed").mkdir(parents=True)
    (project_root / "data" / "metadata").mkdir(parents=True)
    (project_root / "data" / "results").mkdir(parents=True)
    
    return project_root

def test_no_synthetic_artifacts_pass(temp_project_dir):
    """Test that a clean data directory passes the audit."""
    # Create a real-looking data file
    real_data = temp_project_dir / "data" / "raw" / "real_data.csv"
    real_data.write_text("id,value\n1,10\n2,20\n")
    
    result = verify_data_integrity(temp_project_dir)
    assert result["status"] == "PASS"
    assert len(result["found_artifacts"]) == 0

def test_synthetic_artifact_detected_fail(temp_project_dir):
    """Test that a synthetic placeholder file triggers a fail."""
    # Create a synthetic placeholder
    synth_data = temp_project_dir / "data" / "raw" / "synthetic_mock.csv"
    synth_data.write_text("id,value\n1,10\n")
    # Append the marker
    synth_data.write_text(synth_data.read_text() + "\nSYNTHETIC_PLACEHOLDER\n")
    
    result = verify_data_integrity(temp_project_dir)
    assert result["status"] == "FAIL"
    assert "data/raw/synthetic_mock.csv" in result["found_artifacts"]

def test_fabrication_audit_report_generation(temp_project_dir):
    """Test that T067 generates the correct report structure."""
    # Setup: Create a clean environment
    (temp_project_dir / "data" / "processed" / "harmonized_data.parquet").touch()
    
    report = run_fabrication_audit(temp_project_dir)
    
    assert "audit_id" in report
    assert report["audit_id"] == "T067-FABRICATION-AUDIT"
    assert "status" in report
    assert "verdict" in report
    assert report["verdict"] == "CLEAN"
    
    # Verify file exists
    report_path = temp_project_dir / "data" / "results" / "fabrication_audit_report.json"
    assert report_path.exists()
    
    with open(report_path) as f:
        saved_report = json.load(f)
    assert saved_report["status"] == report["status"]

def test_fabrication_audit_fails_on_synthetic(temp_project_dir):
    """Test that T067 fails if synthetic artifacts are found."""
    synth_data = temp_project_dir / "data" / "raw" / "synthetic_test.csv"
    synth_data.write_text("col1,col2\n1,2\nSYNTHETIC_PLACEHOLDER\n")
    
    # Create a harmonized file to simulate real-data context
    (temp_project_dir / "data" / "processed" / "harmonized_data.parquet").touch()
    
    report = run_fabrication_audit(temp_project_dir)
    
    assert report["status"] == "FAIL"
    assert report["verdict"] == "FABRICATION_DETECTED"
    assert len(report["synthetic_artifacts_found"]) > 0
