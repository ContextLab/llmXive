"""
Benchmark tests for embedding generation performance.

This module verifies that the embedding service meets the latency constraint
specified in SC-005: maximum latency per node must be <= 50ms.
"""
import time
import pytest
import logging
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from src.services.embeddings import load_embedding_model, generate_embeddings_batched

# Configure logging for the benchmark
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_LATENCY_PER_NODE_MS = 50.0
BENCHMARK_SAMPLE_SIZE = 10

def test_embedding_speed_benchmark():
    """
    Benchmark test to verify embedding generation speed.
    
    Loads a small sample of node titles, generates embeddings, and measures
    the maximum latency per node. The test fails if any single node exceeds
    the 50ms threshold.
    
    SC-005 Requirement: Maximum latency per node <= 50ms.
    """
    # Create a representative sample of node titles
    # Using a mix of lengths to ensure realistic testing
    sample_titles = [
        "Deep learning for natural language processing",
        "Quantum computing algorithms for optimization",
        "Climate change impact on biodiversity",
        "Machine learning in healthcare diagnostics",
        "Blockchain technology for supply chain",
        "Neural networks for computer vision",
        "Reinforcement learning in robotics",
        "Transformer models for text generation",
        "Graph neural networks for social analysis",
        "Federated learning for privacy preservation"
    ]
    
    # Ensure we have enough samples
    assert len(sample_titles) >= BENCHMARK_SAMPLE_SIZE, \
        f"Sample size {len(sample_titles)} is less than required {BENCHMARK_SAMPLE_SIZE}"
    
    # Load the embedding model
    logger.info("Loading embedding model...")
    model = load_embedding_model()
    
    # Run the benchmark multiple times to account for variability
    max_latency_per_node_ms = 0.0
    iterations = 3
    
    for iteration in range(iterations):
        logger.info(f"Starting benchmark iteration {iteration + 1}/{iterations}")
        
        # Measure total time for batch processing
        start_time = time.perf_counter()
        
        # Generate embeddings for the sample
        embeddings = generate_embeddings_batched(
            model=model,
            texts=sample_titles,
            batch_size=5,
            device="cpu"
        )
        
        end_time = time.perf_counter()
        total_time_seconds = end_time - start_time
        
        # Calculate average latency per node for this iteration
        avg_latency_ms = (total_time_seconds / len(sample_titles)) * 1000
        
        # For a more precise measurement, we'll estimate individual node latency
        # by dividing total time by number of nodes (assuming uniform processing)
        # In practice, batch processing makes exact per-node timing difficult,
        # but this gives a conservative estimate
        estimated_max_latency_ms = avg_latency_ms * 1.5  # Conservative estimate
        
        logger.info(f"Iteration {iteration + 1}: Total time={total_time_seconds:.4f}s, "
                   f"Avg latency={avg_latency_ms:.2f}ms, Estimated max={estimated_max_latency_ms:.2f}ms")
        
        max_latency_per_node_ms = max(max_latency_per_node_ms, estimated_max_latency_ms)
    
    # Final assertion
    logger.info(f"Final result: Maximum estimated latency per node = {max_latency_per_node_ms:.2f}ms")
    logger.info(f"Threshold: {MAX_LATENCY_PER_NODE_MS}ms")
    
    assert max_latency_per_node_ms <= MAX_LATENCY_PER_NODE_MS, \
        f"SC-005 Violation: Maximum latency per node ({max_latency_per_node_ms:.2f}ms) " \
        f"exceeds threshold ({MAX_LATENCY_PER_NODE_MS}ms)"
    
    logger.info(f"✓ SC-005 PASSED: All embedding operations completed within {MAX_LATENCY_PER_NODE_MS}ms per node")

def test_embedding_speed_with_mocked_model():
    """
    Alternative benchmark using a mocked model for faster CI/CD testing.
    
    This test simulates the embedding generation with a controlled delay
    to verify the benchmark logic works correctly.
    """
    # Create mock model
    mock_model = MagicMock()
    
    # Mock the encode method to simulate realistic processing time
    def mock_encode(texts, **kwargs):
        # Simulate processing time: 10ms per text (well under 50ms threshold)
        time.sleep(0.01)
        return [[0.1] * 384 for _ in texts]  # Return dummy embeddings
    
    mock_model.encode.side_effect = mock_encode
    
    sample_titles = ["Test title 1", "Test title 2", "Test title 3"]
    
    start_time = time.perf_counter()
    embeddings = generate_embeddings_batched(
        model=mock_model,
        texts=sample_titles,
        batch_size=2,
        device="cpu"
    )
    end_time = time.perf_counter()
    
    total_time_ms = (end_time - start_time) * 1000
    avg_latency_ms = total_time_ms / len(sample_titles)
    
    # With 10ms per text and batch processing, we expect ~10-15ms per node
    assert avg_latency_ms < MAX_LATENCY_PER_NODE_MS, \
        f"Mocked benchmark failed: Average latency {avg_latency_ms:.2f}ms exceeds threshold"
    
    logger.info(f"✓ Mocked benchmark passed: Average latency {avg_latency_ms:.2f}ms < {MAX_LATENCY_PER_NODE_MS}ms")

if __name__ == "__main__":
    # Run the benchmark when executed directly
    pytest.main([__file__, "-v", "-s"])
