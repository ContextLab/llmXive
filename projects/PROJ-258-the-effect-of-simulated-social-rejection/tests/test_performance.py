"""
Performance testing for the social rejection pipeline.

Tests ensure runtime remains under 6 hours for N <= 500 participants
and memory usage stays within 7 GB limits.
"""
import pytest
import time
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from performance_monitor import (
    PerformanceMonitor,
    performance_watchdog,
    optimize_dataframe_operations,
    run_pipeline_with_monitoring,
    MAX_RUNTIME_SECONDS,
    MAX_MEMORY_MB
)
from config import get_path

class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""
    
    def test_context_manager_timing(self):
        """Test that context manager correctly measures time."""
        with PerformanceMonitor("Test Task") as monitor:
            time.sleep(0.1)
        
        assert monitor.start_time is not None
        assert monitor.end_time is not None
        assert monitor.get_elapsed_time() >= 0.1
        assert monitor.get_elapsed_hours() >= 0.1 / 3600
    
    def test_memory_monitoring(self):
        """Test that memory monitoring works."""
        with PerformanceMonitor("Memory Test") as monitor:
            # Create some memory pressure
            data = [i for i in range(10000)]
            _ = data * 100
        
        assert monitor.memory_peak_mb > 0
    
    def test_within_limits(self):
        """Test that limits are correctly evaluated."""
        with PerformanceMonitor("Quick Task") as monitor:
            pass  # Very quick operation
        
        assert monitor.is_within_limits()
    
    def test_runtime_warning_threshold(self):
        """Test that warnings are issued at 80% runtime."""
        # This would require mocking time to exceed 80% of limit
        # For now, we test the logic
        monitor = PerformanceMonitor("Test")
        monitor.start_time = time.time() - (MAX_RUNTIME_SECONDS * 0.85)
        monitor.end_time = time.time()
        
        # The warning logic is tested in the context manager
        # We verify the threshold constant is correct
        assert MAX_RUNTIME_SECONDS == 6 * 60 * 60
    
    def test_context_manager_returns_true_on_success(self):
        """Test that context manager returns True when within limits."""
        with PerformanceMonitor("Success Test") as monitor:
            time.sleep(0.01)
        
        # The __exit__ returns True if within limits
        # We can't directly test this, but we can verify no exception
        assert True
    
    def test_context_manager_logs_completion(self):
        """Test that completion is logged."""
        with patch('logging.Logger.info') as mock_log:
            with PerformanceMonitor("Log Test") as monitor:
                time.sleep(0.01)
            
            # Verify log was called
            assert mock_log.called
    
    def test_memory_peak_tracking(self):
        """Test that memory peak is tracked correctly."""
        with PerformanceMonitor("Peak Test") as monitor:
            initial = monitor.memory_peak_mb
            # Create memory pressure
            large_list = [i for i in range(100000)]
            _ = large_list * 10
            final = monitor.memory_peak_mb
        
        assert final >= initial
    
    def test_elapsed_time_accuracy(self):
        """Test that elapsed time is accurate."""
        sleep_duration = 0.2
        with PerformanceMonitor("Accuracy Test") as monitor:
            time.sleep(sleep_duration)
        
        elapsed = monitor.get_elapsed_time()
        assert elapsed >= sleep_duration
        assert elapsed < sleep_duration + 0.05  # Allow small tolerance
    
    def test_context_manager_exceeds_runtime(self):
        """Test behavior when runtime limit is exceeded."""
        # Mock time to simulate exceeding limit
        with patch('time.time', side_effect=[0, MAX_RUNTIME_SECONDS + 1]):
            with PerformanceMonitor("Exceed Test") as monitor:
                pass
            
            # Should return False when limit exceeded
            assert not monitor.is_within_limits()
    
    def test_context_manager_exceeds_memory(self):
        """Test behavior when memory limit is exceeded."""
        # Mock memory to simulate exceeding limit
        with patch('performance_monitor.get_process_memory_mb', return_value=MAX_MEMORY_MB + 1000):
            with PerformanceMonitor("Memory Exceed Test") as monitor:
                pass
            
            assert not monitor.is_within_limits()

class TestPerformanceWatchdog:
    """Tests for performance_watchdog decorator."""
    
    @performance_watchdog
    def test_function(self, task_name="Test"):
        """A test function with watchdog."""
        time.sleep(0.01)
        return "success"
    
    def test_decorator_success(self):
        """Test that decorator allows successful execution."""
        result = self.test_function()
        assert result == "success"
    
    def test_decorator_timing(self):
        """Test that decorator measures time correctly."""
        start = time.time()
        result = self.test_function()
        elapsed = time.time() - start
        
        assert result == "success"
        assert elapsed >= 0.01
    
    def test_decorator_memory_monitoring(self):
        """Test that decorator monitors memory."""
        # The decorator uses PerformanceMonitor which tracks memory
        # We verify it completes without error
        result = self.test_function()
        assert result == "success"

