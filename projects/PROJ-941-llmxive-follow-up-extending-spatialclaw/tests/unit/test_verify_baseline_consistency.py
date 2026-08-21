"""
Unit tests for verify_baseline_consistency.py (T060)
"""
import os
import sys
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.verify_baseline_consistency import (
    load_json_file,
    hash_result,
    verify_consistency,
    generate_report
)

class TestHashResult:
    """Tests for the hash_result function."""
    
    def test_hash_consistency(self):
        """Same result should produce same hash."""
        result = {
            'task_id': 'test-123',
            'success': True,
            'latency_ms': 100.5,
            'details': {'foo': 'bar'}
        }
        hash1 = hash_result(result)
        hash2 = hash_result(result)
        assert hash1 == hash2
    
    def test_hash_different_results(self):
        """Different results should produce different hashes."""
        result1 = {'task_id': 'test-1', 'success': True}
        result2 = {'task_id': 'test-2', 'success': False}
        assert hash_result(result1) != hash_result(result2)
    
    def test_hash_order_independence(self):
        """Hash should be independent of key order."""
        result1 = {'a': 1, 'b': 2}
        result2 = {'b': 2, 'a': 1}
        assert hash_result(result1) == hash_result(result2)

class TestVerifyConsistency:
    """Tests for the verify_consistency function."""
    
    def test_perfect_consistency(self):
        """Identical runs should be consistent."""
        run1 = [
            {'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'abc'},
            {'task_id': '2', 'success': False, 'latency_ms': 200.0, 'result_hash': 'def'}
        ]
        run2 = [
            {'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'abc'},
            {'task_id': '2', 'success': False, 'latency_ms': 200.0, 'result_hash': 'def'}
        ]
        result = verify_consistency(run1, run2)
        assert result['consistent'] is True
        assert result['inconsistency_count'] == 0
    
    def test_success_mismatch(self):
        """Different success status should be flagged."""
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'abc'}]
        run2 = [{'task_id': '1', 'success': False, 'latency_ms': 100.0, 'result_hash': 'def'}]
        result = verify_consistency(run1, run2)
        assert result['consistent'] is False
        assert result['inconsistency_count'] == 1
        assert any(i['issue'] == 'Success status mismatch' for i in result['inconsistencies'])
    
    def test_hash_mismatch(self):
        """Different result hashes should be flagged."""
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'abc'}]
        run2 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'xyz'}]
        result = verify_consistency(run1, run2)
        assert result['consistent'] is False
        assert any(i['issue'] == 'Result hash mismatch' for i in result['inconsistencies'])
    
    def test_latency_variance_tolerance(self):
        """Small latency differences (< 1ms) should be tolerated."""
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'abc'}]
        run2 = [{'task_id': '1', 'success': True, 'latency_ms': 100.5, 'result_hash': 'abc'}]
        result = verify_consistency(run1, run2)
        assert result['consistent'] is True  # 0.5ms < 1ms tolerance
    
    def test_large_latency_variance(self):
        """Large latency differences (> 1ms) should be flagged."""
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'abc'}]
        run2 = [{'task_id': '1', 'success': True, 'latency_ms': 105.0, 'result_hash': 'abc'}]
        result = verify_consistency(run1, run2)
        assert result['consistent'] is False
        assert any(i['issue'] == 'Latency variance exceeds threshold' for i in result['inconsistencies'])
    
    def test_different_counts(self):
        """Different number of results should fail."""
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0, 'result_hash': 'abc'}]
        run2 = []
        result = verify_consistency(run1, run2)
        assert result['consistent'] is False
        assert 'Different number of results' in result['reason']

class TestGenerateReport:
    """Tests for the generate_report function."""
    
    def test_report_contains_summary(self):
        """Report should contain summary section."""
        consistency_results = {
            'consistent': True,
            'total_tasks': 5,
            'inconsistency_count': 0,
            'average_latency_variance_ms': 0.1,
            'max_variance_ms': 0.3
        }
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0}]
        run2 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0}]
        task_ids = ['1']
        
        report = generate_report(consistency_results, run1, run2, task_ids)
        assert "Baseline Determinism Verification Report" in report
        assert "Summary" in report
        assert "Consistency Status" in report
    
    def test_report_pass_format(self):
        """Passing report should show checkmark."""
        consistency_results = {
            'consistent': True,
            'total_tasks': 1,
            'inconsistency_count': 0,
            'average_latency_variance_ms': 0.0,
            'max_variance_ms': 0.0
        }
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0}]
        run2 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0}]
        task_ids = ['1']
        
        report = generate_report(consistency_results, run1, run2, task_ids)
        assert "✅ PASS" in report
        assert "demonstrates **deterministic behavior**" in report
    
    def test_report_fail_format(self):
        """Failing report should show warning."""
        consistency_results = {
            'consistent': False,
            'total_tasks': 1,
            'inconsistency_count': 1,
            'average_latency_variance_ms': 5.0,
            'max_variance_ms': 5.0,
            'inconsistencies': [{'task_id': '1', 'issue': 'Test issue'}]
        }
        run1 = [{'task_id': '1', 'success': True, 'latency_ms': 100.0}]
        run2 = [{'task_id': '1', 'success': True, 'latency_ms': 105.0}]
        task_ids = ['1']
        
        report = generate_report(consistency_results, run1, run2, task_ids)
        assert "❌ FAIL" in report
        assert "NOT fully deterministic" in report
        assert "Test issue" in report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])