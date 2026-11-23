import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Import the functions from the module
# Assuming the test is run from the project root or added to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from data.spec_ratification import check_plan_for_amendment, create_ratification_log

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure for testing."""
    tmpdir = tempfile.mkdtemp()
    project_root = Path(tmpdir)
    
    # Create necessary directories
    (project_root / "data").mkdir()
    (project_root / "docs").mkdir()
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(tmpdir)

def test_check_plan_for_amendment_missing(temp_project_dir):
    """Test checking for amendment when file does not exist."""
    amendment_path = temp_project_dir / "docs" / "amendment_record.md"
    result = check_plan_for_amendment(amendment_path)
    
    assert result["exists"] is False
    assert result["status"] is None

def test_check_plan_for_amendment_pending(temp_project_dir):
    """Test checking for amendment when file exists with PENDING status."""
    amendment_path = temp_project_dir / "docs" / "amendment_record.md"
    amendment_path.write_text("# Amendment Record\nStatus: PENDING")
    
    result = check_plan_for_amendment(amendment_path)
    
    assert result["exists"] is True
    assert result["status"] == "PENDING"

def test_check_plan_for_amendment_ratified(temp_project_dir):
    """Test checking for amendment when file exists with RATIFIED status."""
    amendment_path = temp_project_dir / "docs" / "amendment_record.md"
    amendment_path.write_text("# Amendment Record\nStatus: RATIFIED")
    
    result = check_plan_for_amendment(amendment_path)
    
    assert result["exists"] is True
    assert result["status"] == "RATIFIED"

def test_create_ratification_log_all_success(temp_project_dir):
    """Test log creation when all downloads are successful."""
    download_status = {
        "recipe1m": {"status": "SUCCESS"},
        "flavordb": {"status": "SUCCESS"},
        "counterfactual": {"status": "SUCCESS"}
    }
    download_path = temp_project_dir / "data" / "download_status.json"
    with open(download_path, 'w') as f:
        json.dump(download_status, f)
    
    amendment_path = temp_project_dir / "data" / "amendment_log.json"
    
    log = create_ratification_log(download_path, amendment_path, temp_project_dir / "docs" / "amendment_record.md")
    
    assert log["status"] == "RATIFIED"
    assert log["methodology"] == "Causal Independence"
    assert log["proxy_source"] is None

def test_create_ratification_log_recipe1m_failed(temp_project_dir):
    """Test that log creation raises error if Recipe1M failed."""
    download_status = {
        "recipe1m": {"status": "FAILED"},
        "flavordb": {"status": "SUCCESS"},
        "counterfactual": {"status": "SUCCESS"}
    }
    download_path = temp_project_dir / "data" / "download_status.json"
    with open(download_path, 'w') as f:
        json.dump(download_status, f)
    
    amendment_path = temp_project_dir / "data" / "amendment_log.json"
    
    with pytest.raises(RuntimeError, match="Pipeline Halt: Recipe1M download failed"):
        create_ratification_log(download_path, amendment_path, temp_project_dir / "docs" / "amendment_record.md")

def test_create_ratification_log_amendment_needed_no_record(temp_project_dir):
    """Test log creation when amendment needed but record missing."""
    download_status = {
        "recipe1m": {"status": "SUCCESS"},
        "flavordb": {"status": "FAILED"},
        "counterfactual": {"status": "SUCCESS"}
    }
    download_path = temp_project_dir / "data" / "download_status.json"
    with open(download_path, 'w') as f:
        json.dump(download_status, f)
    
    amendment_path = temp_project_dir / "data" / "amendment_log.json"
    amendment_record_path = temp_project_dir / "docs" / "amendment_record.md"
    # Ensure record does not exist
    
    log = create_ratification_log(download_path, amendment_path, amendment_record_path)
    
    assert log["status"] == "PENDING"
    assert log["methodology"] == "Correlational Analysis"
    assert log["proxy_source"] == "Recipe1M"
    
    # Verify file was written
    assert amendment_path.exists()
    with open(amendment_path, 'r') as f:
        written_log = json.load(f)
    assert written_log["status"] == "PENDING"

def test_create_ratification_log_amendment_needed_record_ratified(temp_project_dir):
    """Test log creation when amendment needed and record is RATIFIED."""
    download_status = {
        "recipe1m": {"status": "SUCCESS"},
        "flavordb": {"status": "FAILED"},
        "counterfactual": {"status": "SUCCESS"}
    }
    download_path = temp_project_dir / "data" / "download_status.json"
    with open(download_path, 'w') as f:
        json.dump(download_status, f)
    
    amendment_path = temp_project_dir / "data" / "amendment_log.json"
    amendment_record_path = temp_project_dir / "docs" / "amendment_record.md"
    amendment_record_path.write_text("# Amendment Record\nStatus: RATIFIED")
    
    log = create_ratification_log(download_path, amendment_path, amendment_record_path)
    
    assert log["status"] == "RATIFIED"
    assert log["methodology"] == "Correlational Analysis"
    assert log["proxy_source"] == "Recipe1M"