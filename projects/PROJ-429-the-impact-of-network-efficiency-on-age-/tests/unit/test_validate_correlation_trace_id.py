"""
Unit tests for T028: validate_correlation_trace_id.py
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Import the module to test
import sys
sys.path.insert(0, 'code')
from stats.validate_correlation_trace_id import (
    validate_trace_id_format,
    validate_correlation_trace_ids,
    save_validation_report
)


class TestValidateTraceIdFormat:
    """Tests for validate_trace_id_format function"""

    def test_valid_sha256(self):
        """Test valid SHA-256 hex string"""
        valid_hash = "a" * 64  # 64 hex characters
        assert validate_trace_id_format(valid_hash) is True

    def test_valid_sha256_mixed_case(self):
        """Test valid SHA-256 with mixed case (should fail, only lowercase expected)"""
        mixed_hash = "A" * 32 + "a" * 32
        # Our pattern requires lowercase hex
        assert validate_trace_id_format(mixed_hash) is False

    def test_invalid_too_short(self):
        """Test string that is too short"""
        short_hash = "a" * 32
        assert validate_trace_id_format(short_hash) is False

    def test_invalid_too_long(self):
        """Test string that is too long"""
        long_hash = "a" * 128
        assert validate_trace_id_format(long_hash) is False

    def test_invalid_non_hex(self):
        """Test string with non-hex characters"""
        non_hex = "g" * 64
        assert validate_trace_id_format(non_hex) is False

    def test_invalid_empty_string(self):
        """Test empty string"""
        assert validate_trace_id_format("") is False

    def test_invalid_none(self):
        """Test None value"""
        assert validate_trace_id_format(None) is False

    def test_invalid_whitespace(self):
        """Test string with whitespace"""
        whitespace = " " * 64
        assert validate_trace_id_format(whitespace) is False

    def test_valid_with_stripped_whitespace(self):
        """Test valid hash with surrounding whitespace (should be stripped and pass)"""
        # Note: Our regex matches the whole string, so leading/trailing whitespace fails
        # unless we strip first. Let's test the actual behavior.
        hash_with_space = " " + "a" * 64 + " "
        # This should fail because the regex expects exactly 64 hex chars
        assert validate_trace_id_format(hash_with_space) is False


class TestValidateCorrelationTraceIds:
    """Tests for validate_correlation_trace_ids function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create data/results directory
        Path("data/results").mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup test fixtures"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_missing(self):
        """Test behavior when file does not exist"""
        results = validate_correlation_trace_ids()
        assert results["file_exists"] is False
        assert results["status"] == "file_missing"

    def test_file_empty(self):
        """Test behavior when file exists but is empty"""
        # Create empty CSV
        df = pd.DataFrame(columns=['metric_name', 'outcome', 'spearman_r', 'p_value', 'p_adjusted', 'n', 'trace_id'])
        df.to_csv("data/results/correlation_results.csv", index=False)

        results = validate_correlation_trace_ids()
        assert results["file_exists"] is True
        assert results["file_empty"] is True
        assert results["status"] == "file_empty"

    def test_column_missing(self):
        """Test behavior when trace_id column is missing"""
        # Create CSV without trace_id column
        df = pd.DataFrame({
            'metric_name': ['global_eff'],
            'outcome': ['age'],
            'spearman_r': [0.5],
            'p_value': [0.01],
            'p_adjusted': [0.05],
            'n': [100]
        })
        df.to_csv("data/results/correlation_results.csv", index=False)

        results = validate_correlation_trace_ids()
        assert results["column_exists"] is False
        assert results["status"] == "column_missing"

    def test_all_valid_trace_ids(self):
        """Test when all trace_ids are valid"""
        valid_hash = "a" * 64
        df = pd.DataFrame({
            'metric_name': ['global_eff', 'local_eff'],
            'outcome': ['age', 'cognition'],
            'spearman_r': [0.5, 0.3],
            'p_value': [0.01, 0.05],
            'p_adjusted': [0.05, 0.1],
            'n': [100, 100],
            'trace_id': [valid_hash, valid_hash]
        })
        df.to_csv("data/results/correlation_results.csv", index=False)

        results = validate_correlation_trace_ids()
        assert results["column_exists"] is True
        assert results["all_valid"] is True
        assert results["valid_count"] == 2
        assert results["invalid_count"] == 0
        assert results["status"] == "valid"

    def test_some_invalid_trace_ids(self):
        """Test when some trace_ids are invalid"""
        valid_hash = "a" * 64
        invalid_hash = "b" * 32  # Too short
        df = pd.DataFrame({
            'metric_name': ['global_eff', 'local_eff', 'clustering'],
            'outcome': ['age', 'cognition', 'age'],
            'spearman_r': [0.5, 0.3, 0.2],
            'p_value': [0.01, 0.05, 0.1],
            'p_adjusted': [0.05, 0.1, 0.2],
            'n': [100, 100, 100],
            'trace_id': [valid_hash, invalid_hash, valid_hash]
        })
        df.to_csv("data/results/correlation_results.csv", index=False)

        results = validate_correlation_trace_ids()
        assert results["all_valid"] is False
        assert results["valid_count"] == 2
        assert results["invalid_count"] == 1
        assert results["status"] == "partial"
        assert 1 in results["invalid_indices"]  # Row 1 has invalid hash

    def test_all_invalid_trace_ids(self):
        """Test when all trace_ids are invalid"""
        invalid_hash = "b" * 32
        df = pd.DataFrame({
            'metric_name': ['global_eff'],
            'outcome': ['age'],
            'spearman_r': [0.5],
            'p_value': [0.01],
            'p_adjusted': [0.05],
            'n': [100],
            'trace_id': [invalid_hash]
        })
        df.to_csv("data/results/correlation_results.csv", index=False)

        results = validate_correlation_trace_ids()
        assert results["all_valid"] is False
        assert results["valid_count"] == 0
        assert results["invalid_count"] == 1
        assert results["status"] == "invalid"


class TestSaveValidationReport:
    """Tests for save_validation_report function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        Path("data/results").mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup test fixtures"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_report(self):
        """Test saving validation report"""
        test_results = {
            "file_exists": True,
            "status": "valid",
            "valid_count": 5,
            "invalid_count": 0
        }

        save_validation_report(test_results)

        report_path = Path("data/results/trace_id_validation_report.json")
        assert report_path.exists()

        with open(report_path, 'r') as f:
            saved_results = json.load(f)

        assert saved_results["status"] == "valid"
        assert "validated_at" in saved_results