import pytest
import math
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from utils.validator import (
    validate_effect_size,
    validate_study_row,
    filter_valid_studies,
    validate_file_size,
    validate_generated_plots
)

import logging

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)


class TestValidateEffectSize:
    """Test the validate_effect_size function"""
    
    def test_valid_effect_size_positive(self):
        """Test valid positive effect size"""
        is_valid, error = validate_effect_size(0.5)
        assert is_valid is True
        assert error is None
    
    def test_valid_effect_size_negative(self):
        """Test valid negative effect size"""
        is_valid, error = validate_effect_size(-0.3)
        assert is_valid is True
        assert error is None
    
    def test_valid_effect_size_zero(self):
        """Test valid zero effect size"""
        is_valid, error = validate_effect_size(0.0)
        assert is_valid is True
        assert error is None
    
    def test_valid_effect_size_boundary_positive(self):
        """Test boundary value 1.0"""
        is_valid, error = validate_effect_size(1.0)
        assert is_valid is True
        assert error is None
    
    def test_valid_effect_size_boundary_negative(self):
        """Test boundary value -1.0"""
        is_valid, error = validate_effect_size(-1.0)
        assert is_valid is True
        assert error is None
    
    def test_invalid_effect_size_too_high(self):
        """Test effect size > 1.0"""
        is_valid, error = validate_effect_size(1.5)
        assert is_valid is False
        assert error is not None
        assert "outside valid range" in error
    
    def test_invalid_effect_size_too_low(self):
        """Test effect size < -1.0"""
        is_valid, error = validate_effect_size(-1.5)
        assert is_valid is False
        assert error is not None
        assert "outside valid range" in error
    
    def test_invalid_effect_size_none(self):
        """Test None effect size"""
        is_valid, error = validate_effect_size(None)
        assert is_valid is False
        assert error is not None
        assert "missing" in error.lower()
    
    def test_invalid_effect_size_nan(self):
        """Test NaN effect size"""
        is_valid, error = validate_effect_size(float('nan'))
        assert is_valid is False
        assert error is not None
        assert "NaN" in error
    
    def test_invalid_effect_size_inf(self):
        """Test infinite effect size"""
        is_valid, error = validate_effect_size(float('inf'))
        assert is_valid is False
        assert error is not None
        assert "infinite" in error
    
    def test_invalid_effect_size_string(self):
        """Test string effect size"""
        is_valid, error = validate_effect_size("0.5")
        assert is_valid is False
        assert error is not None
        assert "not numeric" in error


class TestValidateStudyRow:
    """Test the validate_study_row function"""
    
    def test_valid_study_row(self):
        """Test a complete valid study row"""
        row = {
            'study_id': 'test_001',
            'r': 0.45,
            'n': 100,
            'tract': 'arcuate_fasciculus'
        }
        is_valid, error = validate_study_row(row, 0)
        assert is_valid is True
        assert error is None
    
    def test_missing_effect_size(self):
        """Test row with missing effect size"""
        row = {
            'study_id': 'test_002',
            'n': 100,
            'tract': 'cingulum'
        }
        is_valid, error = validate_study_row(row, 1)
        assert is_valid is False
        assert error is not None
        assert "Missing effect size" in error
    
    def test_invalid_effect_size_value(self):
        """Test row with invalid effect size value"""
        row = {
            'study_id': 'test_003',
            'r': 1.5,
            'n': 100
        }
        is_valid, error = validate_study_row(row, 2)
        assert is_valid is False
        assert error is not None
        assert "Invalid effect size" in error
    
    def test_missing_sample_size(self):
        """Test row with missing sample size"""
        row = {
            'study_id': 'test_004',
            'r': 0.3
        }
        is_valid, error = validate_study_row(row, 3)
        assert is_valid is False
        assert error is not None
        assert "Missing sample size" in error
    
    def test_invalid_sample_size_zero(self):
        """Test row with zero sample size"""
        row = {
            'study_id': 'test_005',
            'r': 0.3,
            'n': 0
        }
        is_valid, error = validate_study_row(row, 4)
        assert is_valid is False
        assert error is not None
        assert "Invalid sample size" in error
    
    def test_invalid_sample_size_negative(self):
        """Test row with negative sample size"""
        row = {
            'study_id': 'test_006',
            'r': 0.3,
            'n': -10
        }
        is_valid, error = validate_study_row(row, 5)
        assert is_valid is False
        assert error is not None
        assert "Invalid sample size" in error
    
    def test_default_study_id(self):
        """Test that missing study_id gets a default"""
        row = {
            'r': 0.3,
            'n': 100
        }
        is_valid, error = validate_study_row(row, 99)
        assert is_valid is True
        assert error is None


