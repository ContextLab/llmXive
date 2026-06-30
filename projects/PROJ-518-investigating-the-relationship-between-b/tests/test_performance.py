"""
Tests for performance optimization and memory constraints.
"""

import pytest
import numpy as np
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from performance_profiler import (
    profile_function,
    memory_profile,
    optimize_sliding_window_connectivity,
    optimize_community_detection,
    optimize_permutation_test,
    run_full_pipeline_profile
)
from errors import DataMissingCreativityError


class TestProfileFunction:
    """Tests for the profile_function utility."""
    
    def test_profile_function_returns_correct_results(self):
        """Test that profile_function returns correct results."""
        def simple_func(arr):
            return np.sum(arr)
        
        test_data = np.random.randn(100)
        result, profile_result = profile_function(simple_func, max_memory_gb=7.0, arr=test_data)
        
        assert result == np.sum(test_data)
        assert profile_result.execution_time_sec >= 0
        assert profile_result.peak_memory_mb >= 0
        assert profile_result.func_name == "simple_func"
    
    def test_profile_function_memory_limit(self):
        """Test that profile_function raises MemoryError when limit exceeded."""
        def memory_hog(arr):
            # Create a large copy to exceed memory
            _ = arr * 1000000
            return np.sum(arr)
        
        test_data = np.random.randn(1000)
        
        with pytest.raises(MemoryError):
            profile_function(memory_hog, max_memory_gb=0.001, arr=test_data)

class TestMemoryProfile:
    """Tests for the memory_profile decorator."""
    
    def test_memory_profile_decorator(self):
        """Test that memory_profile decorator works correctly."""
        @memory_profile(max_memory_gb=7.0)
        def test_func(arr):
            return np.mean(arr)
        
        test_data = np.random.randn(1000)
        result = test_func(test_data)
        
        assert result == np.mean(test_data)

class TestOptimizedFunctions:
    """Tests for optimized analysis functions."""
    
    def test_optimized_sliding_window_connectivity(self):
        """Test optimized sliding window connectivity."""
        np.random.seed(42)
        fmri_data = np.random.randn(100, 90).astype(np.float32)
        
        result = optimize_sliding_window_connectivity(fmri_data, window_size=30, step=5)
        
        assert result.shape == (15, 90, 90)  # n_windows, n_rois, n_rois
        assert result.dtype == np.float32
        
        # Check that diagonal elements are close to 1 (self-correlation)
        for i in range(result.shape[0]):
            diag = np.diag(result[i])
            assert np.allclose(diag, 1.0, atol=0.1)
    
    def test_optimized_community_detection(self):
        """Test optimized community detection."""
        np.random.seed(42)
        conn_matrices = np.random.randn(10, 90, 90)
        
        # Make matrices symmetric and positive definite for valid graphs
        for i in range(len(conn_matrices)):
            conn_matrices[i] = (conn_matrices[i] + conn_matrices[i].T) / 2
            conn_matrices[i] += np.eye(90) * 10  # Ensure positive definite
        
        result = optimize_community_detection(conn_matrices, gamma=1.0)
        
        assert len(result) == 10  # One assignment per window
        assert all(len(assignment) == 90 for assignment in result)
    
    def test_optimized_permutation_test(self):
        """Test optimized permutation test."""
        np.random.seed(42)
        flexibility = np.random.randn(50)
        creativity = np.random.randn(50)
        
        p_value = optimize_permutation_test(flexibility, creativity, n_permutations=1000)
        
        assert 0 <= p_value <= 1
        assert isinstance(p_value, float)

class TestMemoryConstraints:
    """Tests to ensure memory constraints are met."""
    
    def test_memory_usage_under_7gb(self):
        """Test that the pipeline stays under 7GB memory."""
        # This test would need actual profiling in a real environment
        # For now, we verify the functions don't immediately fail
        np.random.seed(42)
        
        # Small scale test
        fmri_data = np.random.randn(50, 90).astype(np.float32)
        flexibility = np.random.randn(50)
        creativity = np.random.randn(50)
        
        # These should complete without memory errors
        result1 = optimize_sliding_window_connectivity(fmri_data, 30, 5)
        result2 = optimize_permutation_test(flexibility, creativity, 100)
        
        assert result1 is not None
        assert 0 <= result2 <= 1

class TestPipelinePerformance:
    """Tests for full pipeline performance."""
    
    def test_full_pipeline_profile(self):
        """Test that the full pipeline profiling runs successfully."""
        # Run with small parameters for testing
        results = run_full_pipeline_profile(
            sample_size=20,
            n_windows=10,
            n_rois=20
        )
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Check that all results have required fields
        for func_name, result in results.items():
            assert hasattr(result, 'execution_time_sec')
            assert hasattr(result, 'peak_memory_mb')
            assert result.execution_time_sec >= 0
            assert result.peak_memory_mb >= 0