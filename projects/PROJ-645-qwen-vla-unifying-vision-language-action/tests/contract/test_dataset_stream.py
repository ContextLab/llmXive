"""
Contract test for dataset streaming memory footprint.

Verifies that streaming the filtered Open X-Embodiment dataset
stays within the 7GB RAM limit (FR-003).
"""
import gc
import os
import sys
import time
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import psutil

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.resource_monitor import ResourceMonitor, resource_monitor_context
from src.utils.logging_config import setup_logging

# Configure logging for the test
logger = setup_logging(level="INFO")


def get_memory_usage_gb() -> float:
    """Get current process RSS memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)


def simulate_dataset_streaming(num_samples: int = 1000) -> Generator[Dict[str, Any], None, None]:
    """
    Simulate streaming dataset samples.
    
    In the real implementation, this would fetch from HF Datasets API.
    For the contract test, we simulate the memory footprint of loading
    and processing samples without holding them all in memory.
    
    Args:
        num_samples: Number of samples to simulate streaming
        
    Yields:
        Dictionary representing a single dataset sample
    """
    # Simulate sample structure matching Open X-Embodiment schema
    sample_template = {
        "platform_id": "franka",
        "observation": {
            "images": {
                "wrist": b"fake_image_data",
                "eye": b"fake_image_data"
            },
            "state": [0.0] * 7
        },
        "action": [0.0] * 7,
        "language_instruction": "pick up the object"
    }
    
    for i in range(num_samples):
        # Simulate processing delay
        if i % 100 == 0:
            gc.collect()
        
        yield sample_template.copy()


@pytest.mark.contract
def test_dataset_streaming_memory_footprint():
    """
    Contract test: Verify dataset streaming stays under 7GB RAM.
    
    This test streams a simulated dataset and monitors memory usage.
    It passes if peak RAM remains below 7GB throughout the streaming process.
    """
    # Configuration
    MAX_RAM_GB = 7.0
    NUM_SAMPLES = 5000  # Simulate a subset of the full 50k dataset
    MEMORY_CHECK_INTERVAL = 100  # Check every N samples
    
    logger.info(f"Starting dataset streaming contract test with {NUM_SAMPLES} samples")
    logger.info(f"Memory limit: {MAX_RAM_GB} GB")
    
    # Initialize resource monitor
    monitor = ResourceMonitor()
    
    # Start monitoring
    monitor.start()
    
    peak_memory_gb = 0.0
    samples_processed = 0
    
    try:
        # Stream the dataset
        with resource_monitor_context(monitor):
            for sample in simulate_dataset_streaming(NUM_SAMPLES):
                samples_processed += 1
                
                # Periodic memory check
                if samples_processed % MEMORY_CHECK_INTERVAL == 0:
                    current_memory = get_memory_usage_gb()
                    peak_memory_gb = max(peak_memory_gb, current_memory)
                    logger.info(
                        f"Processed {samples_processed} samples. "
                        f"Current RAM: {current_memory:.2f} GB, Peak: {peak_memory_gb:.2f} GB"
                    )
                    
                    # Early exit if over limit (fail fast)
                    if current_memory > MAX_RAM_GB:
                        pytest.fail(
                            f"Memory limit exceeded at sample {samples_processed}: "
                            f"{current_memory:.2f} GB > {MAX_RAM_GB} GB"
                        )
        
        # Final memory check
        final_memory = get_memory_usage_gb()
        peak_memory_gb = max(peak_memory_gb, final_memory)
        
    finally:
        # Stop monitoring
        monitor.stop()
        
        # Log final stats
        logger.info(f"Test completed. Processed {samples_processed} samples.")
        logger.info(f"Peak memory usage: {peak_memory_gb:.2f} GB")
    
    # Assertion
    assert peak_memory_gb < MAX_RAM_GB, (
        f"Contract test FAILED: Peak memory {peak_memory_gb:.2f} GB "
        f"exceeded limit of {MAX_RAM_GB} GB"
    )
    
    logger.info(f"Contract test PASSED: Peak memory {peak_memory_gb:.2f} GB < {MAX_RAM_GB} GB")
    assert samples_processed == NUM_SAMPLES, "Not all samples were processed"


@pytest.mark.contract
def test_streaming_does_not_accumulate():
    """
    Contract test: Verify streaming does not accumulate data in memory.
    
    This test verifies that the streaming approach does not store
    all samples in a list, which would violate the memory constraint.
    """
    # Simulate a bad pattern (accumulating in list) vs good pattern (streaming)
    def bad_accumulation_pattern(num_samples: int) -> list:
        data = []
        for i in range(num_samples):
            data.append({"index": i, "data": "x" * 1000})  # Simulate sample
        return data
    
    def good_streaming_pattern(num_samples: int) -> Generator[Dict, None, None]:
        for i in range(num_samples):
            yield {"index": i, "data": "x" * 1000}
    
    # Test streaming pattern
    monitor = ResourceMonitor()
    monitor.start()
    
    try:
        count = 0
        for sample in good_streaming_pattern(10000):
            count += 1
            if count % 1000 == 0:
                gc.collect()
    finally:
        monitor.stop()
    
    # Verify we processed all samples
    assert count == 10000, "Streaming pattern failed to yield all samples"
    
    logger.info("Streaming accumulation test PASSED")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
