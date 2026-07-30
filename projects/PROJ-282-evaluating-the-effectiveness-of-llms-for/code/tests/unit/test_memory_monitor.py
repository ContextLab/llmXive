"""
Unit tests for the memory monitoring utilities.

Tests cover:
- Memory detection functions
- MemoryMonitor context manager behavior
- Batch size adjustment logic
- Memory constraint checking
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import gc

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.memory_monitor import (
    MemoryMonitor,
    get_available_ram_gb,
    get_current_memory_usage_gb,
    get_memory_usage_ratio,
    check_memory_constraint,
    force_gc,
    get_memory_snapshot,
    MEMORY_WARNING_THRESHOLD,
    MEMORY_CRITICAL_THRESHOLD
)


class TestMemoryDetection:
    """Tests for memory detection utility functions."""
    
    def test_get_available_ram_gb_positive(self):
        """Test that get_available_ram_gb returns a positive number."""
        ram = get_available_ram_gb()
        assert ram > 0, "RAM should be positive"
        assert isinstance(ram, float), "RAM should be a float"
    
    def test_get_available_ram_gb_reasonable_range(self):
        """Test that RAM is within a reasonable range (1GB to 1TB)."""
        ram = get_available_ram_gb()
        assert 1.0 <= ram <= 1024.0, f"RAM {ram}GB is outside reasonable range"
    
    def test_get_current_memory_usage_gb_positive(self):
        """Test that current memory usage is positive or zero."""
        usage = get_current_memory_usage_gb()
        assert usage >= 0, "Memory usage should be non-negative"
    
    def test_get_memory_usage_ratio_bounds(self):
        """Test that memory usage ratio is between 0 and 1."""
        ratio = get_memory_usage_ratio()
        assert 0.0 <= ratio <= 1.0, f"Ratio {ratio} should be between 0 and 1"


class TestMemoryConstraintChecking:
    """Tests for memory constraint checking logic."""
    
    @patch('src.utils.memory_monitor.get_memory_usage_ratio')
    def test_check_memory_constraint_below_threshold(self, mock_ratio):
        """Test that constraint check returns False when below threshold."""
        mock_ratio.return_value = 0.5  # 50% usage
        result = check_memory_constraint(threshold=0.85)
        assert result is False, "Should return False when below threshold"
    
    @patch('src.utils.memory_monitor.get_memory_usage_ratio')
    def test_check_memory_constraint_above_threshold(self, mock_ratio):
        """Test that constraint check returns True when above threshold."""
        mock_ratio.return_value = 0.90  # 90% usage
        result = check_memory_constraint(threshold=0.85)
        assert result is True, "Should return True when above threshold"
    
    @patch('src.utils.memory_monitor.get_memory_usage_ratio')
    def test_check_memory_constraint_at_threshold(self, mock_ratio):
        """Test behavior exactly at threshold."""
        mock_ratio.return_value = 0.85  # Exactly at threshold
        result = check_memory_constraint(threshold=0.85)
        # Should return True if ratio > threshold, False if equal
        # Our implementation uses >, so this should be False
        assert result is False, "Should return False when exactly at threshold"


class TestForceGC:
    """Tests for garbage collection forcing."""
    
    def test_force_gc_runs_without_error(self):
        """Test that force_gc executes without raising exceptions."""
        # Should not raise any exceptions
        force_gc()
        
        # Verify gc module was called (we can't easily verify it actually ran)
        # but we can at least ensure no errors occurred
        assert True


class TestMemoryMonitorContextManager:
    """Tests for the MemoryMonitor context manager."""
    
    def test_context_manager_enter_exit(self):
        """Test that context manager can enter and exit normally."""
        with MemoryMonitor() as monitor:
            assert monitor is not None
            assert monitor.batch_size == 32  # default
        # Should exit without error
    
    def test_context_manager_with_exception(self):
        """Test that context manager handles exceptions properly."""
        try:
            with MemoryMonitor() as monitor:
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        # Context manager should have cleaned up properly
    
    def test_memory_monitor_initialization(self):
        """Test MemoryMonitor initialization with custom parameters."""
        monitor = MemoryMonitor(
            threshold_warning=0.80,
            threshold_critical=0.90,
            batch_size=64,
            min_batch_size=8
        )
        assert monitor.threshold_warning == 0.80
        assert monitor.threshold_critical == 0.90
        assert monitor.batch_size == 64
        assert monitor.min_batch_size == 8
    
    def test_check_and_adjust_no_reduction_below_threshold(self):
        """Test that batch size is not reduced when memory is low."""
        with patch('src.utils.memory_monitor.get_memory_usage_ratio') as mock_ratio:
            mock_ratio.return_value = 0.50  # 50% usage
            
            monitor = MemoryMonitor(batch_size=32, min_batch_size=8)
            with monitor:
                new_batch = monitor.check_and_adjust()
                assert new_batch == 32, "Batch size should not be reduced at low usage"
    
    def test_check_and_adjust_reduction_at_critical(self):
        """Test that batch size is reduced when memory is critical."""
        with patch('src.utils.memory_monitor.get_memory_usage_ratio') as mock_ratio:
            mock_ratio.return_value = 0.96  # 96% usage (critical)
            
            monitor = MemoryMonitor(batch_size=32, min_batch_size=8)
            with monitor:
                new_batch = monitor.check_and_adjust()
                # Should be reduced by half: 32 -> 16
                assert new_batch == 16, "Batch size should be halved at critical usage"
    
    def test_check_and_adjust_respects_minimum(self):
        """Test that batch size doesn't go below minimum."""
        with patch('src.utils.memory_monitor.get_memory_usage_ratio') as mock_ratio:
            mock_ratio.return_value = 0.96  # Critical
            
            monitor = MemoryMonitor(batch_size=8, min_batch_size=8)
            with monitor:
                new_batch = monitor.check_and_adjust()
                # Should stay at minimum: 8 -> 8 (not 4)
                assert new_batch == 8, "Batch size should not go below minimum"
    
    def test_max_ratio_observed_tracking(self):
        """Test that max ratio is tracked correctly."""
        with patch('src.utils.memory_monitor.get_memory_usage_ratio') as mock_ratio:
            # First check: 60%
            mock_ratio.return_value = 0.60
            
            monitor = MemoryMonitor(batch_size=32)
            with monitor:
                monitor.check_and_adjust()
                assert monitor.max_ratio_observed == 0.60
                
                # Second check: 80%
                mock_ratio.return_value = 0.80
                monitor.check_and_adjust()
                assert monitor.max_ratio_observed == 0.80
                
                # Third check: 70% (should not update max)
                mock_ratio.return_value = 0.70
                monitor.check_and_adjust()
                assert monitor.max_ratio_observed == 0.80


