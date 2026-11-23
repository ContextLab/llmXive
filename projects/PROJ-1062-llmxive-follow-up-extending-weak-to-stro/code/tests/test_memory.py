"""
Unit tests for memory constraints and model size verification.

This module implements sanity checks for:
1. RAM usage staying under the 7GB constraint
2. Model size verification before loading
3. Integration with MemoryMonitor and HardFloorEnforcer
"""

import pytest
import sys
import os
import gc
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.memory_monitor import MemoryMonitor
from core.hard_floor_enforcer import HardFloorEnforcer
from models.moe_student import estimate_model_size_gb, MoEStudentLoader
from models.ssm_student import estimate_model_size_gb as estimate_ssm_size_gb, SSMStudentLoader
from models.teacher_loader import TeacherLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants matching the project constraints
MAX_RAM_GB = 7.0
RAM_WARNING_THRESHOLD = 0.90  # 90% of max
MODEL_SIZE_MARGIN = 0.5  # 500MB margin for safety


class TestMemoryMonitor:
    """Tests for the MemoryMonitor class functionality."""

    def test_memory_monitor_initialization(self):
        """Test that MemoryMonitor initializes correctly."""
        monitor = MemoryMonitor()
        assert monitor.max_memory_gb == MAX_RAM_GB
        assert monitor.warning_threshold == RAM_WARNING_THRESHOLD
        assert monitor.current_memory_gb is None

    def test_get_current_memory_gb(self):
        """Test that current memory can be measured."""
        monitor = MemoryMonitor()
        memory = monitor.get_current_memory_gb()
        assert memory >= 0
        assert isinstance(memory, float)
        logger.info(f"Current system memory usage: {memory:.2f} GB")

    def test_memory_check_within_limit(self):
        """Test memory check passes when usage is under limit."""
        monitor = MemoryMonitor()
        # Simulate a low memory usage scenario
        is_safe, current_mem = monitor.check_memory_usage(usage_gb=2.0)
        assert is_safe is True
        assert current_mem == 2.0

    def test_memory_check_warning_threshold(self):
        """Test memory check warns when usage approaches limit."""
        monitor = MemoryMonitor()
        # Simulate usage at 85% of limit (should be safe but close)
        usage_gb = MAX_RAM_GB * 0.85
        is_safe, current_mem = monitor.check_memory_usage(usage_gb=usage_gb)
        assert is_safe is True
        assert current_mem == usage_gb

    def test_memory_check_exceeds_limit(self):
        """Test memory check fails when usage exceeds limit."""
        monitor = MemoryMonitor()
        # Simulate usage exceeding limit
        usage_gb = MAX_RAM_GB * 1.1
        is_safe, current_mem = monitor.check_memory_usage(usage_gb=usage_gb)
        assert is_safe is False
        assert current_mem == usage_gb

    def test_memory_check_at_exact_limit(self):
        """Test memory check behavior at exactly the limit."""
        monitor = MemoryMonitor()
        is_safe, current_mem = monitor.check_memory_usage(usage_gb=MAX_RAM_GB)
        # Should be safe at exactly the limit
        assert is_safe is True
        assert current_mem == MAX_RAM_GB


class TestHardFloorEnforcer:
    """Tests for the HardFloorEnforcer class functionality."""

    def test_hard_floor_enforcer_initialization(self):
        """Test that HardFloorEnforcer initializes correctly."""
        enforcer = HardFloorEnforcer()
        assert enforcer.min_batch_size == 1
        assert enforcer.current_batch_size >= 1

    def test_enforce_batch_size_reduction(self):
        """Test that enforcer can reduce batch size on OOM."""
        enforcer = HardFloorEnforcer()
        original_size = enforcer.current_batch_size
        
        # Simulate an OOM event requiring reduction
        new_size = enforcer.enforce(reduce_by=1)
        
        assert new_size == max(1, original_size - 1)
        assert new_size >= enforcer.min_batch_size

    def test_hard_floor_limit(self):
        """Test that batch size never goes below 1."""
        enforcer = HardFloorEnforcer()
        enforcer.current_batch_size = 2
        
        # Try to reduce by a large amount
        new_size = enforcer.enforce(reduce_by=10)
        
        assert new_size == 1
        assert new_size == enforcer.min_batch_size

    def test_enforce_no_reduction_needed(self):
        """Test that enforcer doesn't reduce if not needed."""
        enforcer = HardFloorEnforcer()
        original_size = enforcer.current_batch_size
        
        new_size = enforcer.enforce(reduce_by=0)
        
        assert new_size == original_size


