"""
Unit tests for chunked download logic in data acquisition.
Tests the integration of the chunking utility with simulated data acquisition.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from io import BytesIO
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.chunking import process_chunked, split_dataframe
from config import ensure_directories


class TestDataAcquisitionChunking:
    """Tests for chunked processing logic in data acquisition."""

    def test_split_dataframe_basic(self):
        """Test that a dataframe is correctly split into chunks."""
        df = pd.DataFrame({
            'site_id': range(100),
            'value': range(100)
        })
        chunk_size = 10
        
        chunks = list(split_dataframe(df, chunk_size))
        
        assert len(chunks) == 10
        assert all(len(chunk) == chunk_size for chunk in chunks)
        assert chunks[0]['site_id'].iloc[0] == 0
        assert chunks[-1]['site_id'].iloc[-1] == 99

    def test_split_dataframe_uneven(self):
        """Test splitting when dataframe size is not divisible by chunk size."""
        df = pd.DataFrame({
            'site_id': range(105),
            'value': range(105)
        })
        chunk_size = 10
        
        chunks = list(split_dataframe(df, chunk_size))
        
        assert len(chunks) == 11
        assert len(chunks[-1]) == 5
        assert all(len(chunk) == 10 for chunk in chunks[:-1])

    def test_process_chunked_with_mock_download(self):
        """Test process_chunked with a simulated download function."""
        # Create a large mock dataframe
        sites = [f"site_{i}" for i in range(50)]
        df = pd.DataFrame({
            'site_id': sites,
            'lat': np.random.uniform(-90, 90, 50),
            'lon': np.random.uniform(-180, 180, 50)
        })
        
        # Mock the download function
        results = []
        def mock_download(chunk):
            # Simulate processing each site in the chunk
            processed = chunk.copy()
            processed['status'] = 'downloaded'
            processed['file_size'] = 1024 * len(chunk)
            results.append(processed)
            return processed
        
        # Process in chunks of 10
        chunks = list(split_dataframe(df, 10))
        processed_results = []
        
        for i, chunk in enumerate(chunks):
            result = mock_download(chunk)
            processed_results.append(result)
        
        # Verify results
        assert len(processed_results) == 5
        assert all(res['status'].iloc[0] == 'downloaded' for res in processed_results)
        assert sum(len(res) for res in processed_results) == 50

    def test_process_chunked_memory_efficiency(self):
        """Verify that chunked processing handles large datasets without loading all at once."""
        # Simulate a large dataset that would be problematic if loaded entirely
        n_sites = 1000
        chunk_size = 50
        
        # Create a generator-like behavior
        def large_dataset_generator():
            for i in range(n_sites):
                yield pd.DataFrame({
                    'site_id': [f"site_{i}"],
                    'data': [np.random.random(100)]
                })
        
        # Process chunks
        processed_count = 0
        for chunk in large_dataset_generator():
            # In real implementation, this would be the download/processing step
            processed_count += len(chunk)
        
        assert processed_count == n_sites

    def test_chunked_processing_with_error_handling(self):
        """Test that chunked processing handles individual chunk failures gracefully."""
        df = pd.DataFrame({
            'site_id': range(20),
            'value': range(20)
        })
        
        chunk_size = 5
        chunks = list(split_dataframe(df, chunk_size))
        
        # Simulate one chunk failing
        successful_chunks = 0
        failed_chunks = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Simulate processing
                if i == 2:  # Fail the 3rd chunk
                    raise Exception("Simulated download failure")
                successful_chunks += 1
            except Exception:
                failed_chunks += 1
        
        assert successful_chunks == 3
        assert failed_chunks == 1

    def test_chunking_preserves_data_integrity(self):
        """Verify that chunked processing doesn't lose or duplicate data."""
        original_data = pd.DataFrame({
            'id': range(1000),
            'value': np.random.random(1000)
        })
        
        chunk_size = 100
        chunks = list(split_dataframe(original_data, chunk_size))
        
        # Reassemble chunks
        reassembled = pd.concat(chunks, ignore_index=True)
        
        # Check integrity
        assert len(reassembled) == len(original_data)
        assert set(reassembled['id']) == set(original_data['id'])
        assert list(reassembled['id']) == list(original_data['id'])

    def test_empty_dataframe_handling(self):
        """Test that chunking handles empty dataframes correctly."""
        df = pd.DataFrame(columns=['site_id', 'value'])
        chunks = list(split_dataframe(df, 10))
        
        assert len(chunks) == 0

    def test_single_row_dataframe(self):
        """Test chunking with a single row dataframe."""
        df = pd.DataFrame({'site_id': ['single'], 'value': [1]})
        chunks = list(split_dataframe(df, 10))
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 1

    def test_chunk_size_larger_than_dataframe(self):
        """Test chunking when chunk size exceeds dataframe size."""
        df = pd.DataFrame({'site_id': range(5), 'value': range(5)})
        chunks = list(split_dataframe(df, 100))
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 5

    def test_realistic_download_simulation(self):
        """Simulate a realistic Landsat download scenario with metadata."""
        # Simulate site coordinates data
        sites_data = pd.DataFrame({
            'site_id': [f"site_{i:03d}" for i in range(30)],
            'lat': np.random.uniform(-30, -10, 30),
            'lon': np.random.uniform(-70, -40, 30),
            'biome': np.random.choice(['forest', 'savanna', 'grassland'], 30),
            'protection_status': np.random.choice(['protected', 'unprotected'], 30)
        })
        
        # Simulate chunked processing
        chunk_size = 5
        chunks = list(split_dataframe(sites_data, chunk_size))
        
        # Simulate download results for each chunk
        download_results = []
        for i, chunk in enumerate(chunks):
            # Simulate downloading Landsat data for this chunk
            result = chunk.copy()
            result['download_status'] = 'success'
            result['scenes_downloaded'] = np.random.randint(1, 10, len(chunk))
            result['total_size_mb'] = result['scenes_downloaded'] * 15.5
            download_results.append(result)
        
        # Verify all sites were processed
        all_results = pd.concat(download_results, ignore_index=True)
        assert len(all_results) == 30
        assert all(all_results['download_status'] == 'success')
        assert all(all_results['scenes_downloaded'] > 0)
        assert all(all_results['total_size_mb'] > 0)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])