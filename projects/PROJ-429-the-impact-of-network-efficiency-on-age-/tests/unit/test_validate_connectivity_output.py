import os
import json
import tempfile
import numpy as np
from pathlib import Path
import pytest

# Import the functions to test
from validate_connectivity_output import (
    load_connectivity_matrix,
    validate_matrix_dimensions,
    validate_non_nan_values,
    validate_connectivity_matrices,
    generate_validation_report
)

class TestLoadConnectivityMatrix:
    def test_load_valid_matrix(self):
        """Test loading a valid connectivity matrix."""
        with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as f:
            test_matrix = np.random.rand(19, 19)
            np.save(f.name, test_matrix)
            temp_path = Path(f.name)
        
        try:
            loaded = load_connectivity_matrix(temp_path)
            assert np.array_equal(loaded, test_matrix)
            assert loaded.shape == (19, 19)
        finally:
            temp_path.unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises ValueError."""
        with pytest.raises(ValueError):
            load_connectivity_matrix(Path('/nonexistent/file.npy'))

class TestValidateMatrixDimensions:
    def test_valid_square_matrix(self):
        """Test validation of a valid square matrix."""
        matrix = np.random.rand(19, 19)
        is_valid, message = validate_matrix_dimensions(matrix, Path('test.npy'))
        assert is_valid
        assert '19x19' in message
    
    def test_non_square_matrix(self):
        """Test validation of a non-square matrix."""
        matrix = np.random.rand(19, 20)
        is_valid, message = validate_matrix_dimensions(matrix, Path('test.npy'))
        assert not is_valid
        assert 'not square' in message
    
    def test_non_2d_matrix(self):
        """Test validation of a non-2D matrix."""
        matrix = np.random.rand(19)
        is_valid, message = validate_matrix_dimensions(matrix, Path('test.npy'))
        assert not is_valid
        assert 'not 2D' in message
    
    def test_invalid_channel_count(self):
        """Test validation of a matrix with invalid channel count."""
        matrix = np.random.rand(5, 5)  # Too small
        is_valid, message = validate_matrix_dimensions(matrix, Path('test.npy'))
        assert not is_valid
        assert 'does not match standard EEG montages' in message

class TestValidateNonNaNValues:
    def test_no_nan_values(self):
        """Test validation of a matrix without NaN values."""
        matrix = np.random.rand(19, 19)
        is_valid, nan_ratio = validate_non_nan_values(matrix, Path('test.npy'))
        assert is_valid
        assert nan_ratio == 0.0
    
    def test_with_nan_values(self):
        """Test validation of a matrix with NaN values."""
        matrix = np.random.rand(19, 19)
        matrix[0, 0] = np.nan
        is_valid, nan_ratio = validate_non_nan_values(matrix, Path('test.npy'))
        assert not is_valid
        assert nan_ratio > 0.0
        assert nan_ratio <= 1.0

class TestValidateConnectivityMatrices:
    def test_empty_directory(self):
        """Test validation of an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            results = validate_connectivity_matrices(output_dir)
            assert results['total_files'] == 0
            assert results['valid_files'] == 0
            assert results['invalid_files'] == 0
    
    def test_valid_matrices(self):
        """Test validation of valid matrices."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Create valid matrices
            for i in range(3):
                matrix = np.random.rand(19, 19)
                np.save(output_dir / f'valid_{i}.npy', matrix)
            
            results = validate_connectivity_matrices(output_dir)
            assert results['total_files'] == 3
            assert results['valid_files'] == 3
            assert results['invalid_files'] == 0
    
    def test_invalid_matrices(self):
        """Test validation of invalid matrices."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Create invalid matrix (non-square)
            matrix = np.random.rand(19, 20)
            np.save(output_dir / 'invalid.npy', matrix)
            
            results = validate_connectivity_matrices(output_dir)
            assert results['total_files'] == 1
            assert results['valid_files'] == 0
            assert results['invalid_files'] == 1
    
    def test_mixed_validity(self):
        """Test validation of mixed valid and invalid matrices."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Create valid matrix
            valid_matrix = np.random.rand(19, 19)
            np.save(output_dir / 'valid.npy', valid_matrix)
            
            # Create invalid matrix (with NaN)
            invalid_matrix = np.random.rand(19, 19)
            invalid_matrix[0, 0] = np.nan
            np.save(output_dir / 'invalid.npy', invalid_matrix)
            
            results = validate_connectivity_matrices(output_dir)
            assert results['total_files'] == 2
            assert results['valid_files'] == 1
            assert results['invalid_files'] == 1

class TestGenerateValidationReport:
    def test_report_generation(self):
        """Test generation of validation report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report_path = output_dir / 'report.json'
            
            results = {
                'total_files': 1,
                'valid_files': 1,
                'invalid_files': 0,
                'missing_directory': False,
                'files': [
                    {
                        'filename': 'test.npy',
                        'dimension_valid': True,
                        'nan_valid': True
                    }
                ]
            }
            
            generate_validation_report(results, report_path)
            
            assert report_path.exists()
            with open(report_path) as f:
                report = json.load(f)
            
            assert report['total_files'] == 1
            assert report['valid_files'] == 1