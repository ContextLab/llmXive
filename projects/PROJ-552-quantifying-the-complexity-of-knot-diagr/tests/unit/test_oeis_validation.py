"""
Unit tests for OEIS A002863 validation module.

Tests the validation logic against known OEIS reference values.
"""
import pytest
from pathlib import Path
import csv
import json
import tempfile
import os

from analysis.oeis_validation import (
    OEIS_A002863_REFERENCE,
    ValidationEntry,
    ValidationResult,
    OeisValidator,
    validate_oeis_a002863,
    load_cleaned_knots,
    count_knots_per_crossing_number,
)


class TestOeisA002863Reference:
    """Tests for the OEIS A002863 reference data."""

    def test_reference_has_expected_crossing_numbers(self):
        """Verify reference includes all crossing numbers 0-13."""
        expected_crossing_numbers = set(range(14))
        actual_crossing_numbers = set(OEIS_A002863_REFERENCE.keys())
        assert expected_crossing_numbers == actual_crossing_numbers

    def test_reference_values_match_known_sequence(self):
        """Verify reference values match published OEIS A002863."""
        known_values = {
            0: 1,   # unknot
            3: 1,   # trefoil
            4: 1,   # figure-eight
            5: 2,
            6: 3,
            7: 7,
            8: 21,
            9: 49,
            10: 165,
        }
        for cn, count in known_values.items():
            assert OEIS_A002863_REFERENCE[cn] == count

    def test_crossing_numbers_1_and_2_are_zero(self):
        """Verify no prime knots exist with 1 or 2 crossings."""
        assert OEIS_A002863_REFERENCE[1] == 0
        assert OEIS_A002863_REFERENCE[2] == 0


class TestValidationEntry:
    """Tests for ValidationEntry dataclass."""

    def test_validation_entry_creation(self):
        """Test creating a ValidationEntry."""
        entry = ValidationEntry(
            crossing_number=5,
            expected_count=2,
            actual_count=2,
            match=True,
            deviation=0
        )
        assert entry.crossing_number == 5
        assert entry.expected_count == 2
        assert entry.actual_count == 2
        assert entry.match is True
        assert entry.deviation == 0

    def test_validation_entry_mismatch(self):
        """Test ValidationEntry with mismatch."""
        entry = ValidationEntry(
            crossing_number=5,
            expected_count=2,
            actual_count=3,
            match=False,
            deviation=1
        )
        assert entry.match is False
        assert entry.deviation == 1


