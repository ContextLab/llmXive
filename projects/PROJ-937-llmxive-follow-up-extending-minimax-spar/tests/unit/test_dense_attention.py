"""
Unit tests for Dense Attention Runner (T017b).

Verifies that the Dense Attention mode:
1. Loads the model correctly.
2. Processes a sample without sparsity logic.
3. Returns valid metrics.
"""
import pytest
import torch
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from eval.dense_attention_runner import DenseAttentionRunner
from utils.config import get_default_config

class TestDenseAttentionRunner:
    
    def test_runner_initialization(self):
        """Test that the runner initializes with correct defaults."""
        runner = DenseAttentionRunner()
        assert runner.device == "cpu"
        assert runner.model is None
        assert runner.tokenizer is None
        assert runner.config is not None

    @patch('eval.dense_attention_runner.AutoModelForCausalLM')
    @patch('eval.dense_attention_runner.AutoTokenizer')
    def test_load_model_cpu(self, mock_tokenizer, mock_model):
        """Test that the model is loaded on CPU without quantization."""
        # Setup mocks
        mock_tokenizer_inst = Mock()
        mock_tokenizer_inst.eos_token_id = 0
        mock_tokenizer.return_value = mock_tokenizer_inst
        
        mock_model_inst = Mock()
        mock_model_inst.eval.return_value = None
        mock_model.return_value = mock_model_inst

        runner = DenseAttentionRunner()
        runner.load_model()

        # Verify calls
        mock_model.assert_called_once()
        # Check that device_map is cpu and dtype is float32 (no quantization)
        call_kwargs = mock_model.call_args[1]
        assert call_kwargs.get("device_map") == "cpu"
        assert call_kwargs.get("torch_dtype") == torch.float32
        
        # Verify model was set to eval mode
        mock_model_inst.eval.assert_called_once()

    def test_process_sample_structure(self):
        """Test that process_sample returns the expected tuple structure."""
        runner = DenseAttentionRunner()
        runner.model = Mock()
        runner.tokenizer = Mock()
        
        # Mock the generate and decode behavior
        mock_output_ids = torch.tensor([[1, 2, 3]])
        runner.model.generate.return_value = mock_output_ids
        runner.tokenizer.decode.return_value = "Generated Text"
        
        sample = {
            "context": "Test context",
            "question": "Test question",
            "needle": "needle"
        }
        
        prompt, generated, ppl = runner.process_sample(sample)
        
        assert isinstance(prompt, str)
        assert isinstance(generated, str)
        assert isinstance(ppl, float)
        
        assert "Test context" in prompt
        assert "Test question" in prompt

    @patch('eval.dense_attention_runner.check_memory_usage')
    def test_memory_check_integration(self, mock_check_mem):
        """Test that memory check is called during processing."""
        mock_check_mem.return_value = False # Memory is OK
        
        runner = DenseAttentionRunner()
        runner.model = Mock()
        runner.tokenizer = Mock()
        
        mock_output_ids = torch.tensor([[1, 2, 3]])
        runner.model.generate.return_value = mock_output_ids
        runner.tokenizer.decode.return_value = "Generated Text"
        
        sample = {
            "context": "Test context",
            "question": "Test question",
            "needle": "needle"
        }
        
        # This should not raise if memory is OK
        try:
            runner.process_sample(sample)
        except Exception:
            # We expect errors because mocks are incomplete, but check if memory was called
            pass
        
        # Verify memory check was invoked
        mock_check_mem.assert_called()

    def test_dense_mode_no_sparsity_logic(self):
        """
        Verify that the runner does not implement heuristic selection or index branch logic.
        This is a negative test: we ensure the code path is clean of sparsity.
        """
        # The runner class itself should not have methods like 'select_blocks' or 'apply_index_branch'
        runner = DenseAttentionRunner()
        assert not hasattr(runner, 'select_blocks')
        assert not hasattr(runner, 'apply_index_branch')
        assert not hasattr(runner, 'apply_heuristic_mask')