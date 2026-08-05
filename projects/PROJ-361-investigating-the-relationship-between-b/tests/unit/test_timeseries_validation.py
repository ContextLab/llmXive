"""
Unit tests for timeseries validation functionality (T016).

Tests the validation of T×N matrices for NaN values.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing.validate_timeseries import (
    validate_timeseries_matrix,
    validate_all_subjects,
    main
)
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class TestValidateTimeseriesMatrix:
    """Tests for the validate_timeseries_matrix function."""

    def test_valid_matrix_no_nan(self):
        """Test that a matrix with no NaN values passes validation."""
        matrix = np.random.rand(100, 200)
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is True
        assert error_msg is None

    def test_matrix_with_nan_values(self):
        """Test that a matrix with NaN values fails validation."""
        matrix = np.random.rand(100, 200)
        matrix[50, 100] = np.nan
        matrix[51, 101] = np.nan
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is False
        assert error_msg is not None
        assert "NaN values" in error_msg
        assert "2" in error_msg  # Should report 2 NaN values

    def test_matrix_with_all_nan(self):
        """Test that a matrix full of NaN values fails validation."""
        matrix = np.full((100, 200), np.nan)
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is False
        assert error_msg is not None
        assert "NaN values" in error_msg

    def test_invalid_dimensions_1d(self):
        """Test that a 1D array fails validation."""
        matrix = np.random.rand(100)
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is False
        assert error_msg is not None
        assert "1 dimensions" in error_msg

    def test_invalid_dimensions_3d(self):
        """Test that a 3D array fails validation."""
        matrix = np.random.rand(10, 100, 200)
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is False
        assert error_msg is not None
        assert "3 dimensions" in error_msg

    def test_empty_matrix_zero_timepoints(self):
        """Test that a matrix with 0 timepoints fails validation."""
        matrix = np.zeros((0, 200))
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is False
        assert error_msg is not None
        assert "invalid dimensions" in error_msg

    def test_empty_matrix_zero_rois(self):
        """Test that a matrix with 0 ROIs fails validation."""
        matrix = np.zeros((100, 0))
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is False
        assert error_msg is not None
        assert "invalid dimensions" in error_msg

    def test_single_element_matrix(self):
        """Test validation of a 1x1 matrix."""
        matrix = np.array([[0.5]])
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is True
        assert error_msg is None

    def test_single_element_matrix_with_nan(self):
        """Test validation of a 1x1 matrix with NaN."""
        matrix = np.array([[np.nan]])
        
        is_valid, error_msg = validate_timeseries_matrix(matrix, "sub-001")
        
        assert is_valid is False
        assert error_msg is not None


class TestValidateAllSubjects:
    """Tests for the validate_all_subjects function."""

    @pytest.fixture
    def temp_processed_dir(self):
        """Create a temporary directory with mock timeseries files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processed_dir = Path(tmpdir)
            
            # Create valid matrix
            valid_matrix = np.random.rand(100, 200)
            np.save(processed_dir / "timeseries_sub-001.npy", valid_matrix)
            
            # Create matrix with NaN
            invalid_matrix = np.random.rand(100, 200)
            invalid_matrix[50, 100] = np.nan
            np.save(processed_dir / "timeseries_sub-002.npy", invalid_matrix)
            
            # Create another valid matrix
            valid_matrix2 = np.random.rand(150, 200)
            np.save(processed_dir / "timeseries_sub-003.npy", valid_matrix2)
            
            yield processed_dir

    def test_mixed_validity_results(self, temp_processed_dir):
        """Test validation of multiple subjects with mixed validity."""
        results = validate_all_subjects(temp_processed_dir)
        
        assert "sub-001" in results
        assert "sub-002" in results
        assert "sub-003" in results
        
        assert results["sub-001"]["valid"] is True
        assert results["sub-002"]["valid"] is False
        assert results["sub-003"]["valid"] is True

    def test_empty_directory(self):
        """Test validation when no timeseries files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = validate_all_subjects(Path(tmpdir))
            
            assert len(results) == 0

    def test_corrupt_file_handling(self):
        """Test handling of corrupt or unreadable files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processed_dir = Path(tmpdir)
            
            # Create a non-npy file with the right naming pattern
            (processed_dir / "timeseries_sub-corrupt.npy").write_text("not a numpy file")
            
            results = validate_all_subjects(processed_dir)
            
            assert "sub-corrupt" in results
            assert results["sub-corrupt"]["valid"] is False
            assert "Failed to load file" in results["sub-corrupt"]["error"]


class TestMainFunction:
    """Tests for the main function entry point."""

    def test_main_with_valid_data(self, temp_processed_dir):
        """Test main function with valid data (should exit 0)."""
        with patch('sys.argv', ['validate_timeseries.py', '--processed-dir', str(temp_processed_dir)]):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)

    def test_main_with_fail_on_error(self, temp_processed_dir):
        """Test main function with --fail-on-error when validation fails."""
        with patch('sys.argv', [
            'validate_timeseries.py',
            '--processed-dir', str(temp_processed_dir),
            '--fail-on-error'
        ]):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)