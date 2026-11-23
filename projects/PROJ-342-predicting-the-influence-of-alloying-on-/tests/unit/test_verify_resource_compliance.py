import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Adjust path if running as module
import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from verify_resource_compliance import verify_resource_compliance, load_resource_usage

@pytest.fixture
def mock_resource_data():
    return {
        "peak_ram_gb": 5.2,
        "total_runtime_h": 3.5,
        "details": "Mocked resource data"
    }

def test_compliance_success(mock_resource_data, tmp_path):
    """Test successful compliance when limits are not exceeded."""
    resource_file = tmp_path / "resource_usage.json"
    resource_file.write_text(json.dumps(mock_resource_data))
    
    with patch('verify_resource_compliance.get_project_root', return_value=tmp_path):
        result = verify_resource_compliance(max_ram_gb=7.0, max_runtime_h=6.0)
    
    assert result["compliant"] is True
    assert result["ram_ok"] is True
    assert result["runtime_ok"] is True

def test_compliance_ram_exceeded(mock_resource_data, tmp_path):
    """Test failure when RAM limit is exceeded."""
    mock_resource_data["peak_ram_gb"] = 8.5
    resource_file = tmp_path / "resource_usage.json"
    resource_file.write_text(json.dumps(mock_resource_data))
    
    with patch('verify_resource_compliance.get_project_root', return_value=tmp_path):
        result = verify_resource_compliance(max_ram_gb=7.0, max_runtime_h=6.0)
    
    assert result["compliant"] is False
    assert result["ram_ok"] is False
    assert result["runtime_ok"] is True

def test_compliance_runtime_exceeded(mock_resource_data, tmp_path):
    """Test failure when runtime limit is exceeded."""
    mock_resource_data["total_runtime_h"] = 7.0
    resource_file = tmp_path / "resource_usage.json"
    resource_file.write_text(json.dumps(mock_resource_data))
    
    with patch('verify_resource_compliance.get_project_root', return_value=tmp_path):
        result = verify_resource_compliance(max_ram_gb=7.0, max_runtime_h=6.0)
    
    assert result["compliant"] is False
    assert result["ram_ok"] is True
    assert result["runtime_ok"] is False

def test_file_not_found(tmp_path):
    """Test handling of missing resource usage file."""
    with patch('verify_resource_compliance.get_project_root', return_value=tmp_path):
        result = verify_resource_compliance()
    
    assert result["compliant"] is False
    assert "Resource usage file not found" in result["error"]

def test_load_resource_usage(tmp_path, mock_resource_data):
    """Test loading resource usage file."""
    resource_file = tmp_path / "resource_usage.json"
    resource_file.write_text(json.dumps(mock_resource_data))
    
    with patch('verify_resource_compliance.get_project_root', return_value=tmp_path):
        data = load_resource_usage()
    
    assert data["peak_ram_gb"] == mock_resource_data["peak_ram_gb"]
    assert data["total_runtime_h"] == mock_resource_data["total_runtime_h"]
