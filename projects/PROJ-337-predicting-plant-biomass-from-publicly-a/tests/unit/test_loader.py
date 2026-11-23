"""
Unit tests for the ChunkedHyperspectralLoader.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.loader import ChunkedDataBatch, ChunkedHyperspectralLoader
from code.utils.timer import get_current_memory_usage_mb

@pytest.fixture
def temp_csv_data():
    """Creates a temporary CSV file with mock hyperspectral data for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir)
        # Create a synthetic dataset
        n_samples = 100
        n_bands = 10
        
        # Generate random spectral data (0-1 range for reflectance)
        spectral_data = np.random.rand(n_samples, n_bands)
        # Generate random biomass labels
        biomass = np.random.rand(n_samples) * 100
        # Generate site IDs
        site_ids = np.array([f"site_{i % 5}" for i in range(n_samples)])
        
        # Create DataFrame
        df = pd.DataFrame(spectral_data, columns=[f"band_{i}" for i in range(n_bands)])
        df["biomass"] = biomass
        df["site_id"] = site_ids
        
        # Save to CSV
        csv_path = data_path / "test_data.csv"
        df.to_csv(csv_path, index=False)
        
        yield data_path
        
        # Cleanup handled by TemporaryDirectory context manager

def test_chunked_loader_initialization(temp_csv_data):
    """Test that the loader initializes correctly."""
    loader = ChunkedHyperspectralLoader(data_path=temp_csv_data, chunk_size=20)
    assert loader.data_path == temp_csv_data
    assert loader.chunk_size == 20
    assert loader.max_memory_gb == 7.0
    assert len(loader.data_files) == 1

def test_chunked_loader_batches(temp_csv_data):
    """Test that the loader yields correct batch sizes and data types."""
    loader = ChunkedHyperspectralLoader(data_path=temp_csv_data, chunk_size=30)
    
    batches = list(loader.load_batches())
    
    assert len(batches) > 0
    assert all(isinstance(b, ChunkedDataBatch) for b in batches)
    
    # Check first batch
    first_batch = batches[0]
    assert isinstance(first_batch.spectral_data, np.ndarray)
    assert isinstance(first_batch.biomass_labels, np.ndarray)
    assert isinstance(first_batch.site_ids, np.ndarray)
    
    # Check shapes
    expected_chunk_size = 30
    # Last batch might be smaller
    assert first_batch.shape[0] <= expected_chunk_size
    assert first_batch.shape[1] == 10  # 10 bands

def test_chunked_loader_memory_check(temp_csv_data, monkeypatch):
    """Test that memory check logic works."""
    # Mock get_current_memory_usage_mb to return a high value
    def mock_high_memory():
        return 8000  # 8GB
    
    monkeypatch.setattr("code.data.loader.get_current_memory_usage_mb", mock_high_memory)
    
    loader = ChunkedHyperspectralLoader(data_path=temp_csv_data, chunk_size=10, max_memory_gb=7.0)
    
    # Should return False when memory is high
    assert loader._check_memory_usage() is False

def test_get_dataset_stats(temp_csv_data):
    """Test that dataset statistics are computed correctly."""
    loader = ChunkedHyperspectralLoader(data_path=temp_csv_data, chunk_size=50)
    stats = loader.get_dataset_stats()
    
    assert "num_samples" in stats
    assert "num_bands" in stats
    assert "band_stats" in stats
    assert "label_stats" in stats
    
    assert stats["num_samples"] == 100
    assert stats["num_bands"] == 10
    assert "mean" in stats["band_stats"]
    assert "std" in stats["band_stats"]
    assert "min" in stats["band_stats"]
    assert "max" in stats["band_stats"]

def test_loader_file_not_found():
    """Test that FileNotFoundError is raised for missing path."""
    with pytest.raises(FileNotFoundError):
        ChunkedHyperspectralLoader(data_path="/nonexistent/path")

def test_loader_no_files():
    """Test that FileNotFoundError is raised if no data files found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir)
        # Create empty directory
        with pytest.raises(FileNotFoundError):
            ChunkedHyperspectralLoader(data_path=data_path)