class TestGetMemorySnapshot:
    """Tests for memory snapshot functionality."""
    
    def test_snapshot_contains_required_keys(self):
        """Test that snapshot contains all required fields."""
        snapshot = get_memory_snapshot()
        
        required_keys = ['timestamp', 'current_memory_gb', 'total_memory_gb', 
                       'usage_ratio', 'pid']
        for key in required_keys:
            assert key in snapshot, f"Snapshot missing required key: {key}"
    
    def test_snapshot_values_are_valid(self):
        """Test that snapshot values are of correct types and ranges."""
        snapshot = get_memory_snapshot()
        
        assert isinstance(snapshot['timestamp'], str)
        assert isinstance(snapshot['current_memory_gb'], float)
        assert isinstance(snapshot['total_memory_gb'], float)
        assert isinstance(snapshot['usage_ratio'], float)
        assert isinstance(snapshot['pid'], int)
        
        assert snapshot['current_memory_gb'] >= 0
        assert snapshot['total_memory_gb'] > 0
        assert 0.0 <= snapshot['usage_ratio'] <= 1.0


class TestMemoryMonitorLogging:
    """Tests for logging behavior in MemoryMonitor."""
    
    def test_context_manager_logs_start(self, caplog):
        """Test that entering context logs a start message."""
        with patch('src.utils.memory_monitor._get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            with MemoryMonitor():
                pass
            
            # Verify info was called with "Memory monitoring started"
            mock_logger_instance.info.assert_called()
    
    def test_context_manager_logs_end(self, caplog):
        """Test that exiting context logs completion."""
        with patch('src.utils.memory_monitor._get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            with MemoryMonitor():
                pass
            
            # Verify info was called for completion
            calls = [call[0][0] for call in mock_logger_instance.info.call_args_list]
            assert any("Memory monitoring completed" in str(call) for call in calls)


class TestIntegration:
    """Integration tests for memory monitoring workflow."""
    
    def test_full_workflow(self):
        """Test a complete monitoring workflow."""
        with patch('src.utils.memory_monitor.get_memory_usage_ratio') as mock_ratio:
            # Simulate increasing memory usage
            mock_ratio.side_effect = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
            
            monitor = MemoryMonitor(
                batch_size=32,
                min_batch_size=4,
                threshold_warning=0.85,
                threshold_critical=0.90
            )
            
            with monitor:
                # First few checks should not reduce batch
                batch1 = monitor.check_and_adjust()
                assert batch1 == 32
                
                # At 0.90 (critical), should reduce
                batch2 = monitor.check_and_adjust()
                assert batch2 == 16  # 32 / 2
                
                # At 0.95 (still critical), should reduce again
                batch3 = monitor.check_and_adjust()
                assert batch3 == 8  # 16 / 2
                
                # Should respect minimum
                batch4 = monitor.check_and_adjust()
                assert batch4 == 8  # Won't go below 4 yet
                
                # One more check
                batch5 = monitor.check_and_adjust()
                assert batch5 == 4  # 8 / 2
                
            # Verify max ratio was tracked
            assert monitor.max_ratio_observed == 0.95
    
    def test_gc_called_on_exit(self):
        """Test that garbage collection is called on context exit."""
        with patch('src.utils.memory_monitor.gc') as mock_gc:
            with MemoryMonitor():
                pass
            
            # Verify gc.collect was called (at least once, typically 3 times)
            assert mock_gc.collect.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])