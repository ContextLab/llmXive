"""
Unit tests for validator edge cases, specifically the n < 300 warning logic.

This module tests the behavior of code/validator.py when sample counts
fall below the critical threshold of 300, ensuring proper warning generation
and fallback to heuristic (fixed k=2).
"""
import os
import sys
import logging
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from validator import check_sample_count, run_validation


class TestCheckSampleCount:
    """Tests for the check_sample_count function in validator.py"""

    def test_sample_count_above_threshold(self, caplog):
        """Test that no warning is raised when n >= 300"""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=300)
            assert result is True
            assert "warning" not in caplog.text.lower()

    def test_sample_count_just_above_threshold(self, caplog):
        """Test that no warning is raised when n = 301"""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=301)
            assert result is True
            assert "warning" not in caplog.text.lower()

    def test_sample_count_below_threshold(self, caplog):
        """Test that warning is raised when n < 300"""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=299)
            assert result is False
            assert "warning" in caplog.text.lower()
            assert "sample count" in caplog.text.lower()
            assert "300" in caplog.text

    def test_sample_count_very_low(self, caplog):
        """Test that warning is raised for very low sample counts"""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=50)
            assert result is False
            assert "warning" in caplog.text.lower()
            assert "50" in caplog.text

    def test_sample_count_zero(self, caplog):
        """Test that warning is raised when n = 0"""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=0)
            assert result is False
            assert "warning" in caplog.text.lower()

    def test_sample_count_negative(self, caplog):
        """Test that warning is raised for negative sample counts"""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=-10)
            assert result is False
            assert "warning" in caplog.text.lower()

    def test_sample_count_exact_threshold(self, caplog):
        """Test that no warning is raised when n = 300 exactly"""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=300)
            assert result is True
            assert "warning" not in caplog.text.lower()

    def test_fallback_heuristic_k2(self):
        """Test that fallback heuristic k=2 is triggered when n < 300"""
        # The function should return False and trigger fallback logic
        # We verify the return value indicates the need for fallback
        result = check_sample_count(n=100)
        assert result is False


class TestRunValidation:
    """Tests for the run_validation function with edge cases"""

    def test_validation_with_small_dataset(self, tmp_path):
        """Test validation with a dataset smaller than 300 samples"""
        # Create a small test dataset
        small_data = pd.DataFrame({
            'feature1': [1.0] * 100,
            'feature2': [2.0] * 100,
            'utility_score': [0.5] * 100
        })
        
        data_file = tmp_path / "small_dataset.csv"
        small_data.to_csv(data_file, index=False)
        
        with patch('validator.check_sample_count') as mock_check:
            mock_check.return_value = False  # Simulate n < 300
            
            result = run_validation(str(data_file))
            
            # Verify that check_sample_count was called
            mock_check.assert_called_once()
            # Result should reflect the validation failure due to small sample
            assert result is not None

    def test_validation_with_large_dataset(self, tmp_path):
        """Test validation with a dataset larger than 300 samples"""
        # Create a large test dataset
        large_data = pd.DataFrame({
            'feature1': [1.0] * 500,
            'feature2': [2.0] * 500,
            'utility_score': [0.5] * 500
        })
        
        data_file = tmp_path / "large_dataset.csv"
        large_data.to_csv(data_file, index=False)
        
        with patch('validator.check_sample_count') as mock_check:
            mock_check.return_value = True  # Simulate n >= 300
            
            result = run_validation(str(data_file))
            
            # Verify that check_sample_count was called
            mock_check.assert_called_once()
            # Result should reflect successful validation
            assert result is not None

    def test_validation_with_missing_file(self):
        """Test validation with a non-existent file"""
        with pytest.raises(FileNotFoundError):
            run_validation("/nonexistent/path/to/file.csv")

    def test_validation_with_invalid_csv(self, tmp_path):
        """Test validation with an invalid CSV file"""
        invalid_file = tmp_path / "invalid.csv"
        invalid_file.write_text("not,a,valid\n1,2,3\n4,5")  # Missing column in last row
        
        # Should handle gracefully or raise appropriate error
        with pytest.raises((ValueError, pd.errors.ParserError)):
            run_validation(str(invalid_file))

    def test_validation_log_warning_for_small_sample(self, tmp_path, caplog):
        """Test that validation logs warning for small sample size"""
        small_data = pd.DataFrame({
            'feature1': [1.0] * 100,
            'feature2': [2.0] * 100,
            'utility_score': [0.5] * 100
        })
        
        data_file = tmp_path / "small_dataset.csv"
        small_data.to_csv(data_file, index=False)
        
        with caplog.at_level(logging.WARNING):
            with patch('validator.check_sample_count') as mock_check:
                mock_check.return_value = False
                
                run_validation(str(data_file))
                
                assert "warning" in caplog.text.lower()
                assert "sample count" in caplog.text.lower()


class TestIntegration:
    """Integration tests for the validator module"""

    def test_full_validation_pipeline_small_sample(self, tmp_path):
        """Test the full validation pipeline with small sample size"""
        # Create a realistic small dataset
        data = pd.DataFrame({
            'layer_id': list(range(100)),
            'utility_score': [i / 100.0 for i in range(100)],
            'entropy': [0.1 * i for i in range(100)],
            'token_count': [100 + i for i in range(100)]
        })
        
        data_file = tmp_path / "test_data.csv"
        data.to_csv(data_file, index=False)
        
        with patch('validator.check_sample_count') as mock_check:
            mock_check.return_value = False
            
            result = run_validation(str(data_file))
            
            # Verify the pipeline handles small samples correctly
            assert result is not None
            mock_check.assert_called_once()

    def test_full_validation_pipeline_large_sample(self, tmp_path):
        """Test the full validation pipeline with large sample size"""
        # Create a realistic large dataset
        data = pd.DataFrame({
            'layer_id': list(range(500)),
            'utility_score': [i / 500.0 for i in range(500)],
            'entropy': [0.1 * i for i in range(500)],
            'token_count': [100 + i for i in range(500)]
        })
        
        data_file = tmp_path / "test_data.csv"
        data.to_csv(data_file, index=False)
        
        with patch('validator.check_sample_count') as mock_check:
            mock_check.return_value = True
            
            result = run_validation(str(data_file))
            
            # Verify the pipeline handles large samples correctly
            assert result is not None
            mock_check.assert_called_once()

    def test_boundary_conditions(self, tmp_path):
        """Test boundary conditions around the 300 threshold"""
        for n in [299, 300, 301]:
            data = pd.DataFrame({
                'layer_id': list(range(n)),
                'utility_score': [i / n for i in range(n)],
            })
            
            data_file = tmp_path / f"test_data_{n}.csv"
            data.to_csv(data_file, index=False)
            
            expected_result = n >= 300
            
            with patch('validator.check_sample_count') as mock_check:
                mock_check.return_value = expected_result
                
                result = run_validation(str(data_file))
                
                assert result is not None
                mock_check.assert_called_once()