class TestFilterValidStudies:
    """Test the filter_valid_studies function"""
    
    def test_filter_all_valid(self):
        """Test filtering when all studies are valid"""
        studies = [
            {'study_id': 's1', 'r': 0.3, 'n': 100},
            {'study_id': 's2', 'r': 0.5, 'n': 150},
            {'study_id': 's3', 'r': -0.2, 'n': 80}
        ]
        valid, excluded = filter_valid_studies(studies, log_exclusions=False)
        assert len(valid) == 3
        assert len(excluded) == 0
    
    def test_filter_some_invalid(self):
        """Test filtering when some studies are invalid"""
        studies = [
            {'study_id': 's1', 'r': 0.3, 'n': 100},
            {'study_id': 's2', 'r': 1.5, 'n': 150},  # Invalid r
            {'study_id': 's3', 'r': 0.2, 'n': 0},    # Invalid n
            {'study_id': 's4', 'r': 0.4, 'n': 200}
        ]
        valid, excluded = filter_valid_studies(studies, log_exclusions=False)
        assert len(valid) == 2
        assert len(excluded) == 2
        assert valid[0]['study_id'] == 's1'
        assert valid[1]['study_id'] == 's4'
    
    def test_filter_all_invalid(self):
        """Test filtering when all studies are invalid"""
        studies = [
            {'study_id': 's1', 'r': 1.5, 'n': 100},
            {'study_id': 's2', 'r': -1.5, 'n': 150}
        ]
        valid, excluded = filter_valid_studies(studies, log_exclusions=False)
        assert len(valid) == 0
        assert len(excluded) == 2
    
    def test_filter_empty_list(self):
        """Test filtering an empty list"""
        studies = []
        valid, excluded = filter_valid_studies(studies, log_exclusions=False)
        assert len(valid) == 0
        assert len(excluded) == 0
    
    def test_exclusion_details(self):
        """Test that exclusion details are properly captured"""
        studies = [
            {'study_id': 's1', 'r': 1.5, 'n': 100}
        ]
        valid, excluded = filter_valid_studies(studies, log_exclusions=False)
        assert len(excluded) == 1
        assert excluded[0]['study']['study_id'] == 's1'
        assert excluded[0]['reason'] is not None
        assert excluded[0]['index'] == 0


class TestValidateFileSize:
    """Test the validate_file_size function"""
    
    def test_valid_file_size(self):
        """Test file within size limit"""
        # Create a temporary small file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            is_valid, size = validate_file_size(temp_path, max_size_mb=1)
            assert is_valid is True
            assert size > 0
        finally:
            os.unlink(temp_path)
    
    def test_file_too_large(self):
        """Test file exceeding size limit"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("x" * (1024 * 1024 * 2))  # 2MB
            temp_path = f.name
        
        try:
            is_valid, size = validate_file_size(temp_path, max_size_mb=1)
            assert is_valid is False
            assert size > 0
        finally:
            os.unlink(temp_path)
    
    def test_file_not_exists(self):
        """Test non-existent file"""
        is_valid, size = validate_file_size("/nonexistent/path/file.txt", max_size_mb=1)
        assert is_valid is False
        assert size == 0


class TestValidateGeneratedPlots:
    """Test the validate_generated_plots function"""
    
    def test_all_plots_valid(self):
        """Test when all plots are valid"""
        import tempfile
        import os
        
        # Create temporary files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write("test")
                temp_files.append(f.name)
        
        try:
            result = validate_generated_plots(temp_files, max_size_mb=1)
            assert result['all_valid'] is True
            assert len(result['valid_files']) == 3
            assert len(result['invalid_files']) == 0
        finally:
            for path in temp_files:
                os.unlink(path)
    
    def test_some_plots_invalid(self):
        """Test when some plots are invalid"""
        import tempfile
        import os
        
        temp_files = []
        # Create a valid small file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("small")
            temp_files.append(f.name)
        
        # Create a large invalid file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("x" * (1024 * 1024 * 2))
            temp_files.append(f.name)
        
        # Create a non-existent file path
        temp_files.append("/nonexistent/file.png")
        
        try:
            result = validate_generated_plots(temp_files, max_size_mb=1)
            assert result['all_valid'] is False
            assert len(result['valid_files']) == 1
            assert len(result['invalid_files']) == 2
        finally:
            for path in temp_files[:2]:
                os.unlink(path)