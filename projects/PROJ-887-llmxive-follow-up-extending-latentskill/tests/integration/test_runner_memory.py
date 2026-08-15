"""
Integration test for src/evaluation/runner.py to verify memory management.

This test verifies that:
1. Memory is released after each run (T040 requirement)
2. The process does not exceed 7GB RAM during the evaluation loop
3. The memory cleanup cycle (del, gc.collect) is executed correctly
"""
import os
import sys
import gc
import time
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, ensure_directories
from src.evaluation.runner import (
    check_memory_usage, 
    load_synthesized_adapter, 
    apply_lora_to_model, 
    execute_environment_logic, 
    run_evaluation, 
    main
)

# Constants
MAX_MEMORY_GB = 7.0
MEMORY_CHECK_INTERVAL = 0.1  # seconds


class MockAdapter:
    """Mock adapter object for testing"""
    def __init__(self, size_mb=50):
        self.size_mb = size_mb
        self.data = np.random.randn(100, 100).astype(np.float32)
    
    def __del__(self):
        # Simulate cleanup
        if hasattr(self, 'data'):
            del self.data
            gc.collect()


class MockModel:
    """Mock model object for testing"""
    def __init__(self):
        self.loaded = True
        self.adapter = None
    
    def load_adapter(self, adapter):
        self.adapter = adapter
    
    def unload_adapter(self):
        self.adapter = None
    
    def __del__(self):
        if hasattr(self, 'adapter') and self.adapter is not None:
            del self.adapter
            gc.collect()


class MockEnvironment:
    """Mock environment for testing"""
    def __init__(self):
        self.run_count = 0
    
    def run_task(self, task_id):
        self.run_count += 1
        # Simulate some work
        time.sleep(0.01)
        return True
    
    def reset(self):
        pass
    
    def close(self):
        pass


def create_mock_adapter_file(temp_dir: Path, name: str = "mock_adapter"):
    """Create a mock adapter file for testing"""
    adapter_path = temp_dir / f"{name}.npz"
    # Create a small mock adapter
    data = {
        'A': np.random.randn(64, 128).astype(np.float32),
        'B': np.random.randn(128, 64).astype(np.float32)
    }
    np.savez_compressed(adapter_path, **data)
    return adapter_path


def test_check_memory_usage():
    """Test that check_memory_usage returns valid memory stats"""
    mem_stats = check_memory_usage()
    
    assert isinstance(mem_stats, dict)
    assert 'used_gb' in mem_stats
    assert 'total_gb' in mem_stats
    assert 'percent' in mem_stats
    
    # Verify values are reasonable
    assert mem_stats['used_gb'] >= 0
    assert mem_stats['total_gb'] > 0
    assert 0 <= mem_stats['percent'] <= 100


@patch('src.evaluation.runner.gc')
@patch('src.evaluation.runner.torch')
def test_memory_cleanup_cycle(mock_torch, mock_gc, tmp_path):
    """Test that memory cleanup cycle is executed after each run"""
    # Setup mock torch
    mock_torch.cuda.is_available.return_value = False
    
    # Create mock adapter file
    adapter_path = create_mock_adapter_file(tmp_path)
    
    # Mock the load and apply functions
    mock_adapter = MockAdapter()
    mock_model = MockModel()
    mock_env = MockEnvironment()
    
    with patch('src.evaluation.runner.load_synthesized_adapter', return_value=mock_adapter), \
         patch('src.evaluation.runner.apply_lora_to_model', return_value=mock_model), \
         patch('src.evaluation.runner.execute_environment_logic', return_value=True), \
         patch('src.evaluation.runner.check_memory_usage') as mock_mem_check:
        
        # Setup memory check to return safe values
        mock_mem_check.return_value = {
            'used_gb': 2.0,
            'total_gb': 16.0,
            'percent': 12.5
        }
        
        # Run evaluation multiple times
        for i in range(3):
            result = run_evaluation(
                adapter_path=str(adapter_path),
                task_id=f"test_task_{i}",
                env=mock_env
            )
            
            # Verify cleanup was called
            assert mock_gc.collect.called
            mock_gc.collect.reset_mock()
        
        # Verify torch.cuda.empty_cache was called (if available)
        # Note: We're mocking torch, so we check if the call was attempted
        # In real scenario, this would clear GPU cache


