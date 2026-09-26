import pytest
import torch
import numpy as np
from unittest.mock import MagicMock, patch
import sys
import os

# Add code to path if running from root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.inference import static_inference, _build_static_attention_mask
from src.models import StaticIndex

class TestStaticInference:
    """
    Contract test for Static-HiLS inference pipeline (T026).
    """

    def test_static_inference_builds_mask_correctly(self):
        """
        Verify that the attention mask is built using the static index mapping.
        """
        # Setup
        batch_size = 1
        seq_len = 4096
        chunk_size = 2048
        
        input_ids = torch.randint(100, 50000, (batch_size, seq_len))
        
        # Create a mock StaticIndex
        # We need a mapping for chunks 0, 1 (since 4096/2048 = 2 chunks)
        mock_index = MagicMock(spec=StaticIndex)
        mock_index.chunk_to_cluster = {
            "0": 10,
            "1": 10,
            "2": 11,
            "3": 11
        }
        mock_index.centroids = np.random.rand(100, 768)
        mock_index.k = 100
        
        # Run
        mask = _build_static_attention_mask(input_ids, mock_index, chunk_size)
        
        # Verify shape
        assert mask.shape == (batch_size, seq_len, seq_len)
        
        # Verify causal: lower triangle should be False (if diagonal is 0)
        # Our mask implementation: True for attend.
        # Causal means we can only attend to current and past tokens.
        # Check a specific point: token 0 should not attend to token 1
        assert mask[0, 0, 1] == False, "Causal mask violated: future token attended"
        
        # Verify local attention: token 0 should attend to token 1000 (same chunk)
        # chunk 0 covers 0..2047. 1000 is in chunk 0.
        assert mask[0, 0, 1000] == True, "Local attention failed"

    def test_static_inference_runs_model(self):
        """
        Verify that static_inference calls the model with the correct mask.
        """
        # Setup
        mock_model = MagicMock()
        mock_logits = torch.randn(1, 1024, 32000)
        mock_model.return_value.logits = mock_logits
        
        mock_index = MagicMock(spec=StaticIndex)
        mock_index.chunk_to_cluster = {"0": 1}
        mock_index.centroids = np.array([])
        mock_index.k = 10
        
        input_ids = torch.randint(100, 5000, (1, 1024))
        
        config = MagicMock()
        config.chunk_size = 2048
        
        # Run
        logits, metrics = static_inference(mock_model, mock_index, input_ids, config)
        
        # Verify model was called
        assert mock_model.called
        call_args = mock_model.call_args
        
        # Verify attention_mask was passed and is int type (standard transformers)
        assert 'attention_mask' in call_args.kwargs
        attn_mask = call_args.kwargs['attention_mask']
        assert attn_mask.dtype == torch.int32 or attn_mask.dtype == torch.int64
        
        # Verify output shape
        assert logits.shape == mock_logits.shape
        
        # Verify metrics
        assert 'latency_ms' in metrics
        assert 'sparsity_ratio' in metrics
        assert metrics['sparsity_ratio'] >= 0.0
        assert metrics['sparsity_ratio'] <= 1.0

    def test_static_inference_with_mismatched_chunks(self):
        """
        Verify behavior when input chunks are not in the index.
        """
        batch_size = 1
        seq_len = 4096
        chunk_size = 2048
        
        input_ids = torch.randint(100, 50000, (batch_size, seq_len))
        
        # Index only has chunk "0", but input has "0" and "1"
        mock_index = MagicMock(spec=StaticIndex)
        mock_index.chunk_to_cluster = {
            "0": 10
        }
        # Chunk 1 is missing
        
        mask = _build_static_attention_mask(input_ids, mock_index, chunk_size)
        
        # Should still run without crashing
        assert mask.shape == (batch_size, seq_len, seq_len)
        
        # Local attention for chunk 1 should still work (same chunk)
        # Chunk 1 is tokens 2048..4095
        # Token 2048 should attend to 2049
        assert mask[0, 2048, 2049] == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
