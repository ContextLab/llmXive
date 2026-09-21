import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from code.data.retention_validation import (
    load_retention_metrics,
    load_behavioral_data,
    validate_retention_threshold,
    generate_exclusion_log,
)


class TestValidateRetentionThreshold:
    def test_passes_threshold(self):
        """Test that validation passes when retention is above threshold."""
        retention_rate = 0.90
        threshold = 0.80

        is_valid, message = validate_retention_threshold(retention_rate, threshold)

        assert is_valid is True
        assert "passes" in message.lower()

    def test_fails_threshold(self):
        """Test that validation fails when retention is below threshold."""
        retention_rate = 0.70
        threshold = 0.80

        is_valid, message = validate_retention_threshold(retention_rate, threshold)

        assert is_valid is False
        assert "fails" in message.lower() or "below" in message.lower()

    def test_exact_threshold(self):
        """Test behavior at exact threshold."""
        retention_rate = 0.80
        threshold = 0.80

        is_valid, message = validate_retention_threshold(retention_rate, threshold)

        # Should pass at exactly the threshold
        assert is_valid is True

    def test_handles_edge_cases(self):
        """Test behavior with edge case retention rates."""
        # Perfect retention
        is_valid, _ = validate_retention_threshold(1.0, 0.80)
        assert is_valid is True

        # Zero retention
        is_valid, _ = validate_retention_threshold(0.0, 0.80)
        assert is_valid is False


class TestGenerateExclusionLog:
    def test_generates_log_correctly(self):
        """Test that exclusion log is generated correctly."""
        retained_subjects = ['sub-001', 'sub-002', 'sub-003']
        excluded_subjects = [
            {'subject_id': 'sub-004', 'reason': 'Missing behavioral data'},
            {'subject_id': 'sub-005', 'reason': 'High motion artifacts'}
        ]
        retention_rate = 0.60

        log_entries = generate_exclusion_log(retained_subjects, excluded_subjects, retention_rate)

        assert isinstance(log_entries, list)
        assert len(log_entries) == len(excluded_subjects) + 1  # Plus summary entry
        assert any('retention' in entry['reason'].lower() for entry in log_entries)

    def test_handles_no_exclusions(self):
        """Test behavior when there are no exclusions."""
        retained_subjects = ['sub-001', 'sub-002', 'sub-003']
        excluded_subjects = []
        retention_rate = 1.0

        log_entries = generate_exclusion_log(retained_subjects, excluded_subjects, retention_rate)

        assert isinstance(log_entries, list)
        # Should still have summary entry
        assert len(log_entries) >= 1

    def test_generates_summary_entry(self):
        """Test that a summary entry is always generated."""
        retained_subjects = ['sub-001']
        excluded_subjects = []
        retention_rate = 0.95

        log_entries = generate_exclusion_log(retained_subjects, excluded_subjects, retention_rate)

        # Check for summary entry
        summary_found = any('retention' in entry.get('reason', '').lower() for entry in log_entries)
        assert summary_found
