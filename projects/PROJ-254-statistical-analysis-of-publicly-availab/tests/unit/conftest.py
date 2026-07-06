"""
Pytest configuration and fixtures for unit tests.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile

@pytest.fixture
def sample_embedding_vector():
    """Return a sample embedding vector of dimension 100."""
    return np.random.rand(100).astype(np.float32)

@pytest.fixture
def sample_yearly_embeddings_dir(tmp_path):
    """Create a temporary directory with sample yearly embedding files."""
    embeddings_dir = tmp_path / "yearly_embeddings"
    embeddings_dir.mkdir()
    
    for year in [2018, 2019, 2020]:
        vecs = np.random.rand(50, 100).astype(np.float32)  # 50 tracks, 100 dims
        np.save(embeddings_dir / f"{year}.npy", vecs)
    
    return embeddings_dir

@pytest.fixture
def mock_api_response():
    """Return a mock API response object."""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self._json_data = json_data or {}
        
        def json(self):
            return self._json_data
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error {self.status_code}")
    
    return MockResponse
