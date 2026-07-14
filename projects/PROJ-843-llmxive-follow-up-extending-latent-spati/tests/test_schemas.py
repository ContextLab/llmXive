"""
Tests for data schemas and directory structure validation.
"""
import os
import json
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.schemas import (
    create_directories,
    get_expected_strata,
    validate_strata_existence,
    validate_directory_structure,
    check_directory_contents,
    create_schema_report,
    ensure_schema_compliance,
    EXPECTED_DIRECTORIES,
    EXPECTED_STRATA
)
from config import get_data_dir, get_raw_dir, get_stratified_dir, get_features_dir, get_results_dir


class TestDataSchemas:
    """Test suite for data schema and directory validation functions."""

    def test_expected_directories_defined(self):
        """Test that expected directories are properly defined."""
        assert len(EXPECTED_DIRECTORIES) > 0
        assert "data/raw" in EXPECTED_DIRECTORIES
        assert "data/stratified" in EXPECTED_DIRECTORIES
        assert "data/features" in EXPECTED_DIRECTORIES
        assert "data/results" in EXPECTED_DIRECTORIES

    def test_expected_strata_defined(self):
        """Test that expected strata are properly defined."""
        assert len(EXPECTED_STRATA) == 4
        assert "Static-High" in EXPECTED_STRATA
        assert "Static-Low" in EXPECTED_STRATA
        assert "Fast-High" in EXPECTED_STRATA
        assert "Fast-Low" in EXPECTED_STRATA

    def test_get_expected_strata_returns_copy(self):
        """Test that get_expected_strata returns a copy, not the original."""
        strata = get_expected_strata()
        strata.append("Fake-Stratum")
        assert "Fake-Stratum" not in get_expected_strata()

    def test_create_directories_creates_all(self):
        """Test that create_directories creates all required directories."""
        results = create_directories()
        
        for dir_path in EXPECTED_DIRECTORIES:
            assert results.get(dir_path, False), f"Directory {dir_path} was not created"
        
        # Check strata subdirectories
        for stratum in EXPECTED_STRATA:
            assert results.get(f"stratified/{stratum}", False), f"Stratum {stratum} not created"
            assert results.get(f"features/{stratum}", False), f"Feature dir for {stratum} not created"

    def test_validate_directory_structure(self):
        """Test directory structure validation."""
        # First create directories
        create_directories()
        
        # Then validate
        all_exist, missing = validate_directory_structure()
        assert all_exist, f"Missing directories: {missing}"
        assert len(missing) == 0

    def test_validate_strata_existence(self):
        """Test strata existence validation."""
        # First create directories
        create_directories()
        
        # Then validate
        strata_exist, missing = validate_strata_existence()
        assert strata_exist, f"Missing strata: {missing}"
        assert len(missing) == 0

    def test_check_directory_contents(self):
        """Test checking directory contents."""
        create_directories()
        
        for dir_type in ["raw", "processed", "stratified", "features", "results"]:
            contents = check_directory_contents(dir_type)
            assert "exists" in contents
            assert "path" in contents
            assert contents["exists"], f"Directory {dir_type} does not exist"

    def test_create_schema_report(self):
        """Test schema report creation."""
        create_directories()
        
        report = create_schema_report()
        
        assert "expected_directories" in report
        assert "expected_strata" in report
        assert "directory_status" in report
        assert "validation_results" in report
        
        assert report["validation_results"]["all_directories_exist"]
        assert report["validation_results"]["all_strata_exist"]

    def test_ensure_schema_compliance(self):
        """Test schema compliance enforcement."""
        result = ensure_schema_compliance()
        assert result, "Schema compliance check failed"

    def test_directory_paths_are_absolute(self):
        """Test that config directory paths are absolute."""
        assert get_data_dir().is_absolute()
        assert get_raw_dir().is_absolute()
        assert get_stratified_dir().is_absolute()
        assert get_features_dir().is_absolute()
        assert get_results_dir().is_absolute()

    def test_strata_directories_exist_after_creation(self):
        """Test that strata subdirectories exist after creation."""
        create_directories()
        
        stratified_dir = get_stratified_dir()
        features_dir = get_features_dir()
        
        for stratum in EXPECTED_STRATA:
            assert (stratified_dir / stratum).exists()
            assert (features_dir / stratum).exists()

    def test_report_can_be_saved_to_file(self):
        """Test that schema report can be saved to a file."""
        create_directories()
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            report = create_schema_report(output_path=temp_path)
            
            # Verify file was created
            assert os.path.exists(temp_path)
            
            # Verify file content is valid JSON
            with open(temp_path, 'r') as f:
                loaded_report = json.load(f)
            
            assert loaded_report == report
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
