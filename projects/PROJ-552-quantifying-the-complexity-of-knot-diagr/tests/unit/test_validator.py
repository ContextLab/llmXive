"""
Unit tests for data quality validation module.

Tests per FR-002 verification criteria:
- null percentage ≤5%
- format pass rate ≥99%
- duplicate records = 0
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from data.validator import (
    check_null_values,
    check_format_validity,
    check_duplicate_records,
    check_value_ranges,
    check_classification_validity,
    check_data_quality_issues,
    validate_dataset_data_quality,
    write_data_quality_report,
    get_data_quality_summary,
    DataQualityFlag,
    DataQualityFlags,
    MissingInvariantFlag,
    MissingInvariantFlags,
)


class TestCheckNullValues:
    """Tests for check_null_values function."""

    def test_no_null_values(self):
        """Test that no flags are generated when all required fields have values."""
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2},
            {'id': 'k2', 'crossing_number': 4, 'braid_index': 3},
        ]
        required_fields = ['crossing_number', 'braid_index']

        flags = check_null_values(records, required_fields)

        assert len(flags.null_flags) == 0
        assert len(flags.flags) == 0

    def test_some_null_values(self):
        """Test that flags are generated for null values."""
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2},
            {'id': 'k2', 'crossing_number': None, 'braid_index': 3},
            {'id': 'k3', 'crossing_number': 4, 'braid_index': ''},
        ]
        required_fields = ['crossing_number', 'braid_index']

        flags = check_null_values(records, required_fields)

        assert len(flags.null_flags) == 2
        assert flags.null_flags[0].record_id == 'k2'
        assert flags.null_flags[0].field_name == 'crossing_number'
        assert flags.null_flags[1].record_id == 'k3'
        assert flags.null_flags[1].field_name == 'braid_index'

    def test_empty_string_treated_as_null(self):
        """Test that empty strings are treated as null values."""
        records = [
            {'id': 'k1', 'crossing_number': '', 'braid_index': ''},
        ]
        required_fields = ['crossing_number', 'braid_index']

        flags = check_null_values(records, required_fields)

        assert len(flags.null_flags) == 2

    def test_severity_for_critical_fields(self):
        """Test that critical fields have 'error' severity."""
        records = [
            {'id': 'k1', 'crossing_number': None, 'braid_index': None, 'hyperbolic_volume': None},
        ]
        required_fields = ['crossing_number', 'braid_index', 'hyperbolic_volume']

        flags = check_null_values(records, required_fields)

        # crossing_number and braid_index should be 'error', hyperbolic_volume should be 'warning'
        critical_flags = [f for f in flags.null_flags if f.field_name in ['crossing_number', 'braid_index']]
        for flag in critical_flags:
            assert flag.severity == 'error'


class TestCheckFormatValidity:
    """Tests for check_format_validity function."""

    def test_all_valid_formats(self):
        """Test that no flags are generated when all formats are valid."""
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2, 'hyperbolic_volume': 1.5},
            {'id': 'k2', 'crossing_number': 4, 'braid_index': 3, 'hyperbolic_volume': 2.3},
        ]
        format_rules = {
            'crossing_number': 'integer',
            'braid_index': 'integer',
            'hyperbolic_volume': 'float',
        }

        flags = check_format_validity(records, format_rules)

        assert len(flags.format_flags) == 0

    def test_invalid_integer_format(self):
        """Test that invalid integer format generates a flag."""
        records = [
            {'id': 'k1', 'crossing_number': 'three', 'braid_index': 2},
        ]
        format_rules = {
            'crossing_number': 'integer',
            'braid_index': 'integer',
        }

        flags = check_format_validity(records, format_rules)

        assert len(flags.format_flags) == 1
        assert flags.format_flags[0].field_name == 'crossing_number'

    def test_invalid_float_format(self):
        """Test that invalid float format generates a flag."""
        records = [
            {'id': 'k1', 'crossing_number': 3, 'hyperbolic_volume': 'not_a_number'},
        ]
        format_rules = {
            'crossing_number': 'integer',
            'hyperbolic_volume': 'float',
        }

        flags = check_format_validity(records, format_rules)

        assert len(flags.format_flags) == 1
        assert flags.format_flags[0].field_name == 'hyperbolic_volume'

    def test_comma_separated_integers_format(self):
        """Test comma-separated integers format validation."""
        records = [
            {'id': 'k1', 'braid_word': '1,2,3,-1'},
            {'id': 'k2', 'braid_word': '1,abc,3'},
        ]
        format_rules = {
            'braid_word': 'comma_separated_integers',
        }

        flags = check_format_validity(records, format_rules)

        assert len(flags.format_flags) == 1
        assert flags.format_flags[0].record_id == 'k2'

    def test_format_pass_rate_calculation(self):
        """Test that format pass rate can be calculated from flags."""
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2},
            {'id': 'k2', 'crossing_number': 4, 'braid_index': 3},
            {'id': 'k3', 'crossing_number': 'invalid', 'braid_index': 4},
        ]
        format_rules = {
            'crossing_number': 'integer',
            'braid_index': 'integer',
        }

        flags = check_format_validity(records, format_rules)

        # 6 total fields, 1 failure = 83.33% pass rate
        total_fields = len(records) * len(format_rules)
        pass_rate = ((total_fields - len(flags.format_flags)) / total_fields) * 100
        assert abs(pass_rate - 83.33) < 0.1


class TestCheckDuplicateRecords:
    """Tests for check_duplicate_records function."""

    def test_no_duplicates(self):
        """Test that no flags are generated when there are no duplicates."""
        records = [
            {'id': 'k1', 'crossing_number': 3},
            {'id': 'k2', 'crossing_number': 4},
            {'id': 'k3', 'crossing_number': 5},
        ]

        flags = check_duplicate_records(records)

        assert len(flags.duplicate_flags) == 0
        assert len(flags.flags) == 0

    def test_with_duplicates(self):
        """Test that flags are generated for duplicate records."""
        records = [
            {'id': 'k1', 'crossing_number': 3},
            {'id': 'k2', 'crossing_number': 4},
            {'id': 'k1', 'crossing_number': 3},  # Duplicate
        ]

        flags = check_duplicate_records(records)

        assert len(flags.duplicate_flags) == 1
        assert flags.duplicate_flags[0].record_id == 'k1'

    def test_multiple_duplicates(self):
        """Test handling of multiple duplicate records."""
        records = [
            {'id': 'k1', 'crossing_number': 3},
            {'id': 'k2', 'crossing_number': 4},
            {'id': 'k1', 'crossing_number': 3},  # Duplicate
            {'id': 'k2', 'crossing_number': 4},  # Duplicate
        ]

        flags = check_duplicate_records(records)

        assert len(flags.duplicate_flags) == 2
        duplicate_ids = {f.record_id for f in flags.duplicate_flags}
        assert duplicate_ids == {'k1', 'k2'}


class TestCheckValueRanges:
    """Tests for check_value_ranges function."""

    def test_values_within_range(self):
        """Test that no flags are generated when values are within range."""
        records = [
            {'id': 'k1', 'crossing_number': 3},
            {'id': 'k2', 'crossing_number': 10},
        ]
        range_rules = {
            'crossing_number': (1, 13),
        }

        flags = check_value_ranges(records, range_rules)

        assert len(flags.range_flags) == 0

    def test_value_below_minimum(self):
        """Test that a flag is generated for values below minimum."""
        records = [
            {'id': 'k1', 'crossing_number': 0},
        ]
        range_rules = {
            'crossing_number': (1, 13),
        }

        flags = check_value_ranges(records, range_rules)

        assert len(flags.range_flags) == 1
        assert flags.range_flags[0].message == "Field 'crossing_number' value 0 is below minimum 1"

    def test_value_above_maximum(self):
        """Test that a flag is generated for values above maximum."""
        records = [
            {'id': 'k1', 'crossing_number': 15},
        ]
        range_rules = {
            'crossing_number': (1, 13),
        }

        flags = check_value_ranges(records, range_rules)

        assert len(flags.range_flags) == 1
        assert flags.range_flags[0].message == "Field 'crossing_number' value 15 is above maximum 13"

    def test_unbounded_range(self):
        """Test handling of unbounded ranges."""
        records = [
            {'id': 'k1', 'hyperbolic_volume': 0.5},
        ]
        range_rules = {
            'hyperbolic_volume': (0, None),  # Only minimum bound
        }

        flags = check_value_ranges(records, range_rules)

        assert len(flags.range_flags) == 0


class TestCheckClassificationValidity:
    """Tests for check_classification_validity function."""

    def test_valid_classifications(self):
        """Test that no flags are generated for valid classifications."""
        records = [
            {'id': 'k1', 'alternating': 'alternating'},
            {'id': 'k2', 'alternating': 'non-alternating'},
        ]
        valid_classifications = ['alternating', 'non-alternating']

        flags = check_classification_validity(records, valid_classifications)

        assert len(flags.classification_flags) == 0

    def test_invalid_classification(self):
        """Test that a flag is generated for invalid classification."""
        records = [
            {'id': 'k1', 'alternating': 'unknown'},
        ]
        valid_classifications = ['alternating', 'non-alternating']

        flags = check_classification_validity(records, valid_classifications)

        assert len(flags.classification_flags) == 1

    def test_missing_classification(self):
        """Test that missing classification does not generate a flag."""
        records = [
            {'id': 'k1'},  # No 'alternating' field
        ]
        valid_classifications = ['alternating', 'non-alternating']

        flags = check_classification_validity(records, valid_classifications)

        assert len(flags.classification_flags) == 0


class TestValidateDatasetDataQuality:
    """Tests for validate_dataset_data_quality function."""

    def test_all_thresholds_passed(self):
        """Test validation when all thresholds are passed."""
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2, 'alternating': 'alternating'},
            {'id': 'k2', 'crossing_number': 4, 'braid_index': 3, 'alternating': 'non-alternating'},
        ]
        required_fields = ['crossing_number', 'braid_index']
        format_rules = {
            'crossing_number': 'integer',
            'braid_index': 'integer',
        }
        range_rules = {
            'crossing_number': (1, 13),
            'braid_index': (1, 13),
        }
        valid_classifications = ['alternating', 'non-alternating']
        thresholds = {
            'max_null_pct': 5.0,
            'min_format_pass_rate': 99.0,
            'max_duplicates': 0,
        }

        is_valid, flags, summary = validate_dataset_data_quality(
            records, required_fields, format_rules, range_rules, valid_classifications, thresholds
        )

        assert is_valid is True
        assert summary['passes_thresholds'] is True
        assert summary['duplicate_count'] == 0

    def test_null_threshold_failed(self):
        """Test validation when null threshold is exceeded."""
        # 50% null rate (2 out of 4 cells)
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2},
            {'id': 'k2', 'crossing_number': None, 'braid_index': None},
        ]
        required_fields = ['crossing_number', 'braid_index']
        format_rules = {
            'crossing_number': 'integer',
            'braid_index': 'integer',
        }
        range_rules = {}
        valid_classifications = ['alternating', 'non-alternating']
        thresholds = {
            'max_null_pct': 5.0,
            'min_format_pass_rate': 99.0,
            'max_duplicates': 0,
        }

        is_valid, flags, summary = validate_dataset_data_quality(
            records, required_fields, format_rules, range_rules, valid_classifications, thresholds
        )

        assert is_valid is False
        assert summary['passes_thresholds'] is False
        assert summary['null_percentage'] == 50.0

    def test_duplicate_threshold_failed(self):
        """Test validation when duplicate threshold is exceeded."""
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2},
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2},  # Duplicate
        ]
        required_fields = ['crossing_number', 'braid_index']
        format_rules = {
            'crossing_number': 'integer',
            'braid_index': 'integer',
        }
        range_rules = {}
        valid_classifications = ['alternating', 'non-alternating']
        thresholds = {
            'max_null_pct': 5.0,
            'min_format_pass_rate': 99.0,
            'max_duplicates': 0,
        }

        is_valid, flags, summary = validate_dataset_data_quality(
            records, required_fields, format_rules, range_rules, valid_classifications, thresholds
        )

        assert is_valid is False
        assert summary['passes_thresholds'] is False
        assert summary['duplicate_count'] == 1

    def test_format_pass_rate_threshold_failed(self):
        """Test validation when format pass rate threshold is not met."""
        # 50% format failure rate
        records = [
            {'id': 'k1', 'crossing_number': 3, 'braid_index': 2},
            {'id': 'k2', 'crossing_number': 'invalid', 'braid_index': 'invalid'},
        ]
        required_fields = ['crossing_number', 'braid_index']
        format_rules = {
            'crossing_number': 'integer',
            'braid_index': 'integer',
        }
        range_rules = {}
        valid_classifications = ['alternating', 'non-alternating']
        thresholds = {
            'max_null_pct': 5.0,
            'min_format_pass_rate': 99.0,
            'max_duplicates': 0,
        }

        is_valid, flags, summary = validate_dataset_data_quality(
            records, required_fields, format_rules, range_rules, valid_classifications, thresholds
        )

        assert is_valid is False
        assert summary['passes_thresholds'] is False
        assert summary['format_pass_rate'] == 50.0


class TestWriteDataQualityReport:
    """Tests for write_data_quality_report function."""

    def test_report_written_correctly(self, tmp_path):
        """Test that data quality report is written correctly to file."""
        flags = DataQualityFlags()
        flags.add_flag(DataQualityFlag(
            record_id='k1',
            field_name='crossing_number',
            flag_type='null',
            message='Field is null',
            severity='error'
        ))

        summary_stats = {
            'total_records': 10,
            'null_percentage': 5.0,
            'format_pass_rate': 99.0,
            'duplicate_count': 0,
        }

        output_path = tmp_path / 'data_quality_report.json'
        write_data_quality_report(flags, summary_stats, output_path)

        assert output_path.exists()

        import json
        with open(output_path, 'r') as f:
            report = json.load(f)

        assert 'summary' in report
        assert 'flag_counts' in report
        assert report['summary']['total_records'] == 10
        assert len(report['null_flags']) == 1


class TestDataQualityFlags:
    """Tests for DataQualityFlags class."""

    def test_add_flag_to_category(self):
        """Test that flags are added to correct category."""
        flags = DataQualityFlags()

        null_flag = DataQualityFlag('k1', 'field', 'null', 'message')
        format_flag = DataQualityFlag('k1', 'field', 'format_failure', 'message')
        duplicate_flag = DataQualityFlag('k1', 'field', 'duplicate', 'message')

        flags.add_flag(null_flag)
        flags.add_flag(format_flag)
        flags.add_flag(duplicate_flag)

        assert len(flags.null_flags) == 1
        assert len(flags.format_flags) == 1
        assert len(flags.duplicate_flags) == 1
        assert len(flags.flags) == 3

    def test_get_summary(self):
        """Test that summary statistics are calculated correctly."""
        flags = DataQualityFlags()

        flags.add_flag(DataQualityFlag('k1', 'f1', 'null', 'm'))
        flags.add_flag(DataQualityFlag('k2', 'f2', 'null', 'm'))
        flags.add_flag(DataQualityFlag('k3', 'f3', 'format_failure', 'm'))

        summary = flags.get_summary()

        assert summary['total_flags'] == 3
        assert summary['null_flags'] == 2
        assert summary['format_flags'] == 1
        assert summary['duplicate_flags'] == 0


class TestMissingInvariantFlags:
    """Tests for MissingInvariantFlags class."""

    def test_add_flag(self):
        """Test that missing invariant flags are added correctly."""
        flags = MissingInvariantFlags()

        flag = MissingInvariantFlag('k1', 'arc_index', 'Arc index missing')
        flags.add_flag(flag)

        assert len(flags.flags) == 1
        assert flags.flags[0].invariant_name == 'arc_index'

    def test_get_summary(self):
        """Test that summary groups by invariant correctly."""
        flags = MissingInvariantFlags()

        flags.add_flag(MissingInvariantFlag('k1', 'arc_index', 'Missing'))
        flags.add_flag(MissingInvariantFlag('k2', 'arc_index', 'Missing'))
        flags.add_flag(MissingInvariantFlag('k3', 'seifert_circles', 'Missing'))

        summary = flags.get_summary()

        assert summary['total_missing'] == 3
        assert summary['by_invariant']['arc_index'] == 2
        assert summary['by_invariant']['seifert_circles'] == 1
