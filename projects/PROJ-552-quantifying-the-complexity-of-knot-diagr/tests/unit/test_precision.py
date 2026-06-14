"""Unit tests for precision validation module.

Tests for code/analysis/precision.py implementing T022.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import csv
import tempfile
import os

from analysis.precision import (
    PrecisionValidationEntry,
    PrecisionValidationResult,
    load_cleaned_knots,
    validate_crossing_number_precision,
    validate_braid_index_precision,
    validate_alternating_classification,
    calculate_precision_score,
    validate_knot_precision,
    validate_precision,
    generate_precision_report,
    save_precision_report
)


class TestPrecisionValidationEntry:
    """Tests for PrecisionValidationEntry dataclass."""

    def test_entry_creation(self):
        """Test creating a validation entry."""
        entry = PrecisionValidationEntry(
            knot_id="3_1",
            crossing_number=3,
            braid_index=2,
            is_alternating=True,
            validation_status="valid",
            precision_score=1.0,
            issues=[]
        )
        assert entry.knot_id == "3_1"
        assert entry.crossing_number == 3
        assert entry.braid_index == 2
        assert entry.validation_status == "valid"
        assert entry.precision_score == 1.0
        assert entry.issues == []

    def test_entry_with_issues(self):
        """Test entry with validation issues."""
        entry = PrecisionValidationEntry(
            knot_id="test_knot",
            crossing_number=5,
            braid_index=6,
            is_alternating=False,
            validation_status="error",
            precision_score=0.5,
            issues=["braid_index exceeds crossing_number"]
        )
        assert len(entry.issues) == 1
        assert "braid_index exceeds crossing_number" in entry.issues[0]


class TestPrecisionValidationResult:
    """Tests for PrecisionValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a validation result."""
        result = PrecisionValidationResult(
            entries=[],
            total_knots=0,
            valid_count=0,
            warning_count=0,
            error_count=0,
            average_precision_score=0.0
        )
        assert result.total_knots == 0
        assert result.valid_count == 0
        assert result.average_precision_score == 0.0

    def test_result_with_entries(self):
        """Test result populated with entries."""
        entry = PrecisionValidationEntry(
            knot_id="3_1",
            crossing_number=3,
            braid_index=2,
            is_alternating=True,
            validation_status="valid",
            precision_score=1.0,
            issues=[]
        )
        result = PrecisionValidationResult(
            entries=[entry],
            total_knots=1,
            valid_count=1,
            warning_count=0,
            error_count=0,
            average_precision_score=1.0
        )
        assert len(result.entries) == 1
        assert result.valid_count == 1


class TestLoadCleanedKnots:
    """Tests for load_cleaned_knots function."""

    def test_load_from_csv(self, tmp_path):
        """Test loading knots from CSV file."""
        csv_path = tmp_path / "test_knots.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['knot_id', 'crossing_number', 'braid_index', 'is_alternating'])
            writer.writeheader()
            writer.writerow({'knot_id': '3_1', 'crossing_number': '3', 'braid_index': '2', 'is_alternating': 'True'})
            writer.writerow({'knot_id': '4_1', 'crossing_number': '4', 'braid_index': '2', 'is_alternating': 'True'})

        knots = load_cleaned_knots(csv_path)
        assert len(knots) == 2
        assert knots[0]['knot_id'] == '3_1'
        assert knots[1]['knot_id'] == '4_1'

    def test_load_empty_csv(self, tmp_path):
        """Test loading from empty CSV (header only)."""
        csv_path = tmp_path / "empty_knots.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['knot_id', 'crossing_number', 'braid_index', 'is_alternating'])
            writer.writeheader()

        knots = load_cleaned_knots(csv_path)
        assert len(knots) == 0


class TestValidateCrossingNumberPrecision:
    """Tests for validate_crossing_number_precision function."""

    def test_valid_crossing_number(self):
        """Test valid crossing number passes validation."""
        is_valid, issues = validate_crossing_number_precision(3, "3_1")
        assert is_valid is True
        assert len(issues) == 0

    def test_crossing_number_zero(self):
        """Test crossing number of zero fails validation."""
        is_valid, issues = validate_crossing_number_precision(0, "invalid")
        assert is_valid is False
        assert len(issues) == 1
        assert "must be ≥ 1" in issues[0]

    def test_crossing_number_negative(self):
        """Test negative crossing number fails validation."""
        is_valid, issues = validate_crossing_number_precision(-1, "invalid")
        assert is_valid is False
        assert len(issues) == 1

    def test_crossing_number_exceeds_max(self):
        """Test crossing number exceeding 13 fails validation."""
        is_valid, issues = validate_crossing_number_precision(14, "invalid")
        assert is_valid is False
        assert len(issues) == 1
        assert "exceeds expected maximum" in issues[0]


class TestValidateBraidIndexPrecision:
    """Tests for validate_braid_index_precision function."""

    def test_valid_braid_index(self):
        """Test valid braid index passes validation."""
        is_valid, issues = validate_braid_index_precision(2, 3, "3_1")
        assert is_valid is True
        assert len(issues) == 0

    def test_braid_index_zero(self):
        """Test braid index of zero fails validation."""
        is_valid, issues = validate_braid_index_precision(0, 3, "invalid")
        assert is_valid is False
        assert len(issues) == 1

    def test_braid_index_exceeds_crossing(self):
        """Test braid index exceeding crossing number fails validation."""
        is_valid, issues = validate_braid_index_precision(5, 3, "invalid")
        assert is_valid is False
        assert len(issues) == 1
        assert "mathematical constraint violated" in issues[0]

    def test_braid_index_equals_crossing(self):
        """Test braid index equal to crossing number passes validation."""
        is_valid, issues = validate_braid_index_precision(3, 3, "valid")
        assert is_valid is True
        assert len(issues) == 0


class TestValidateAlternatingClassification:
    """Tests for validate_alternating_classification function."""

    def test_valid_alternating_true(self):
        """Test valid True alternating classification."""
        is_valid, issues = validate_alternating_classification(True, "3_1")
        assert is_valid is True
        assert len(issues) == 0

    def test_valid_alternating_false(self):
        """Test valid False alternating classification."""
        is_valid, issues = validate_alternating_classification(False, "4_1")
        assert is_valid is True
        assert len(issues) == 0

    def test_invalid_alternating_string(self):
        """Test invalid string alternating classification."""
        is_valid, issues = validate_alternating_classification("true", "invalid")
        assert is_valid is False
        assert len(issues) == 1


class TestCalculatePrecisionScore:
    """Tests for calculate_precision_score function."""

    def test_perfect_score_no_issues(self):
        """Test perfect score with no issues."""
        score = calculate_precision_score(3, 2, True, [])
        assert score == 1.0

    def test_score_with_one_issue(self):
        """Test score deduction with one issue."""
        score = calculate_precision_score(3, 2, True, ["test issue"])
        assert score == 0.85  # 1.0 - 0.15

    def test_score_with_multiple_issues(self):
        """Test score deduction with multiple issues."""
        score = calculate_precision_score(3, 2, True, ["issue1", "issue2"])
        assert score == 0.70  # 1.0 - 0.30

    def test_score_bounded_below(self):
        """Test score is bounded at 0.0."""
        score = calculate_precision_score(3, 2, True, ["i1", "i2", "i3", "i4", "i5", "i6"])
        assert score >= 0.0
        assert score <= 1.0


class TestValidateKnotPrecision:
    """Tests for validate_knot_precision function."""

    def test_valid_knot(self):
        """Test validation of a valid knot."""
        knot = {
            'knot_id': '3_1',
            'crossing_number': '3',
            'braid_index': '2',
            'is_alternating': 'True'
        }
        entry = validate_knot_precision(knot)
        assert entry.knot_id == '3_1'
        assert entry.crossing_number == 3
        assert entry.braid_index == 2
        assert entry.is_alternating is True
        assert entry.validation_status == 'valid'

    def test_knot_with_mathematical_violation(self):
        """Test validation of knot with mathematical constraint violation."""
        knot = {
            'knot_id': 'invalid',
            'crossing_number': '3',
            'braid_index': '5',
            'is_alternating': 'True'
        }
        entry = validate_knot_precision(knot)
        assert entry.validation_status == 'error'
        assert len(entry.issues) > 0
        assert any("mathematical constraint" in issue for issue in entry.issues)

    def test_knot_string_alternating(self):
        """Test knot with string alternating value."""
        knot = {
            'knot_id': '4_1',
            'crossing_number': '4',
            'braid_index': '2',
            'is_alternating': 'true'
        }
        entry = validate_knot_precision(knot)
        assert entry.is_alternating is True


class TestValidatePrecision:
    """Tests for validate_precision function."""

    def test_validate_all_knots(self, tmp_path):
        """Test validation of multiple knots."""
        # Create test CSV
        csv_path = tmp_path / "test_knots.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['knot_id', 'crossing_number', 'braid_index', 'is_alternating'])
            writer.writeheader()
            writer.writerow({'knot_id': '3_1', 'crossing_number': '3', 'braid_index': '2', 'is_alternating': 'True'})
            writer.writerow({'knot_id': '4_1', 'crossing_number': '4', 'braid_index': '2', 'is_alternating': 'True'})

        result = validate_precision(filepath=csv_path, output_path=tmp_path)
        assert result.total_knots == 2
        assert result.valid_count == 2
        assert result.error_count == 0

    def test_validate_with_errors(self, tmp_path):
        """Test validation including knots with errors."""
        csv_path = tmp_path / "test_knots.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['knot_id', 'crossing_number', 'braid_index', 'is_alternating'])
            writer.writeheader()
            writer.writerow({'knot_id': '3_1', 'crossing_number': '3', 'braid_index': '2', 'is_alternating': 'True'})
            writer.writerow({'knot_id': 'invalid', 'crossing_number': '3', 'braid_index': '5', 'is_alternating': 'True'})

        result = validate_precision(filepath=csv_path, output_path=tmp_path)
        assert result.total_knots == 2
        assert result.valid_count == 1
        assert result.error_count == 1


class TestGeneratePrecisionReport:
    """Tests for generate_precision_report function."""

    def test_report_generation(self):
        """Test report generation."""
        entry = PrecisionValidationEntry(
            knot_id="3_1",
            crossing_number=3,
            braid_index=2,
            is_alternating=True,
            validation_status="valid",
            precision_score=1.0,
            issues=[]
        )
        result = PrecisionValidationResult(
            entries=[entry],
            total_knots=1,
            valid_count=1,
            warning_count=0,
            error_count=0,
            average_precision_score=1.0
        )
        report = generate_precision_report(result)
        assert "Precision Validation Report" in report
        assert "3_1" in report
        assert "Summary Statistics" in report

    def test_report_with_issues(self):
        """Test report includes issues."""
        entry = PrecisionValidationEntry(
            knot_id="invalid",
            crossing_number=3,
            braid_index=5,
            is_alternating=True,
            validation_status="error",
            precision_score=0.5,
            issues=["mathematical constraint violated"]
        )
        result = PrecisionValidationResult(
            entries=[entry],
            total_knots=1,
            valid_count=0,
            warning_count=0,
            error_count=1,
            average_precision_score=0.5
        )
        report = generate_precision_report(result)
        assert "mathematical constraint violated" in report


class TestSavePrecisionReport:
    """Tests for save_precision_report function."""

    def test_save_json_and_markdown(self, tmp_path):
        """Test saving both JSON and markdown files."""
        entry = PrecisionValidationEntry(
            knot_id="3_1",
            crossing_number=3,
            braid_index=2,
            is_alternating=True,
            validation_status="valid",
            precision_score=1.0,
            issues=[]
        )
        result = PrecisionValidationResult(
            entries=[entry],
            total_knots=1,
            valid_count=1,
            warning_count=0,
            error_count=0,
            average_precision_score=1.0
        )

        json_path = save_precision_report(result, tmp_path)
        assert json_path.exists()

        # Check JSON file content
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert 'summary' in data
            assert 'entries' in data
            assert data['summary']['total_knots'] == 1

        # Check markdown file exists
        md_path = tmp_path / "precision_validation_report.md"
        assert md_path.exists()