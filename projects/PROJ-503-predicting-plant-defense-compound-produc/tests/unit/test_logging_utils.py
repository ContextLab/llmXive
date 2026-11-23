"""
test_logging_utils.py

Unit tests for logging utilities.
"""
import json
import csv
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the PROJECT_ROOT and LOGS_DIR in logging_utils
# Since the module uses absolute paths based on __file__, we'll test
# the functions by directly manipulating the files they create.

# Import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_utils import (
    log_data_pairing_mismatch,
    log_data_pairing_mismatches_batch,
    get_pairing_log_stats,
    log_zero_variance_feature,
    log_zero_variance_features_batch,
    get_filtering_log_stats,
    DATA_PAIRING_LOG,
    FEATURE_FILTERING_LOG,
    LOGS_DIR
)


@pytest.fixture
def clean_logs():
    """Fixture to clean up log files before and after tests."""
    # Clean up before test
    if LOGS_DIR.exists():
        shutil.rmtree(LOGS_DIR)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Clean up after test
    if LOGS_DIR.exists():
        shutil.rmtree(LOGS_DIR)


class TestDataPairingMismatch:
    """Tests for data pairing mismatch logging functions."""

    def test_log_single_mismatch_creates_file(self, clean_logs):
        """Test that logging a single mismatch creates the JSON file."""
        log_data_pairing_mismatch(
            sample_id="TEST_001",
            expression_source="geo_test",
            metabolite_source="mw_test",
            reason="test_reason"
        )

        assert DATA_PAIRING_LOG.exists()

        with open(DATA_PAIRING_LOG, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["sample_id"] == "TEST_001"
        assert data[0]["expression_source"] == "geo_test"
        assert data[0]["metabolite_source"] == "mw_test"
        assert data[0]["reason"] == "test_reason"
        assert "timestamp" in data[0]

    def test_log_multiple_mismatches_appends(self, clean_logs):
        """Test that logging multiple mismatches appends to the file."""
        log_data_pairing_mismatch(
            sample_id="TEST_001",
            expression_source="geo_test",
            metabolite_source="mw_test",
            reason="reason1"
        )
        log_data_pairing_mismatch(
            sample_id="TEST_002",
            expression_source="geo_test",
            metabolite_source="mw_test",
            reason="reason2"
        )

        with open(DATA_PAIRING_LOG, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["sample_id"] == "TEST_001"
        assert data[1]["sample_id"] == "TEST_002"

    def test_batch_logging(self, clean_logs):
        """Test batch logging of mismatches."""
        mismatches = [
            {"sample_id": "BATCH_001", "expression_source": "geo", "metabolite_source": "mw", "reason": "r1"},
            {"sample_id": "BATCH_002", "expression_source": "geo", "metabolite_source": "mw", "reason": "r2"},
            {"sample_id": "BATCH_003", "expression_source": "geo", "metabolite_source": "mw", "reason": "r3"}
        ]
        log_data_pairing_mismatches_batch(mismatches)

        stats = get_pairing_log_stats()
        assert stats["total_mismatches"] == 3
        assert stats["unique_sample_ids"] == 3

    def test_get_pairing_log_stats_empty(self, clean_logs):
        """Test stats when no log exists."""
        stats = get_pairing_log_stats()
        assert stats["total_mismatches"] == 0
        assert stats["unique_sample_ids"] == 0
        assert stats["reason_counts"] == {}

    def test_get_pairing_log_stats_populated(self, clean_logs):
        """Test stats when log has entries."""
        log_data_pairing_mismatch("S1", "E", "M", "reason1")
        log_data_pairing_mismatch("S2", "E", "M", "reason1")
        log_data_pairing_mismatch("S3", "E", "M", "reason2")

        stats = get_pairing_log_stats()
        assert stats["total_mismatches"] == 3
        assert stats["unique_sample_ids"] == 3
        assert stats["reason_counts"]["reason1"] == 2
        assert stats["reason_counts"]["reason2"] == 1


class TestZeroVarianceFeature:
    """Tests for zero-variance feature logging functions."""

    def test_log_single_feature_creates_file(self, clean_logs):
        """Test that logging a single feature creates the CSV file."""
        log_zero_variance_feature(
            gene_id="AT1G01010",
            variance=0.0,
            reason="zero_variance"
        )

        assert FEATURE_FILTERING_LOG.exists()

        with open(FEATURE_FILTERING_LOG, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["gene_id"] == "AT1G01010"
        assert rows[0]["variance"] == "0.00e+00"
        assert rows[0]["reason"] == "zero_variance"

    def test_log_multiple_features_appends(self, clean_logs):
        """Test that logging multiple features appends to the file."""
        log_zero_variance_feature("AT1G01010", 0.0, "zero_variance")
        log_zero_variance_feature("AT1G01020", 1e-15, "near_zero")

        with open(FEATURE_FILTERING_LOG, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["gene_id"] == "AT1G01010"
        assert rows[1]["gene_id"] == "AT1G01020"

    def test_batch_logging(self, clean_logs):
        """Test batch logging of zero-variance features."""
        features = [
            {"gene_id": "AT1G01010", "variance": 0.0, "reason": "zero"},
            {"gene_id": "AT1G01020", "variance": 1e-15, "reason": "near_zero"},
            {"gene_id": "AT1G01030", "variance": 5e-11, "reason": "low"}
        ]
        log_zero_variance_features_batch(features)

        stats = get_filtering_log_stats()
        assert stats["total_filtered"] == 3
        assert stats["unique_genes"] == 3

    def test_get_filtering_log_stats_empty(self, clean_logs):
        """Test stats when no log exists."""
        stats = get_filtering_log_stats()
        assert stats["total_filtered"] == 0
        assert stats["unique_genes"] == 0
        assert stats["reason_counts"] == {}

    def test_get_filtering_log_stats_populated(self, clean_logs):
        """Test stats when log has entries."""
        log_zero_variance_feature("G1", 0.0, "reason1")
        log_zero_variance_feature("G2", 0.0, "reason1")
        log_zero_variance_feature("G3", 0.0, "reason2")

        stats = get_filtering_log_stats()
        assert stats["total_filtered"] == 3
        assert stats["unique_genes"] == 3
        assert stats["reason_counts"]["reason1"] == 2
        assert stats["reason_counts"]["reason2"] == 1

    def test_variance_formatting(self, clean_logs):
        """Test that variance is formatted in scientific notation."""
        log_zero_variance_feature("AT1G01010", 1.23e-15, "test")

        with open(FEATURE_FILTERING_LOG, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check that variance is in scientific notation
        assert "e" in rows[0]["variance"] or "E" in rows[0]["variance"]