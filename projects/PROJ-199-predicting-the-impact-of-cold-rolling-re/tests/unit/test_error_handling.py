"""
Unit tests for error handling utilities.

Tests the error handling functionality for missing reduction levels
and corrupted EBSD files as implemented in code/data/error_handling.py.
"""
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from data.error_handling import (
    validate_reduction_levels,
    check_file_integrity,
    handle_corrupted_file,
    handle_missing_reduction,
    process_with_error_handling
)
from config import ConfigurationError


class TestValidateReductionLevels:
    """Tests for validate_reduction_levels function."""
    
    def test_valid_reduction(self):
        """Test validation of a valid reduction level."""
        metadata = {'reduction': 0.2, 'material': 'Al'}
        is_valid, error_msg = validate_reduction_levels(metadata)
        assert is_valid is True
        assert error_msg is None
    
    def test_missing_reduction(self):
        """Test validation when reduction is missing."""
        metadata = {'material': 'Al'}
        is_valid, error_msg = validate_reduction_levels(metadata)
        assert is_valid is False
        assert "Missing 'reduction' field" in error_msg
    
    def test_none_reduction(self):
        """Test validation when reduction is None."""
        metadata = {'reduction': None, 'material': 'Al'}
        is_valid, error_msg = validate_reduction_levels(metadata)
        assert is_valid is False
        assert "None or NaN" in error_msg
    
    def test_nan_reduction(self):
        """Test validation when reduction is NaN."""
        metadata = {'reduction': np.nan, 'material': 'Al'}
        is_valid, error_msg = validate_reduction_levels(metadata)
        assert is_valid is False
        assert "None or NaN" in error_msg
    
    def test_invalid_type(self):
        """Test validation when reduction has invalid type."""
        metadata = {'reduction': 'invalid', 'material': 'Al'}
        is_valid, error_msg = validate_reduction_levels(metadata)
        assert is_valid is False
        assert "Invalid reduction type" in error_msg
    
    def test_reduction_not_in_allowed_set(self):
        """Test validation when reduction is not in allowed set."""
        metadata = {'reduction': 0.5, 'material': 'Al'}
        allowed_reductions = [0.1, 0.2, 0.3]
        is_valid, error_msg = validate_reduction_levels(metadata, allowed_reductions)
        assert is_valid is False
        assert "not in allowed set" in error_msg
    
    def test_reduction_in_allowed_set(self):
        """Test validation when reduction is in allowed set."""
        metadata = {'reduction': 0.2, 'material': 'Al'}
        allowed_reductions = [0.1, 0.2, 0.3]
        is_valid, error_msg = validate_reduction_levels(metadata, allowed_reductions)
        assert is_valid is True
        assert error_msg is None


