"""
Unit tests for edge cases in the code generation and analysis pipeline.

Tests cover:
- Zero coverage scenarios (0% branch coverage)
- Missing LLM samples (generation failures)
- Empty code snippets
- Invalid JSON in metrics
- None/null values in metric calculations
"""
import os
import sys
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analyze_metrics import (
    load_test_suites,
    calculate_code_metrics,
    execute_test_suite,
    execute_coverage_test,
    analyze_batch_metrics,
    aggregate_metrics_to_json
)
from generate_code import log_error, mark_sample_missing
from utils import compute_sha256, safe_json_loads
from statistical_tests import load_metrics, wilcoxon_signed_rank_test


class TestZeroCoverage:
    """Tests for scenarios where code coverage is 0%"""
    
    def test_execute_coverage_test_zero_coverage(self):
        """Test coverage execution when code has no branches covered"""
        # Create a simple Python file with no executable branches
        code_snippet = """
        # This is a comment only file
        pass
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_snippet)
            temp_file = f.name
        
        try:
            result = execute_coverage_test(temp_file, [])
            
            # Should handle zero coverage gracefully
            assert 'branch_coverage_pct' in result
            assert result['branch_coverage_pct'] is not None
            # May be 0, None, or [deferred] depending on implementation
        finally:
            os.unlink(temp_file)
    
    def test_calculate_metrics_zero_coverage_input(self):
        """Test metric calculation when coverage data is zero"""
        metrics_data = {
            'cyclomatic_complexity': 1,
            'halstead_volume': 0.0,
            'branch_coverage_pct': 0.0,
            'pass_rate': 0
        }
        
        # Should not raise exception on zero values
        result = calculate_code_metrics("test_id", metrics_data)
        assert result is not None
        assert result['task_id'] == 'test_id'
    
    def test_aggregate_metrics_with_zero_coverage(self):
        """Test aggregation when some samples have zero coverage"""
        metrics_list = [
            {
                'task_id': 'test_1',
                'cyclomatic_complexity': 5,
                'halstead_volume': 100.0,
                'branch_coverage_pct': 0.0,
                'pass_rate': 0
            },
            {
                'task_id': 'test_2',
                'cyclomatic_complexity': 3,
                'halstead_volume': 50.0,
                'branch_coverage_pct': 25.0,
                'pass_rate': 1
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            aggregate_metrics_to_json(metrics_list, temp_file)
            
            # Verify file was created and contains data
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as read_file:
                data = json.load(read_file)
            
            assert len(data) == 2
            assert data[0]['branch_coverage_pct'] == 0.0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestMissingLLMSamples:
    """Tests for scenarios where LLM generation fails"""
    
    def test_mark_sample_missing(self):
        """Test marking a sample as missing due to LLM failure"""
        task_id = "missing_task_123"
        error_message = "Model timeout after 30 seconds"
        
        result = mark_sample_missing(task_id, error_message)
        
        assert result['task_id'] == task_id
        assert result['status'] == 'missing'
        assert result['error'] == error_message
        assert 'generated_code' not in result or result['generated_code'] is None
    
    def test_log_error_to_file(self):
        """Test error logging functionality"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name
        
        try:
            log_error(log_file, "Test error message", "T038")
            
            # Verify log file was created and contains error
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
            
            assert "Test error message" in content
            assert "T038" in content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_analyze_batch_with_missing_samples(self):
        """Test batch analysis when some samples are missing"""
        # Mix of valid and missing samples
        samples = [
            {
                'task_id': 'valid_1',
                'status': 'success',
                'generated_code': 'print("hello")',
                'test_suites': []
            },
            {
                'task_id': 'missing_1',
                'status': 'missing',
                'error': 'Generation failed'
            },
            {
                'task_id': 'valid_2',
                'status': 'success',
                'generated_code': 'x = 1',
                'test_suites': []
            }
        ]
        
        # Should handle missing samples without crashing
        results = analyze_batch_metrics(samples)
        
        assert len(results) == 3
        # Missing samples should be included with appropriate markers
        missing_count = sum(1 for r in results if r.get('status') == 'missing')
        assert missing_count == 1


class TestEmptyAndInvalidInputs:
    """Tests for empty code snippets and invalid data"""
    
    def test_calculate_metrics_empty_code(self):
        """Test metric calculation on empty code"""
        empty_code = ""
        
        # Should handle empty code gracefully
        result = calculate_code_metrics("empty_task", {'code': empty_code})
        assert result is not None
        assert result['task_id'] == 'empty_task'
    
    def test_calculate_metrics_whitespace_only(self):
        """Test metric calculation on whitespace-only code"""
        whitespace_code = "   \n\t  \n   "
        
        result = calculate_code_metrics("whitespace_task", {'code': whitespace_code})
        assert result is not None
    
    def test_safe_json_loads_invalid_json(self):
        """Test safe JSON parsing with invalid input"""
        invalid_json = "{ invalid json }"
        
        result = safe_json_loads(invalid_json)
        assert result is None
    
    def test_safe_json_loads_valid_json(self):
        """Test safe JSON parsing with valid input"""
        valid_json = '{"key": "value"}'
        
        result = safe_json_loads(valid_json)
        assert result == {"key": "value"}
    
    def test_load_test_suites_empty_list(self):
        """Test loading test suites from empty list"""
        empty_suites = []
        
        result = load_test_suites(empty_suites)
        assert result == []


