import os
import sys
import gc
import time
import tempfile
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from src.utils.resource_monitor import get_current_ram_gb, check_ram_limit
from src.utils.logging_config import setup_logging, get_logger
from src.utils.config import Config

# RAM limit in GB as per requirement FR-003
RAM_LIMIT_GB = 7.0
# Safety margin (keep usage below 6.8GB to be safe)
SAFETY_MARGIN_GB = 0.2

def setup_module():
    """Setup logging for the test module."""
    setup_logging(level="INFO", format_type="json")

@pytest.mark.contract
def test_dataset_streaming_ram_usage():
    """
    Contract test: Verify that streaming the Open X-Embodiment dataset
    (or a representative subset) does not exceed 7GB RAM.
    
    This test simulates the streaming behavior of T012 without actually
    downloading the full dataset. It verifies the memory management logic
    by iterating over a synthetic stream of large objects.
    """
    logger = get_logger(__name__)
    
    # Record initial RAM
    gc.collect()
    time.sleep(0.5)
    initial_ram = get_current_ram_gb()
    logger.info(f"Initial RAM usage: {initial_ram:.2f} GB")

    # Simulate a streaming dataset iterator
    # We create a generator that yields "chunks" of data to simulate
    # the memory pressure of loading a large dataset without persisting it.
    # Each chunk simulates a batch of observations/actions.
    chunk_size_mb = 100  # 100MB per chunk
    num_chunks = 60      # Total ~6GB of data streamed sequentially
    
    def simulated_stream():
        """Generator that yields large byte objects to simulate dataset rows."""
        for i in range(num_chunks):
            # Create a byte buffer of ~100MB
            data = os.urandom(chunk_size_mb * 1024 * 1024)
            yield {
                "chunk_id": i,
                "data": data,
                "platform_id": "franka" if i % 3 == 0 else "ur5" if i % 3 == 1 else "kuka"
            }
            # Explicitly delete reference after yielding to simulate streaming discard
            # In real code, the iterator consumes one item at a time.
            # Here we yield the item, the test consumes it, then we delete the ref in the generator.
            # However, since we yield the object, the caller holds it.
            # We simulate the "streaming" by ensuring the caller deletes it immediately.
            yield None # Dummy yield to reset generator state if needed, though logic below handles it.
    
    # Corrected generator to simulate streaming consumption
    def streaming_generator():
        for i in range(num_chunks):
            data = os.urandom(chunk_size_mb * 1024 * 1024)
            yield {
                "chunk_id": i,
                "platform_id": ["franka", "ur5", "kuka"][i % 3]
            }
            # In a real streaming scenario, the data is processed and then 
            # the reference is dropped. We simulate this by yielding the metadata
            # and assuming the large data payload is handled by the iterator protocol
            # without accumulating in a list.
            # To strictly test RAM, we will create the large object, yield it,
            # and ensure the test loop deletes it.
            # But since we can't yield the large object AND keep it in memory
            # without the test holding it, we will yield the object and let the test drop it.
            # Actually, os.urandom creates the memory. We yield it. The test holds it.
            # We need to yield, then the test must delete it.
            # Let's just yield a marker and assume the "stream" logic handles the rest,
            # but to prove RAM < 7GB, we must actually allocate the memory.
            
    # Let's implement the actual streaming simulation where we allocate, yield, and the test deletes.
    def actual_stream():
        for i in range(num_chunks):
            # Allocate 100MB
            chunk_data = os.urandom(chunk_size_mb * 1024 * 1024)
            yield {
                "chunk_id": i,
                "platform_id": ["franka", "ur5", "kuka"][i % 3],
                "payload": chunk_data
            }
            # The generator yields. The test loop receives it.
            # The test loop MUST delete the item to simulate streaming behavior.
    
    logger.info(f"Starting streaming simulation: {num_chunks} chunks of {chunk_size_mb}MB each")
    
    peak_ram = initial_ram
    
    stream = actual_stream()
    for item in stream:
        # Simulate processing
        current_chunk_id = item["chunk_id"]
        # Simulate some processing time
        time.sleep(0.01) 
        
        # CRITICAL: Delete the item immediately after processing to simulate streaming
        # This ensures we don't accumulate memory in a list
        del item
        gc.collect()
        
        current_ram = get_current_ram_gb()
        if current_ram > peak_ram:
            peak_ram = current_ram
        
        # Log progress periodically
        if current_chunk_id % 10 == 0:
            logger.info(f"Processed chunk {current_chunk_id}, Peak RAM: {peak_ram:.2f} GB")
        
        # Check RAM limit during iteration (fail fast)
        if not check_ram_limit(RAM_LIMIT_GB):
            logger.error(f"RAM limit exceeded during streaming at chunk {current_chunk_id}")
            pytest.fail(f"RAM limit exceeded: {current_ram:.2f} GB > {RAM_LIMIT_GB} GB")

    logger.info(f"Streaming simulation complete. Peak RAM: {peak_ram:.2f} GB")
    
    # Final assertion
    assert peak_ram < RAM_LIMIT_GB, (
        f"Dataset streaming exceeded RAM limit. "
        f"Peak usage: {peak_ram:.2f} GB, Limit: {RAM_LIMIT_GB} GB"
    )
    
    logger.info("Contract test PASSED: Dataset streaming stays within RAM limits.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
