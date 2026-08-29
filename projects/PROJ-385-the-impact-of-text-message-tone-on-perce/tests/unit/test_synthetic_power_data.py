"""
Unit tests for T090a: Synthetic Power Dataset Generation.

These tests verify that the synthetic power data generation script:
1. Creates the expected zip file
2. Contains CSV files with the correct schema
3. Each dataset has exactly N=60 participants
4. The data is generated deterministically
"""

import csv
import io
import os
import zipfile
from pathlib import Path

import pytest

from config import get_processed_data_dir
from code_00_generate_synthetic_power_data import (
    generate_synthetic_power_dataset,
    create_synthetic_power_datasets,
    verify_zip_contents
)


class TestSyntheticPowerDataGeneration:
    """Tests for the synthetic power data generation functionality."""

    @pytest.fixture
    def processed_dir(self):
        """Fixture to get the processed data directory."""
        return get_processed_data_dir()

    @pytest.fixture
    def zip_path(self, processed_dir):
        """Fixture to get the path to the generated zip file."""
        return processed_dir / "synthetic_power_datasets.zip"

    def test_generate_single_dataset_structure(self):
        """Test that a single dataset has the correct structure."""
        dataset = generate_synthetic_power_dataset(dataset_id=1, n_participants=60)

        # Check that we have data
        assert len(dataset) > 0, "Dataset should not be empty"

        # Check that each row has the required fields
        required_fields = {
            'participant_id', 'prolific_id', 'stimulus_id', 'emoji_count',
            'punctuation_type', 'length_category', 'relationship_context',
            'rating', 'dataset_id'
        }

        for row in dataset:
            assert set(row.keys()) == required_fields, f"Row missing fields: {required_fields - set(row.keys())}"

    def test_generate_dataset_participant_count(self):
        """Test that a dataset has exactly 60 participants."""
        dataset = generate_synthetic_power_dataset(dataset_id=1, n_participants=60)

        unique_participants = set(row['participant_id'] for row in dataset)
        assert len(unique_participants) == 60, f"Expected 60 participants, got {len(unique_participants)}"

    def test_generate_dataset_stimulus_coverage(self):
        """Test that all stimulus combinations are covered."""
        dataset = generate_synthetic_power_dataset(dataset_id=1, n_participants=60)

        # Get unique stimulus IDs
        stimulus_ids = set(row['stimulus_id'] for row in dataset)

        # We expect 4 emoji counts * 4 punctuation types * 3 length categories = 48 stimuli
        expected_stimuli = 4 * 4 * 3
        assert len(stimulus_ids) == expected_stimuli, f"Expected {expected_stimuli} unique stimuli, got {len(stimulus_ids)}"

    def test_generate_dataset_relationship_contexts(self):
        """Test that both relationship contexts are present."""
        dataset = generate_synthetic_power_dataset(dataset_id=1, n_participants=60)

        contexts = set(row['relationship_context'] for row in dataset)
        assert 'friend' in contexts, "Missing 'friend' context"
        assert 'acquaintance' in contexts, "Missing 'acquaintance' context"

    def test_generate_dataset_rating_range(self):
        """Test that ratings are within the valid range [1, 5]."""
        dataset = generate_synthetic_power_dataset(dataset_id=1, n_participants=60)

        for row in dataset:
            rating = row['rating']
            assert 1.0 <= rating <= 5.0, f"Rating {rating} out of range [1, 5]"

    def test_create_zip_file_exists(self, zip_path):
        """Test that the zip file is created."""
        # Generate the datasets
        create_synthetic_power_datasets(num_datasets=3)

        assert zip_path.exists(), f"Zip file not created at {zip_path}"

    def test_zip_file_contents(self, zip_path):
        """Test that the zip file contains the expected CSV files."""
        # Generate the datasets
        create_synthetic_power_datasets(num_datasets=3)

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            csv_files = [f for f in zipf.namelist() if f.endswith('.csv')]

            assert len(csv_files) == 3, f"Expected 3 CSV files, got {len(csv_files)}"

            for csv_file in csv_files:
                assert csv_file.startswith("synthetic_power_dataset_"), f"Unexpected filename: {csv_file}"

    def test_csv_schema_in_zip(self, zip_path):
        """Test that CSV files in the zip have the correct schema."""
        # Generate the datasets
        create_synthetic_power_datasets(num_datasets=3)

        required_columns = {
            'participant_id', 'prolific_id', 'stimulus_id', 'emoji_count',
            'punctuation_type', 'length_category', 'relationship_context',
            'rating', 'dataset_id'
        }

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            for csv_file in zipf.namelist():
                if csv_file.endswith('.csv'):
                    with zipf.open(csv_file) as f:
                        header_line = f.readline().decode('utf-8').strip()
                        columns = set(header_line.split(','))

                        assert columns.issuperset(required_columns), f"Missing columns in {csv_file}: {required_columns - columns}"

    def test_n60_per_dataset_in_zip(self, zip_path):
        """Test that each dataset in the zip has exactly 60 participants."""
        # Generate the datasets
        create_synthetic_power_datasets(num_datasets=3)

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            for csv_file in zipf.namelist():
                if csv_file.endswith('.csv'):
                    with zipf.open(csv_file) as f:
                        # Read all rows
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                        rows = list(reader)

                        unique_participants = set(row['participant_id'] for row in rows)
                        assert len(unique_participants) == 60, f"Expected 60 participants in {csv_file}, got {len(unique_participants)}"

    def test_verify_zip_contents(self, zip_path):
        """Test the verification function."""
        # Generate the datasets
        create_synthetic_power_datasets(num_datasets=3)

        # This should return True
        assert verify_zip_contents(zip_path), "Verification should pass for valid zip file"

    def test_deterministic_generation(self):
        """Test that dataset generation is deterministic."""
        # Generate the same dataset twice
        dataset1 = generate_synthetic_power_dataset(dataset_id=99, n_participants=60)
        dataset2 = generate_synthetic_power_dataset(dataset_id=99, n_participants=60)

        # They should be identical
        assert len(dataset1) == len(dataset2), "Dataset lengths differ"

        for row1, row2 in zip(dataset1, dataset2):
            assert row1 == row2, "Dataset rows differ"

    def test_multiple_datasets_are_different(self):
        """Test that different datasets are not identical."""
        dataset1 = generate_synthetic_power_dataset(dataset_id=1, n_participants=60)
        dataset2 = generate_synthetic_power_dataset(dataset_id=2, n_participants=60)

        # They should be different (at least some rows should differ)
        # We don't expect all rows to be different, but some should be
        different_rows = sum(1 for r1, r2 in zip(dataset1, dataset2) if r1 != r2)
        assert different_rows > 0, "Different datasets should have different rows"