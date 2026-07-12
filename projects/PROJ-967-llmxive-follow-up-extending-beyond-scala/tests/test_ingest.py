"""
Tests for the ingest module (User Story 1).
"""
import os
import tempfile
from pathlib import Path
import csv

import pytest

# Import the module under test
# Note: We are testing within the project root where ingest.py is located.
# The import assumes the test runner is invoked from the project root or code/ is in sys.path.
# To ensure robustness in the test environment, we attempt to import from 'code.ingest' if 'ingest' fails,
# or rely on the user adding 'code' to sys.path. However, per the prompt's existing test file,
# it assumes 'from ingest import ...'. We will maintain this assumption but ensure the test
# handles the scenario where the data file has missing values (the core of T011).
try:
    from ingest import parse_args, setup_directories, validate_schema
except ImportError:
    # Fallback for if tests are run from a different directory structure
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from ingest import parse_args, setup_directories, validate_schema


class TestSetupDirectories:
    """Tests for the setup_directories function."""

    def test_creates_required_directories(self, tmp_path):
        """Test that setup_directories creates the expected directory structure."""
        # Define expected directories
        expected_dirs = ["data/raw", "data/processed", "results"]

        # Run setup
        setup_directories(tmp_path)

        # Verify directories exist
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_does_not_fail_if_directories_exist(self, tmp_path):
        """Test that setup_directories handles existing directories gracefully."""
        # Pre-create a directory
        existing_dir = tmp_path / "data" / "raw"
        existing_dir.mkdir(parents=True)

        # Should not raise an exception
        setup_directories(tmp_path)
        assert existing_dir.exists()


class TestValidateSchema:
    """Tests for the validate_schema function."""

    def test_valid_schema(self, tmp_path):
        """Test validation passes with a correctly structured file."""
        # Create a mock CSV with required columns
        csv_path = tmp_path / "valid.csv"
        content = "sample_id,alignment,realism,aesthetics,plausibility,human_score\n1,0.5,0.6,0.7,0.8,0.9\n"
        csv_path.write_text(content)

        # Should not raise
        result = validate_schema(str(csv_path))
        assert result is True

    def test_missing_required_column(self, tmp_path):
        """Test validation fails if a required rubric dimension is missing."""
        csv_path = tmp_path / "invalid.csv"
        # Missing 'alignment' column
        content = "sample_id,realism,aesthetics,plausibility,human_score\n1,0.5,0.6,0.7,0.9\n"
        csv_path.write_text(content)

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema(str(csv_path))

    def test_empty_file(self, tmp_path):
        """Test validation fails on an empty file."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")

        with pytest.raises(ValueError):
            validate_schema(str(csv_path))


    def test_missing_data_handling_and_exclusion_logic(self, tmp_path):
        """
        Integration test for missing data handling and exclusion logic.
        
        Verifies that:
        1. validate_schema does NOT crash on rows with missing values (empty strings or 'NaN').
        2. The function correctly identifies the presence of the schema.
        3. The logic implies that downstream processing (T012/T016) will need to exclude these,
           but the schema validator itself should only care about column headers and data type presence.
           
        Note: Based on T038, the schema validation checks for the *presence* of columns.
        T011 specifically tests the behavior when data *within* those columns is missing,
        ensuring the pipeline doesn't crash and flags these rows for exclusion later.
        """
        csv_path = tmp_path / "missing_data.csv"
        # Create a CSV with valid headers but missing values in the data rows
        # Row 2 has missing 'alignment'
        # Row 3 has missing 'human_score'
        content = (
            "sample_id,alignment,realism,aesthetics,plausibility,human_score\n"
            "1,0.5,0.6,0.7,0.8,0.9\n"
            "2,,0.6,0.7,0.8,0.9\n"
            "3,0.5,0.6,0.7,0.8,\n"
        )
        csv_path.write_text(content)

        # Schema validation should pass because columns exist
        # It does NOT check for missing values in rows (that is a data cleaning step)
        # However, if the implementation of validate_schema is too strict and checks for non-empty rows,
        # we need to ensure it handles this gracefully or raises a specific warning.
        # Per T038, it verifies presence of dimensions.
        
        # We expect validate_schema to return True (schema is valid)
        # The actual exclusion of missing rows is a downstream concern (T016/T024),
        # but T011 ensures the system doesn't crash here.
        result = validate_schema(str(csv_path))
        assert result is True

        # Additional check: ensure the file can be read and missing values detected
        # This simulates the "flagging" logic mentioned in T011 description
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Verify we have 3 rows
        assert len(rows) == 3
        
        # Verify row 2 has missing alignment
        assert rows[1]['alignment'] == ''
        
        # Verify row 3 has missing human_score
        assert rows[2]['human_score'] == ''

class TestParseArgs:
    """Tests for the argument parser."""

    def test_default_values(self):
        """Test that parse_args returns correct default values."""
        args = parse_args([])
        assert args.input_url is None
        assert args.output_dir == Path("data/raw")
        assert args.validate_only is False

    def test_custom_output_dir(self):
        """Test that custom output directory is parsed correctly."""
        test_dir = "/tmp/test_output"
        args = parse_args(["--output-dir", test_dir])
        assert args.output_dir == Path(test_dir)