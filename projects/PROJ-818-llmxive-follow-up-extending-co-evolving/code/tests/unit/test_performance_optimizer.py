"""
Unit tests for performance optimization utilities.
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.performance_optimizer import (
    PerformanceConfig,
    RunBatchExecutor,
    ensure_ci_completeness,
    AVAILABLE_CORES
)

class TestPerformanceConfig:
    """Tests for PerformanceConfig class."""
    
    def test_get_optimal_config_defaults(self):
        """Test default configuration generation."""
        config = PerformanceConfig.get_optimal_config()
        
        assert config.max_workers >= 1
        assert config.adaptive_batch_size >= 1
        assert config.min_runs_for_early_stop >= 20
        assert config.early_stopping_threshold == 0.01
        assert config.use_caching is True
        assert config.reduced_precision is True
    
    def test_get_optimal_config_with_different_targets(self):
        """Test configuration with different target run counts."""
        config_30 = PerformanceConfig.get_optimal_config(target_total_runs=30)
        config_60 = PerformanceConfig.get_optimal_config(target_total_runs=60)
        
        # Both should have valid configurations
        assert config_30.max_workers > 0
        assert config_60.max_workers > 0
        
        # Higher target might adjust batch sizes
        assert config_30.adaptive_batch_size > 0
        assert config_60.adaptive_batch_size > 0

class TestRunBatchExecutor:
    """Tests for RunBatchExecutor class."""
    
    def test_executor_initialization(self):
        """Test executor initialization with config."""
        config = PerformanceConfig.get_optimal_config()
        executor = RunBatchExecutor(config)
        
        assert executor.config == config
        assert executor.results_cache == {}
    
    def test_early_stopping_check_insufficient_runs(self):
        """Test early stopping returns False when runs are insufficient."""
        config = PerformanceConfig.get_optimal_config()
        executor = RunBatchExecutor(config)
        
        results = {
            'coevolving': [{'id': 1}, {'id': 2}],  # Only 2 runs
            'mixed': [{'id': 1}],
            'sequential': [{'id': 1}, {'id': 2}, {'id': 3}]
        }
        
        condition_counts = {
            'coevolving': 30,
            'mixed': 30,
            'sequential': 30
        }
        
        should_stop, reason = executor.check_early_stopping(results, condition_counts)
        
        assert should_stop is False
        assert "runs" in reason.lower()
    
    def test_early_stopping_check_sufficient_runs(self):
        """Test early stopping returns True when runs are sufficient."""
        config = PerformanceConfig.get_optimal_config()
        executor = RunBatchExecutor(config)
        
        # Create mock results with enough runs
        sufficient_results = {
            'coevolving': [{'id': i} for i in range(25)],
            'mixed': [{'id': i} for i in range(25)],
            'sequential': [{'id': i} for i in range(25)]
        }
        
        condition_counts = {
            'coevolving': 30,
            'mixed': 30,
            'sequential': 30
        }
        
        should_stop, reason = executor.check_early_stopping(sufficient_results, condition_counts)
        
        assert should_stop is True
        assert "sufficient" in reason.lower()

class TestEnsureCiCompleteness:
    """Tests for ensure_ci_completeness function."""
    
    def test_feasible_scenario(self):
        """Test scenario where CI completion is feasible."""
        result = ensure_ci_completeness(
            target_total_runs=30,
            ci_time_limit_seconds=300,
            estimated_run_time_seconds=5.0
        )
        
        assert 'feasible' in result
        assert 'estimated_time_seconds' in result
        assert 'recommendations' in result
        assert result['available_cores'] == AVAILABLE_CORES
    
    def test_infeasible_scenario_recommendations(self):
        """Test scenario where CI completion is not feasible."""
        # Simulate a slow run time
        result = ensure_ci_completeness(
            target_total_runs=100,
            ci_time_limit_seconds=120,
            estimated_run_time_seconds=10.0
        )
        
        assert result['feasible'] is False
        assert len(result['recommendations']) > 0
    
    def test_available_cores_calculation(self):
        """Test that available cores is calculated correctly."""
        result = ensure_ci_completeness(
            target_total_runs=30,
            ci_time_limit_seconds=300
        )
        
        # Should be at least 1 core available
        assert result['available_cores'] >= 1

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_config_serialization(temp_data_dir):
    """Test that performance config can be serialized to JSON."""
    config = PerformanceConfig.get_optimal_config()
    config_dict = {
        "max_workers": config.max_workers,
        "early_stopping_threshold": config.early_stopping_threshold,
        "min_runs_for_early_stop": config.min_runs_for_early_stop,
        "adaptive_batch_size": config.adaptive_batch_size,
        "use_caching": config.use_caching,
        "reduced_precision": config.reduced_precision
    }
    
    output_file = temp_data_dir / "config.json"
    with open(output_file, 'w') as f:
        json.dump(config_dict, f)
    
    # Verify it can be loaded back
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == config_dict