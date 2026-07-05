"""
Unit tests for src/analysis/verification.py
"""
import os
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
# Ensure the code directory is in the path for imports if running standalone
code_root = Path(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.analysis.verification import count_valid_species, verify_species_count_for_modeling


class TestSpeciesCountVerification:
    
    @pytest.fixture
    def temp_dataset(self, tmp_path):
        """Create a temporary final_dataset.csv with known species count."""
        dataset_file = tmp_path / "final_dataset.csv"
        species_list = [f"Species_{i}" for i in range(60)]  # 60 unique species
        
        with open(dataset_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["species_id", "location_id", "noise_level_db", "complexity_score"])
            # Write 100 rows, rotating through the 60 species
            for i in range(100):
                writer.writerow([species_list[i % 60], f"Loc_{i}", 45.0, 0.8])
        
        return dataset_file

    @pytest.fixture
    def temp_insufficient_dataset(self, tmp_path):
        """Create a temporary final_dataset.csv with < 50 species."""
        dataset_file = tmp_path / "final_dataset.csv"
        species_list = [f"Species_{i}" for i in range(40)]  # 40 unique species
        
        with open(dataset_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["species_id", "location_id", "noise_level_db", "complexity_score"])
            for i in range(50):
                writer.writerow([species_list[i % 40], f"Loc_{i}", 45.0, 0.8])
        
        return dataset_file

    @pytest.fixture
    def temp_empty_species_dataset(self, tmp_path):
        """Create a dataset with empty species IDs."""
        dataset_file = tmp_path / "final_dataset.csv"
        with open(dataset_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["species_id", "location_id", "noise_level_db", "complexity_score"])
            for i in range(10):
                writer.writerow(["", f"Loc_{i}", 45.0, 0.8])
        
        return dataset_file

    def test_count_valid_species_passes(self, temp_dataset):
        """Test that a dataset with >= 50 species passes verification."""
        count, passed, error_msg = count_valid_species(
            dataset_path=temp_dataset,
            min_threshold=50
        )
        assert count == 60
        assert passed is True
        assert error_msg is None

    def test_count_valid_species_fails(self, temp_insufficient_dataset):
        """Test that a dataset with < 50 species fails verification."""
        count, passed, error_msg = count_valid_species(
            dataset_path=temp_insufficient_dataset,
            min_threshold=50
        )
        assert count == 40
        assert passed is False
        assert error_msg is not None
        assert "SC-004" in error_msg
        assert "40" in error_msg
        assert "50" in error_msg

    def test_count_valid_species_handles_empty_ids(self, temp_empty_species_dataset):
        """Test that empty species IDs are not counted."""
        count, passed, error_msg = count_valid_species(
            dataset_path=temp_empty_species_dataset,
            min_threshold=50
        )
        assert count == 0
        assert passed is False

    def test_count_valid_species_file_not_found(self, tmp_path):
        """Test behavior when the dataset file does not exist."""
        nonexistent = tmp_path / "missing.csv"
        count, passed, error_msg = count_valid_species(dataset_path=nonexistent)
        assert count == 0
        assert passed is False
        assert "not found" in error_msg

    def test_verify_wrapper_passes(self, temp_dataset):
        """Test the wrapper function for successful case."""
        count, status = verify_species_count_for_modeling(dataset_path=temp_dataset)
        assert count == 60
        assert status == "OK"

    def test_verify_wrapper_fails(self, temp_insufficient_dataset):
        """Test the wrapper function for failure case."""
        count, status = verify_species_count_for_modeling(dataset_path=temp_insufficient_dataset)
        assert count == 40
        assert status != "OK"
        assert "SC-004" in status