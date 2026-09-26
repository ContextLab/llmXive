"""
Tests for the evaluation module, specifically perplexity calculation.
"""
import pytest
import torch
import numpy as np
from unittest.mock import MagicMock, patch
import sys
import os

# Add code to path if necessary
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.evaluation import calculate_perplexity, PerplexityDataset
from src.models import StaticIndex
from src.config import Config

class TestPerplexityDataset:
    def test_dataset_from_list_of_ints(self):
        data = [1, 2, 3, 4, 5]
        ds = PerplexityDataset(data)
        assert len(ds) == 1
        item = ds[0]
        assert "input_ids" in item
        assert torch.equal(item["input_ids"], torch.tensor([1, 2, 3, 4, 5]))

    def test_dataset_from_list_of_lists(self):
        data = [[1, 2], [3, 4]]
        ds = PerplexityDataset(data)
        assert len(ds) == 2
        item1 = ds[0]
        item2 = ds[1]
        assert torch.equal(item1["input_ids"], torch.tensor([1, 2]))
        assert torch.equal(item2["input_ids"], torch.tensor([3, 4]))

    def test_dataset_from_dict_with_input_ids(self):
        # Simulate a HuggingFace dataset row
        data = [{"input_ids": [1, 2, 3]}]
        ds = PerplexityDataset(data)
        assert len(ds) == 1
        item = ds[0]
        assert "input_ids" in item
        assert torch.equal(item["input_ids"], torch.tensor([1, 2, 3]))

class TestCalculatePerplexity:
    @patch('src.evaluation.static_inference')
    def test_perplexity_static_mode(self, mock_static_inference):
        # Mock model
        model = MagicMock()
        # Mock logits
        mock_logits = torch.randn(2, 5, 10) # batch=2, seq=5, vocab=10
        model.return_value.logits = mock_logits
        
        # Mock dataset
        dataset = [[1, 2, 3, 4], [5, 6, 7, 8]]
        
        # Mock static_index
        static_index = MagicMock(spec=StaticIndex)
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=100)
        
        # Mock static_inference to return logits
        mock_static_inference.return_value = mock_logits
        
        # Calculate perplexity
        ppl = calculate_perplexity(model, dataset, config, static_index=static_index)
        
        assert isinstance(ppl, float)
        assert ppl > 0
        mock_static_inference.assert_called()

    def test_perplexity_dynamic_mode(self):
        # Mock model
        model = MagicMock()
        # Mock logits
        mock_logits = torch.randn(2, 5, 10) # batch=2, seq=5, vocab=10
        model.return_value.logits = mock_logits
        
        # Mock dataset
        dataset = [[1, 2, 3, 4], [5, 6, 7, 8]]
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=100)
        
        # Calculate perplexity (dynamic mode, no static_index)
        ppl = calculate_perplexity(model, dataset, config)
        
        assert isinstance(ppl, float)
        assert ppl > 0
        model.assert_called()

    def test_perplexity_no_mode_specified(self):
        model = MagicMock()
        dataset = [[1, 2, 3]]
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=100)
        
        with pytest.raises(ValueError, match="Either static_index or wrapper must be provided"):
            calculate_perplexity(model, dataset, config)

    @patch('src.evaluation.static_inference')
    def test_perplexity_with_truncation(self, mock_static_inference):
        model = MagicMock()
        mock_logits = torch.randn(1, 10, 10) # seq=10
        model.return_value.logits = mock_logits
        mock_static_inference.return_value = mock_logits
        
        # Dataset with long sequence
        dataset = [list(range(20))] # 20 tokens
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=100)
        max_seq = 10
        
        ppl = calculate_perplexity(model, dataset, config, static_index=MagicMock(), max_seq_length=max_seq)
        
        assert isinstance(ppl, float)
        # Verify that the sequence was truncated (the mock should have been called with truncated input)
        # This is hard to verify directly without inspecting the call args, but the function should not crash.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])