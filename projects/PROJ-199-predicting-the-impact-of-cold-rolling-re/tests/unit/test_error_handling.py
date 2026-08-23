import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data.error_handling import (
    validate_reduction_levels,
    check_file_integrity,
    handle_missing_reduction,
    calculate_reliability_metrics,
    apply_exclusion_logic,
    process_with_error_handling
)


class TestValidateReductionLevels:
    def test_all_levels_present(self):
        available = [0, 10, 20, 30, 40, 50]
        required = [0, 10, 20, 30, 40, 50]

        valid, missing = validate_reduction_levels(available, required)

        assert valid == required
        assert missing == []

    def test_some_levels_missing(self):
        available = [0, 10, 30, 50]
        required = [0, 10, 20, 30, 40, 50]

        valid, missing = validate_reduction_levels(available, required)

        assert valid == [0, 10, 30, 50]
        assert missing == [20, 40]

    def test_no_levels_present(self):
        available = [100, 200]
        required = [0, 10, 20]

        valid, missing = validate_reduction_levels(available, required)

        assert valid == []
        assert missing == required


class TestCheckFileIntegrity:
    def test_existing_valid_csv(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2\n3,4")

        assert check_file_integrity(csv_file) is True

    def test_nonexistent_file(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.csv"
        assert check_file_integrity(non_existent) is False

    def test_empty_csv(self, tmp_path):
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")

        assert check_file_integrity(empty_file) is False

    def test_corrupted_csv(self, tmp_path):
        # Create a file that looks like CSV but has binary garbage
        corrupted_file = tmp_path / "corrupted.csv"
        corrupted_file.write_bytes(b'\x00\x01\x02\x03')

        assert check_file_integrity(corrupted_file) is False


class TestHandleMissingReduction:
    def test_handles_missing_entry(self):
        available_data = {
            'Al': {0: 'data0', 10: 'data10', 20: 'data20'}
        }

        result = handle_missing_reduction('Al', 30, available_data)

        assert result is False

    def test_handles_missing_material(self):
        available_data = {
            'Al': {0: 'data0'}
        }

        result = handle_missing_reduction('Cu', 10, available_data)

        assert result is False


class TestCalculateReliabilityMetrics:
    def test_no_filtering(self):
        df = pd.DataFrame({
            'confidence': [0.5, 0.6, 0.7, 0.8]
        })

        metrics = calculate_reliability_metrics(df, threshold=0.1)

        assert metrics['total_points'] == 4
        assert metrics['filtered_points'] == 4
        assert metrics['filtered_ratio'] == 1.0
        assert metrics['reliability_score'] == 1.0

    def test_partial_filtering(self):
        df = pd.DataFrame({
            'confidence': [0.05, 0.15, 0.2, 0.08, 0.3]
        })

        metrics = calculate_reliability_metrics(df, threshold=0.1)

        assert metrics['total_points'] == 5
        assert metrics['filtered_points'] == 3
        assert metrics['filtered_ratio'] == 0.6
        assert metrics['reliability_score'] == 0.6

    def test_all_filtered(self):
        df = pd.DataFrame({
            'confidence': [0.01, 0.02, 0.03]
        })

        metrics = calculate_reliability_metrics(df, threshold=0.1)

        assert metrics['total_points'] == 3
        assert metrics['filtered_points'] == 0
        assert metrics['filtered_ratio'] == 0.0

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['confidence'])

        metrics = calculate_reliability_metrics(df, threshold=0.1)

        assert metrics['total_points'] == 0
        assert metrics['filtered_points'] == 0
        assert metrics['filtered_ratio'] == 0.0


class TestApplyExclusionLogic:
    def test_acceptable_reliability(self):
        metrics = {'filtered_ratio': 0.3}

        should_exclude, reason = apply_exclusion_logic(metrics, exclusion_threshold=0.5)

        assert should_exclude is False
        assert "Reliability acceptable" in reason

    def test_low_reliability_exceeds_threshold(self):
        metrics = {'filtered_ratio': 0.7}

        should_exclude, reason = apply_exclusion_logic(metrics, exclusion_threshold=0.5)

        assert should_exclude is True
        assert "Low reliability" in reason
        assert "Exceeds threshold" in reason

    def test_exactly_at_threshold(self):
        metrics = {'filtered_ratio': 0.5}

        should_exclude, reason = apply_exclusion_logic(metrics, exclusion_threshold=0.5)

        assert should_exclude is False

    def test_just_above_threshold(self):
        metrics = {'filtered_ratio': 0.51}

        should_exclude, reason = apply_exclusion_logic(metrics, exclusion_threshold=0.5)

        assert should_exclude is True


class TestProcessWithErrorHandling:
    def test_successful_processing(self):
        def mock_process(data):
            return data * 2

        result, warnings = process_with_error_handling(5, mock_process)

        assert result == 10
        assert warnings == []

    def test_file_not_found(self):
        def mock_process(data):
            raise FileNotFoundError("File not found")

        result, warnings = process_with_error_handling(None, mock_process)

        assert result is None
        assert len(warnings) == 1
        assert "File not found" in warnings[0]

    def test_empty_data_error(self):
        def mock_process(data):
            raise pd.errors.EmptyDataError("No columns to parse")

        result, warnings = process_with_error_handling(None, mock_process)

        assert result is None
        assert len(warnings) == 1
        assert "empty" in warnings[0].lower()

    def test_general_exception(self):
        def mock_process(data):
            raise ValueError("General error")

        result, warnings = process_with_error_handling(None, mock_process)

        assert result is None
        assert len(warnings) == 1
        assert "Unexpected error" in warnings[0]

    def test_none_data_source(self):
        def mock_process(data):
            return data

        result, warnings = process_with_error_handling(None, mock_process)

        assert result is None
        assert len(warnings) == 1
        assert "Data source is None" in warnings[0]