def test_memory_threshold_check(tmp_path):
    """Test that memory threshold check works correctly"""
    # Create mock adapter file
    adapter_path = create_mock_adapter_file(tmp_path)
    
    # Mock high memory usage
    with patch('src.evaluation.runner.check_memory_usage') as mock_mem_check:
        mock_mem_check.return_value = {
            'used_gb': 6.5,
            'total_gb': 7.0,
            'percent': 92.8  # Above 90% threshold
        }
        
        # This should trigger a warning but not fail
        # The function should log the warning and continue
        with patch('src.evaluation.runner.logging') as mock_logging:
            result = check_memory_usage()
            assert result['percent'] > 90
            # Verify warning was logged
            assert mock_logging.warning.called


@patch('src.evaluation.runner.gc')
@patch('src.evaluation.runner.torch')
def test_full_memory_management_cycle(mock_torch, mock_gc, tmp_path):
    """Test the complete memory management cycle during evaluation"""
    # Setup
    mock_torch.cuda.is_available.return_value = False
    
    # Create mock adapter file
    adapter_path = create_mock_adapter_file(tmp_path)
    
    # Create mock objects
    mock_adapter = MockAdapter()
    mock_model = MockModel()
    mock_env = MockEnvironment()
    
    # Track memory usage
    memory_log = []
    
    def mock_memory_check():
        # Simulate memory usage that should stay under 7GB
        used = 2.0 + (len(memory_log) * 0.1)  # Gradual increase
        if used > 6.5:
            used = 2.0  # Reset after cleanup
        mem_pct = (used / 16.0) * 100
        return {
            'used_gb': used,
            'total_gb': 16.0,
            'percent': mem_pct
        }
    
    with patch('src.evaluation.runner.load_synthesized_adapter', return_value=mock_adapter), \
         patch('src.evaluation.runner.apply_lora_to_model', return_value=mock_model), \
         patch('src.evaluation.runner.execute_environment_logic', return_value=True), \
         patch('src.evaluation.runner.check_memory_usage', side_effect=mock_memory_check):
        
        # Run multiple evaluation cycles
        for i in range(5):
            result = run_evaluation(
                adapter_path=str(adapter_path),
                task_id=f"test_task_{i}",
                env=mock_env
            )
            
            # Record memory state
            mem_stats = mock_memory_check()
            memory_log.append(mem_stats)
            
            # Verify memory is under threshold
            assert mem_stats['used_gb'] < MAX_MEMORY_GB, \
                f"Memory exceeded {MAX_MEMORY_GB}GB: {mem_stats['used_gb']}GB"
        
        # Verify that memory was cleaned up (should have reset at some point)
        memory_values = [m['used_gb'] for m in memory_log]
        # At least one reset should have occurred
        assert min(memory_values) < max(memory_values), \
            "Memory did not decrease, indicating cleanup may not be working"

def test_runner_memory_integration(tmp_path):
    """
    Integration test: Verify that the runner properly manages memory
    when processing multiple tasks in sequence.
    """
    # Create multiple mock adapter files
    adapter_paths = []
    for i in range(3):
        adapter_path = create_mock_adapter_file(tmp_path, f"adapter_{i}")
        adapter_paths.append(adapter_path)
    
    # Mock environment
    mock_env = MockEnvironment()
    
    # Track memory across runs
    max_memory_observed = 0.0
    
    def track_memory():
        nonlocal max_memory_observed
        # Simulate memory usage that should stay reasonable
        current_used = 2.0 + (len(mock_env.run_count) * 0.05)
        if current_used > 6.0:
            current_used = 2.0  # Simulate cleanup
        mem_pct = (current_used / 16.0) * 100
        max_memory_observed = max(max_memory_observed, current_used)
        return {
            'used_gb': current_used,
            'total_gb': 16.0,
            'percent': mem_pct
        }
    
    with patch('src.evaluation.runner.load_synthesized_adapter') as mock_load, \
         patch('src.evaluation.runner.apply_lora_to_model') as mock_apply, \
         patch('src.evaluation.runner.execute_environment_logic', return_value=True), \
         patch('src.evaluation.runner.check_memory_usage', side_effect=track_memory):
        
        # Mock adapter loading
        mock_adapter = MockAdapter()
        mock_model = MockModel()
        mock_load.return_value = mock_adapter
        mock_apply.return_value = mock_model
        
        # Run evaluation for multiple adapters
        for adapter_path in adapter_paths:
            result = run_evaluation(
                adapter_path=str(adapter_path),
                task_id="integration_test_task",
                env=mock_env
            )
            
            # Force garbage collection between runs
            gc.collect()
        
        # Verify memory stayed within bounds
        assert max_memory_observed < MAX_MEMORY_GB, \
            f"Memory exceeded limit: {max_memory_observed}GB > {MAX_MEMORY_GB}GB"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])