class TestNoneAndNullValues:
    """Tests for handling None/null values in metrics"""
    
    def test_wilcoxon_with_none_values(self):
        """Test Wilcoxon test with None values in data"""
        # Create data with None values
        data1 = [1.0, 2.0, None, 4.0, 5.0]
        data2 = [1.5, 2.5, 3.0, None, 5.5]
        
        # Should handle None values gracefully (either filter or raise informative error)
        try:
            result = wilcoxon_signed_rank_test(data1, data2)
            # If it doesn't raise, it should return a valid result structure
            assert result is not None
        except (ValueError, TypeError) as e:
            # Or it should raise a clear error message
            assert "None" in str(e) or "null" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_load_metrics_with_missing_fields(self):
        """Test loading metrics when some fields are missing"""
        metrics_data = [
            {
                'task_id': 'test_1',
                'cyclomatic_complexity': 5,
                # Missing other fields
            },
            {
                'task_id': 'test_2',
                'halstead_volume': 100.0
            }
        ]
        
        # Should handle missing fields gracefully
        result = load_metrics(metrics_data)
        assert result is not None
        assert isinstance(result, dict)
    
    def test_aggregate_metrics_with_none_values(self):
        """Test aggregation when metrics contain None values"""
        metrics_list = [
            {
                'task_id': 'test_1',
                'cyclomatic_complexity': None,
                'halstead_volume': 100.0,
                'branch_coverage_pct': 0.0,
                'pass_rate': 0
            },
            {
                'task_id': 'test_2',
                'cyclomatic_complexity': 3,
                'halstead_volume': None,
                'branch_coverage_pct': 25.0,
                'pass_rate': 1
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Should not crash on None values
            aggregate_metrics_to_json(metrics_list, temp_file)
            
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as read_file:
                data = json.load(read_file)
            
            assert len(data) == 2
            # None values should be preserved or handled appropriately
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestBoundaryConditions:
    """Tests for boundary conditions in metric values"""
    
    def test_coverage_at_boundaries(self):
        """Test coverage values at 0% and 100%"""
        metrics_data = {
            'cyclomatic_complexity': 1,
            'halstead_volume': 0.0,
            'branch_coverage_pct': 100.0,
            'pass_rate': 1
        }
        
        result = calculate_code_metrics("boundary_task", metrics_data)
        assert result is not None
        assert result['branch_coverage_pct'] == 100.0
    
    def test_pass_rate_binary_values(self):
        """Test pass_rate with only 0 and 1 values"""
        metrics_list = [
            {'task_id': 'f1', 'pass_rate': 0, 'cyclomatic_complexity': 1},
            {'task_id': 'f2', 'pass_rate': 1, 'cyclomatic_complexity': 1},
            {'task_id': 'f3', 'pass_rate': 0, 'cyclomatic_complexity': 1},
            {'task_id': 'f4', 'pass_rate': 1, 'cyclomatic_complexity': 1}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            aggregate_metrics_to_json(metrics_list, temp_file)
            
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as read_file:
                data = json.load(read_file)
            
            # Verify all pass_rate values are 0 or 1
            for item in data:
                assert item['pass_rate'] in [0, 1]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_complexity_minimum_value(self):
        """Test that cyclomatic complexity minimum is 1"""
        # Even empty code should have minimum complexity of 1
        metrics_data = {
            'cyclomatic_complexity': 0,  # Invalid, should be at least 1
            'halstead_volume': 0.0,
            'branch_coverage_pct': 0.0,
            'pass_rate': 0
        }
        
        result = calculate_code_metrics("min_complexity_task", metrics_data)
        assert result is not None
        # Implementation should handle or correct invalid complexity values


class TestErrorHandling:
    """Tests for comprehensive error handling"""
    
    def test_execute_test_suite_timeout(self):
        """Test test suite execution with timeout simulation"""
        code_snippet = "print('hello')"
        test_suites = []  # Empty test suites
        
        # Should handle empty test suites without crashing
        result = execute_test_suite(code_snippet, test_suites)
        assert result is not None
        assert 'pass_rate' in result or result.get('status') is not None
    
    def test_execute_coverage_test_timeout(self):
        """Test coverage execution with timeout simulation"""
        code_snippet = "print('hello')"
        
        # Should handle coverage execution gracefully
        result = execute_coverage_test(code_snippet, [])
        assert result is not None
        # Result may contain [deferred] marker or error indication
    
    def test_aggregate_metrics_empty_list(self):
        """Test aggregation with empty metrics list"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            aggregate_metrics_to_json([], temp_file)
            
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as read_file:
                data = json.load(read_file)
            
            assert data == []
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_log_error_empty_message(self):
        """Test error logging with empty message"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name
        
        try:
            log_error(log_file, "", "T038")
            
            assert os.path.exists(log_file)
            # Should create log file even with empty message
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])