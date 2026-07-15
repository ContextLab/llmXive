"""
Tests for directory structure management and CSV validation.
"""
import pytest
import os
import csv
from pathlib import Path
import tempfile
import shutil

from generation.directories import (
    ensure_output_dirs,
    validate_csv_structure,
    validate_all_artifacts,
    create_sample_csvs,
    run_directory_validation,
    REQUIRED_DIRS,
    REQUIRED_CSVS,
)


class TestEnsureOutputDirs:
    """Tests for directory creation functionality."""

    def test_creates_missing_directories(self, tmp_path):
        """Verify that missing directories are created."""
        result = ensure_output_dirs(tmp_path)
        
        # Check that all required directories were created
        for dir_name in REQUIRED_DIRS:
            full_path = tmp_path / dir_name
            assert full_path.exists()
            assert full_path.is_dir()

    def test_returns_created_directories(self, tmp_path):
        """Verify that the function returns paths of created directories."""
        result = ensure_output_dirs(tmp_path)
        
        # All returned paths should exist
        for path_str in result:
            path = Path(path_str)
            assert path.exists()
            assert path.is_dir()

    def test_no_error_when_directories_exist(self, tmp_path):
        """Verify that no error occurs if directories already exist."""
        # Create directories first
        for dir_name in REQUIRED_DIRS:
            (tmp_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        # Should not raise
        result = ensure_output_dirs(tmp_path)
        
        # Should return the existing directories
        assert len(result) == len(REQUIRED_DIRS)


class TestValidateCsvStructure:
    """Tests for CSV validation functionality."""

    def test_file_not_exists(self, tmp_path):
        """Verify validation returns error when file doesn't exist."""
        non_existent = tmp_path / "nonexistent.csv"
        result = validate_csv_structure(non_existent, ["col1", "col2"])
        
        assert result["exists"] is False
        assert result["valid_headers"] is False
        assert len(result["errors"]) > 0
        assert "does not exist" in result["errors"][0]

    def test_empty_file(self, tmp_path):
        """Verify validation handles empty CSV files."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.touch()
        
        result = validate_csv_structure(empty_csv, ["col1", "col2"])
        
        assert result["exists"] is True
        assert result["valid_headers"] is False
        assert "empty" in result["errors"][0].lower()

    def test_valid_csv_with_correct_headers(self, tmp_path):
        """Verify validation succeeds with correct headers."""
        valid_csv = tmp_path / "valid.csv"
        with open(valid_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2", "col3"])
            writer.writerow(["val1", "val2", "val3"])
            writer.writerow(["val4", "val5", "val6"])
        
        result = validate_csv_structure(valid_csv, ["col1", "col2", "col3"])
        
        assert result["exists"] is True
        assert result["valid_headers"] is True
        assert result["row_count"] == 2
        assert result["headers"] == ["col1", "col2", "col3"]

    def test_missing_headers(self, tmp_path):
        """Verify validation fails when headers are missing."""
        invalid_csv = tmp_path / "invalid.csv"
        with open(invalid_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2"])  # Missing col3
            writer.writerow(["val1", "val2"])
        
        result = validate_csv_structure(invalid_csv, ["col1", "col2", "col3"])
        
        assert result["exists"] is True
        assert result["valid_headers"] is False
        assert len(result["errors"]) > 0
        assert "Missing headers" in result["errors"][0]

    def test_extra_headers(self, tmp_path):
        """Verify validation warns about extra headers but succeeds."""
        extra_csv = tmp_path / "extra.csv"
        with open(extra_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2", "col3", "col4"])
            writer.writerow(["val1", "val2", "val3", "val4"])
        
        result = validate_csv_structure(extra_csv, ["col1", "col2", "col3"])
        
        assert result["exists"] is True
        assert result["valid_headers"] is True
        # Extra headers should not cause failure
        assert len(result["errors"]) == 0


class TestCreateSampleCsvs:
    """Tests for sample CSV creation."""

    def test_creates_all_required_csvs(self, tmp_path):
        """Verify that all required CSV files are created."""
        result = create_sample_csvs(tmp_path)
        
        assert len(result) == len(REQUIRED_CSVS)
        
        for csv_name, path in result.items():
            assert path.exists()
            assert path.is_file()

    def test_csvs_have_correct_headers(self, tmp_path):
        """Verify that created CSVs have the correct headers."""
        result = create_sample_csvs(tmp_path)
        
        for csv_name, expected_headers in REQUIRED_CSVS.items():
            path = tmp_path / "data/processed" / csv_name
            
            with open(path, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
                assert headers == expected_headers

    def test_no_overwrite_existing_csvs(self, tmp_path):
        """Verify that existing CSVs are not overwritten."""
        # Create a CSV with custom content
        processed_dir = tmp_path / "data/processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        test_csv = processed_dir / "samples_all.csv"
        with open(test_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["custom_header"])
            writer.writerow(["custom_value"])
        
        # Run creation
        create_sample_csvs(tmp_path)
        
        # Verify original content is preserved
        with open(test_csv, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            assert headers == ["custom_header"]


class TestValidateAllArtifacts:
    """Tests for full artifact validation."""

    def test_all_valid(self, tmp_path):
        """Verify validation passes when all artifacts are valid."""
        # Create all required CSVs
        create_sample_csvs(tmp_path)
        
        result = validate_all_artifacts(tmp_path)
        
        assert result["all_valid"] is True
        assert len(result["artifacts"]) == len(REQUIRED_CSVS)

    def test_missing_csv(self, tmp_path):
        """Verify validation fails when a CSV is missing."""
        # Create only some CSVs
        processed_dir = tmp_path / "data/processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create only one CSV
        with open(processed_dir / "samples_all.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["task_id", "style"])
        
        result = validate_all_artifacts(tmp_path)
        
        assert result["all_valid"] is False
        assert result["artifacts"]["samples_all.csv"]["valid_headers"] is True
        assert result["artifacts"]["samples_valid.csv"]["exists"] is False

    def test_invalid_headers(self, tmp_path):
        """Verify validation fails when CSV has wrong headers."""
        # Create CSVs with wrong headers
        processed_dir = tmp_path / "data/processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        for csv_name, expected_headers in REQUIRED_CSVS.items():
            path = processed_dir / csv_name
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["wrong_header"])
        
        result = validate_all_artifacts(tmp_path)
        
        assert result["all_valid"] is False
        for csv_name in REQUIRED_CSVS:
            assert result["artifacts"][csv_name]["valid_headers"] is False


class TestRunDirectoryValidation:
    """Tests for the full validation pipeline."""

    def test_success_case(self, tmp_path):
        """Verify validation succeeds in a clean environment."""
        # Create all required CSVs
        create_sample_csvs(tmp_path)
        
        result = run_directory_validation(tmp_path)
        
        assert result is True

    def test_failure_case(self, tmp_path):
        """Verify validation fails when artifacts are missing."""
        # Don't create any CSVs
        result = run_directory_validation(tmp_path)
        
        assert result is False

    def test_creates_missing_directories(self, tmp_path):
        """Verify that validation creates missing directories."""
        # Remove data/processed directory
        processed_dir = tmp_path / "data" / "processed"
        if processed_dir.exists():
            shutil.rmtree(processed_dir)
        
        result = run_directory_validation(tmp_path)
        
        # Should still fail due to missing CSVs, but directories should exist
        assert (tmp_path / "data/processed").exists()