"""
Tests for data_loader.py module.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import itertools
from datasets import Dataset

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_loader import (
    DataFetchError,
    load_pg19_streaming,
    estimate_token_count,
    filter_long_documents,
    get_document_iterator,
    save_filtered_dataset,
    run_filter_pipeline,
    sample_dataset,
    save_filtered_sampled_dataset
)

class TestTokenCounting:
    def test_estimate_token_count_basic(self):
        """Test basic token count estimation."""
        text = "Hello world"
        # 11 characters * 0.5 = 5.5 -> 5 tokens
        assert estimate_token_count(text) == 5

    def test_estimate_token_count_empty(self):
        """Test token count estimation for empty string."""
        assert estimate_token_count("") == 0

    def test_estimate_token_count_large(self):
        """Test token count estimation for large text."""
        text = "a" * 10000
        assert estimate_token_count(text) == 5000

class TestFiltering:
    def test_filter_long_documents(self):
        """Test filtering logic for long documents."""
        # Create mock documents
        docs = [
            {"text": "a" * 100},       # ~50 tokens
            {"text": "a" * 100000},    # ~50000 tokens
            {"text": "a" * 10000},     # ~5000 tokens
            {"text": ""},              # 0 tokens
        ]
        
        # Filter with threshold of 1000 tokens
        filtered = list(filter_long_documents(iter(docs), min_tokens=1000))
        
        # Only the 100000-char document should pass
        assert len(filtered) == 1
        assert len(filtered[0]["text"]) == 100000

    def test_filter_long_documents_empty(self):
        """Test filtering when no documents pass."""
        docs = [{"text": "a" * 100}]
        filtered = list(filter_long_documents(iter(docs), min_tokens=1000))
        assert len(filtered) == 0

class TestSampling:
    def test_sample_dataset_no_limit(self):
        """Test sampling without limit returns all."""
        docs = [{"text": f"doc_{i}"} for i in range(10)]
        result = sample_dataset(iter(docs))
        assert len(result) == 10

    def test_sample_dataset_with_limit(self):
        """Test sampling with max_samples limit."""
        docs = [{"text": f"doc_{i}"} for i in range(10)]
        result = sample_dataset(iter(docs), max_samples=5)
        assert len(result) == 5

    def test_sample_dataset_with_seed(self):
        """Test sampling with seed for reproducibility."""
        docs = [{"text": f"doc_{i}"} for i in range(10)]
        
        result1 = sample_dataset(iter(docs), max_samples=5, seed=42)
        result2 = sample_dataset(iter(docs), max_samples=5, seed=42)
        
        # Same seed should produce same results
        assert result1 == result2

    def test_sample_dataset_random_order(self):
        """Test that sampling with seed shuffles correctly."""
        docs = [{"text": f"doc_{i}"} for i in range(20)]
        
        result1 = sample_dataset(iter(docs), max_samples=5, seed=100)
        result2 = sample_dataset(iter(docs), max_samples=5, seed=200)
        
        # Different seeds should likely produce different results
        # (Not guaranteed, but highly probable)
        assert result1 != result2

class TestIntegration:
    @patch('src.data_loader.load_dataset')
    def test_save_filtered_sampled_dataset(self, mock_load_dataset):
        """Test end-to-end save of filtered and sampled dataset."""
        # Mock the dataset
        mock_docs = [{"text": "a" * 100000} for _ in range(10)]
        mock_dataset = Dataset.from_list(mock_docs)
        mock_load_dataset.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_sampled.parquet")
            
            # Run the function
            save_filtered_sampled_dataset(output_path, max_samples=5, seed=42)
            
            # Verify file was created
            assert os.path.exists(output_path)
            
            # Verify content
            loaded = Dataset.from_parquet(output_path)
            assert len(loaded) == 5

    @patch('src.data_loader.load_dataset')
    def test_filter_and_sample_pipeline(self, mock_load_dataset):
        """Test the full pipeline: load -> filter -> sample -> save."""
        # Create a mix of short and long documents
        mock_docs = [
            {"text": "a" * 100},       # Short
            {"text": "a" * 100000},    # Long
            {"text": "a" * 10000},     # Long
            {"text": "a" * 50},        # Short
        ]
        mock_dataset = Dataset.from_list(mock_docs)
        mock_load_dataset.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_final.parquet")
            
            # Run sampling (should filter to 2 long docs, then sample 1)
            save_filtered_sampled_dataset(output_path, max_samples=1, seed=42)
            
            assert os.path.exists(output_path)
            loaded = Dataset.from_parquet(output_path)
            assert len(loaded) == 1

    def test_data_fetch_error_raised(self):
        """Test that DataFetchError is raised on failed fetch."""
        with patch('src.data_loader.load_dataset', side_effect=Exception("Network error")):
            with pytest.raises(DataFetchError):
                list(load_pg19_streaming())