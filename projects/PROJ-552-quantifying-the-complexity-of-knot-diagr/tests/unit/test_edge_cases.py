"""Unit tests for edge case handling scenarios in the knot complexity pipeline.

This module validates the robustness of data processing, analysis, and
reproducibility components against edge cases such as:
- Empty datasets
- Missing invariants
- Invalid numerical values (NaN, Inf)
- Duplicate knot identifiers
- Boundary crossing numbers
- Malformed diagram codes
"""

import math
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd
import numpy as np

# Import modules under test
from code.data.validator import apply_missing_and_quality_flags, validate_knot_records
from code.data.parser import parse_knot_atlas_data, ParsedKnotData
from code.analysis.model_fitting import fit_linear_model, identify_residual_families
from code.reproducibility.logs import get_logger, log_operation, LogEntry


class TestEmptyDatasetHandling:
    """Tests for handling empty datasets gracefully."""

    def test_empty_dataframe_validation(self):
        """Validator should handle empty DataFrames without crashing."""
        df = pd.DataFrame(columns=['knot_id', 'crossing_number', 'braid_index'])
        
        result = validate_knot_records(df)
        
        assert result is not None
        assert len(result) == 0

    def test_empty_dataset_model_fitting(self):
        """Model fitting should handle empty data with appropriate error or empty result."""
        df = pd.DataFrame(columns=['crossing_number', 'hyperbolic_volume'])
        
        # Should not crash, but may return empty results or raise a specific exception
        with pytest.raises((ValueError, RuntimeError)):
            fit_linear_model(df, 'crossing_number', 'hyperbolic_volume')

    def test_empty_dataset_coverage_analysis(self):
        """Coverage analysis should handle empty datasets."""
        from code.analysis.coverage import analyze_knot_invariant_coverage
        
        df = pd.DataFrame(columns=['knot_id', 'has_diagram'])
        
        with pytest.raises((ValueError, RuntimeError)):
            analyze_knot_invariant_coverage(df)


class TestMissingInvariants:
    """Tests for handling missing invariant values."""

    def test_missing_crossing_number_flagging(self):
        """Records with missing crossing numbers should be flagged appropriately."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'braid_index': 3},
            {'knot_id': 'K002', 'crossing_number': None, 'braid_index': 2},
            {'knot_id': 'K003', 'crossing_number': 7, 'braid_index': None},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        # K002 should have missing_invariant_flags for crossing_number
        # K003 should have missing_invariant_flags for braid_index
        assert len(result) == 3
        
        # Check that flags are set appropriately
        missing_flags = [r.get('missing_invariant_flags', []) for r in result]
        assert any('crossing_number' in str(f) for f in missing_flags[1])
        assert any('braid_index' in str(f) for f in missing_flags[2])

    def test_missing_hyperbolic_volume_handling(self):
        """Records with missing hyperbolic volume should be handled gracefully."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'hyperbolic_volume': 2.5},
            {'knot_id': 'K002', 'crossing_number': 6, 'hyperbolic_volume': None},
            {'knot_id': 'K003', 'crossing_number': 7, 'hyperbolic_volume': 1.8},
        ])
        
        # Should not crash
        result = apply_missing_and_quality_flags(df)
        assert len(result) == 3

    def test_missing_all_invariants(self):
        """Records with all invariants missing should be flagged comprehensively."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': None, 'braid_index': None, 'hyperbolic_volume': None},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 1
        flags = result[0].get('missing_invariant_flags', [])
        assert len(flags) >= 1  # Should have at least one flag


class TestInvalidNumericalValues:
    """Tests for handling invalid numerical values (NaN, Inf, negative)."""

    def test_nan_values_in_crossing_number(self):
        """NaN values in crossing number should be flagged or filtered."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5.0, 'braid_index': 3},
            {'knot_id': 'K002', 'crossing_number': np.nan, 'braid_index': 2},
            {'knot_id': 'K003', 'crossing_number': 7.0, 'braid_index': 4},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 3
        # K002 should have a quality flag or missing invariant flag
        k002_flags = result[1].get('data_quality_flags', []) + result[1].get('missing_invariant_flags', [])
        assert len(k002_flags) >= 1

    def test_inf_values_in_hyperbolic_volume(self):
        """Infinite values in hyperbolic volume should be flagged."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'hyperbolic_volume': 2.5},
            {'knot_id': 'K002', 'crossing_number': 6, 'hyperbolic_volume': np.inf},
            {'knot_id': 'K003', 'crossing_number': 7, 'hyperbolic_volume': -np.inf},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 3
        # Both K002 and K003 should have quality flags
        for i in [1, 2]:
            flags = result[i].get('data_quality_flags', [])
            assert len(flags) >= 1

    def test_negative_crossing_number(self):
        """Negative crossing numbers should be flagged as invalid."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'braid_index': 3},
            {'knot_id': 'K002', 'crossing_number': -1, 'braid_index': 2},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 2
        flags = result[1].get('data_quality_flags', [])
        assert any('negative' in str(f).lower() for f in flags) or any('invalid' in str(f).lower() for f in flags)


