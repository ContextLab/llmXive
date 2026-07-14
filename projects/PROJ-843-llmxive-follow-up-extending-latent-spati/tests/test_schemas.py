import pytest
from pathlib import Path
import json
import shutil
import tempfile

# Import the module under test
from data.schemas import (
    create_directories,
    get_expected_strata,
    validate_strata_existence,
    validate_directory_structure,
    check_directory_contents,
    create_schema_report,
    ensure_schema_compliance,
    DATA_SCHEMA
)
from config import get_data_dir, get_stratified_dir, get_results_dir


@pytest.fixture
def temp_data_root(tmp_path):
    """
    Create a temporary directory to simulate the project data root.
    We monkeypatch the config functions to use this temp path for the duration of the test.
    """
    # Save original functions
    import config
    original_get_data_dir = config.get_data_dir
    
    # Mock the config functions to point to temp_path
    def mock_get_data_dir():
        return tmp_path / "data"
    
    def mock_get_raw_dir():
        return mock_get_data_dir() / "raw"
    
    def mock_get_processed_dir():
        return mock_get_data_dir() / "processed"
    
    def mock_get_stratified_dir():
        return mock_get_data_dir() / "stratified"
    
    def mock_get_features_dir():
        return mock_get_data_dir() / "features"
    
    def mock_get_results_dir():
        return mock_get_data_dir() / "results"

    # Patch
    config.get_data_dir = mock_get_data_dir
    config.get_raw_dir = mock_get_raw_dir
    config.get_processed_dir = mock_get_processed_dir
    config.get_stratified_dir = mock_get_stratified_dir
    config.get_features_dir = mock_get_features_dir
    config.get_results_dir = mock_get_results_dir

    yield tmp_path / "data"

    # Restore
    config.get_data_dir = original_get_data_dir


def test_create_directories_creates_all_required_paths(temp_data_root):
    """Test that create_directories creates the full hierarchy."""
    paths = create_directories()
    
    assert "root" in paths
    assert "raw" in paths
    assert "processed" in paths
    assert "stratified" in paths
    assert "features" in paths
    assert "results" in paths
    
    # Check existence on disk
    for key, path in paths.items():
        assert path.exists(), f"Directory {key} ({path}) was not created"

    # Check strata subdirectories
    strata = get_expected_strata()
    for s in strata:
        strata_path = temp_data_root / "stratified" / s
        assert strata_path.exists(), f"Stratum directory {s} was not created"
        
        feature_path = temp_data_root / "features" / s
        assert feature_path.exists(), f"Feature directory for {s} was not created"


def test_get_expected_strata_returns_correct_list():
    """Test that the expected strata list is correct."""
    strata = get_expected_strata()
    expected = ["static_high", "static_low", "fast_high", "fast_low"]
    assert strata == expected


def test_validate_strata_existence_false_when_missing(temp_data_root):
    """Test validation fails if strata are missing."""
    # Delete one stratum
    missing_stratum = temp_data_root / "stratified" / "static_high"
    if missing_stratum.exists():
        shutil.rmtree(missing_stratum)
    
    is_valid, missing_list = validate_strata_existence()
    
    assert not is_valid
    assert "static_high" in missing_list


def test_validate_directory_structure(temp_data_root):
    """Test full structure validation."""
    # Initially valid after creation
    create_directories()
    is_valid, missing = validate_directory_structure()
    assert is_valid, f"Structure should be valid, but missing: {missing}"


def test_check_directory_contents(temp_data_root):
    """Test checking for required files in a directory."""
    create_directories()
    
    # Test empty directory (no required files)
    valid, missing = check_directory_contents(temp_data_root / "raw", [])
    assert valid
    assert len(missing) == 0

    # Test with required file that doesn't exist
    valid, missing = check_directory_contents(temp_data_root / "results", ["metrics.json"])
    assert not valid
    assert "metrics.json" in missing

    # Create the file and test again
    (temp_data_root / "results" / "metrics.json").touch()
    valid, missing = check_directory_contents(temp_data_root / "results", ["metrics.json"])
    assert valid


def test_create_schema_report(temp_data_root):
    """Test schema report generation."""
    create_directories()
    report_path = temp_data_root / "schema_report.json"
    
    create_schema_report(report_path)
    
    assert report_path.exists()
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["structure_valid"] is True
    assert report["strata_valid"] is True
    assert "details" in report


def test_ensure_schema_compliance_creates_missing(temp_data_root):
    """Test that ensure_schema_compliance creates missing dirs."""
    # Remove a directory
    shutil.rmtree(temp_data_root / "results")
    
    result = ensure_schema_compliance()
    
    assert result is True
    assert (temp_data_root / "results").exists()
