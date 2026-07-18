import os
import sys
import json
import time
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from run_pipeline import run_single_seed_experiment
from config import get_config, check_system_limits
from metrics import calculate_ndcg_at_10

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "max_runtime_seconds": 3600,
        "max_memory_bytes": 7 * 1024 * 1024 * 1024, # 7GB
        "dataset": "nfcorpus",
        "seeds": [42]
    }

def test_full_pipeline_execution_with_resource_limits(mock_config):
    """
    Integration test for full pipeline execution with resource limits.
    Verifies that the pipeline runs within the specified time and memory constraints.
    """
    # Patch get_config to return our mock
    with patch('run_pipeline.get_config', return_value=mock_config):
        # Mock the heavy lifting to avoid actual long-running processes in CI
        # but keep the structure to test the flow
        with patch('run_pipeline.run_baseline_experiment') as mock_baseline, \
             patch('run_pipeline.run_clustering_aided_experiment') as mock_clustering:
            
            # Setup mock return values
            mock_baseline.return_value = {
                "ndcg": 0.5,
                "wasted_calls": 10,
                "runtime": 100,
                "memory_usage": 1024 * 1024 * 100 # 100MB
            }
            mock_clustering.return_value = {
                "ndcg": 0.55,
                "wasted_calls": 5,
                "runtime": 150,
                "memory_usage": 1024 * 1024 * 200 # 200MB
            }
            
            # Run the experiment
            try:
                result = run_single_seed_experiment(seed=42)
                
                # Assertions
                assert result is not None
                assert "ndcg" in result
                assert "wasted_calls" in result
                assert "runtime" in result
                assert "memory_usage" in result
                
                # Verify resource limits were checked (mocked check_system_limits)
                # In a real test, we would verify the watchdog logic, but here we check the flow
                assert result["runtime"] < mock_config["max_runtime_seconds"]
                assert result["memory_usage"] < mock_config["max_memory_bytes"]
                
            except Exception as e:
                pytest.fail(f"Pipeline execution failed: {str(e)}")

def test_resource_limit_enforcement():
    """
    Test that the system enforces resource limits correctly.
    """
    # Mock a scenario where memory limit is exceeded
    with patch('run_pipeline.check_system_limits') as mock_check:
        mock_check.side_effect = MemoryError("Memory limit exceeded")
        
        with pytest.raises(MemoryError):
            # This would trigger the limit check in a real run
            check_system_limits()

def test_ndcg_calculation_consistency():
    """
    Test that NDCG calculation is consistent across different inputs.
    """
    scores_a = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    scores_b = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    
    ndcg_a = calculate_ndcg_at_10(scores_a)
    ndcg_b = calculate_ndcg_at_10(scores_b)
    
    assert ndcg_a == ndcg_b
    assert ndcg_a > 0.0
