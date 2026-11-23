"""
Integration tests for batch processing memory constraints.

These tests verify that the batch processing logic stays within
the 6GB memory limit when processing batches of 50 queries.
"""
import os
import sys
import gc
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.batch_processor import (
    get_memory_usage_gb,
    check_memory_limit,
    process_batch_with_memory_monitor,
    run_optimized_batch_permutation,
    MEMORY_THRESHOLD_GB
)
from code.config import RESULTS_DIR

@pytest.fixture
def sample_queries():
    """Generate sample query data for testing."""
    queries = []
    for i in range(50):
        queries.append({
            'query_id': i,
            'relevance_labels': [3, 2, 1, 0, 0, 1, 2, 3, 0, 0],
            'scores': [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]
        })
    return queries

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_memory_usage_measurement():
    """Test that memory usage measurement works correctly."""
    mem_gb = get_memory_usage_gb()
    assert mem_gb > 0, "Memory usage should be positive"
    assert mem_gb < 100, "Memory usage should be reasonable (< 100GB)"

def test_memory_limit_check():
    """Test that memory limit check works."""
    # This should not raise an error
    result = check_memory_limit()
    assert isinstance(result, bool)

def test_batch_processing_memory_constraints(sample_queries, temp_output_dir):
    """
    Test that batch processing stays within memory limits.
    
    This is the core test for T036: verify memory < 6GB during batch of 50 queries.
    """
    # Force garbage collection before test
    gc.collect()
    
    initial_memory = get_memory_usage_gb()
    
    # Process a batch of 50 queries
    results = process_batch_with_memory_monitor(
        queries=sample_queries,
        metric='ndcg',
        k=10,
        permutation_count=100,  # Use fewer permutations for faster test
        base_seed=42,
        output_dir=temp_output_dir
    )
    
    final_memory = get_memory_usage_gb()
    
    # Verify results
    assert len(results) == 50, "Should process all 50 queries"
    assert all('p_value' in r for r in results), "All results should have p_values"
    
    # Check memory usage (should be well below 6GB)
    # Note: The actual memory usage depends on the system, but should be < 6GB
    assert final_memory < MEMORY_THRESHOLD_GB, \
        f"Memory usage {final_memory:.2f}GB exceeds threshold {MEMORY_THRESHOLD_GB}GB"
    
    # Log memory usage for verification
    print(f"Initial memory: {initial_memory:.2f}GB")
    print(f"Final memory: {final_memory:.2f}GB")
    print(f"Memory increase: {final_memory - initial_memory:.2f}GB")

def test_memory_cleanup_between_queries(sample_queries, temp_output_dir):
    """Test that memory is properly cleaned up between queries."""
    gc.collect()
    
    memory_before = get_memory_usage_gb()
    
    # Process first half of queries
    results1 = process_batch_with_memory_monitor(
        queries=sample_queries[:25],
        metric='ndcg',
        k=10,
        permutation_count=50,
        base_seed=42,
        output_dir=temp_output_dir
    )
    
    memory_mid = get_memory_usage_gb()
    
    # Force garbage collection
    gc.collect()
    
    # Process second half
    results2 = process_batch_with_memory_monitor(
        queries=sample_queries[25:],
        metric='ndcg',
        k=10,
        permutation_count=50,
        base_seed=42,
        output_dir=temp_output_dir
    )
    
    memory_after = get_memory_usage_gb()
    
    # Verify both halves were processed
    assert len(results1) == 25
    assert len(results2) == 25
    
    # Memory should not grow unboundedly
    assert memory_after < MEMORY_THRESHOLD_GB, \
        f"Memory {memory_after:.2f}GB exceeds limit after full batch"

def test_multiple_metrics_batch(sample_queries, temp_output_dir):
    """Test batch processing with multiple metrics."""
    gc.collect()
    
    # Process with multiple metrics
    results_ndcg = process_batch_with_memory_monitor(
        queries=sample_queries,
        metric='ndcg',
        k=10,
        permutation_count=50,
        base_seed=42,
        output_dir=temp_output_dir
    )
    
    results_map = process_batch_with_memory_monitor(
        queries=sample_queries,
        metric='map',
        k=10,
        permutation_count=50,
        base_seed=42,
        output_dir=temp_output_dir
    )
    
    assert len(results_ndcg) == 50
    assert len(results_map) == 50
    
    final_memory = get_memory_usage_gb()
    assert final_memory < MEMORY_THRESHOLD_GB

def test_large_batch_memory_pressure(temp_output_dir):
    """Test with a larger batch to ensure memory management is robust."""
    # Generate 100 queries (larger than standard batch size)
    large_queries = []
    for i in range(100):
        large_queries.append({
            'query_id': i,
            'relevance_labels': [3, 2, 1, 0, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0],
            'scores': [0.9 - i*0.001 for _ in range(15)]
        })
    
    gc.collect()
    
    # Process in smaller batches
    batch_size = 50
    all_results = []
    
    for i in range(0, len(large_queries), batch_size):
        batch = large_queries[i:i+batch_size]
        results = process_batch_with_memory_monitor(
            queries=batch,
            metric='ndcg',
            k=10,
            permutation_count=50,
            base_seed=42,
            output_dir=temp_output_dir
        )
        all_results.extend(results)
        
        # Check memory after each batch
        current_mem = get_memory_usage_gb()
        assert current_mem < MEMORY_THRESHOLD_GB, \
            f"Memory {current_mem:.2f}GB exceeds limit after batch"
    
    assert len(all_results) == 100

def test_memory_threshold_enforcement():
    """Test that memory threshold enforcement works correctly."""
    # This test verifies the logic, not the actual threshold (which is system-dependent)
    assert MEMORY_THRESHOLD_GB == 6.0, "Memory threshold should be 6GB"
    
    # Verify check_memory_limit doesn't crash
    result = check_memory_limit()
    assert isinstance(result, bool)
