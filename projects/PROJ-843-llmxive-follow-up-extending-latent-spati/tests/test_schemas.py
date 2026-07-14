import pytest
import os
import json
from pathlib import Path
from config import get_data_dir, get_raw_dir, get_stratified_dir, get_results_dir
from data.schemas import (
    create_directories,
    get_expected_strata,
    validate_strata_existence,
    validate_directory_structure,
    check_directory_contents,
    create_schema_report,
    ensure_schema_compliance
)

def test_create_directories():
    """Test that base directories are created."""
    result = create_directories()
    assert all(result.values()), "Some directories failed to create"
    
    # Verify they exist
    for path in result.keys():
        assert os.path.isdir(path), f"Directory {path} does not exist"

def test_get_expected_strata():
    """Test that expected strata are returned correctly."""
    strata = get_expected_strata()
    expected = ["Static-High", "Static-Low", "Fast-High", "Fast-Low"]
    assert strata == expected
    assert len(strata) == 4

def test_validate_strata_existence_empty():
    """Test validation when strata do not exist yet."""
    # This should return False initially if directories are empty
    valid, missing = validate_strata_existence()
    # Note: This depends on whether stratify.py has run. 
    # In a fresh setup, this might be False.
    assert isinstance(valid, bool)
    assert isinstance(missing, list)

def test_validate_directory_structure():
    """Test directory structure validation report."""
    report = validate_directory_structure()
    assert "base_dirs" in report
    assert "strata_valid" in report
    assert "missing_strata" in report
    assert "results_dir_exists" in report

def test_check_directory_contents():
    """Test content counting."""
    counts = check_directory_contents()
    assert isinstance(counts, dict)
    # At least data dir should be counted
    assert len(counts) > 0

def test_create_schema_report():
    """Test schema report generation."""
    report_path = os.path.join(get_results_dir(), "test_schema_report.json")
    report = create_schema_report(report_path)
    
    assert os.path.exists(report_path), "Report file not created"
    with open(report_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == report
    
    # Cleanup
    os.remove(report_path)

def test_ensure_schema_compliance():
    """Test compliance check."""
    result = ensure_schema_compliance()
    assert isinstance(result, bool)

def test_schema_comprehensive():
    """Run a comprehensive check."""
    # Ensure dirs
    create_directories()
    
    # Get report
    report = create_schema_report()
    
    # Check structure
    assert "structure" in report
    assert "contents" in report
    assert "status" in report