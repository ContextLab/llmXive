"""
Unit tests for code/transform/metrics.py (T012a-c)

Tests:
- T012a: Aggregation of validation results
- T012b: Calculation of transformation success rate
- T012c: Saving results to JSON
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from transform.metrics import TransformationMetrics, run_transformation_metrics


class TestTransformationMetrics:
    """Test cases for TransformationMetrics class"""
    
    def test_initialization(self):
        """Test that metrics initializes with correct default values"""
        metrics = TransformationMetrics()
        
        assert metrics.total_variants == 0
        assert metrics.valid_variants == 0
        assert metrics.invalid_variants == 0
        assert metrics.success_rate == 0.0
        assert metrics.validation_details == []
        assert hasattr(metrics, 'timestamp')
    
    def test_aggregate_empty_variants(self):
        """Test aggregation with empty variants list"""
        metrics = TransformationMetrics()
        metrics.aggregate_validation_results([])
        
        assert metrics.total_variants == 0
        assert metrics.valid_variants == 0
        assert metrics.invalid_variants == 0
        assert metrics.success_rate == 0.0
    
    def test_aggregate_valid_variants(self):
        """Test aggregation with all valid variants"""
        variants = [
            {"id": "v1", "code": "def f(): pass"},
            {"id": "v2", "code": "def g(): return 1"},
            {"id": "v3", "code": "x = 1 + 2"}
        ]
        
        metrics = TransformationMetrics()
        metrics.aggregate_validation_results(variants)
        
        assert metrics.total_variants == 3
        assert metrics.valid_variants == 3
        assert metrics.invalid_variants == 0
        assert metrics.success_rate == 1.0
        assert len(metrics.validation_details) == 3
    
    def test_aggregate_invalid_variants(self):
        """Test aggregation with invalid syntax variants"""
        variants = [
            {"id": "v1", "code": "def invalid("},  # Syntax error
            {"id": "v2", "code": "return 1"},  # Invalid outside function
            {"id": "v3", "code": "x ="}  # Incomplete expression
        ]
        
        metrics = TransformationMetrics()
        metrics.aggregate_validation_results(variants)
        
        assert metrics.total_variants == 3
        assert metrics.valid_variants == 0
        assert metrics.invalid_variants == 3
        assert metrics.success_rate == 0.0
    
    def test_aggregate_mixed_variants(self):
        """Test aggregation with mix of valid and invalid variants"""
        variants = [
            {"id": "v1", "code": "def valid(): pass"},
            {"id": "v2", "code": "def invalid("},
            {"id": "v3", "code": "x = 1"},
            {"id": "v4", "code": "y ="}
        ]
        
        metrics = TransformationMetrics()
        metrics.aggregate_validation_results(variants)
        
        assert metrics.total_variants == 4
        assert metrics.valid_variants == 2
        assert metrics.invalid_variants == 2
        assert metrics.success_rate == 0.5
    
    def test_calculate_success_rate(self):
        """Test success rate calculation"""
        metrics = TransformationMetrics()
        metrics.total_variants = 10
        metrics.valid_variants = 7
        metrics.invalid_variants = 3
        
        assert metrics.calculate_success_rate() == 0.7
    
    def test_save_results_creates_file(self):
        """Test that save_results creates the output file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            
            metrics = TransformationMetrics()
            metrics.total_variants = 5
            metrics.valid_variants = 4
            metrics.invalid_variants = 1
            metrics.success_rate = 0.8
            
            saved_path = metrics.save_results(output_path)
            
            assert os.path.exists(saved_path)
            
            with open(saved_path, 'r') as f:
                data = json.load(f)
            
            assert data['total_variants'] == 5
            assert data['valid_variants'] == 4
            assert data['invalid_variants'] == 1
            assert data['success_rate'] == 0.8
            assert 'timestamp' in data
    
    def test_save_results_creates_directory(self):
        """Test that save_results creates directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test_results.json")
            
            metrics = TransformationMetrics()
            saved_path = metrics.save_results(output_path)
            
            assert os.path.exists(os.path.dirname(saved_path))
            assert os.path.exists(saved_path)
    
    def test_get_summary(self):
        """Test summary generation"""
        metrics = TransformationMetrics()
        metrics.total_variants = 100
        metrics.valid_variants = 95
        metrics.invalid_variants = 5
        metrics.success_rate = 0.95
        
        summary = metrics.get_summary()
        
        assert summary['total_variants'] == 100
        assert summary['valid_variants'] == 95
        assert summary['invalid_variants'] == 5
        assert summary['success_rate'] == 0.95
        assert summary['success_rate_percentage'] == '95.00%'
        assert 'timestamp' in summary


class TestRunTransformationMetrics:
    """Test cases for run_transformation_metrics convenience function"""
    
    def test_run_metrics_function(self):
        """Test the convenience function"""
        variants = [
            {"id": "v1", "code": "def f(): pass"},
            {"id": "v2", "code": "def g(): return 1"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metrics.json")
            
            result = run_transformation_metrics(variants, output_path)
            
            assert result['total_variants'] == 2
            assert result['valid_variants'] == 2
            assert result['success_rate'] == 1.0
            assert os.path.exists(output_path)
    
    def test_run_metrics_with_invalid(self):
        """Test convenience function with invalid variants"""
        variants = [
            {"id": "v1", "code": "def valid(): pass"},
            {"id": "v2", "code": "invalid syntax ("}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metrics.json")
            
            result = run_transformation_metrics(variants, output_path)
            
            assert result['total_variants'] == 2
            assert result['valid_variants'] == 1
            assert result['invalid_variants'] == 1
            assert result['success_rate'] == 0.5


class TestIntegrationWithValidator:
    """Integration tests with the validator module"""
    
    def test_integration_with_valid_variants(self):
        """Test metrics aggregation with valid variants from validator perspective"""
        valid_variants = [
            {"id": "test1", "code": "def add(a, b):\n    return a + b\n"},
            {"id": "test2", "code": "class Calculator:\n    def run(self):\n        return 42\n"},
            {"id": "test3", "code": "x = [i for i in range(10)]"}
        ]
        
        metrics = TransformationMetrics()
        metrics.aggregate_validation_results(valid_variants)
        
        # All should be valid
        assert metrics.valid_variants == 3
        assert metrics.invalid_variants == 0
        assert metrics.success_rate == 1.0
    
    def test_integration_with_invalid_variants(self):
        """Test metrics aggregation with invalid variants"""
        invalid_variants = [
            {"id": "test1", "code": "def broken("},
            {"id": "test2", "code": "x = 1\nif\n    pass"}
        ]
        
        metrics = TransformationMetrics()
        metrics.aggregate_validation_results(invalid_variants)
        
        # All should be invalid
        assert metrics.valid_variants == 0
        assert metrics.invalid_variants == 2
        assert metrics.success_rate == 0.0
    
    def test_integration_with_mixed_variants(self):
        """Test metrics aggregation with mixed valid/invalid variants"""
        mixed_variants = [
            {"id": "test1", "code": "def good(): pass"},
            {"id": "test2", "code": "def bad("},
            {"id": "test3", "code": "y = 2 + 2"},
            {"id": "test4", "code": "z ="}
        ]
        
        metrics = TransformationMetrics()
        metrics.aggregate_validation_results(mixed_variants)
        
        assert metrics.total_variants == 4
        assert metrics.valid_variants == 2
        assert metrics.invalid_variants == 2
        assert metrics.success_rate == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
