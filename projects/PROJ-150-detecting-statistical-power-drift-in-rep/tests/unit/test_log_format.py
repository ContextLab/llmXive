"""
Unit tests for T015b: Verification of log output format.

This test suite asserts that the logging output from the data filtering
steps (implemented in T015) strictly matches the required format:
`WARNING: Skipping row {index} due to {reason}`.

It verifies the structure of log messages generated during:
1. Missing data handling (NaN in effect_size or sample_size)
2. Zero-variance field handling
3. Extreme value capping/filtering
"""
import logging
import io
import re
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path if running from tests/
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.power_calc import load_and_validate_data, filter_and_log_invalid_rows
from code.logging_config import setup_logging, get_module_logger


class TestLogFormatVerification:
    """Tests to ensure log messages follow the strict format required by FR-008."""

    @pytest.fixture
    def log_capture(self, caplog):
        """Capture log output for inspection."""
        # Ensure we capture WARNING level and above
        caplog.set_level(logging.WARNING)
        return caplog

    @pytest.fixture
    def sample_data_with_issues(self):
        """Create a DataFrame with various data quality issues."""
        data = {
            'study_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
            'year': [2010, 2015, 2018, 2020, 2021, 2022],
            'field': ['Psych', 'Bio', 'Med', 'Phys', 'Chem', 'Soc'],
            'original_study_id': ['O1', 'O2', 'O3', 'O4', 'O5', 'O6'],
            'effect_size': [0.5, np.nan, 0.3, 0.8, 0.1, 0.4],
            'sample_size': [100, 50, -10, 0, 200, np.nan]
        }
        return pd.DataFrame(data)

    def test_log_format_matches_specification(self, log_capture, sample_data_with_issues):
        """
        Verify that all warnings logged during data filtering match:
        'WARNING: Skipping row {index} due to {reason}'
        """
        # Run the filtering logic which should log warnings
        filtered_df, logs = filter_and_log_invalid_rows(sample_data_with_issues)

        # Regex pattern for the required format
        pattern = r"WARNING: Skipping row (\d+) due to (.+)"

        # Check that all captured log messages match the pattern
        matching_count = 0
        for record in log_capture.records:
            if record.levelno == logging.WARNING:
                match = re.match(pattern, record.message)
                if match:
                    matching_count += 1
                    index = int(match.group(1))
                    reason = match.group(2)
                    # Verify index is an integer
                    assert isinstance(index, int), f"Index should be integer, got {type(index)}"
                    # Verify reason is a non-empty string
                    assert len(reason) > 0, f"Reason should not be empty for row {index}"
                else:
                    pytest.fail(f"Log message does not match required format: {record.message}")

        # Ensure at least some warnings were generated (since we have bad data)
        assert matching_count > 0, "Expected at least one warning log for invalid data"

    def test_specific_error_reasons_logged(self, log_capture, sample_data_with_issues):
        """
        Verify that specific error reasons are logged correctly:
        - NaN in effect_size
        - NaN in sample_size
        - Negative sample_size
        - Zero sample_size
        """
        filtered_df, logs = filter_and_log_invalid_rows(sample_data_with_issues)

        log_messages = [r.message for r in log_capture.records if r.levelno == logging.WARNING]

        # Check for specific expected reasons
        expected_reasons = [
            "NaN in effect_size",
            "NaN in sample_size",
            "Negative sample_size",
            "Zero sample_size"
        ]

        found_reasons = []
        for msg in log_messages:
            for reason in expected_reasons:
                if reason in msg:
                    found_reasons.append(reason)

        # We expect to find most of these since we have those issues in data
        # (S2 has NaN effect, S6 has NaN sample, S3 has negative, S4 has zero)
        assert "NaN in effect_size" in found_reasons, "Missing log for NaN effect_size"
        assert "NaN in sample_size" in found_reasons, "Missing log for NaN sample_size"
        assert "Negative sample_size" in found_reasons, "Missing log for negative sample_size"
        assert "Zero sample_size" in found_reasons, "Missing log for zero sample_size"

    def test_log_format_no_extra_text(self, log_capture, sample_data_with_issues):
        """
        Ensure log messages do not contain extra text outside the required format.
        """
        filtered_df, logs = filter_and_log_invalid_rows(sample_data_with_issues)

        pattern = r"^WARNING: Skipping row \d+ due to .+$"
        
        for record in log_capture.records:
            if record.levelno == logging.WARNING:
                assert re.match(pattern, record.message), (
                    f"Log message has extra text or wrong format: '{record.message}'"
                )

    def test_row_index_accuracy(self, log_capture, sample_data_with_issues):
        """
        Verify that the logged row index matches the actual DataFrame index.
        """
        filtered_df, logs = filter_and_log_invalid_rows(sample_data_with_issues)

        # Get indices that should be skipped
        # S2 (index 1): NaN effect_size
        # S3 (index 2): Negative sample_size
        # S4 (index 3): Zero sample_size
        # S6 (index 5): NaN sample_size
        expected_skipped_indices = {1, 2, 3, 5}

        logged_indices = set()
        for record in log_capture.records:
            if record.levelno == logging.WARNING:
                match = re.match(r"WARNING: Skipping row (\d+) due to (.+)", record.message)
                if match:
                    logged_indices.add(int(match.group(1)))

        assert logged_indices == expected_skipped_indices, (
            f"Logged indices {logged_indices} do not match expected {expected_skipped_indices}"
        )

    def test_no_synthetic_fallback_logs(self, log_capture, sample_data_with_issues):
        """
        Verify that no synthetic fallback or placeholder messages are logged.
        This ensures we are not fabricating data or using mock fallbacks.
        """
        filtered_df, logs = filter_and_log_invalid_rows(sample_data_with_issues)

        forbidden_phrases = [
            "synthetic", "mock", "fake", "placeholder", "sample", "dummy"
        ]

        for record in log_capture.records:
            if record.levelno == logging.WARNING:
                msg_lower = record.message.lower()
                for phrase in forbidden_phrases:
                    assert phrase not in msg_lower, (
                        f"Found forbidden phrase '{phrase}' in log: {record.message}"
                    )