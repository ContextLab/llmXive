"""
Unit tests for the validate_data module.

These tests verify the data validation logic without requiring
actual data files to be present.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from validate_data import (
    calculate_file_checksum,
    validate_data_file,
    count_processed_meta_analyses,
    aggregate_success_rate,
    write_success_rate_report,
    TARGET_COUNT
)


class TestCalculateFileChecksum:
    """Tests for checksum calculation."""

    def test_calculate_checksum_sha256(self, tmp_path):
        """Test SHA256 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        assert isinstance(checksum, str)

    def test_calculate_checksum_consistency(self, tmp_path):
        """Test that checksum is consistent across multiple calls."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content for checksum"
        test_file.write_bytes(test_content)
        
        checksum1 = calculate_file_checksum(test_file)
        checksum2 = calculate_file_checksum(test_file)
        
        assert checksum1 == checksum2

    def test_calculate_checksum_different_content(self, tmp_path):
        """Test that different content produces different checksums."""
        test_file1 = tmp_path / "test1.txt"
        test_file2 = tmp_path / "test2.txt"
        
        test_file1.write_bytes(b"Content 1")
        test_file2.write_bytes(b"Content 2")
        
        checksum1 = calculate_file_checksum(test_file1)
        checksum2 = calculate_file_checksum(test_file2)
        
        assert checksum1 != checksum2


class TestValidateDataFile:
    """Tests for data file validation."""

    def test_validate_nonexistent_file(self, tmp_path):
        """Test validation of a non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"
        result = validate_data_file(nonexistent)
        
        assert result['valid'] is False
        assert result['error'] is not None
        assert 'not found' in result['error'].lower()

    def test_validate_json_file(self, tmp_path):
        """Test validation of a valid JSON file."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "list": [1, 2, 3]}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = validate_data_file(test_file)
        
        assert result['valid'] is True
        assert result['checksum'] is not None
        assert result['row_count'] == 1  # Single object

    def test_validate_json_array_file(self, tmp_path):
        """Test validation of a JSON array file."""
        test_file = tmp_path / "test_array.json"
        test_data = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = validate_data_file(test_file)
        
        assert result['valid'] is True
        assert result['row_count'] == 3

    def test_validate_csv_file(self, tmp_path):
        """Test validation of a valid CSV file."""
        test_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        df.to_csv(test_file, index=False)
        
        result = validate_data_file(test_file)
        
        assert result['valid'] is True
        assert result['checksum'] is not None
        assert result['row_count'] == 3

    def test_validate_parquet_file(self, tmp_path):
        """Test validation of a valid Parquet file."""
        test_file = tmp_path / "test.parquet"
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })
        df.to_parquet(test_file)
        
        result = validate_data_file(test_file)
        
        assert result['valid'] is True
        assert result['checksum'] is not None
        assert result['row_count'] == 5

    def test_validate_invalid_json_file(self, tmp_path):
        """Test validation of an invalid JSON file."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")
        
        result = validate_data_file(test_file)
        
        assert result['valid'] is False
        assert result['error'] is not None


class TestAggregateSuccessRate:
    """Tests for success rate aggregation."""

    @patch('validate_data.is_real_mode')
    @patch('validate_data.is_simulation_mode')
    @patch('validate_data.count_processed_meta_analyses')
    def test_aggregate_real_mode(self, mock_count, mock_sim_mode, mock_real_mode):
        """Test aggregation in real mode."""
        mock_count.return_value = 60
        mock_real_mode.return_value = True
        mock_sim_mode.return_value = False
        
        report = aggregate_success_rate()
        
        assert report['actual_processed'] == 60
        assert report['total_target'] == TARGET_COUNT
        assert report['success_rate'] == 60 / TARGET_COUNT
        assert report['mode'] == 'real'
        assert report['meets_requirement'] is True

    @patch('validate_data.is_real_mode')
    @patch('validate_data.is_simulation_mode')
    @patch('validate_data.count_processed_meta_analyses')
    def test_aggregate_simulation_mode(self, mock_count, mock_sim_mode, mock_real_mode):
        """Test aggregation in simulation mode."""
        mock_count.return_value = 25
        mock_real_mode.return_value = False
        mock_sim_mode.return_value = True
        
        report = aggregate_success_rate()
        
        assert report['actual_processed'] == 25
        assert report['mode'] == 'simulation'
        assert report['meets_requirement'] is False

    @patch('validate_data.is_real_mode')
    @patch('validate_data.is_simulation_mode')
    @patch('validate_data.count_processed_meta_analyses')
    def test_aggregate_below_threshold(self, mock_count, mock_sim_mode, mock_real_mode):
        """Test aggregation when below threshold."""
        mock_count.return_value = 40
        mock_real_mode.return_value = True
        mock_sim_mode.return_value = False
        
        report = aggregate_success_rate()
        
        assert report['actual_processed'] == 40
        assert report['meets_requirement'] is False
        assert report['success_rate'] < 1.0


class TestWriteSuccessRateReport:
    """Tests for report writing."""

    def test_write_report_creates_file(self, tmp_path):
        """Test that report writing creates the output file."""
        # Mock the output directory
        with patch('validate_data.DATA_OUTPUT_DIR', tmp_path):
            report = {
                'total_target': 50,
                'actual_processed': 45,
                'success_rate': 0.9,
                'mode': 'real'
            }
            
            output_path = write_success_rate_report(report)
            
            assert output_path.exists()
            assert output_path.name == 'success_rate_report.json'
            
            # Verify content
            with open(output_path, 'r') as f:
                written_report = json.load(f)
            
            assert written_report['actual_processed'] == 45
            assert written_report['mode'] == 'real'

    def test_write_report_creates_directory(self, tmp_path):
        """Test that report writing creates the output directory if needed."""
        nested_dir = tmp_path / "nested" / "output"
        
        with patch('validate_data.DATA_OUTPUT_DIR', nested_dir):
            report = {
                'total_target': 50,
                'actual_processed': 50,
                'success_rate': 1.0,
                'mode': 'real'
            }
            
            output_path = write_success_rate_report(report)
            
            assert nested_dir.exists()
            assert output_path.exists()
