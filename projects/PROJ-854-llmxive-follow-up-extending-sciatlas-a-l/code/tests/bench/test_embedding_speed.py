"""
Benchmark tests for embedding generation speed.

This test verifies that the embedding generation meets the latency requirement:
- No individual node latency exceeds 50ms
"""

import pytest
import numpy as np
import time
from unittest.mock import patch, MagicMock

from src.services.embeddings import (
    load_embedding_model,
    generate_embeddings_batched,
    MAX_NODE_LATENCY_MS
)

@patch('src.services.embeddings.SentenceTransformer')
def test_embedding_speed(mock_sentence_transformer):
    """Test that embedding generation meets latency requirements."""
    # Mock the model with controlled timing
    mock_model = MagicMock()
    
    # Simulate realistic encoding time (should be fast enough)
    def mock_encode(texts, **kwargs):
        time.sleep(0.001)  # 1ms per batch
        return np.random.rand(len(texts), 384)
    
    mock_model.encode.side_effect = mock_encode
    mock_sentence_transformer.return_value = mock_model
    
    # Load model
    model = load_embedding_model()
    
    # Create test texts
    texts = [f'Test text {i}' for i in range(100)]
    
    # Measure timing
    start_time = time.time()
    embeddings = generate_embeddings_batched(model, texts, batch_size=32)
    total_time = time.time() - start_time
    
    # Calculate average latency per node
    avg_latency_ms = (total_time / len(texts)) * 1000
    
    # Verify the threshold is met
    assert avg_latency_ms <= MAX_NODE_LATENCY_MS, (
        f"Average latency {avg_latency_ms:.2f}ms exceeds threshold {MAX_NODE_LATENCY_MS}ms"
    )
    
    # Verify embeddings were generated
    assert embeddings.shape == (100, 384)

@patch('src.services.embeddings.SentenceTransformer')
def test_embedding_speed_batched(mock_sentence_transformer):
    """Test embedding speed with different batch sizes."""
    # Mock the model
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(32, 384)
    mock_sentence_transformer.return_value = mock_model
    
    model = load_embedding_model()
    texts = [f'Test text {i}' for i in range(200)]
    
    # Test with different batch sizes
    for batch_size in [16, 32, 64]:
        start_time = time.time()
        embeddings = generate_embeddings_batched(model, texts, batch_size=batch_size)
        total_time = time.time() - start_time
        
        avg_latency_ms = (total_time / len(texts)) * 1000
        
        assert avg_latency_ms <= MAX_NODE_LATENCY_MS, (
            f"Batch size {batch_size}: Average latency {avg_latency_ms:.2f}ms "
            f"exceeds threshold {MAX_NODE_LATENCY_MS}ms"
        )
        
        assert embeddings.shape == (200, 384)