class TestOeisValidator:
    """Tests for OeisValidator class."""

    @pytest.fixture
    def sample_knots_csv(self, tmp_path):
        """Create a sample knots CSV file for testing."""
        csv_path = tmp_path / "knots_cleaned.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['knot_id', 'crossing_number', 'braid_index', 'hyperbolic_volume'])
            # Add knots matching OEIS A002863 for n=3,4,5
            for i in range(OEIS_A002863_REFERENCE[3]):
                writer.writerow([f'knot_3_{i}', 3, 2, 0.5])
            for i in range(OEIS_A002863_REFERENCE[4]):
                writer.writerow([f'knot_4_{i}', 4, 3, 0.8])
            for i in range(OEIS_A002863_REFERENCE[5]):
                writer.writerow([f'knot_5_{i}', 5, 3, 1.2])
        return csv_path

    def test_load_cleaned_knots(self, sample_knots_csv):
        """Test loading knots from CSV."""
        validator = OeisValidator(sample_knots_csv)
        knots = validator.load_cleaned_knots()
        assert len(knots) == OEIS_A002863_REFERENCE[3] + OEIS_A002863_REFERENCE[4] + OEIS_A002863_REFERENCE[5]

    def test_count_knots_per_crossing_number(self, sample_knots_csv):
        """Test counting knots by crossing number."""
        validator = OeisValidator(sample_knots_csv)
        knots = validator.load_cleaned_knots()
        counts = validator.count_knots_per_crossing_number(knots)

        assert counts[3] == OEIS_A002863_REFERENCE[3]
        assert counts[4] == OEIS_A002863_REFERENCE[4]
        assert counts[5] == OEIS_A002863_REFERENCE[5]

    def test_validate_against_oeis_all_match(self, sample_knots_csv):
        """Test validation when all counts match OEIS."""
        validator = OeisValidator(sample_knots_csv)
        knots = validator.load_cleaned_knots()
        actual_counts = validator.count_knots_per_crossing_number(knots)
        result = validator.validate_against_oeis(actual_counts)

        # Check that entries for n=3,4,5 all match
        for entry in result.entries:
            if entry.crossing_number in [3, 4, 5]:
                assert entry.match is True

    def test_validate_against_oeis_with_mismatch(self, tmp_path):
        """Test validation when counts don't match OEIS."""
        csv_path = tmp_path / "knots_mismatch.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['knot_id', 'crossing_number', 'braid_index', 'hyperbolic_volume'])
            # Add wrong count for n=5 (should be 2, add 3)
            for i in range(3):
                writer.writerow([f'knot_5_{i}', 5, 3, 1.2])

        validator = OeisValidator(csv_path)
        knots = validator.load_cleaned_knots()
        actual_counts = validator.count_knots_per_crossing_number(knots)
        result = validator.validate_against_oeis(actual_counts)

        # Find entry for n=5 and verify mismatch
        entry_5 = next(e for e in result.entries if e.crossing_number == 5)
        assert entry_5.match is False
        assert entry_5.expected_count == 2
        assert entry_5.actual_count == 3
        assert entry_5.deviation == 1
        assert result.validation_passed is False

    def test_save_results(self, sample_knots_csv, tmp_path):
        """Test saving validation results to JSON."""
        validator = OeisValidator(sample_knots_csv)
        knots = validator.load_cleaned_knots()
        actual_counts = validator.count_knots_per_crossing_number(knots)
        result = validator.validate_against_oeis(actual_counts)

        output_path = tmp_path / "validation_results.json"
        validator.save_results(result, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data['source'] == 'OEIS A002863'
        assert data['validation_passed'] == result.validation_passed


class TestValidateOeisA002863:
    """Tests for the main validation function."""

    def test_validate_oeis_a002863_success(self, tmp_path):
        """Test successful validation with correct counts."""
        csv_path = tmp_path / "knots_correct.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['knot_id', 'crossing_number', 'braid_index', 'hyperbolic_volume'])
            for cn in [3, 4, 5]:
                for i in range(OEIS_A002863_REFERENCE[cn]):
                    writer.writerow([f'knot_{cn}_{i}', cn, 2, 0.5])

        output_path = tmp_path / "results.json"
        result = validate_oeis_a002863(csv_path, output_path)

        assert result.validation_passed is True
        assert output_path.exists()

    def test_validate_oeis_a002863_failure(self, tmp_path):
        """Test validation failure with incorrect counts."""
        csv_path = tmp_path / "knots_wrong.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['knot_id', 'crossing_number', 'braid_index', 'hyperbolic_volume'])
            # Wrong count for n=3 (should be 1, add 2)
            for i in range(2):
                writer.writerow([f'knot_3_{i}', 3, 2, 0.5])

        output_path = tmp_path / "results.json"
        result = validate_oeis_a002863(csv_path, output_path)

        assert result.validation_passed is False
        assert result.mismatches > 0


class TestLoadCleanedKnots:
    """Tests for convenience function load_cleaned_knots."""

    def test_load_cleaned_knots_empty_file(self, tmp_path):
        """Test loading from empty CSV (header only)."""
        csv_path = tmp_path / "empty.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['knot_id', 'crossing_number'])

        knots = load_cleaned_knots(csv_path)
        assert len(knots) == 0

    def test_load_cleaned_knots_with_data(self, tmp_path):
        """Test loading from CSV with data."""
        csv_path = tmp_path / "data.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['knot_id', 'crossing_number'])
            writer.writerow(['k1', 3])
            writer.writerow(['k2', 4])

        knots = load_cleaned_knots(csv_path)
        assert len(knots) == 2
        assert knots[0]['knot_id'] == 'k1'
        assert knots[1]['crossing_number'] == '4'


class TestCountKnotsPerCrossingNumber:
    """Tests for convenience function count_knots_per_crossing_number."""

    def test_count_empty_list(self):
        """Test counting from empty list."""
        counts = count_knots_per_crossing_number([])
        assert counts == {}

    def test_count_single_crossing_number(self):
        """Test counting with single crossing number."""
        knots = [
            {'crossing_number': '3'},
            {'crossing_number': '3'},
            {'crossing_number': '3'},
        ]
        counts = count_knots_per_crossing_number(knots)
        assert counts[3] == 3

    def test_count_multiple_crossing_numbers(self):
        """Test counting with multiple crossing numbers."""
        knots = [
            {'crossing_number': '3'},
            {'crossing_number': '4'},
            {'crossing_number': '3'},
            {'crossing_number': '5'},
        ]
        counts = count_knots_per_crossing_number(knots)
        assert counts[3] == 2
        assert counts[4] == 1
        assert counts[5] == 1

    def test_count_with_missing_crossing_number(self):
        """Test handling of missing crossing_number field."""
        knots = [
            {'crossing_number': '3'},
            {},  # missing field
            {'crossing_number': '4'},
        ]
        counts = count_knots_per_crossing_number(knots)
        assert counts[3] == 1
        assert counts[0] == 1  # defaults to 0
        assert counts[4] == 1
