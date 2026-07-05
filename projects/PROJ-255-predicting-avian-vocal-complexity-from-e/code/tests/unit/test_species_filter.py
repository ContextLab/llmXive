import os
import sys
import tempfile
import csv
import pytest
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocessing import filter_species_by_recording_count

class TestSpeciesFilter:
    """Tests for the species filtering logic (T018b)."""

    def test_filter_species_by_recording_count_basic(self):
        """Test basic filtering: keep groups with >= 5 records, drop others."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.csv"
            output_file = tmpdir / "output.csv"
            audit_file = tmpdir / "audit.csv"

            # Create test data
            # Group 1: 5 records (should be kept)
            # Group 2: 3 records (should be dropped)
            # Group 3: 6 records (should be kept)
            data = [
                {"species_id": "A", "location_id": "L1", "value": 1},
                {"species_id": "A", "location_id": "L1", "value": 2},
                {"species_id": "A", "location_id": "L1", "value": 3},
                {"species_id": "A", "location_id": "L1", "value": 4},
                {"species_id": "A", "location_id": "L1", "value": 5},
                {"species_id": "B", "location_id": "L1", "value": 1},
                {"species_id": "B", "location_id": "L1", "value": 2},
                {"species_id": "B", "location_id": "L1", "value": 3},
                {"species_id": "C", "location_id": "L2", "value": 1},
                {"species_id": "C", "location_id": "L2", "value": 2},
                {"species_id": "C", "location_id": "L2", "value": 3},
                {"species_id": "C", "location_id": "L2", "value": 4},
                {"species_id": "C", "location_id": "L2", "value": 5},
                {"species_id": "C", "location_id": "L2", "value": 6},
            ]

            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["species_id", "location_id", "value"])
                writer.writeheader()
                writer.writerows(data)

            retained, excluded = filter_species_by_recording_count(
                input_file=str(input_file),
                min_count=5,
                output_file=str(output_file),
                audit_file=str(audit_file)
            )

            # Group A (5 records) and Group C (6 records) should be retained
            # Group B (3 records) should be excluded
            assert len(retained) == 11  # 5 + 6
            assert len(excluded) == 3   # 3

            # Check that excluded records have the reason
            for rec in excluded:
                assert "exclusion_reason" in rec
                assert "insufficient_count" in rec["exclusion_reason"]

            # Verify output file content
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                output_data = list(reader)
                assert len(output_data) == 11

            # Verify audit file content
            with open(audit_file, 'r') as f:
                reader = csv.DictReader(f)
                audit_data = list(reader)
                assert len(audit_data) == 3
                # Check species_id of excluded records
                excluded_species = [r['species_id'] for r in audit_data]
                assert all(s == 'B' for s in excluded_species)

    def test_filter_species_all_excluded(self):
        """Test when all groups have fewer than min_count records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.csv"
            output_file = tmpdir / "output.csv"
            audit_file = tmpdir / "audit.csv"

            data = [
                {"species_id": "A", "location_id": "L1", "value": 1},
                {"species_id": "A", "location_id": "L1", "value": 2},
                {"species_id": "B", "location_id": "L2", "value": 1},
            ]

            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["species_id", "location_id", "value"])
                writer.writeheader()
                writer.writerows(data)

            retained, excluded = filter_species_by_recording_count(
                input_file=str(input_file),
                min_count=5,
                output_file=str(output_file),
                audit_file=str(audit_file)
            )

            assert len(retained) == 0
            assert len(excluded) == 3

    def test_filter_species_all_retained(self):
        """Test when all groups have >= min_count records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.csv"
            output_file = tmpdir / "output.csv"
            audit_file = tmpdir / "audit.csv"

            data = [
                {"species_id": "A", "location_id": "L1", "value": 1},
                {"species_id": "A", "location_id": "L1", "value": 2},
                {"species_id": "A", "location_id": "L1", "value": 3},
                {"species_id": "A", "location_id": "L1", "value": 4},
                {"species_id": "A", "location_id": "L1", "value": 5},
                {"species_id": "B", "location_id": "L2", "value": 1},
                {"species_id": "B", "location_id": "L2", "value": 2},
                {"species_id": "B", "location_id": "L2", "value": 3},
                {"species_id": "B", "location_id": "L2", "value": 4},
                {"species_id": "B", "location_id": "L2", "value": 5},
            ]

            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["species_id", "location_id", "value"])
                writer.writeheader()
                writer.writerows(data)

            retained, excluded = filter_species_by_recording_count(
                input_file=str(input_file),
                min_count=5,
                output_file=str(output_file),
                audit_file=str(audit_file)
            )

            assert len(retained) == 10
            assert len(excluded) == 0

    def test_empty_input(self):
        """Test with an empty input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.csv"
            output_file = tmpdir / "output.csv"
            audit_file = tmpdir / "audit.csv"

            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["species_id", "location_id", "value"])
                writer.writeheader()
                # No data rows

            retained, excluded = filter_species_by_recording_count(
                input_file=str(input_file),
                min_count=5,
                output_file=str(output_file),
                audit_file=str(audit_file)
            )

            assert len(retained) == 0
            assert len(excluded) == 0