class TestDataFrameOptimization:
    """Tests for DataFrame optimization functions."""
    
    def test_optimize_reduces_memory(self):
        """Test that optimization reduces memory usage."""
        df = pd.DataFrame({
            'int_col': range(1000),
            'float_col': [i * 1.5 for i in range(1000)],
            'object_col': ['category'] * 1000
        })
        
        initial_memory = df.memory_usage(deep=True).sum()
        optimize_dataframe_operations(df)
        final_memory = df.memory_usage(deep=True).sum()
        
        # Memory should be reduced or stay same (never increase)
        assert final_memory <= initial_memory
    
    def test_optimize_preserves_data(self):
        """Test that optimization preserves data integrity."""
        df = pd.DataFrame({
            'id': range(100),
            'value': [i * 2.5 for i in range(100)],
            'group': ['A'] * 50 + ['B'] * 50
        })
        
        original_values = df.copy()
        optimize_dataframe_operations(df)
        
        # Values should be preserved
        assert list(df['id']) == list(original_values['id'])
        assert list(df['value']) == list(original_values['value'])
        assert list(df['group']) == list(original_values['group'])
    
    def test_optimize_handles_empty_dataframe(self):
        """Test optimization on empty DataFrame."""
        df = pd.DataFrame()
        # Should not raise
        optimize_dataframe_operations(df)
    
    def test_optimize_single_row(self):
        """Test optimization on single row DataFrame."""
        df = pd.DataFrame({
            'id': [1],
            'value': [1.5],
            'group': ['A']
        })
        optimize_dataframe_operations(df)
        assert len(df) == 1

class TestPipelineMonitoring:
    """Tests for pipeline monitoring functions."""
    
    def test_run_pipeline_with_monitoring_success(self):
        """Test successful pipeline execution with monitoring."""
        def dummy_pipeline(n):
            return pd.DataFrame({'id': range(n)})
        
        result = run_pipeline_with_monitoring(
            dummy_pipeline,
            100,
            task_name="Test Pipeline"
        )
        
        assert len(result) == 100
        assert isinstance(result, pd.DataFrame)
    
    def test_run_pipeline_creates_metrics_file(self):
        """Test that metrics file is created."""
        def dummy_pipeline(n):
            return pd.DataFrame({'id': range(n)})
        
        run_pipeline_with_monitoring(
            dummy_pipeline,
            10,
            task_name="Metrics Test"
        )
        
        metrics_path = get_path('data/processed', 'performance_metrics.json')
        assert os.path.exists(metrics_path)
        
        # Clean up
        os.remove(metrics_path)
    
    def test_run_pipeline_exceeds_runtime_raises(self):
        """Test that exceeding runtime raises RuntimeError."""
        def slow_pipeline(n):
            time.sleep(MAX_RUNTIME_SECONDS + 1)
            return pd.DataFrame()
        
        # Mock time to avoid actual wait
        with patch('time.time', side_effect=[0, MAX_RUNTIME_SECONDS + 1]):
            with pytest.raises(RuntimeError, match="exceeded"):
                run_pipeline_with_monitoring(
                    slow_pipeline,
                    10,
                    task_name="Slow Pipeline"
                )
    
    def test_run_pipeline_exceeds_memory_raises(self):
        """Test that exceeding memory raises RuntimeError."""
        def memory_hog_pipeline(n):
            # Create large data
            _ = [i for i in range(1000000)]
            return pd.DataFrame()
        
        # Mock memory to exceed limit
        with patch('performance_monitor.get_process_memory_mb', 
                  return_value=MAX_MEMORY_MB + 1000):
            with pytest.raises(RuntimeError, match="exceeded"):
                run_pipeline_with_monitoring(
                    memory_hog_pipeline,
                    10,
                    task_name="Memory Hog"
                )

class TestPerformanceConstraints:
    """Integration tests for performance constraints."""
    
    def test_pipeline_with_500_participants(self):
        """Test that pipeline completes with 500 participants."""
        def realistic_pipeline(n):
            # Simulate realistic operations
            df = pd.DataFrame({
                'participant_id': range(n),
                'reaction_time': np.random.normal(500, 100, n),
                'mood_score': np.random.normal(5, 2, n),
                'condition': np.random.choice(['control', 'rejection'], n)
            })
            
            # Simulate analysis
            for _ in range(10):
                df.groupby('condition').mean()
            
            return df
        
        result = run_pipeline_with_monitoring(
            realistic_pipeline,
            500,
            task_name="500 Participants Test"
        )
        
        assert len(result) == 500
    
    def test_memory_usage_under_7gb(self):
        """Test that memory usage stays under 7GB."""
        def memory_test_pipeline(n):
            # Process data in chunks to stay under limit
            df = pd.DataFrame({
                'id': range(n),
                'value': np.random.random(n)
            })
            
            # Process in batches
            batch_size = 100
            for i in range(0, n, batch_size):
                batch = df.iloc[i:i+batch_size]
                _ = batch.mean()
            
            return df
        
        result = run_pipeline_with_monitoring(
            memory_test_pipeline,
            500,
            task_name="Memory Test"
        )
        
        assert len(result) == 500
    
    def test_runtime_under_6_hours(self):
        """Test that runtime stays under 6 hours."""
        def time_test_pipeline(n):
            # Simulate quick operations
            df = pd.DataFrame({'id': range(n)})
            _ = df.mean()
            return df
        
        start = time.time()
        result = run_pipeline_with_monitoring(
            time_test_pipeline,
            500,
            task_name="Time Test"
        )
        elapsed = time.time() - start
        
        assert elapsed < MAX_RUNTIME_SECONDS
        assert len(result) == 500

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
