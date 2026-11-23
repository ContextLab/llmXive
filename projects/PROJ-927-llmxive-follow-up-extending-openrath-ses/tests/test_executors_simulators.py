"""
Tests for executors and simulators base classes.

These tests verify that the base classes are correctly defined and
provide the expected interfaces for downstream implementations.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.executors import BaseExecutor, ExecutionResult
from code.simulators import CorruptionInjector, NetworkJitterSimulator


class TestExecutionResult:
    """Tests for the ExecutionResult dataclass."""
    
    def test_default_initialization(self):
        """Test that ExecutionResult initializes with defaults."""
        result = ExecutionResult(
            workflow_id="test-123",
            architecture="test",
            success=True,
            final_state={"key": "value"},
            latency_ms=100.0
        )
        
        assert result.workflow_id == "test-123"
        assert result.architecture == "test"
        assert result.success is True
        assert result.final_state == {"key": "value"}
        assert result.latency_ms == 100.0
        assert result.error_message is None
        assert result.corrupted_entries == []
        
    def test_custom_corrupted_entries(self):
        """Test that corrupted_entries can be provided."""
        result = ExecutionResult(
            workflow_id="test-123",
            architecture="test",
            success=False,
            final_state=None,
            latency_ms=0.0,
            error_message="Failed",
            corrupted_entries=["key1", "key2"]
        )
        
        assert result.corrupted_entries == ["key1", "key2"]
        
class TestCorruptionInjector:
    """Tests for the CorruptionInjector class."""
    
    def test_no_corruption_when_rate_is_zero(self):
        """Test that no corruption occurs when rate is 0."""
        injector = CorruptionInjector(corruption_rate=0.0, seed=42)
        data = {"key1": "value1", "key2": 123}
        
        corrupted_data, was_corrupted = injector.inject_corruption(data, "test-1")
        
        assert was_corrupted is False
        assert corrupted_data == data
        assert len(injector.corruption_log) == 0
        
    def test_corruption_occurs_with_high_rate(self):
        """Test that corruption occurs when rate is 1.0."""
        injector = CorruptionInjector(corruption_rate=1.0, seed=42)
        data = {"key1": "value1", "key2": 123}
        
        # Run multiple times to ensure at least one corruption
        was_corrupted = False
        for _ in range(10):
            _, result = injector.inject_corruption(data.copy(), "test-2")
            if result:
                was_corrupted = True
                break
                
        assert was_corrupted is True
        assert len(injector.corruption_log) > 0
        
    def test_corruption_types(self):
        """Test that different corruption types are applied."""
        injector = CorruptionInjector(corruption_rate=1.0, seed=42)
        
        # Test delete
        data = {"key1": "value1", "key2": "value2"}
        corrupted, _ = injector.inject_corruption(data, "test-3")
        assert "key1" not in corrupted or "key2" not in corrupted
        
    def test_corruption_map_generation(self):
        """Test that corruption map is generated correctly."""
        injector = CorruptionInjector(corruption_rate=1.0, seed=42)
        
        injector.inject_corruption({"key": "val"}, "wf-1")
        injector.inject_corruption({"key": "val"}, "wf-1")
        injector.inject_corruption({"key": "val"}, "wf-2")
        
        corruption_map = injector.get_corruption_map()
        
        assert "wf-1" in corruption_map
        assert "wf-2" in corruption_map
        assert len(corruption_map["wf-1"]) == 2
        assert len(corruption_map["wf-2"]) == 1
        
class TestNetworkJitterSimulator:
    """Tests for the NetworkJitterSimulator class."""
    
    def test_jitter_sampling(self):
        """Test that jitter is sampled within bounds."""
        simulator = NetworkJitterSimulator(max_jitter_ms=100.0, seed=42)
        
        for _ in range(100):
            jitter = simulator.sample_jitter()
            assert 0 <= jitter <= 100.0
            
    def test_deterministic_with_seed(self):
        """Test that jitter is deterministic with same seed."""
        sim1 = NetworkJitterSimulator(max_jitter_ms=100.0, seed=123)
        sim2 = NetworkJitterSimulator(max_jitter_ms=100.0, seed=123)
        
        jitters1 = [sim1.sample_jitter() for _ in range(10)]
        jitters2 = [sim2.sample_jitter() for _ in range(10)]
        
        assert jitters1 == jitters2
        
    def test_jitter_in_seconds(self):
        """Test jitter sampling in seconds."""
        simulator = NetworkJitterSimulator(max_jitter_ms=1000.0, seed=42)
        
        for _ in range(100):
            jitter = simulator.sample_jitter_seconds()
            assert 0 <= jitter <= 1.0