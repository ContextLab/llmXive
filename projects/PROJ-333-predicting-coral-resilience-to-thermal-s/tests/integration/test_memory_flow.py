"""
Memory flow integration test using mock data.

This test verifies that the pipeline can process data without
exceeding memory limits, using small mock FASTQ files.
"""
import pytest
import gzip
import json
from pathlib import Path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import get_memory_usage_mb, setup_logger

MOCK_FASTQ_DIR = Path(__file__).parent / "data" / "mock_fastq"

def test_memory_tracking_with_mock_files():
    """
    Test that memory tracking works correctly during mock file processing.
    """
    logger = setup_logger("mem_test", "data/processed/test_logs")
    
    initial_mem = get_memory_usage_mb()
    logger.info(f"Initial memory usage: {initial_mem:.2f} MB")
    
    # Process mock files
    if not MOCK_FASTQ_DIR.exists():
        pytest.skip("Mock data not generated. Run test_pipeline_flow.py first.")
    
    total_reads = 0
    for f in MOCK_FASTQ_DIR.glob("*.fastq.gz"):
        with gzip.open(f, 'rt') as fh:
            lines = fh.readlines()
            # Count reads (every 4 lines is one read)
            total_reads += len(lines) // 4
    
    current_mem = get_memory_usage_mb()
    mem_diff = current_mem - initial_mem
    
    logger.info(f"Processed {total_reads} reads. Memory delta: {mem_diff:.2f} MB")
    
    # Assert that memory usage is reasonable (should be very low for mock data)
    # 7GB is the limit, but for 20 reads per file, it should be < 100MB
    assert mem_diff < 100, f"Memory usage spiked unexpectedly: {mem_diff} MB"
    
    print(f"Memory flow test passed. Delta: {mem_diff:.2f} MB")