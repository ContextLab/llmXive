"""Unit tests for data loader integrity."""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from src.llmxive.data_loader import GSM8KLoader
from src.llmxive.config import Config
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

class TestStalenessQueueIntegrity:
    """Tests for data loader integrity."""
    
    @patch('src.llmxive.data_loader.load_dataset')
    def test_load_dataset_success(self, mock_load):
        """Test successful dataset loading."""
        mock_load.return_value = MagicMock(__iter__=lambda self: iter([]))
        
        loader = GSM8KLoader(split="train", streaming=True)
        assert loader is not None
    
    @patch('src.llmxive.data_loader.load_dataset')
    def test_load_dataset_failure_raises_error(self, mock_load):
        """Test that dataset load failure raises DATA_INTEGRITY_ERROR."""
        mock_load.side_effect = Exception("Network error")
        
        with pytest.raises(DATA_INTEGRITY_ERROR):
            GSM8KLoader(split="train", streaming=True)
    
    def test_verify_no_overlap_no_overlap(self):
        """Test that no overlap returns True."""
        loader = GSM8KLoader(split="train", streaming=False)
        training_indices = {1, 2, 3}
        test_indices = {4, 5, 6}
        
        assert loader.verify_no_overlap(training_indices, test_indices)
    
    def test_verify_no_overlap_with_overlap(self):
        """Test that overlap raises DATA_INTEGRITY_ERROR."""
        loader = GSM8KLoader(split="train", streaming=False)
        training_indices = {1, 2, 3}
        test_indices = {3, 4, 5}
        
        with pytest.raises(DATA_INTEGRITY_ERROR):
            loader.verify_no_overlap(training_indices, test_indices)

class TestIndexRetrieval:
    """Tests for index retrieval functionality."""
    
    def test_get_sample_streaming(self):
        """Test getting sample from streaming dataset."""
        loader = GSM8KLoader(split="train", streaming=True)
        sample = loader.get_sample(n=5)
        assert len(sample) <= 5