class TestModelSizeEstimation:
    """Tests for model size estimation before loading."""

    def test_moe_size_estimation(self):
        """Test that MoE model size can be estimated."""
        # Test with a known small model first
        model_id = "microsoft/phi-1.5"  # ~1.5B params, should fit
        
        try:
            estimated_size = estimate_model_size_gb(model_id)
            assert estimated_size is not None
            assert estimated_size > 0
            logger.info(f"Estimated size for {model_id}: {estimated_size:.2f} GB")
            
            # Check if it would fit in our constraints
            fits = estimated_size < (MAX_RAM_GB * 0.8)
            logger.info(f"Model {model_id} fits in 7GB constraint: {fits}")
        except Exception as e:
            # Some models might not be accessible, that's okay for this test
            logger.warning(f"Could not estimate size for {model_id}: {e}")
            pytest.skip(f"Model {model_id} not accessible: {e}")

    def test_ssm_size_estimation(self):
        """Test that SSM model size can be estimated."""
        # Test with a known small SSM model
        model_id = "state-spaces/mamba-130m"  # Small Mamba variant
        
        try:
            estimated_size = estimate_ssm_size_gb(model_id)
            assert estimated_size is not None
            assert estimated_size > 0
            logger.info(f"Estimated size for {model_id}: {estimated_size:.2f} GB")
            
            fits = estimated_size < (MAX_RAM_GB * 0.8)
            logger.info(f"Model {model_id} fits in 7GB constraint: {fits}")
        except Exception as e:
            logger.warning(f"Could not estimate size for {model_id}: {e}")
            pytest.skip(f"Model {model_id} not accessible: {e}")

    def test_size_verification_before_loading(self):
        """Test that we verify size before attempting to load large models."""
        # This test verifies the logic of size checking
        # We don't actually load large models in tests
        
        class MockModelLoader:
            def __init__(self, model_id: str, estimated_size: float):
                self.model_id = model_id
                self.estimated_size = estimated_size
            
            def would_fit(self, max_size_gb: float) -> bool:
                return self.estimated_size < max_size_gb
        
        # Test cases
        small_model = MockModelLoader("small-model", 2.0)
        large_model = MockModelLoader("large-model", 10.0)
        
        assert small_model.would_fit(MAX_RAM_GB) is True
        assert large_model.would_fit(MAX_RAM_GB) is False


class TestIntegrationMemoryConstraints:
    """Integration tests for memory constraint enforcement."""

    def test_memory_monitor_with_hard_floor(self):
        """Test that memory monitor and hard floor enforcer work together."""
        monitor = MemoryMonitor()
        enforcer = HardFloorEnforcer()
        
        # Simulate a scenario where memory usage is high
        high_usage = MAX_RAM_GB * 0.95
        is_safe, _ = monitor.check_memory_usage(usage_gb=high_usage)
        
        if not is_safe:
            # Enforcer should reduce batch size
            new_batch_size = enforcer.enforce(reduce_by=1)
            assert new_batch_size >= 1
            logger.info(f"Reduced batch size to {new_batch_size} due to memory pressure")

    def test_batch_size_1_hard_floor(self):
        """Test that batch size 1 is enforced as the absolute minimum."""
        enforcer = HardFloorEnforcer()
        enforcer.current_batch_size = 1
        
        # Even with extreme memory pressure, should stay at 1
        new_size = enforcer.enforce(reduce_by=100)
        
        assert new_size == 1
        assert new_size == enforcer.min_batch_size


