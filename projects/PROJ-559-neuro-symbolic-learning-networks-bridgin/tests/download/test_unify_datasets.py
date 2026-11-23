"""
Unit tests for code/download/unify_datasets.py
"""

import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code/ to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from download.unify_datasets import (
    validate_file_exists,
    validate_columns,
    REQUIRED_FIELDS,
    RAW_DATA_DIR
)


class TestUnifyDatasets:
    """Tests for the unify_datasets module."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        # Save original paths
        original_raw_dir = str(RAW_DATA_DIR)
        
        # Mock the global RAW_DATA_DIR for the module
        # Note: In a real scenario, we'd mock the module's variables, 
        # but for simplicity we will test the helper functions directly
        # with explicit paths.
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_validate_file_exists(self, temp_data_dir):
        """Test that validate_file_exists correctly identifies existing and missing files."""
        existing_file = Path(temp_data_dir) / "existing.csv"
        existing_file.touch()
        
        missing_file = Path(temp_data_dir) / "missing.csv"
        
        assert validate_file_exists(existing_file) is True
        assert validate_file_exists(missing_file) is False

    def test_validate_columns_valid(self, temp_data_dir):
        """Test validation with a file containing all required columns."""
        test_file = Path(temp_data_dir) / "valid.csv"
        with open(test_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["problem_id", "prompt_text", "difficulty", "skill", "extra_col"])
            writer.writeheader()
            writer.writerow({"problem_id": "1", "prompt_text": "Q", "difficulty": "1", "skill": "Math"})
        
        assert validate_columns(test_file, REQUIRED_FIELDS) is True

    def test_validate_columns_missing(self, temp_data_dir):
        """Test validation with a file missing required columns."""
        test_file = Path(temp_data_dir) / "invalid.csv"
        with open(test_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["problem_id", "prompt_text"])
            writer.writeheader()
            writer.writerow({"problem_id": "1", "prompt_text": "Q"})
        
        assert validate_columns(test_file, REQUIRED_FIELDS) is False

    def test_validate_columns_empty_header(self, temp_data_dir):
        """Test validation with an empty file."""
        test_file = Path(temp_data_dir) / "empty.csv"
        test_file.touch()
        
        assert validate_columns(test_file, REQUIRED_FIELDS) is False