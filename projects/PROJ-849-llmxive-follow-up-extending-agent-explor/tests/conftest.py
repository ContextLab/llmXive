"""
Pytest configuration and shared fixtures.
"""
import pytest
import numpy as np

@pytest.fixture
def sample_embedding_768():
    """Provide a sample 768-dimensional vector (DistilBERT default)"""
    return np.random.rand(768).astype(np.float32)

@pytest.fixture
def sample_thinking_vector():
    """Sample thinking prefix embedding"""
    return np.array([1.0, 0.5, 0.2, 0.1] + [0.0] * 764)

@pytest.fixture
def sample_tool_centroid():
    """Sample tool centroid embedding"""
    return np.array([0.1, 0.2, 0.3, 0.4] + [0.0] * 764)