class TestCheckFileIntegrity:
    """Tests for check_file_integrity function."""
    
    def test_file_not_found(self, tmp_path):
        """Test when file does not exist."""
        file_path = tmp_path / "nonexistent.csv"
        is_valid, error_msg = check_file_integrity(file_path)
        assert is_valid is False
        assert "File not found" in error_msg
    
    def test_path_is_directory(self, tmp_path):
        """Test when path is a directory."""
        is_valid, error_msg = check_file_integrity(tmp_path)
        assert is_valid is False
        assert "not a file" in error_msg
    
    def test_valid_csv_file(self, tmp_path):
        """Test with a valid CSV file."""
        file_path = tmp_path / "valid.csv"
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        df.to_csv(file_path, index=False)
        
        is_valid, error_msg = check_file_integrity(file_path)
        assert is_valid is True
        assert error_msg is None
    
    def test_valid_parquet_file(self, tmp_path):
        """Test with a valid Parquet file."""
        file_path = tmp_path / "valid.parquet"
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        df.to_parquet(file_path)
        
        is_valid, error_msg = check_file_integrity(file_path)
        assert is_valid is True
        assert error_msg is None
    
    def test_corrupted_file(self, tmp_path):
        """Test with a corrupted/unreadable file."""
        file_path = tmp_path / "corrupted.csv"
        # Write binary data to a CSV file
        with open(file_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')
        
        is_valid, error_msg = check_file_integrity(file_path)
        assert is_valid is False
        assert "corrupted or unreadable" in error_msg


class TestHandleCorruptedFile:
    """Tests for handle_corrupted_file function."""
    
    def test_skip_mode(self, caplog, tmp_path):
        """Test that corrupted file is skipped in skip mode."""
        file_path = tmp_path / "corrupted.csv"
        error_msg = "Test error message"
        
        with caplog.at_level(logging.WARNING):
            result = handle_corrupted_file(file_path, error_msg, skip_mode=True)
        
        assert result is True
        assert "Corrupted file detected" in caplog.text
        assert "Skipping corrupted file" in caplog.text
    
    def test_no_skip_mode(self, caplog, tmp_path):
        """Test that error is raised when skip mode is False."""
        file_path = tmp_path / "corrupted.csv"
        error_msg = "Test error message"
        
        with caplog.at_level(logging.ERROR):
            result = handle_corrupted_file(file_path, error_msg, skip_mode=False)
        
        assert result is False
        assert "Cannot proceed with corrupted file" in caplog.text


class TestHandleMissingReduction:
    """Tests for handle_missing_reduction function."""
    
    def test_skip_mode(self, caplog):
        """Test that sample with missing reduction is skipped in skip mode."""
        sample_id = "test_sample"
        
        with caplog.at_level(logging.WARNING):
            result = handle_missing_reduction(sample_id, skip_mode=True)
        
        assert result is True
        assert "missing reduction level" in caplog.text
        assert "Skipping sample" in caplog.text
    
    def test_no_skip_mode(self, caplog):
        """Test that error is raised when skip mode is False."""
        sample_id = "test_sample"
        
        with caplog.at_level(logging.ERROR):
            result = handle_missing_reduction(sample_id, skip_mode=False)
        
        assert result is False
        assert "Cannot proceed with sample" in caplog.text


class TestProcessWithErrorHandling:
    """Tests for process_with_error_handling function."""
    
    def test_all_valid(self, tmp_path):
        """Test processing when all files are valid."""
        # Create valid files
        file1 = tmp_path / "valid1.csv"
        file2 = tmp_path / "valid2.csv"
        pd.DataFrame({'col': [1]}).to_csv(file1)
        pd.DataFrame({'col': [2]}).to_csv(file2)
        
        metadata1 = {'sample_id': 's1', 'reduction': 0.2}
        metadata2 = {'sample_id': 's2', 'reduction': 0.3}
        
        valid_files, valid_metadata, skipped_reasons = process_with_error_handling(
            [file1, file2],
            [metadata1, metadata2],
            skip_corrupted=True,
            skip_missing_reduction=True
        )
        
        assert len(valid_files) == 2
        assert len(valid_metadata) == 2
        assert len(skipped_reasons) == 0
    
    def test_missing_reduction_skipped(self, tmp_path):
        """Test that samples with missing reduction are skipped."""
        file1 = tmp_path / "valid1.csv"
        file2 = tmp_path / "valid2.csv"
        pd.DataFrame({'col': [1]}).to_csv(file1)
        pd.DataFrame({'col': [2]}).to_csv(file2)
        
        metadata1 = {'sample_id': 's1', 'reduction': 0.2}
        metadata2 = {'sample_id': 's2'}  # Missing reduction
        
        valid_files, valid_metadata, skipped_reasons = process_with_error_handling(
            [file1, file2],
            [metadata1, metadata2],
            skip_corrupted=True,
            skip_missing_reduction=True
        )
        
        assert len(valid_files) == 1
        assert len(valid_metadata) == 1
        assert len(skipped_reasons) == 1
        assert "missing reduction" in skipped_reasons[0].lower()
    
    def test_corrupted_file_skipped(self, tmp_path):
        """Test that corrupted files are skipped."""
        file1 = tmp_path / "valid.csv"
        file2 = tmp_path / "corrupted.csv"
        pd.DataFrame({'col': [1]}).to_csv(file1)
        # Create corrupted file
        with open(file2, 'wb') as f:
            f.write(b'\x00\x01\x02')
        
        metadata1 = {'sample_id': 's1', 'reduction': 0.2}
        metadata2 = {'sample_id': 's2', 'reduction': 0.3}
        
        valid_files, valid_metadata, skipped_reasons = process_with_error_handling(
            [file1, file2],
            [metadata1, metadata2],
            skip_corrupted=True,
            skip_missing_reduction=True
        )
        
        assert len(valid_files) == 1
        assert len(valid_metadata) == 1
        assert len(skipped_reasons) == 1
        assert "corrupted" in skipped_reasons[0].lower()
    
    def test_mismatched_lengths_raises(self, tmp_path):
        """Test that mismatched lengths raise ValueError."""
        file1 = tmp_path / "valid.csv"
        pd.DataFrame({'col': [1]}).to_csv(file1)
        
        with pytest.raises(ValueError):
            process_with_error_handling(
                [file1],
                [{'sample_id': 's1', 'reduction': 0.2}, {'sample_id': 's2', 'reduction': 0.3}],
                skip_corrupted=True,
                skip_missing_reduction=True
            )
    
    def test_config_error_handling(self, tmp_path):
        """Test handling when config raises ConfigurationError."""
        file1 = tmp_path / "valid.csv"
        pd.DataFrame({'col': [1]}).to_csv(file1)
        
        metadata = {'sample_id': 's1', 'reduction': 0.2}
        
        # Patch get_reductions to raise ConfigurationError
        with patch('data.error_handling.get_reductions', side_effect=ConfigurationError("Test error")):
            valid_files, valid_metadata, skipped_reasons = process_with_error_handling(
                [file1],
                [metadata],
                required_reductions=None,  # Force loading from config
                skip_corrupted=True,
                skip_missing_reduction=True
            )
        
        # Should still process the valid file
        assert len(valid_files) == 1
        assert len(valid_metadata) == 1