class TestDuplicateIdentifiers:
    """Tests for handling duplicate knot identifiers."""

    def test_duplicate_knot_ids(self):
        """Duplicate knot IDs should be detected and flagged."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'braid_index': 3},
            {'knot_id': 'K002', 'crossing_number': 6, 'braid_index': 4},
            {'knot_id': 'K001', 'crossing_number': 5, 'braid_index': 3},  # Duplicate
        ])
        
        result = validate_knot_records(df)
        
        assert len(result) == 3
        # Should have detected the duplicate
        duplicate_flags = [r.get('data_quality_flags', []) for r in result]
        assert any(any('duplicate' in str(f).lower() for f in flags) for flags in duplicate_flags)

    def test_duplicate_ids_with_different_values(self):
        """Duplicate IDs with different values should be flagged as data quality issues."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'braid_index': 3},
            {'knot_id': 'K001', 'crossing_number': 6, 'braid_index': 4},  # Same ID, different values
        ])
        
        result = validate_knot_records(df)
        
        assert len(result) == 2
        duplicate_flags = [r.get('data_quality_flags', []) for r in result]
        assert any(any('duplicate' in str(f).lower() for f in flags) for flags in duplicate_flags)


class TestBoundaryCrossingNumbers:
    """Tests for boundary cases in crossing numbers."""

    def test_minimum_crossing_number(self):
        """Crossing number of 0 (unknot) should be handled."""
        df = pd.DataFrame([
            {'knot_id': 'unknot', 'crossing_number': 0, 'braid_index': 1},
            {'knot_id': 'K001', 'crossing_number': 3, 'braid_index': 2},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 2
        # Unknot is valid but may have special handling
        unknot_flags = result[0].get('data_quality_flags', [])
        # Should not be flagged as an error, but may have a note
        assert not any('error' in str(f).lower() for f in unknot_flags)

    def test_maximum_crossing_number_boundary(self):
        """Crossing numbers at the project limit (13) should be handled."""
        df = pd.DataFrame([
            {'knot_id': 'K13_001', 'crossing_number': 13, 'braid_index': 5},
            {'knot_id': 'K14_001', 'crossing_number': 14, 'braid_index': 6},  # Outside limit
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 2
        # K14_001 should be flagged as outside expected range
        k14_flags = result[1].get('data_quality_flags', [])
        assert any('range' in str(f).lower() or 'limit' in str(f).lower() for f in k14_flags)

    def test_fractional_crossing_number(self):
        """Fractional crossing numbers should be flagged as invalid."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5.0, 'braid_index': 3},
            {'knot_id': 'K002', 'crossing_number': 5.5, 'braid_index': 3},  # Invalid
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 2
        k002_flags = result[1].get('data_quality_flags', [])
        assert any('fractional' in str(f).lower() or 'invalid' in str(f).lower() for f in k002_flags)


class TestMalformedDiagramCodes:
    """Tests for handling malformed Dowker-Thistlethwaite codes."""

    def test_empty_dowker_code(self):
        """Empty Dowker codes should be flagged."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'dowker_code': '[]'},
            {'knot_id': 'K002', 'crossing_number': 6, 'dowker_code': ''},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 2
        k002_flags = result[1].get('data_quality_flags', [])
        assert any('empty' in str(f).lower() or 'missing' in str(f).lower() for f in k002_flags)

    def test_malformed_dowker_code_format(self):
        """Malformed Dowker codes should be flagged."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'dowker_code': '[1, 2, 3, 4, 5]'},
            {'knot_id': 'K002', 'crossing_number': 6, 'dowker_code': 'invalid_format'},
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 2
        k002_flags = result[1].get('data_quality_flags', [])
        assert any('malformed' in str(f).lower() or 'invalid' in str(f).lower() for f in k002_flags)

    def test_dowker_code_length_mismatch(self):
        """Dowker codes with length mismatch to crossing number should be flagged."""
        df = pd.DataFrame([
            {'knot_id': 'K001', 'crossing_number': 5, 'dowker_code': '[1, 2, 3, 4, 5]'},
            {'knot_id': 'K002', 'crossing_number': 5, 'dowker_code': '[1, 2, 3, 4, 5, 6, 7]'},  # Too long
        ])
        
        result = apply_missing_and_quality_flags(df)
        
        assert len(result) == 2
        k002_flags = result[1].get('data_quality_flags', [])
        assert any('length' in str(f).lower() or 'mismatch' in str(f).lower() for f in k002_flags)


class TestLoggingEdgeCases:
    """Tests for edge cases in the logging system."""

    def test_logger_with_none_name(self):
        """Logger should handle None or empty names gracefully."""
        logger = get_logger(None)
        assert logger is not None
        
        entry = logger.log("test_operation", parameters={})
        assert isinstance(entry, LogEntry)
        assert entry.operation == "test_operation"

    def test_logger_with_special_characters_in_name(self):
        """Logger should handle special characters in names."""
        logger = get_logger("test/logger:name")
        assert logger is not None
        
        entry = logger.log("test_op", parameters={"key": "value"})
        assert isinstance(entry, LogEntry)

    def test_log_operation_with_empty_parameters(self):
        """log_operation should handle empty parameters."""
        entry = log_operation("test_op", parameters={})
        assert isinstance(entry, LogEntry)
        assert entry.parameters == {}

    def test_log_operation_with_none_parameters(self):
        """log_operation should handle None parameters."""
        entry = log_operation("test_op", parameters=None)
        assert isinstance(entry, LogEntry)
        assert entry.parameters == {}

    def test_log_operation_as_decorator(self):
        """log_operation should work as a decorator."""
        @log_operation
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        assert result == 5

    def test_log_operation_with_exception_in_wrapped_function(self):
        """log_operation decorator should handle exceptions in wrapped functions."""
        @log_operation
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_func()


class TestParserEdgeCases:
    """Tests for edge cases in the knot data parser."""

    def test_parser_with_empty_json_array(self):
        """Parser should handle empty JSON arrays."""
        empty_json = "[]"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(empty_json)
            temp_path = f.name
        
        try:
            result = parse_knot_atlas_data(Path(temp_path))
            assert len(result) == 0
        finally:
            Path(temp_path).unlink()

    def test_parser_with_malformed_json(self):
        """Parser should handle malformed JSON gracefully."""
        malformed_json = '{"knots": [{'  # Incomplete JSON
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(malformed_json)
            temp_path = f.name
        
        try:
            with pytest.raises((json.JSONDecodeError, ValueError)):
                parse_knot_atlas_data(Path(temp_path))
        finally:
            Path(temp_path).unlink()

    def test_parser_with_missing_required_fields(self):
        """Parser should handle records with missing required fields."""
        incomplete_json = json.dumps([
            {'knot_id': 'K001'},  # Missing crossing_number, braid_index
            {'knot_id': 'K002', 'crossing_number': 5, 'braid_index': 3},
        ])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(incomplete_json)
            temp_path = f.name
        
        try:
            result = parse_knot_atlas_data(Path(temp_path))
            assert len(result) == 2
            # First record should have None for missing fields
            assert result[0].crossing_number is None
            assert result[0].braid_index is None
        finally:
            Path(temp_path).unlink()

    def test_parser_with_unicode_characters(self):
        """Parser should handle unicode characters in knot data."""
        unicode_json = json.dumps([
            {
                'knot_id': 'K001',
                'crossing_number': 5,
                'braid_index': 3,
                'description': 'Knot with unicode: αβγδ'
            },
        ])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write(unicode_json)
            temp_path = f.name
        
        try:
            result = parse_knot_atlas_data(Path(temp_path))
            assert len(result) == 1
            assert 'αβγδ' in result[0].description
        finally:
            Path(temp_path).unlink()


class TestModelFittingEdgeCases:
    """Tests for edge cases in model fitting."""

    def test_single_data_point_regression(self):
        """Regression with a single data point should handle gracefully."""
        df = pd.DataFrame([
            {'crossing_number': 5, 'hyperbolic_volume': 2.5},
        ])
        
        with pytest.raises((ValueError, RuntimeError)):
            fit_linear_model(df, 'crossing_number', 'hyperbolic_volume')

    def test_constant_target_variable(self):
        """Regression with constant target variable should handle gracefully."""
        df = pd.DataFrame([
            {'crossing_number': 5, 'hyperbolic_volume': 2.5},
            {'crossing_number': 6, 'hyperbolic_volume': 2.5},
            {'crossing_number': 7, 'hyperbolic_volume': 2.5},
        ])
        
        # Should not crash, but R² will be undefined or 0
        result = fit_linear_model(df, 'crossing_number', 'hyperbolic_volume')
        assert result is not None

    def test_perfectly_correlated_variables(self):
        """Regression with perfectly correlated variables should handle."""
        df = pd.DataFrame([
            {'crossing_number': 5, 'hyperbolic_volume': 5.0},
            {'crossing_number': 6, 'hyperbolic_volume': 6.0},
            {'crossing_number': 7, 'hyperbolic_volume': 7.0},
        ])
        
        result = fit_linear_model(df, 'crossing_number', 'hyperbolic_volume')
        assert result is not None
        assert result.r_squared == 1.0

    def test_identify_residual_families_with_empty_data(self):
        """Identifying residual families should handle empty data."""
        df = pd.DataFrame(columns=['crossing_number', 'hyperbolic_volume', 'family'])
        
        with pytest.raises((ValueError, RuntimeError)):
            identify_residual_families(df, 'crossing_number', 'hyperbolic_volume')


class TestReproducibilityEdgeCases:
    """Tests for edge cases in reproducibility documentation."""

    def test_checksum_generation_with_empty_file(self):
        """Checksum generation should handle empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('')
            temp_path = f.name
        
        try:
            import hashlib
            with open(temp_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            assert checksum == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'  # SHA256 of empty string
        finally:
            Path(temp_path).unlink()

    def test_report_generation_with_no_data(self):
        """Report generation should handle cases with no data."""
        from code.analysis.data_quantities import generate_data_quantities_report
        
        df = pd.DataFrame(columns=['knot_id', 'crossing_number'])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            temp_path = f.name
        
        try:
            # Should not crash, but report will indicate no data
            report = generate_data_quantities_report(Path(temp_path))
            assert report is not None
        finally:
            Path(temp_path).unlink()

    def test_log_rotation_with_large_entries(self):
        """Log rotation should handle large log entries."""
        logger = get_logger("test_rotation")
        
        # Create a large parameter entry
        large_params = {"data": "x" * 10000}
        entry = logger.log("large_entry", parameters=large_params)
        
        assert len(entry.to_json()) > 10000

    def test_timestamp_precision_edge_cases(self):
        """Log timestamps should handle edge cases in precision."""
        logger = get_logger("test_timestamp")
        
        entry1 = logger.log("op1")
        entry2 = logger.log("op2")
        
        # Both should have valid ISO format timestamps
        from datetime import datetime
        datetime.fromisoformat(entry1.timestamp.replace('Z', '+00:00'))
        datetime.fromisoformat(entry2.timestamp.replace('Z', '+00:00'))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])