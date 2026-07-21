"""
Unit tests for T018: Species filtering by minimum recordings per location.

Tests the filter_species_by_min_recordings function in src/data/preprocessing.py
"""
import os
import sys
import tempfile
import csv
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.preprocessing import filter_species_by_min_recordings, load_csv, save_csv

class TestSpeciesFilter:
    """Test suite for species filtering logic."""

    def _create_test_csv(self, records, filepath):
        """Helper to create a test CSV file."""
        if records:
            fieldnames = list(records[0].keys())
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("")

    def test_filter_keeps_species_with_sufficient_recordings(self, tmp_path):
        """Test that species with >=5 recordings per location are kept."""
        # Create test data: Species A has 5 recordings at Loc1, Species B has 3
        records = [
            {'record_id': '1', 'species_id': 'A', 'location_id': 'L1'},
            {'record_id': '2', 'species_id': 'A', 'location_id': 'L1'},
            {'record_id': '3', 'species_id': 'A', 'location_id': 'L1'},
            {'record_id': '4', 'species_id': 'A', 'location_id': 'L1'},
            {'record_id': '5', 'species_id': 'A', 'location_id': 'L1'},  # Exactly 5
            {'record_id': '6', 'species_id': 'B', 'location_id': 'L1'},
            {'record_id': '7', 'species_id': 'B', 'location_id': 'L1'},
            {'record_id': '8', 'species_id': 'B', 'location_id': 'L1'},  # Only 3
        ]
        
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        excluded_file = tmp_path / "excluded.csv"
        
        self._create_test_csv(records, input_file)
        
        kept, excluded = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=5,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        
        # Species A should be kept (5 records)
        assert len(kept) == 5
        assert all(rec['species_id'] == 'A' for rec in kept)
        
        # Species B should be excluded (3 records)
        assert len(excluded) == 3
        assert all(rec['species_id'] == 'B' for rec in excluded)

    def test_filter_exactly_at_threshold(self, tmp_path):
        """Test boundary condition: exactly 5 recordings should be kept."""
        records = [
            {'record_id': str(i), 'species_id': 'X', 'location_id': 'Y'}
            for i in range(1, 6)  # Exactly 5 records
        ]
        
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        excluded_file = tmp_path / "excluded.csv"
        
        self._create_test_csv(records, input_file)
        
        kept, excluded = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=5,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        
        assert len(kept) == 5
        assert len(excluded) == 0

    def test_filter_below_threshold(self, tmp_path):
        """Test that species with 4 recordings are excluded."""
        records = [
            {'record_id': str(i), 'species_id': 'Z', 'location_id': 'M'}
            for i in range(1, 5)  # Only 4 records
        ]
        
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        excluded_file = tmp_path / "excluded.csv"
        
        self._create_test_csv(records, input_file)
        
        kept, excluded = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=5,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        
        assert len(kept) == 0
        assert len(excluded) == 4

    def test_multiple_locations_same_species(self, tmp_path):
        """Test species with sufficient records at one location but not another."""
        records = [
            # Species A: 5 at L1 (keep), 3 at L2 (exclude those)
            {'record_id': f'A_L1_{i}', 'species_id': 'A', 'location_id': 'L1'} for i in range(1, 6)
        ] + [
            {'record_id': f'A_L2_{i}', 'species_id': 'A', 'location_id': 'L2'} for i in range(1, 4)
        ]
        
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        excluded_file = tmp_path / "excluded.csv"
        
        self._create_test_csv(records, input_file)
        
        kept, excluded = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=5,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        
        # Only L1 records should be kept
        assert len(kept) == 5
        assert all(rec['location_id'] == 'L1' for rec in kept)
        
        # L2 records should be excluded
        assert len(excluded) == 3
        assert all(rec['location_id'] == 'L2' for rec in excluded)

    def test_empty_input(self, tmp_path):
        """Test handling of empty input file."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        excluded_file = tmp_path / "excluded.csv"
        
        # Create empty file
        input_file.touch()
        
        kept, excluded = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=5,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        
        assert len(kept) == 0
        assert len(excluded) == 0

    def test_output_files_created(self, tmp_path):
        """Test that output files are actually written to disk."""
        records = [
            {'record_id': str(i), 'species_id': 'S', 'location_id': 'L'}
            for i in range(1, 6)
        ]
        
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        excluded_file = tmp_path / "excluded.csv"
        
        self._create_test_csv(records, input_file)
        
        filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=5,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        
        assert output_file.exists(), "Output file should be created"
        assert excluded_file.exists(), "Excluded file should be created"
        
        # Verify content
        kept_records = load_csv(output_file)
        assert len(kept_records) == 5

    def test_custom_min_threshold(self, tmp_path):
        """Test with different minimum threshold values."""
        records = [
            {'record_id': str(i), 'species_id': 'T', 'location_id': 'X'}
            for i in range(1, 8)  # 7 records
        ]
        
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        excluded_file = tmp_path / "excluded.csv"
        
        self._create_test_csv(records, input_file)
        
        # Test with threshold 3: should keep all
        kept, _ = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=3,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        assert len(kept) == 7

        # Test with threshold 8: should exclude all
        kept, excluded = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=8,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        assert len(kept) == 0
        assert len(excluded) == 7