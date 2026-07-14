import pytest
from pathlib import Path
import tempfile
import shutil
import json

# Import functions to test
from data.schemas import (
    validate_directory_structure,
    create_directories,
    check_directory_contents,
    get_expected_strata,
    validate_strata_existence,
    create_schema_report,
    ensure_schema_compliance,
    EXPECTED_DIRS,
    EXPECTED_STRATA,
    DIRECTORY_SCHEMA,
)

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_get_expected_strata():
    """Test that expected strata are correctly defined."""
    strata = get_expected_strata()
    assert len(strata) == 4
    assert "Static-High" in strata
    assert "Static-Low" in strata
    assert "Fast-High" in strata
    assert "Fast-Low" in strata

def test_validate_directory_structure_empty(temp_project_root):
    """Test validation on empty directory structure."""
    is_valid, missing = validate_directory_structure(temp_project_root)
    assert not is_valid
    assert len(missing) == len(EXPECTED_DIRS)
    for dir_name in EXPECTED_DIRS:
        assert str(temp_project_root / dir_name) in missing

def test_create_directories(temp_project_root):
    """Test directory creation."""
    success = create_directories(temp_project_root)
    assert success
    
    # Verify directories were created
    is_valid, _ = validate_directory_structure(temp_project_root)
    assert is_valid

def test_ensure_schema_compliance(temp_project_root):
    """Test full schema compliance setup."""
    success = ensure_schema_compliance(temp_project_root)
    assert success
    
    # Verify structure
    is_valid, _ = validate_directory_structure(temp_project_root)
    assert is_valid
    
    # Verify strata
    strata_valid, _ = validate_strata_existence(temp_project_root)
    assert strata_valid

def test_validate_strata_existence(temp_project_root):
    """Test strata validation."""
    # Initially should fail
    is_valid, missing = validate_strata_existence(temp_project_root)
    assert not is_valid
    assert len(missing) == len(EXPECTED_STRATA)
    
    # Create strata
    ensure_schema_compliance(temp_project_root)
    
    # Now should pass
    is_valid, missing = validate_strata_existence(temp_project_root)
    assert is_valid
    assert len(missing) == 0

def test_check_directory_contents(temp_project_root):
    """Test directory contents checking."""
    # Create structure first
    ensure_schema_compliance(temp_project_root)
    
    # Check raw directory (should be empty but exist)
    has_content, details = check_directory_contents("data/raw", temp_project_root)
    assert details["directory"] == str(temp_project_root / "data" / "raw")
    
    # Check results directory (should have required files if created)
    has_content, details = check_directory_contents("data/results", temp_project_root)
    assert details["directory"] == str(temp_project_root / "data" / "results")

def test_create_schema_report(temp_project_root):
    """Test schema report generation."""
    # Create structure
    ensure_schema_compliance(temp_project_root)
    
    # Generate report
    report = create_schema_report(temp_project_root)
    
    # Verify report structure
    assert "structure_valid" in report
    assert "strata_valid" in report
    assert "missing_dirs" in report
    assert "missing_strata" in report
    assert "directory_details" in report
    
    # Verify values
    assert report["structure_valid"] is True
    assert report["strata_valid"] is True
    assert len(report["missing_dirs"]) == 0
    assert len(report["missing_strata"]) == 0

def test_directory_schema_definition():
    """Test that directory schema is properly defined."""
    assert "data/raw" in DIRECTORY_SCHEMA
    assert "data/stratified" in DIRECTORY_SCHEMA
    assert "data/features" in DIRECTORY_SCHEMA
    assert "data/results" in DIRECTORY_SCHEMA
    
    # Check required fields
    assert "description" in DIRECTORY_SCHEMA["data/results"]
    assert "required_files" in DIRECTORY_SCHEMA["data/results"]
    
    # Check results directory requirements
    results_schema = DIRECTORY_SCHEMA["data/results"]
    assert "metrics.json" in results_schema["required_files"]
    assert "hypothesis_verification.md" in results_schema["required_files"]

def test_expected_dirs_constant():
    """Test that EXPECTED_DIRS constant is properly defined."""
    assert len(EXPECTED_DIRS) == 5
    assert "data/raw" in EXPECTED_DIRS
    assert "data/processed" in EXPECTED_DIRS
    assert "data/stratified" in EXPECTED_DIRS
    assert "data/features" in EXPECTED_DIRS
    assert "data/results" in EXPECTED_DIRS
