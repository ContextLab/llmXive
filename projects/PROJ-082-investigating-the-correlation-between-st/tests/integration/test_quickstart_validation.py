"""
Integration tests for the Quickstart Validation script (T036).

These tests verify that the validation script correctly identifies
a successful pipeline run and correctly flags failures.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Setup path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directories
    dirs = ["code", "tests", "data", "data/derived", "docs", "contracts", "figures"]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    
    # Create a mock input CSV
    input_csv = tmp_path / "data" / "input" / "studies.csv"
    input_csv.write_text("id,tract,r,n\n1,Arcuate,0.5,20\n")
    
    # Create a mock result JSON
    result_json = tmp_path / "data" / "derived" / "meta_analysis_result.json"
    result_json.write_text(json.dumps({
        "study_count": 1,
        "synthesis_mode": "narrative",
        "weighted_mean_r": 0.5,
        "qualitative_notes": "Test notes"
    }))
    
    # Create mock plots
    (tmp_path / "figures" / "forest_plot.png").write_bytes(b"fake_png_data")
    (tmp_path / "figures" / "funnel_plot.png").write_bytes(b"fake_png_data")
    (tmp_path / "figures" / "correlation_summary.png").write_bytes(b"fake_png_data")
    
    # Create mock report
    (tmp_path / "docs" / "paper_draft.md").write_text("# Test Report")
    
    return tmp_path

def test_check_directories_pass(temp_project_root):
    """Test that directory check passes when structure is correct."""
    # We need to patch the project_root variable in the module
    import code.quickstart_validator as validator
    
    with patch.object(validator, 'project_root', temp_project_root):
        assert validator.check_directories() is True

def test_check_directories_fail(temp_project_root):
    """Test that directory check fails when structure is missing."""
    import code.quickstart_validator as validator
    
    # Remove a required directory
    (temp_project_root / "docs").rmdir()
    
    with patch.object(validator, 'project_root', temp_project_root):
        assert validator.check_directories() is False

def test_verify_artifacts_pass(temp_project_root):
    """Test artifact verification passes when all files exist."""
    import code.quickstart_validator as validator
    
    with patch.object(validator, 'project_root', temp_project_root):
        assert validator.verify_artifacts() is True

def test_verify_artifacts_fail(temp_project_root):
    """Test artifact verification fails when a file is missing."""
    import code.quickstart_validator as validator
    
    # Remove a required artifact
    (temp_project_root / "figures" / "forest_plot.png").unlink()
    
    with patch.object(validator, 'project_root', temp_project_root):
        assert validator.verify_artifacts() is False

def test_validate_json_content_pass(temp_project_root):
    """Test JSON validation passes with valid content."""
    import code.quickstart_validator as validator
    
    json_path = temp_project_root / "data" / "derived" / "meta_analysis_result.json"
    assert validator.validate_json_content(json_path) is True

def test_validate_json_content_fail(temp_project_root):
    """Test JSON validation fails with missing keys."""
    import code.quickstart_validator as validator
    
    json_path = temp_project_root / "data" / "derived" / "meta_analysis_result.json"
    json_path.write_text(json.dumps({"study_count": 1})) # Missing other keys
    
    assert validator.validate_json_content(json_path) is False

def test_validate_json_content_invalid_json(temp_project_root):
    """Test JSON validation fails with invalid JSON."""
    import code.quickstart_validator as validator
    
    json_path = temp_project_root / "data" / "derived" / "meta_analysis_result.json"
    json_path.write_text("not valid json")
    
    assert validator.validate_json_content(json_path) is False