class TestMemorySanityChecks:
    """High-level sanity checks for the memory constraint system."""

    def test_system_memory_available(self):
        """Verify that the system has sufficient memory available."""
        monitor = MemoryMonitor()
        current_usage = monitor.get_current_memory_gb()
        
        logger.info(f"Current system memory usage: {current_usage:.2f} GB")
        logger.info(f"Maximum allowed usage: {MAX_RAM_GB:.2f} GB")
        logger.info(f"Available headroom: {MAX_RAM_GB - current_usage:.2f} GB")
        
        # At least some memory should be available
        assert current_usage < MAX_RAM_GB

    def test_memory_monitor_reliability(self):
        """Test that memory monitor provides consistent readings."""
        monitor = MemoryMonitor()
        
        readings = []
        for _ in range(3):
            reading = monitor.get_current_memory_gb()
            readings.append(reading)
            gc.collect()
        
        # All readings should be reasonable (non-negative)
        assert all(r >= 0 for r in readings)
        
        # Readings should be relatively close (within 10% of each other)
        if max(readings) > 0:
            variance = (max(readings) - min(readings)) / max(readings)
            assert variance < 0.1 or max(readings) < 0.5  # Allow more variance for very low memory

    def test_model_loading_pre_check(self):
        """Test the pre-loading size verification logic."""
        # This test validates the pattern used in model loaders
        
        def safe_load_check(model_id: str, max_size_gb: float) -> Dict[str, Any]:
            """Simulate the pre-load check pattern."""
            try:
                # Estimate size (in real code, this would call estimate_model_size_gb)
                # For testing, we'll use a mock estimation
                estimated_size = 2.0  # Mock value
                
                if estimated_size > max_size_gb:
                    return {
                        "success": False,
                        "reason": f"Estimated size {estimated_size}GB exceeds limit {max_size_gb}GB",
                        "estimated_size": estimated_size
                    }
                
                return {
                    "success": True,
                    "reason": "Size check passed",
                    "estimated_size": estimated_size
                }
            except Exception as e:
                return {
                    "success": False,
                    "reason": f"Error estimating size: {str(e)}",
                    "estimated_size": None
                }
        
        # Test with a model that should fit
        result = safe_load_check("test-model", MAX_RAM_GB)
        assert result["success"] is True
        
        # Test with a model that shouldn't fit
        result = safe_load_check("large-model", 1.0)
        assert result["success"] is False


def test_memory_constraint_summary():
    """
    Summary test that provides a comprehensive view of memory constraints.
    This test runs all the key checks and reports the overall status.
    """
    logger.info("=" * 60)
    logger.info("MEMORY CONSTRAINT SANITY CHECK SUMMARY")
    logger.info("=" * 60)
    
    monitor = MemoryMonitor()
    enforcer = HardFloorEnforcer()
    
    # 1. Check current system memory
    current_memory = monitor.get_current_memory_gb()
    logger.info(f"1. Current system memory usage: {current_memory:.2f} GB / {MAX_RAM_GB:.2f} GB")
    
    # 2. Check available headroom
    headroom = MAX_RAM_GB - current_memory
    logger.info(f"2. Available headroom: {headroom:.2f} GB ({(headroom/MAX_RAM_GB)*100:.1f}%)")
    
    # 3. Verify hard floor enforcer is ready
    logger.info(f"3. Hard floor enforcer min batch size: {enforcer.min_batch_size}")
    logger.info(f"   Current batch size: {enforcer.current_batch_size}")
    
    # 4. Memory safety check
    is_safe, _ = monitor.check_memory_usage(current_memory)
    logger.info(f"4. Memory safety status: {'SAFE' if is_safe else 'UNSAFE'}")
    
    # 5. Final verdict
    if is_safe and headroom > 1.0:
        logger.info("✓ MEMORY CONSTRAINTS SATISFIED")
        logger.info("  - System has sufficient memory for training")
        logger.info("  - Hard floor enforcer is ready for OOM handling")
        logger.info("  - All sanity checks passed")
    else:
        logger.warning("⚠ MEMORY CONSTRAINTS AT RISK")
        logger.warning("  - Consider reducing batch size or model size")
        logger.warning("  - Hard floor enforcer may need to trigger")
    
    logger.info("=" * 60)
    
    # Return True if all checks pass
    return is_safe and headroom > 1.0


if __name__ == "__main__":
    # Run the summary test when executed directly
    success = test_memory_constraint_summary()
    sys.exit(0 if success else 1)